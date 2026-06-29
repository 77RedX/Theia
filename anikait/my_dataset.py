#Akshay dont modify this. You can import this
import os
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as T

class VimeoTripletDataset(Dataset):
    def __init__(self, root: str, list_file: str):
        self.root = root

        if not os.path.exists(list_file):
            raise FileNotFoundError(f"List file not found: {list_file}")
        if not os.path.isdir(root):
            raise NotADirectoryError(f"Dataset root not found: {root}")

        with open(list_file, "r") as f:
            self.samples = [line.strip() for line in f if line.strip()]

        if len(self.samples) == 0:
            raise ValueError(f"List file is empty: {list_file}")
        self.transform = T.ToTensor()
    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq = self.samples[idx]
        base = os.path.join(self.root, "sequences", seq)

        im1 = self.transform(Image.open(os.path.join(base, "im1.png")).convert("RGB"))
        im2 = self.transform(Image.open(os.path.join(base, "im2.png")).convert("RGB"))
        im3 = self.transform(Image.open(os.path.join(base, "im3.png")).convert("RGB"))
        x = torch.cat([im1, im3], dim=0)
        y = im2

        return x, y


    def get_dataloaders(
        preprocessed_root: str,
        train_list: str,
        val_list: str,
        batch_size: int = 8,
        num_workers: int = 4,):
        
        
        train_dataset = VimeoTripletDataset(preprocessed_root, train_list)
        val_dataset   = VimeoTripletDataset(preprocessed_root, val_list)

        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True,        # shuffle training order each epoch
            num_workers=num_workers,
            pin_memory=True,     # faster CPU→GPU transfer
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size,
            shuffle=False,       # validation order doesn't matter
            num_workers=num_workers,
            pin_memory=True,
        )

        print(f"Train sequences : {len(train_dataset)}")
        print(f"Val sequences   : {len(val_dataset)}")

        return train_loader, val_loader
