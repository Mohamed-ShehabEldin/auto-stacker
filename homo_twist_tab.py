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

class HomoTwistTab(QWidget):
    def __init__(self, image_frame_manager, settings_tab):
        super().__init__()
        uic.loadUi("homo_twist_tab.ui", self)
        self.image_frame_manager = image_frame_manager
        self.settings_tab=settings_tab
        self.target_binary_mask = None
        self.target_binary_mask_image = None #once the segment btn is pressed this will be generated
        self.receiver_binary_mask = None
        self.receiver_binary_mask_image = None #once the segment btn is pressed this will be generated

        self.settings_tab.get_temperature() # this will use the device initialized in the settings tab
        #note: you can put "if self.settings_tab.temperature_controller:" do avoid crashing if the user forgets to initialize the device
        #self.settings_tab.set_temperature(-10)

        #self.pick_btn = self.findChild(QPushButton, "select_target_pick_btn")
        #why do I need to this and rename my button? I can just use clicked ethod on it directly, right?

        self.select_target_pick_btn.clicked.connect(self.segment_target)
        self.select_receiver_btn.clicked.connect(self.segment_receiver)
        self.start_homotwist_btn.clicked.connect(self.start_twisting_sequence)

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
        target_segmented_image, target_binary_mask=self.image_frame_manager.run_target_sam()
        self.target_segmentation_overlay = target_segmented_image
        self.target_binary_mask = target_binary_mask
        self.target_binary_mask_image = cv2.cvtColor(target_binary_mask, cv2.COLOR_GRAY2RGB)
        self.show_pixmap(self.target_binary_mask_image)
        end = time.time()
        length = end - start
        #print("It took", length, "seconds!")
        image=self.image_frame_manager.get_screenshot()
        avg_color=self.get_avg_color(image, target_binary_mask)
        #print("avg segment color: ", avg_color )
        return
    
    def segment_receiver(self):
        start = time.time()
        receiver_segmented_image, receiver_binary_mask=self.image_frame_manager.run_receiver_sam()
        self.receiver_segmentation_overlay = receiver_segmented_image
        self.receiver_binary_mask = receiver_binary_mask
        self.receiver_binary_mask_image = cv2.cvtColor(receiver_binary_mask, cv2.COLOR_GRAY2RGB)
        self.show_pixmap(self.receiver_binary_mask_image)
        end = time.time()
        length = end - start
        #print("It took", length, "seconds!")
        image=self.image_frame_manager.get_screenshot()
        avg_color=self.get_avg_color(image, receiver_binary_mask)
        #print("avg segment color: ", avg_color )
        return
    
    def start_twisting_sequence(self):
        print("🔁 Starting Homo Twisting sequence...")

        if self.target_binary_mask is None or self.receiver_binary_mask is None:
            print("⚠️ Please segment both target and receiver flakes first.")
            return

        # Move receiver to cover half the target — placeholder
        #dx, dy = self.move_receiver(self.receiver_mask, self.target_binary_mask)
        #print(f"🛠 (Manual) Move receiver to overlap half of target: dx={dx}, dy={dy}")

        # First pickup
        print("📥 Starting first pickup...")
        self.start_pickup_sequence()

        # # Rotate the stage
        # print("🔄 Rotating stage")
        # twist_angle=float(self.twist_angel_txt.toPlainText())
        # #self.settings_tab.pyMcc.rotate_stage(twist_angle)  # replace with actual rotation call
        # ret, current_angle_list = self.settings_tab.mccard.MoCtrCard_GetAxisPos(1)
        # current_angle = current_angle_list[0]
        # target_angle=current_angle+twist_angle
        # self.settings_tab.mccard.MoCtrCard_MCrlAxisAbsMove(1,target_angle,1,0)
        # self.wait_until_reached(axis_id=1, target_pos=target_angle)

        # # Estimate new position of target_half_2
        # #dx2, dy2 = self.rotate_target(target_angle=180, step_angle=10)
        # #print(f"🧭 (Manual) Adjust receiver to second half: dx={dx2}, dy={dy2}")

        # # Second pickup
        # print("📥 Starting second pickup...")
        # self.start_pickup_sequence()

        # print("✅ Homo Twist complete.")

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


    def start_pickup_sequence(self):
        print("🚀 Starting pickup sequence...")
        hot_txt=float(self.hot_txt.toPlainText())
        cold_txt=float(self.cold_txt.toPlainText())

        speed1, speed2, speed3 = 2, 0.5, 0.1
        speed4, speed5, speed6 = 0.1, 0.5, 4
        distance1, distance2 = 70,70 # safe minimum distance, distance after pickup
        temperature1, temperature2 = 130, 10
        threshold = 10.0 #if the difference between RGB is more than that, we consider color changed

        image = self.image_frame_manager.get_screenshot()
        color1 = self.get_avg_color(image, self.target_binary_mask)
        print(f"🎯 color1 saved: {color1}")

        print(f"⬇️ Moving down to {distance1} with speed {speed1}")
        self.settings_tab.mccard.MoCtrCard_MCrlAxisAbsMove(AxisId=2, PosCmnd=distance1, VCmnd=speed1)  #distance1, speed1
        self.wait_until_reached(axis_id=2, target_pos=distance1)

        #QtTest.QTest.qWait(2000) # this should be better than time.sleep
        #self.settings_tab.move_z(speed1)
        #time.sleep(1)
        image_pil = Image.fromarray(image)  # Convert NumPy → PIL
        image_pil.save("color1.png")

        baseline_regions = self.get_edge_and_corner_regions_split(image)
        regions_changed = [False] * len(baseline_regions)

        print("👁 Monitoring each region...")

        while True:
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)

            for i, (base, curr) in enumerate(zip(baseline_regions, current_regions)):
                if not regions_changed[i]:
                    if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                        regions_changed[i] = True
                        print(f"🟥 Region {i} changed!")

            if any(regions_changed):
                print("⚠️ At least one region changed. Slowing down.")
                break

            self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.3, 0.15, 0)  # speed2
            QtTest.QTest.qWait(500)

        print("🟠 Slowing down...")
        # Continue descending with speed3 until at least 5 out of 8 regions have changed
        while regions_changed.count(True) < 4:
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)

            for i, (base, curr) in enumerate(zip(baseline_regions, current_regions)):
                if not regions_changed[i]:
                    if self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                        regions_changed[i] = True
                        print(f"✅ Region {i} now changed.")

            self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, -0.08, 0.04, 0)  # speed3
            QtTest.QTest.qWait(500)

        print("🔥 PC is on. Begin heating.")

        self.settings_tab.set_temperature(hot_txt) #temprature1
        #while self.settings_tab.get_temperature() < temperature1:
        #    time.sleep(0.5)
        print("⏱ Holding temperature for 3 minutes...")
        #time.sleep(1 * 60)
        QtTest.QTest.qWait(120000)


        #post_heating_baseline = self.get_edge_and_corner_regions_split(self.image_frame_manager.get_screenshot())
        print("❄️ Cooling the stage...")
        self.settings_tab.set_temperature(cold_txt) #temprature2
        QtTest.QTest.qWait(120000)
        #while self.settings_tab.get_temperature() < temperature2:
        #    time.sleep(0.5)

        print(f"⬆️ Moving up with speed {speed4}, watching for region reversion...")
        post_heating_baseline = self.get_edge_and_corner_regions_split(self.image_frame_manager.get_screenshot())
        reverted_flags = [False] * len(post_heating_baseline)

        while reverted_flags.count(True) < 4:
            current_image = self.image_frame_manager.get_screenshot()
            current_regions = self.get_edge_and_corner_regions_split(current_image)

            for i, (base, curr) in enumerate(zip(post_heating_baseline, current_regions)):
                if not reverted_flags[i]:
                    if not self.is_color_changed(np.mean(base, axis=0), np.mean(curr, axis=0), threshold=40):
                        reverted_flags[i] = True
                        print(f"🔄 Region {i} reverted.")

            self.settings_tab.mccard.MoCtrCard_MCrlAxisRelMove(2, 0.08, 0.04, 0)  # speed4
            QtTest.QTest.qWait(500)

        print("✅ PC reverted — speeding up!")

        image = self.image_frame_manager.get_screenshot()
        color3 = self.get_avg_color(image, self.target_binary_mask)

        print(f"🔼 Final lift to {distance2} with speed {speed6}...")
        self.settings_tab.mccard.MoCtrCard_MCrlAxisAbsMove(AxisId=2, PosCmnd=distance2*2, VCmnd=speed6*0.5) #distacne2, speed6
        #QtTest.QTest.qWait(1000)
        self.wait_until_reached(axis_id=2, target_pos=distance1)

        if not self.is_color_changed(color1, color3, threshold=40):
            print("❌ Pickup failed (color1 ≈ color3)")
        else:
            print("✅ Pickup successful!")
