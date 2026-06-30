import torch
import torch.nn as nn
from dataset import VimeoTripletDataset
from models.basic_flow import BasicFlowInterp
from tqdm import tqdm
import os
import csv
import torch.nn.functional as F
os.makedirs("outputs", exist_ok=True)
os.makedirs("checkpoints", exist_ok=True)

# ---------------- CONFIG ----------------
PREPROCESSED_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"
TRAIN_LIST = "/home/akshaygautam4451/Theia/splits/train_list.txt"
VAL_LIST = "/home/akshaygautam4451/Theia/splits/val_list.txt"
BATCH_SIZE = 24 # Increased due to AMP
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

model = BasicFlowInterp().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
criterion = nn.L1Loss()

# Initialize AMP Scaler
scaler = torch.amp.GradScaler('cuda')

log_file = "training_log.csv"

with open(log_file, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "epoch",
        "lr",
        "train_loss",
        "val_loss",
        "val_psnr"
    ])

best_val_loss = float("inf")

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0
    current_lr = optimizer.param_groups[0]["lr"]

    pbar = tqdm(
        train_loader,
        desc=f"Epoch {epoch+1}/{EPOCHS} [Train]"
    )
    for x, y in pbar:
        x = x.to(device, non_blocking=True)
        y = y.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none = True)
        
        # Mixed precision forward pass
        with torch.amp.autocast(device_type=device, enabled=(device == "cuda")):
            result = model(x)
            pred = result["pred"]
            loss = criterion(pred, y)

        # Scaled backward pass
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        running_loss += loss.item()
        pbar.set_postfix(loss=loss.item())

    avg_train_loss = running_loss / len(train_loader)

    model.eval()

    val_loss = 0.0
    val_psnr = 0.0

    with torch.no_grad():

        pbar = tqdm(
            val_loader,
            desc=f"Epoch {epoch+1}/{EPOCHS} [Val]"
        )

        for x, y in pbar:

            x = x.to(device, non_blocking=True)
            y = y.to(device, non_blocking=True)

            with torch.amp.autocast('cuda'):

                result = model(x)
                pred = result["pred"]

                loss = criterion(pred, y)

            val_loss += loss.item()
            val_psnr += calculate_psnr(pred, y)

    avg_val_loss = val_loss / len(val_loader)
    avg_val_psnr = val_psnr / len(val_loader)

    print(
        f"Epoch {epoch+1} | "
        f"LR {current_lr:.2e} | "
        f"Train: {avg_train_loss:.6f} | "
        f"Val: {avg_val_loss:.6f} | "
        f"PSNR: {avg_val_psnr:.2f} dB"
    )


    with open(log_file, "a", newline="") as f:

        writer = csv.writer(f)

        writer.writerow([
            epoch + 1,
            current_lr,
            avg_train_loss,
            avg_val_loss,
            avg_val_psnr
        ])

    checkpoint = {
        "epoch": epoch,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
        "train_loss": avg_train_loss,
        "val_loss": avg_val_loss,
        "val_psnr": avg_val_psnr,
    }
    
    torch.save(checkpoint, f"checkpoints/checkpoint_epoch_{epoch+1}.pth")

    if avg_val_loss < best_val_loss:

        best_val_loss = avg_val_loss

        torch.save(checkpoint, "checkpoints/best_model.pth")