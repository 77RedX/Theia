import os
import torch
import torchvision.utils as vutils

from dataset import VimeoTripletDataset
from models.pro_model import ProModel 

# ---------------- CONFIG ----------------
PREPROCESSED_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"
VAL_LIST = "/home/akshaygautam4451/Theia/splits/val_list.txt"
# Pointing to the new ProModel checkpoint
CHECKPOINT = "checkpoints/best_pro_model.pth" 

NUM_SAMPLES = 5
OUT_DIR = f"/tmp/{os.environ.get('USER', 'akshaygautam4451')}/theia_visuals"
# ----------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
os.makedirs(OUT_DIR, exist_ok=True)

dataset = VimeoTripletDataset(PREPROCESSED_ROOT, VAL_LIST)

model = ProModel().to(device)
ckpt = torch.load(CHECKPOINT, map_location=device, weights_only=False)
model.load_state_dict(ckpt["model"])
model.eval()

with torch.no_grad():
    for i in range(NUM_SAMPLES):
        x, y = dataset[i]

        x = x.unsqueeze(0).to(device)
        y = y.unsqueeze(0).to(device)
        
        # Split the 6-channel input into separate frames for ProModel
        im1 = x[:, :3]
        im3 = x[:, 3:]

        # Mixed precision inference to match training
        with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
            # ProModel returns the predicted tensor directly during eval
            pred = model(im1, im3)

        # Save images
        vutils.save_image(im1,  f"{OUT_DIR}/sample_{i}_1_im1.png")
        vutils.save_image(y,    f"{OUT_DIR}/sample_{i}_2_gt.png")
        vutils.save_image(pred, f"{OUT_DIR}/sample_{i}_3_pred.png")
        vutils.save_image(im3,  f"{OUT_DIR}/sample_{i}_4_im3.png")

        print(f"Saved validation sample {i}")

print("All visuals saved to:", OUT_DIR)