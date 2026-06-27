import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from dataset import VimeoTripletDataset
from model import SimpleVFI
from tqdm import tqdm
#from torch.utils.data import Subset
import os
os.makedirs("checkpoints", exist_ok=True)

# ---------------- CONFIG ----------------
DATA_ROOT = "/home/akshaygautam4451/Theia/data/vimeo_triplet"
TRAIN_LIST = "/home/akshaygautam4451/Theia/data/vimeo_triplet/tri_trainlist.txt"
BATCH_SIZE = 12
EPOCHS = 10 # make 10 after test phase
LR = 1e-4
# ----------------------------------------

device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)
if device == "cuda":
    print("GPU:", torch.cuda.get_device_name(0))

dataset = VimeoTripletDataset(DATA_ROOT, TRAIN_LIST)

#limiting dataset for testing purposes
#subset_size=1000;
#dataset = Subset(dataset, range(subset_size))

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=4,
    pin_memory=True
)

model = SimpleVFI().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=LR)
criterion = nn.L1Loss()

for epoch in range(EPOCHS):
    model.train()
    running_loss = 0.0

    pbar = tqdm(loader, desc=f"Epoch {epoch+1}/{EPOCHS}")
    for x, y in pbar:
        x = x.to(device)
        y = y.to(device)

        pred = model(x)
        loss = criterion(pred, y)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        running_loss += loss.item()
        pbar.set_postfix(loss=loss.item())

    print(f"Epoch {epoch+1} avg loss: {running_loss / len(loader):.6f}")

    torch.save({
        "epoch": epoch,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict()
    }, f"checkpoints/checkpoint_epoch_{epoch+1}.pth")
