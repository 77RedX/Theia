import torch
import torch.nn as nn
import torch.nn.functional as F
from torchmetrics.image import StructuralSimilarityIndexMeasure
from tqdm import tqdm
import os
import csv
import time

from dataset import VimeoTripletDataset
from models.plus_model import PlusModel
from models.modules.warp import Warper
from utils.loss import VFILoss

os.makedirs("outputs", exist_ok=True)
os.makedirs("checkpoints", exist_ok=True)

# ---------------- CONFIG ----------------
PREPROCESSED_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"
TRAIN_LIST = "/home/akshaygautam4451/Theia/splits/train_list.txt"
VAL_LIST = "/home/akshaygautam4451/Theia/splits/val_list.txt"
BATCH_SIZE = 24  # Should fit comfortably on the L40's 48GB VRAM
EPOCHS = 10
LR = 1e-4
NUM_WORKERS = 16
# ----------------------------------------

def calculate_psnr(pred, target):
    mse = F.mse_loss(pred, target)
    if mse.item() == 0:
        return 100.0
    return -10 * torch.log10(mse).item()

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))

train_loader, val_loader = VimeoTripletDataset.get_dataloaders(
    preprocessed_root=PREPROCESSED_ROOT,
    train_list=TRAIN_LIST,
    val_list=VAL_LIST,
    batch_size=BATCH_SIZE,
    num_workers=NUM_WORKERS
)

# Initialize PlusModel, Multi-Scale Loss, and Warper (for loss calculation)
model = PlusModel().to(device)
criterion = VFILoss().to(device)
warper = Warper().to(device)

optimizer = torch.optim.Adam(model.parameters(), lr=LR)
ssim_metric = StructuralSimilarityIndexMeasure(data_range=1.0).to(device)

# Initialize AMP Scaler
scaler = torch.amp.GradScaler('cuda')

log_file = "outputs/training_log.csv"

# Initialize CSV Headers
with open(log_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "epoch",
        "lr",
        "train_loss",
        "val_loss",
        "val_psnr",
        "val_ssim",
        "epoch_time"
    ])

best_val_loss = float("inf")

for epoch in range(EPOCHS):
    epoch_start = time.time()
    
    # --- TRAINING LOOP ---
    model.train()
    running_loss = 0.0
    current_lr = optimizer.param_groups[0]["lr"]

    pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Train]")
    
    for x, y in pbar:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)
        
        # Split 6-channel input into separate frames
        img1 = x[:, :3, :, :]
        img3 = x[:, 3:, :, :]

        optimizer.zero_grad(set_to_none=True)
        
        # Mixed precision forward pass
        with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
            # training=True returns the dictionary for VFILoss
            result = model(img1, img3, training=True) 
            loss = criterion(result, y, img1, img3, warper)

        # Scaled backward pass
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item()
        pbar.set_postfix(loss=loss.item())

    avg_train_loss = running_loss / len(train_loader)

    # --- VALIDATION LOOP ---
    model.eval()
    val_loss = 0.0
    val_psnr = 0.0
    val_ssim = 0.0

    with torch.no_grad():
        pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Val]")

        for x, y in pbar:
            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)
            
            img1 = x[:, :3, :, :]
            img3 = x[:, 3:, :, :]

            with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
                # Keep training=True here strictly to calculate the multi-scale validation loss
                result = model(img1, img3, training=True)
                pred = result["pred"]
                loss = criterion(result, y, img1, img3, warper)

            val_loss += loss.item()
            val_psnr += calculate_psnr(pred, y)
            val_ssim += ssim_metric(pred, y).item()

    avg_val_loss = val_loss / len(val_loader)
    avg_val_psnr = val_psnr / len(val_loader)
    avg_val_ssim = val_ssim / len(val_loader)
    epoch_time = time.time() - epoch_start

    print(
        f"Epoch {epoch+1} | "
        f"LR {current_lr:.2e} | "
        f"Train: {avg_train_loss:.6f} | "
        f"Val: {avg_val_loss:.6f} | "
        f"PSNR: {avg_val_psnr:.2f} dB | "
        f"SSIM {avg_val_ssim:.4f} | "
        f"Time {epoch_time:.1f}s"
    )

    with open(log_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            epoch + 1,
            current_lr,
            avg_train_loss,
            avg_val_loss,
            avg_val_psnr,
            avg_val_ssim,
            epoch_time
        ])

    checkpoint = {
        "epoch": epoch,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
        "train_loss": avg_train_loss,
        "val_loss": avg_val_loss,
        "val_psnr": avg_val_psnr,
        "val_ssim": avg_val_ssim,
        "epoch_time": epoch_time,
    }
    
    # Save standard checkpoint
    torch.save(checkpoint, f"checkpoints/plus_checkpoint_epoch_{epoch+1}.pth")

    if avg_val_loss < best_val_loss:
        best_val_loss = avg_val_loss
        print("New Best Model saved")
        torch.save(checkpoint, "checkpoints/best_plus_model.pth")
