import os
import torch
import torchvision.utils as vutils
from dataset import VimeoTripletDataset
from model import SimpleVFI

# ---------------- CONFIG ----------------
DATA_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet"
LIST_FILE = "/home/akshaygautam4451/Theia/data/vimeo_triplet/tri_trainlist.txt"
CHECKPOINT = "checkpoints/checkpoint_epoch_10.pth"

NUM_SAMPLES = 5
START_INDEX = 5000   # avoid memorized samples

OUT_DIR = f"/tmp/{os.environ['USER']}/theia_visuals"
# ----------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Using device:", device)

os.makedirs(OUT_DIR, exist_ok=True)

# Dataset
dataset = VimeoTripletDataset(DATA_ROOT, LIST_FILE)

# Model
model = SimpleVFI().to(device)
ckpt = torch.load(CHECKPOINT, map_location=device)
model.load_state_dict(ckpt["model"])
model.eval()

with torch.no_grad():
    for i in range(NUM_SAMPLES):
        idx = START_INDEX + i
        x, y = dataset[idx]

        x = x.unsqueeze(0).to(device)
        y = y.unsqueeze(0).to(device)

        pred = model(x)

        im1 = x[:, :3]
        im3 = x[:, 3:]

        # Save images
        vutils.save_image(im1,  f"{OUT_DIR}/sample_{i}_im1.png")
        vutils.save_image(y,    f"{OUT_DIR}/sample_{i}_gt.png")
        vutils.save_image(pred,f"{OUT_DIR}/sample_{i}_pred.png")
        vutils.save_image(im3, f"{OUT_DIR}/sample_{i}_im3.png")

        print(f"Saved sample {i} (dataset index {idx})")

print("All visuals saved to:", OUT_DIR)

