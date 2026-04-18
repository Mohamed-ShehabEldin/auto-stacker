# sam_predictor.py
#pip install segment-anything onnxruntime opencv-python numpy matplotlib

import numpy as np
import cv2
from segment_anything import SamPredictor, sam_model_registry
import torch
from PIL import Image  # Make sure this is at the top if not already

class FastSAMPredictor:
    def __init__(self, model_type='vit_b', device='cpu'):
        self.device = device
        sam = sam_model_registry[model_type](checkpoint="sam_vit_b_01ec64.pth")
        sam.to(device)
        self.predictor = SamPredictor(sam)

    def set_image(self, image):
        self.original = image.copy()
        if isinstance(image, Image.Image):
            image = np.array(image)
        # If it's RGB (from PIL), convert to BGR for SAM
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        self.image = image
        self.predictor.set_image(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))

    def segment_point(self, x, y):
        input_point = np.array([[x, y]])
        input_label = np.array([1])
        masks, scores, logits = self.predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=False
        )
        mask = masks[0]
        overlay = self.original.copy()
        overlay[~mask] = (overlay[~mask] * 0.4).astype(np.uint8)
        
        return overlay, mask.astype(np.uint8) * 255  # ← second return is B&W mask
