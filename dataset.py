import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as T

class VimeoTripletDataset(Dataset):
    def __init__(self, root, list_file):
        self.root = root
        with open(list_file, "r") as f:
            self.samples = [line.strip() for line in f]

        self.transform = T.Compose([
            T.Resize((256, 448)),
            T.ToTensor(),
        ])


    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq = self.samples[idx]
        base = os.path.join(self.root, "sequences", seq)

        img1 = self.transform(Image.open(os.path.join(base, "im1.png")).convert("RGB"))
        img2 = self.transform(Image.open(os.path.join(base, "im2.png")).convert("RGB"))
        img3 = self.transform(Image.open(os.path.join(base, "im3.png")).convert("RGB"))

        # input = frame1 + frame3
        x = torch.cat([img1, img3], dim=0)  # (6,H,W)
        y = img2                              # (3,H,W)

        return x, y
