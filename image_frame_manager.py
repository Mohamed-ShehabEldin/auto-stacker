from PyQt5.QtCore import QPoint
import pyautogui
import numpy as np
#from sam_predictor import FastSAMPredictor
from sam2_predictor import FastSAMPredictor
from PyQt5 import QtTest



class ImageFrameManager:
    def __init__(self, image_frame, target_star_marker, receiver_star_marker):
        self.image_frame = image_frame
        self.target_star_marker = target_star_marker
        self.receiver_star_marker = receiver_star_marker

        #self.sam = FastSAMPredictor(model_type='vit_b', device='cpu')
        self.sam = FastSAMPredictor(model_cfg="configs/sam2.1/sam2.1_hiera_s.yaml",checkpoint="sam2.1_hiera_small.pt", device='cpu')


    def get_target_star_position(self):
        return self.target_star_marker.pos()

    def get_target_star_position_global(self):
        return self.target_star_marker.mapToGlobal(QPoint(0, 0))
    
    def get_receiver_star_position(self):
        return self.receiver_star_marker.pos()

    def get_receiver_star_position_global(self):
        return self.receiver_star_marker.mapToGlobal(QPoint(0, 0))

    def get_screenshot(self):
        self.target_star_marker.move(2, 2)
        self.receiver_star_marker.move(2, 4)
        QtTest.QTest.qWait(500)
        top_left = self.image_frame.mapToGlobal(self.image_frame.pos())
        width = self.image_frame.width()
        height = self.image_frame.height()
        screenshot = pyautogui.screenshot(region=(top_left.x(), top_left.y(), width, height))
        return np.array(screenshot.convert("RGB"))
    
    # def run_sam(self):
    #     # Run SAM
    #     star_position=self.get_star_position()
    #     screenshot_np=self.get_screenshot()

    #     self.sam.set_image(screenshot_np)
    #     segmented_image, binary_mask = self.sam.segment_point(star_position.x(), star_position.y())
    #     return segmented_image, binary_mask

    def run_target_sam(self):
        # Run SAM
        target_star_position=self.get_target_star_position()
        self.target_star_marker.move(2, 2)
        self.receiver_star_marker.move(2, 4)
        QtTest.QTest.qWait(500)

        top_left = self.image_frame.mapToGlobal(self.image_frame.pos())
        width = self.image_frame.width()
        height = self.image_frame.height()
        screenshot = pyautogui.screenshot(region=(top_left.x(), top_left.y(), width, height))
        screenshot_np = np.array(screenshot.convert("RGB"))

        self.sam.set_image(screenshot_np)
        segmented_image, binary_mask = self.sam.segment_point(target_star_position.x(), target_star_position.y())
        return segmented_image, binary_mask

    def run_receiver_sam(self):
        # Run SAM
        receiver_star_position=self.get_receiver_star_position()
        self.target_star_marker.move(2, 2)
        self.receiver_star_marker.move(2, 4)
        QtTest.QTest.qWait(500)

        top_left = self.image_frame.mapToGlobal(self.image_frame.pos())
        width = self.image_frame.width()
        height = self.image_frame.height()
        screenshot = pyautogui.screenshot(region=(top_left.x(), top_left.y(), width, height))
        screenshot_np = np.array(screenshot.convert("RGB"))

        self.sam.set_image(screenshot_np)
        segmented_image, binary_mask = self.sam.segment_point(receiver_star_position.x(), receiver_star_position.y())
        return segmented_image, binary_mask