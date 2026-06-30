import os
import torch
import torchvision.utils as vutils

# Updated imports based on the new folder structure
from dataset import VimeoTripletDataset
from models.basic_flow import BasicFlowInterp 

# ---------------- CONFIG ----------------
PREPROCESSED_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"
VAL_LIST = "/home/akshaygautam4451/Theia/splits/val_list.txt"
# Pointing to the new best model checkpoint you created in train.py
CHECKPOINT = "checkpoints/best_model.pth" 

NUM_SAMPLES = 5
OUT_DIR = f"/tmp/{os.environ['USER']}/theia_visuals"
# ----------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
os.makedirs(OUT_DIR, exist_ok=True)

dataset = VimeoTripletDataset(PREPROCESSED_ROOT, VAL_LIST)

model = BasicFlowInterp().to(device)
ckpt = torch.load(CHECKPOINT, map_location=device, weights_only=False)
model.load_state_dict(ckpt["model"])
model.eval()

with torch.no_grad():
    for i in range(NUM_SAMPLES):
        x, y = dataset[i]

        x = x.unsqueeze(0).to(device)
        y = y.unsqueeze(0).to(device)

        # Mixed precision inference to match training
        with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
            result = model(x)
            pred = result["pred"]

        im1 = x[:, :3]
        im3 = x[:, 3:]

        # Save images
        vutils.save_image(im1,  f"{OUT_DIR}/sample_{i}_im1.png")
        vutils.save_image(y,    f"{OUT_DIR}/sample_{i}_gt.png")
        vutils.save_image(pred, f"{OUT_DIR}/sample_{i}_pred.png")
        vutils.save_image(im3,  f"{OUT_DIR}/sample_{i}_im3.png")

        print(f"Saved validation sample {i}")

print("All visuals saved to:", OUT_DIR)