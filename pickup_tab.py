from PyQt5.QtWidgets import QWidget
from PyQt5 import uic
import cv2
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
#this file should make the elements in the "pickup_tabWidget" functional

import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QVBoxLayout, QWidget, QSlider, QLineEdit, QHBoxLayout, QPushButton, QRadioButton, QMessageBox, QFileDialog, QTabWidget, QLabel, QComboBox, QCheckBox,QSizePolicy
from PyQt5 import uic, QtWidgets
import serial.tools.list_ports
import time
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPainter, QBrush, QPen
from PyQt5 import QtTest

import argparse
import json
import os
import time
import cv2
import numpy as np
# start by importing the necessary packages
import matplotlib.pyplot as plt
import json
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QImage
import pyautogui

from PIL import Image

class PickupTab(QWidget):
    def __init__(self, image_frame_manager, settings_tab):
        super().__init__()
        uic.loadUi("pickup_tab.ui", self)
        self.image_frame_manager = image_frame_manager
        self.settings_tab=settings_tab
        self.binary_mask = None
        self.binary_mask_image = None #once the segment btn is pressed this will be generated

        self.settings_tab.get_temperature() # this will use the device initialized in the settings tab
        #note: you can put "if self.settings_tab.temperature_controller:" do avoid crashing if the user forgets to initialize the device
        #self.settings_tab.set_temperature(-10)

        #self.pick_btn = self.findChild(QPushButton, "select_target_pick_btn")
        #why do I need to this and rename my button? I can just use clicked ethod on it directly, right?

        self.select_target_pick_btn.clicked.connect(self.segment_target)
        self.start_pickup_btn.clicked.connect(self.start_pickup_sequence)

    def show_pixmap(self,image):
                # Convert to QImage and show in QLabel
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        # Optional: scale it to fit the QLabel
        pixmap = pixmap.scaled(self.image_pick.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.image_pick.setPixmap(pixmap)
        self.image_pick.show()

    def segment_target(self):
        start = time.time()
        segmented_image, binary_mask=self.image_frame_manager.run_target_sam()
        self.segmentation_overlay = segmented_image
        self.binary_mask = binary_mask
        self.binary_mask_image = cv2.cvtColor(binary_mask, cv2.COLOR_GRAY2RGB)
        self.show_pixmap(self.binary_mask_image)
        end = time.time()
        length = end - start
        #print("It took", length, "seconds!")
        image=self.image_frame_manager.get_screenshot() #comment it
        avg_color=self.get_avg_color(image, binary_mask) #comment it
        #print("avg segment color: ", avg_color ) #comment it
        return


    def get_avg_color(self, image, mask):
        masked_pixels = image[mask > 0]
        blurred = cv2.blur(masked_pixels.astype(np.float32), (1, 1))
        return np.mean(blurred, axis=0)

    def is_color_changed(self, color_a, color_b, threshold=20.0):
        return np.linalg.norm(np.array(color_a) - np.array(color_b)) > threshold


    def get_edge_and_corner_regions_split(self, image, edge_width=30, corner_depth=50):
        h, w, _ = image.shape
        regions = []

        top = image[0:edge_width, :, :].reshape(-1, 3)
        bottom = image[-edge_width:, :, :].reshape(-1, 3)
        left = image[:, 0:edge_width, :].reshape(-1, 3)
        right = image[:, -edge_width:, :].reshape(-1, 3)
        regions.extend([top, bottom, left, right])

        mask = np.tri(corner_depth, corner_depth, dtype=bool)
        regions.append(image[0:corner_depth, 0:corner_depth, :][mask])  # top-left

        mask = np.fliplr(np.tri(corner_depth, corner_depth, dtype=bool))
        regions.append(image[0:corner_depth, -corner_depth:, :][mask])  # top-right

        regions.append(np.flipud(image[-corner_depth:, 0:corner_depth, :])[mask])  # bottom-left
        mask = np.tri(corner_depth, corner_depth, dtype=bool)
        regions.append(np.flipud(image[-corner_depth:, -corner_depth:, :])[mask])  # bottom-right

        return regions  # List of (N, 3) arrays, 8 regions total

    def wait_until_reached(self, axis_id, target_pos, tolerance=0.1):
        while True:
            ret, pos_list = self.settings_tab.mccard.MoCtrCard_GetAxisPos(axis_id)
            current_pos = pos_list[0]
            if abs(current_pos - target_pos) <= tolerance:
                print(f"✅ Axis {axis_id} reached {target_pos:.2f}")
                break
            QtTest.QTest.qWait(100)
            #print(pos_list)


    def start_pickup_sequence(self):
        """
        Main pickup workflow orchestrator.
        Reads all parameters from UI and executes the transfer sequence step by step.
        """
        print("🚀 Starting pickup sequence...\n")
        
        # Read all UI parameters
        params = self._get_ui_params()
        
        # Validate preconditions
        if self.binary_mask is None:
            print("❌ Error: No target selected. Please click 'Select Target' first.")
            return
        if self.settings_tab.mccard is None:
            print("❌ Error: Motor controller not initialized. Check settings.")
            return
        
        try:
            # Step 1: Move to safe unengaged Z position
            print("=" * 60)
            print("STEP 1: Moving to unengaged Z position")
            print("=" * 60)
            self._move_to_unengaged_z(params)
            
            # Step 2: Optional preheat
            if params['preheat_chk']:
                print("\n" + "=" * 60)
                print(f"STEP 2: Preheating to {params['preheat_spin']}°C")
                print("=" * 60)
                self.settings_tab.set_temperature(params['preheat_spin'])
                QtTest.QTest.qWait(2000)  # Short wait for temperature stabilization
            
            # Step 3: Approach slowly until engagement detected
            print("\n" + "=" * 60)
            print(f"STEP 3: Approaching at {params['preengagedSPD_spin']} speed")
            print("=" * 60)
            engagement_image = self._approach_until_engagement(params)
            
            # Step 4: Optional further approach with even slower speed (until ~flake_aura distance)
            if params['engagedSPD_chk']:
                print("\n" + "=" * 60)
                print(f"STEP 4: Further approach at {params['engagedSPD_spin']} speed")
                print("=" * 60)
                self._approach_flake_aura(params)
            
            # Step 5: Check action radio buttons (push or heat)
            print("\n" + "=" * 60)
            print("STEP 5: Executing action (push or heat)")
            print("=" * 60)
            
            # Get current image to check flake coverage
            current_image = self.image_frame_manager.get_screenshot()
            current_color = self.get_avg_color(current_image, self.binary_mask)
            
            if params['push_ON_rad']:
                print("→ PUSH mode: continuing to cover flake completely")
                self._push_through_flake(params, current_image)
            elif params['heat_ON_rad']:
                print("→ HEAT mode: halting for heat cycle")
            else:
                print("→ No action selected (push/heat off)")
            
            # Step 6: Heat cycle (heat, wait, cool)
            if params['heat_chk'] or params['cool_chk']:
                print("\n" + "=" * 60)
                print("STEP 6: Heat cycle")
                print("=" * 60)
                self._heat_cycle(params)
            
            # Step 7: Retract with adaptive speeds
            print("\n" + "=" * 60)
            print("STEP 7: Retraction with adaptive speed")
            print("=" * 60)
            self._retract_with_dynamic_speed(params, current_image)
            
            print("\n" + "=" * 60)
            print("✅ Pickup sequence completed!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Sequence error: {e}")
            import traceback
            traceback.print_exc()

    # ========== UI Parameter Reader ==========
    def _get_ui_params(self):
        """Read all UI spinboxes, checkboxes, and radio buttons."""
        return {
            # Unengaged position
            'unengagedZ': float(self.unengagedZ_spin.value()),
            'unengagedSPD': float(self.unengagedSPD_spin.value()),
            
            # Preheat
            'preheat_chk': self.preheat_chk.isChecked(),
            'preheat_spin': float(self.preheat_spin.value()),
            
            # Pre-engagement approach
            'preengagedSPD_spin': float(self.preengagedSPD_spin.value()),
            
            # Post-engagement approach
            'engagedSPD_chk': self.engagedSPD_chk.isChecked(),
            'engagedSPD_spin': float(self.engagedSPD_spin.value()),
            
            # Flake aura threshold
            'flake_aura_spin': float(self.flake_aura_spin.value()),
            
            # Action during engagement
            'push_ON_rad': self.push_ON_rad.isChecked(),
            'heat_ON_rad': self.heat_ON_rad.isChecked(),
            'flakeSPD_spin': float(self.flakeSPD_spin.value()),
            
            # Heat cycle
            'heat_chk': self.heat_chk.isChecked(),
            'heat_spin': float(self.heat_spin.value()),
            
            # Wait
            'wait_chk': self.wait_chk.isChecked(),
            'wait_spin': float(self.wait_spin.value()),
            
            # Cool cycle
            'cool_chk': self.cool_chk.isChecked(),
            'cool_spin': float(self.cool_spin.value()),
            
            # Keep-on feedback during cooling
            'keepON_chk': self.keepON_chk.isChecked(),
            'keepON_spin': float(self.keepON_spin.value()),
        }

    # ========== Movement Primitives ==========
    def _move_to_unengaged_z(self, params):
        """Move Z axis to safe unengaged position."""
        target_z = params['unengagedZ']
        speed = params['unengagedSPD']
        
        print(f"Moving Z to {target_z} mm with speed {speed}...")
        self.settings_tab.mccard.MoCtrCard_MCrlAxisAbsMove(AxisId=2, PosCmnd=target_z, VCmnd=speed)
        self.wait_until_reached(axis_id=2, target_pos=target_z)
        print(f"✅ Reached unengaged Z: {target_z} mm\n")

    def _approach_until_engagement(self, params):
        """Descend slowly until film/slide engages with chip (color change detected)."""
        speed = params['preengagedSPD_spin']
        print(f"Descending at speed {speed}, monitoring edge/corner regions...")
        
        # Capture baseline image and region colors
        baseline_image = self.image_frame_manager.get_screenshot()
        baseline_regions = self.get_edge_and_corner_regions_split(baseline_image)
        regions_changed = [False] * len(baseline_regions)
        
        # Descend until at least one region shows a color change
        step_count = 0
        while not any(regions_changed):
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)
            
            for i, (base, curr) in enumerate(zip(baseline_regions, current_regions)):
                if not regions_changed[i]:
                    if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                        regions_changed[i] = True
                        print(f"  🟥 Region {i} changed — ENGAGEMENT detected!")
            
            if not any(regions_changed):
                # Relative move down
                self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.5, speed, 0)
                QtTest.QTest.qWait(500)
                step_count += 1
        
        print(f"✅ Film/slide is engaged after {step_count} steps\n")
        return baseline_image

    def _approach_flake_aura(self, params):
        """Continue approaching at slower speed until distance ~flake_aura from target."""
        speed = params['engagedSPD_spin']
        flake_aura = params['flake_aura_spin']
        
        print(f"Approaching target flake aura at speed {speed}...")
        print(f"Will approach until ~{flake_aura} pixels from target center...")
        
        # Capture new baseline for this phase
        baseline_image = self.image_frame_manager.get_screenshot()
        baseline_regions = self.get_edge_and_corner_regions_split(baseline_image)
        regions_changed = [False] * len(baseline_regions)
        
        # Continue descending slowly until multiple regions have changed significantly
        step_count = 0
        target_changed_regions = 4  # Approximately 50% of regions
        
        while regions_changed.count(True) < target_changed_regions:
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)
            
            for i, (base, curr) in enumerate(zip(baseline_regions, current_regions)):
                if not regions_changed[i]:
                    if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                        regions_changed[i] = True
                        print(f"  ✅ Region {i} changed")
            
            if regions_changed.count(True) < target_changed_regions:
                self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.2, speed, 0)
                QtTest.QTest.qWait(500)
                step_count += 1
        
        print(f"✅ Approached flake aura after {step_count} steps\n")

    def _push_through_flake(self, params, reference_image):
        """Continue approaching to cover flake completely plus the aura distance."""
        speed = params['flakeSPD_spin']
        flake_aura = params['flake_aura_spin']
        
        print(f"Pushing through flake at speed {speed}...")
        print(f"Will cover completely and extend by {flake_aura} pixels...")
        
        baseline_regions = self.get_edge_and_corner_regions_split(reference_image)
        max_regions_changed = [False] * len(baseline_regions)
        
        step_count = 0
        while max_regions_changed.count(True) < 6:  # Most regions have changed dramatically
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)
            
            for i, (base, curr) in enumerate(zip(baseline_regions, current_regions)):
                if not max_regions_changed[i]:
                    if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=60):
                        max_regions_changed[i] = True
                        print(f"  🔴 Region {i} heavily changed")
            
            if max_regions_changed.count(True) < 6:
                self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.2, speed, 0)
                QtTest.QTest.qWait(500)
                step_count += 1
        
        print(f"✅ Flake fully covered after {step_count} steps\n")

    def _heat_cycle(self, params):
        """Execute optional heat, wait, and cool phases with optional keep-on feedback."""
        # Heating phase
        if params['heat_chk']:
            heat_temp = params['heat_spin']
            print(f"🔥 Heating to {heat_temp}°C...")
            self.settings_tab.set_temperature(heat_temp)
            QtTest.QTest.qWait(1000)  # Initial wait for ramp
            print(f"✅ Heating phase started")
        
        # Wait phase
        if params['wait_chk']:
            wait_time = int(params['wait_spin'] * 1000)  # Convert to ms
            print(f"⏱ Waiting {params['wait_spin']} sec...")
            QtTest.QTest.qWait(wait_time)
            print(f"✅ Wait complete")
        
        # Cooling phase with optional keep-on feedback loop
        if params['cool_chk']:
            cool_temp = params['cool_spin']
            print(f"❄️ Cooling to {cool_temp}°C...")
            self.settings_tab.set_temperature(cool_temp)
            
            # If keep-on is enabled, maintain flake coverage during cool-down
            if params['keepON_chk']:
                print(f"🔄 Feedback loop: keeping flake covered during cool-down...")
                target_temp = params['keepON_spin']
                baseline_image = self.image_frame_manager.get_screenshot()
                baseline_regions = self.get_edge_and_corner_regions_split(baseline_image)
                
                # Monitor and maintain coverage
                step_count = 0
                while True:
                    current_temp = self.settings_tab.get_temperature()
                    if current_temp <= target_temp:
                        print(f"✅ Reached target cool-down temp {target_temp}°C")
                        break
                    
                    # Check if coverage is still maintained
                    current_image = self.image_frame_manager.get_screenshot()
                    current_regions = self.get_edge_and_corner_regions_split(current_image)
                    
                    regions_still_changed = 0
                    for base, curr in zip(baseline_regions, current_regions):
                        if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                            regions_still_changed += 1
                    
                    # If losing coverage, push down to maintain
                    if regions_still_changed < 4:
                        print(f"  ⚠️ Coverage reducing, pushing down...")
                        self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.1, 0.05, 0)
                    
                    QtTest.QTest.qWait(1000)
                    step_count += 1
                
                print(f"✅ Keep-on loop completed after {step_count} iterations")
            else:
                # Passive cool-down
                QtTest.QTest.qWait(2000)
                print(f"✅ Cooling phase complete")

    def _retract_with_dynamic_speed(self, params, reference_image):
        """
        Retract Z axis with speed adaptive to coverage state:
        - If flake still covered: use flakeSPD_spin
        - If engaged but uncovered: use engagedSPD_spin
        - If unengaged: use preengagedSPD_spin
        """
        target_z = params['unengagedZ']
        flake_speed = params['flakeSPD_spin']
        engaged_speed = params['engagedSPD_spin']
        unengaged_speed = params['preengagedSPD_spin']
        
        print(f"Retracting to unengaged Z: {target_z} mm")
        print(f"  - Flake covered speed: {flake_speed}")
        print(f"  - Engaged speed: {engaged_speed}")
        print(f"  - Unengaged speed: {unengaged_speed}\n")
        
        baseline_regions = self.get_edge_and_corner_regions_split(reference_image)
        step_count = 0
        
        # Phase 1: Retract while flake is still covered (use flakeSPD)
        phase1_active = True
        while phase1_active:
            current_image = self.image_frame_manager.get_screenshot()
            baseline_regions = self.get_edge_and_corner_regions_split(current_image)
            
            # Re-baseline to check coverage state
            next_image = self.image_frame_manager.get_screenshot()
            next_regions = self.get_edge_and_corner_regions_split(next_image)
            
            regions_still_show_coverage = 0
            for base, nxt in zip(baseline_regions, next_regions):
                if self.is_color_changed(np.mean(base, axis=0), np.mean(nxt, axis=0), threshold=40):
                    regions_still_show_coverage += 1
            
            if regions_still_show_coverage < 2:  # Flake uncovered
                print(f"  → Flake uncovered. Switching to engaged/unengaged retraction.")
                phase1_active = False
            else:
                self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, 0.2, flake_speed, 0)
                QtTest.QTest.qWait(500)
                step_count += 1
        
        # Phase 2: Retract while engaged but uncovered (use engagedSPD)
        phase2_active = True
        while phase2_active:
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)
            
            # Check if still engaged
            any_region_changed = False
            for base, curr in zip(baseline_regions, current_regions):
                if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                    any_region_changed = True
                    break
            
            if not any_region_changed:  # Disengaged
                print(f"  → Film/slide disengaged. Reaching unengaged position.")
                phase2_active = False
            else:
                self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, 0.3, engaged_speed, 0)
                QtTest.QTest.qWait(500)
                step_count += 1
        
        # Phase 3: Final retraction to unengaged Z (use unengagedSPD)
        print(f"  → Moving to safe unengaged Z at speed {unengaged_speed}...")
        self.settings_tab.mccard.MoCtrCard_MCrlAxisAbsMove(AxisId=2, PosCmnd=target_z, VCmnd=unengaged_speed)
        self.wait_until_reached(axis_id=2, target_pos=target_z)
        
        print(f"✅ Retraction complete. Back at unengaged Z.\n")

