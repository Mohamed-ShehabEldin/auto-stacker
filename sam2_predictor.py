import time
import numpy as np
import torch
import matplotlib.pyplot as plt
import cv2
import sys
from pathlib import Path
from PIL import Image  # Make sure this is at the top if not already
from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor


# def show_mask(mask, ax, random_color=False):
#     if random_color:
#         color = np.concatenate([np.random.random(3), np.array([0.6])], axis=0)
#     else:
#         color = np.array([30/255, 144/255, 255/255, 0.6])
#     h, w = mask.shape[-2:]
#     mask_image = mask.reshape(h, w, 1) * color.reshape(1, 1, -1)
#     ax.imshow(mask_image)
    
# def show_points(coords, labels, ax, marker_size=375):
#     pos_points = coords[labels==1]
#     neg_points = coords[labels==0]
#     ax.scatter(pos_points[:, 0], pos_points[:, 1], color='green', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)
#     ax.scatter(neg_points[:, 0], neg_points[:, 1], color='red', marker='*', s=marker_size, edgecolor='white', linewidth=1.25)   
    
# def show_box(box, ax):
#     x0, y0 = box[0], box[1]
#     w, h = box[2] - box[0], box[3] - box[1]
#     ax.add_patch(plt.Rectangle((x0, y0), w, h, edgecolor='green', facecolor=(0,0,0,0), lw=2))    




# # sam_checkpoint = "sam_vit_b_01ec64.pth"
# # model_type = "vit_b"
# # device = "cpu"

# # sam = sam_model_registry[model_type](checkpoint=sam_checkpoint)
# # sam.to(device=device)

# # predictor = SamPredictor(sam)
# checkpoint = "sam2.1_hiera_small.pt"
# model_cfg = "configs/sam2.1/sam2.1_hiera_s.yaml"
# device = "cpu"

# model = build_sam2(model_cfg, checkpoint, device=device)

# predictor = SAM2ImagePredictor(model)


# start = time.time()

# image = cv2.imread('Screenshot 2025-04-09 150607.png')
# image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
# predictor.set_image(image)

# input_point = np.array([[510, 410]])
# input_label = np.array([1])

# masks, scores, logits = predictor.predict(
#     point_coords=input_point,
#     point_labels=input_label,
#     multimask_output=False,
# )
# end = time.time()
# length = end - start
# print("It took", length, "seconds!")

# for i, (mask, score) in enumerate(zip(masks, scores)):
#     plt.figure(figsize=(10,10))
#     plt.imshow(image)
#     show_mask(mask, plt.gca())
#     show_points(input_point, input_label, plt.gca())
#     plt.title(f"Mask {i+1}, Score: {score:.3f}", fontsize=18)
#     plt.axis('off')
#     plt.show()  



def validate_checkpoint_path(checkpoint_path):
    checkpoint_file = Path(checkpoint_path)
    if not checkpoint_file.exists():
        raise FileNotFoundError(
            f"SAM2 checkpoint not found: {checkpoint_path}.\n"
            "Please download a valid checkpoint file and place it in the project root."
        )
    if checkpoint_file.stat().st_size == 0:
        raise FileNotFoundError(
            f"SAM2 checkpoint is empty or corrupted: {checkpoint_path}.\n"
            "Delete it and download a valid checkpoint file again."
        )


class FastSAMPredictor:
    def __init__(self, model_cfg="configs/sam2.1/sam2.1_hiera_s.yaml",checkpoint="sam2.1_hiera_small.pt", device='cpu'):
        self.device = device
        validate_checkpoint_path(checkpoint)

        model = build_sam2(model_cfg, checkpoint, device=device)
        self.predictor = SAM2ImagePredictor(model)
        

    def set_image(self, image):
        self.original = image.copy()
        if isinstance(image, Image.Image):
            image = np.array(image)
        # If it's RGB (from PIL), convert to BGR for SAM
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        self.image = image
        self.predictor.set_image(cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
    #just edit this to give you segment from x,y pint
    def segment_point(self, x, y):
        input_point = np.array([[x, y]])
        input_label = np.array([1])
        masks, scores, logits = self.predictor.predict(
            point_coords=input_point,
            point_labels=input_label,
            multimask_output=False
        )

        mask = masks[0]
        mask_bool = mask.astype(bool)

        overlay = self.original.copy()
        overlay[~mask_bool] = (overlay[~mask_bool] * 0.4).astype(np.uint8)
        
        return overlay, mask.astype(np.uint8) * 255  # ← second return is B&W mask


# It took 6.440640687942505 seconds!
# It took 3.8832457065582275 seconds!
# It took 4.1801369190216064 seconds!
# It took 3.849233388900757 seconds!
# It took 3.9216063022613525 seconds!
# It took 3.886096477508545 seconds!