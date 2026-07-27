import os
import time
import csv
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torch.optim.lr_scheduler import MultiStepLR
from tqdm import tqdm
from torchmetrics.image import StructuralSimilarityIndexMeasure

# Import the Pro Architecture and Loss
from models.pro_model import ProModel
from utils.loss_pro import ProLoss

# TODO: Adjust this import to match your actual dataset class name
from dataset import VimeoTripletDataset 

# ---------------- CONFIG ----------------
PREPROCESSED_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"
TRAIN_LIST = "/home/akshaygautam4451/Theia/splits/train_list.txt"
VAL_LIST = "/home/akshaygautam4451/Theia/splits/val_list.txt"

BATCH_SIZE = 12  
EPOCHS = 30  
LR = 1e-4
NUM_WORKERS = 8 

CHECKPOINT_DIR = "checkpoints"
OUTPUT_DIR = "outputs"
LOG_FILE = os.path.join(OUTPUT_DIR, "training_log_pro.csv")
BEST_MODEL_PATH = os.path.join(CHECKPOINT_DIR, "best_pro_model.pth")
LATEST_MODEL_PATH = os.path.join(CHECKPOINT_DIR, "latest_pro_model.pth")
RESUME_CHECKPOINT = LATEST_MODEL_PATH  # Point this to BEST_MODEL_PATH if preferred
# ----------------------------------------

def calculate_psnr(pred, target):
    mse = F.mse_loss(pred, target)
    if mse == 0:
        return 100.0
    return -10 * torch.log10(mse).item()

def main():
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # --- DATALOADERS ---
    train_dataset = VimeoTripletDataset(PREPROCESSED_ROOT, TRAIN_LIST)
    val_dataset = VimeoTripletDataset(PREPROCESSED_ROOT, VAL_LIST)

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True, num_workers=NUM_WORKERS, pin_memory=True, persistent_workers=True, prefetch_factor=2)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False, num_workers=NUM_WORKERS, pin_memory=True, persistent_workers=True, prefetch_factor=2)

    # --- MODEL, LOSS, METRICS ---
    model = ProModel().to(device)
    criterion = ProLoss().to(device)
    ssim_metric = StructuralSimilarityIndexMeasure(data_range=1.0).to(device)

    # --- OPTIMIZER & SCHEDULER ---
    optimizer = torch.optim.Adam(model.parameters(), lr=LR)
    scheduler = MultiStepLR(optimizer, milestones=[20, 27], gamma=0.5)
    scaler = torch.amp.GradScaler(
        enabled=(device.type == "cuda")
    )

    start_epoch = 0
    best_val_psnr = 0.0  # Track best PSNR instead of loss for saving models

    # --- RESUME LOGIC ---
    if os.path.exists(RESUME_CHECKPOINT):
        print(f"Resuming from checkpoint: {RESUME_CHECKPOINT}")
        checkpoint = torch.load(RESUME_CHECKPOINT, map_location=device, weights_only=False)
        
        model.load_state_dict(checkpoint["model"])
        optimizer.load_state_dict(checkpoint["optimizer"])
        scaler.load_state_dict(checkpoint["scaler"])
        
        start_epoch = checkpoint["epoch"] + 1 
        best_val_psnr = checkpoint.get("val_psnr", 0.0)
        
        if "scheduler" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler"])
        else:
            print("No scheduler state found. Fast-forwarding to current epoch...")
            for _ in range(start_epoch):
                scheduler.step()
                
        print(f"Successfully restored state. Resuming at Epoch {start_epoch + 1}")
    else:
        print("Starting training from scratch.")
        with open(LOG_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "epoch", "lr", "train_loss", "val_psnr", "val_ssim", "epoch_time"
            ])

    # --- TRAINING LOOP ---
    for epoch in range(start_epoch, EPOCHS):
        epoch_start = time.time()
        current_lr = optimizer.param_groups[0]["lr"]
        
        # 1. Training Phase
        model.train()
        running_loss = 0.0
        
        train_pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Train]")
        for img1, img2, img3 in train_pbar:
            img1, img2, img3 = img1.to(device, non_blocking=True), img2.to(device, non_blocking=True), img3.to(device, non_blocking=True)

            optimizer.zero_grad(set_to_none=True)

            with torch.amp.autocast('cuda'):
                # ProModel returns a dict with pred_full, pred_half, pred_quarter during training
                preds_dict = model(img1, img3)
                loss = criterion(preds_dict, img2)

            scaler.scale(loss).backward()
            
            # Optional: Gradient clipping is highly recommended for Transformers/DCNs
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            scaler.step(optimizer)
            scaler.update()

            running_loss += loss.item()
            train_pbar.set_postfix(loss=f"{loss.item():.4f}")

        avg_train_loss = running_loss / len(train_loader)
        ssim_metric.reset()
        # 2. Validation Phase
        model.eval()
        val_psnr_total = 0.0
        val_ssim_total = 0.0

        val_pbar = tqdm(val_loader, desc=f"Epoch {epoch+1}/{EPOCHS} [Val]")
        with torch.no_grad():
            for img1, img2, img3 in val_pbar:
                img1, img2, img3 = img1.to(device, non_blocking=True), img2.to(device, non_blocking=True), img3.to(device, non_blocking=True)

                with torch.amp.autocast('cuda'):
                    # ProModel returns just the final tensor during eval
                    pred = model(img1, img3)

                # Clamp outputs to valid image range before metric calculation
                pred_clamped = torch.clamp(pred, 0.0, 1.0)
                
                val_psnr_total += calculate_psnr(pred_clamped, img2)
                val_ssim_total += ssim_metric(pred_clamped, img2).item()

        avg_val_psnr = val_psnr_total / len(val_loader)
        avg_val_ssim = val_ssim_total / len(val_loader)
        epoch_time = time.time() - epoch_start

        # 3. Print & Log
        print(f"Epoch {epoch+1} | LR {current_lr:.2e} | Train Loss: {avg_train_loss:.4f} | "
              f"Val PSNR: {avg_val_psnr:.2f} dB | SSIM: {avg_val_ssim:.4f} | Time: {epoch_time:.1f}s")

        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                epoch + 1, current_lr, avg_train_loss, avg_val_psnr, avg_val_ssim, epoch_time
            ])

        # 4. Checkpointing
        checkpoint = {
            "epoch": epoch,
            "model": model.state_dict(),
            "optimizer": optimizer.state_dict(),
            "scaler": scaler.state_dict(),
            "scheduler": scheduler.state_dict(),
            "train_loss": avg_train_loss,
            "val_psnr": avg_val_psnr,
            "val_ssim": avg_val_ssim,
            "epoch_time": epoch_time,
        }

        # Save latest model every epoch
        torch.save(checkpoint, LATEST_MODEL_PATH)

        # Save best model if PSNR improves
        if avg_val_psnr > best_val_psnr:
            best_val_psnr = avg_val_psnr
            torch.save(checkpoint, BEST_MODEL_PATH)
            print("🌟 New Best Model saved!")
            
        # 5. Step Scheduler
        scheduler.step()

if __name__ == "__main__":
    main()
