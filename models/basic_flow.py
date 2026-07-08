import torch
import torch.nn as nn
import torch.nn.functional as F

def warp(img, flow):
    """Warps an image using an optical flow field."""
    B, C, H, W = img.size()
    # Create mesh grid
    yy, xx = torch.meshgrid(torch.arange(H), torch.arange(W), indexing='ij')
    grid = torch.stack((xx, yy), dim=0).unsqueeze(0).float().to(img.device) # (1, 2, H, W)
    grid = grid.repeat(B, 1, 1, 1)
    
    # Add flow to the grid
    vgrid = grid + flow
    
    # Normalize grid to [-1, 1] for grid_sample
    vgrid[:, 0, :, :] = 2.0 * vgrid[:, 0, :, :] / max(W - 1, 1) - 1.0
    vgrid[:, 1, :, :] = 2.0 * vgrid[:, 1, :, :] / max(H - 1, 1) - 1.0
    vgrid = vgrid.permute(0, 2, 3, 1) # (B, H, W, 2)
    
    return F.grid_sample(img, vgrid, padding_mode='border', align_corners=True)

class BasicFlowInterp(nn.Module):
    def __init__(self):
        super().__init__()
        # Lightweight Encoder-Decoder to predict flow and mask
        self.enc1 = nn.Sequential(
            nn.Conv2d(6, 32, 3, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.enc2 = nn.Sequential(
            nn.Conv2d(32, 64, 3, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.enc3 = nn.Sequential(
            nn.Conv2d(64, 128, 3, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )
        
        self.up1 = nn.Sequential(
            nn.ConvTranspose2d(128, 64, 4, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.up2 = nn.Sequential(
            nn.ConvTranspose2d(64, 32, 4, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.up3 = nn.Sequential(
            nn.ConvTranspose2d(32, 16, 4, padding=1, stride=2),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.head = nn.Conv2d(16, 5, 3, padding=1)

    def forward(self, x):
        img0 = x[:, :3, :, :]
        img1 = x[:, 3:, :, :]
        
        # Predict flow and mask
        e1 = self.enc1(x)
        e2 = self.enc2(e1)
        e3 = self.enc3(e2)

        d1 = self.up1(e3)
        d2 = self.up2(d1)
        d3 = self.up3(d2)

        out = self.head(d3)
        
        flow0 = out[:, :2, :, :]
        flow1 = out[:, 2:4, :, :]
        mask = torch.sigmoid(out[:, 4:5, :, :])
        
        # Warp images
        warped_img0 = warp(img0, flow0)
        warped_img1 = warp(img1, flow1)
        
        # Blend using the mask
        pred = mask * warped_img0 + (1 - mask) * warped_img1
        
        return {
            "pred": pred,
            "flow0": flow0,
            "flow1": flow1,
            "mask": mask,
        }