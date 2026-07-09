import torch
import torch.nn as nn
from .residual import ResidualBlock, DownBlock

BASE_CHANNELS = 32
PYRAMID_LEVELS = 4

class FeaturePyramid(nn.Module):
    """
    Extracts multi-scale contextual features from an input frame.
    Returns a dictionary of features at 1x, 1/2x, 1/4x, and 1/8x spatial resolutions.
    """
    def __init__(self, base_channels=BASE_CHANNELS):
        super(FeaturePyramid, self).__init__()
        
        # Level 0: Full Resolution (1x)
        # These are the "shallow features" that will be warped and sent to the U-Net
        self.conv0 = nn.Conv2d(3, base_channels, kernel_size=3, padding=1, bias=False)
        self.act0 = nn.PReLU(base_channels)
        self.res0 = nn.Sequential(
            ResidualBlock(base_channels),
            ResidualBlock(base_channels)
        )
        
        # Level 1: 1/2 Resolution
        self.down1 = DownBlock(base_channels, base_channels * 2)
        
        # Level 2: 1/4 Resolution
        self.down2 = DownBlock(base_channels * 2, base_channels * 4)
        
        # Level 3: 1/8 Resolution
        # Captures large motion vectors
        self.down3 = DownBlock(base_channels * 4, base_channels * 8)

    def forward(self, x):
        # Extract full-resolution shallow features
        out = self.conv0(x)
        out = self.act0(out)
        f0 = self.res0(out)       # Shape: (B, 32, H, W)
        
        # Extract hierarchical features for flow estimation
        f1 = self.down1(f0)       # Shape: (B, 64, H/2, W/2)
        f2 = self.down2(f1)       # Shape: (B, 128, H/4, W/4)
        f3 = self.down3(f2)       # Shape: (B, 256, H/8, W/8)
        
        return {
            "l0": f0,
            "l1": f1,
            "l2": f2,
            "l3": f3,
        }