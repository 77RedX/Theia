import torch
import torch.nn as nn
from .residual import DownBlock, UpBlock, ResidualBlock
from .feature import BASE_CHANNELS

class RefineUNet(nn.Module):
    """
    U-Net based refinement module.
    Takes warped frames, original frames, flows, and warped shallow features 
    to predict a final residual correction.
    """
    def __init__(self, base_channels=BASE_CHANNELS):
        super(RefineUNet, self).__init__()
        
        # Input Channel Calculation:
        # img1 (3), img3 (3)
        # warp1_img (3), warp3_img (3)
        # flow0 (2), flow1 (2)
        # mask (1)
        # warp1_feat (32), warp3_feat (32)
        # Total = 3*4 + 2*2 + 1 + 32*2 = 81
        in_channels = 12 + 4 + 1 + (base_channels * 2)
        
        self.conv_in = nn.Sequential(
            nn.Conv2d(in_channels, base_channels, kernel_size=3, padding=1, bias=False),
            nn.PReLU(base_channels),
            ResidualBlock(base_channels)
        )
        
        # Downsampling
        self.down1 = DownBlock(base_channels, base_channels * 2)
        self.down2 = DownBlock(base_channels * 2, base_channels * 4)
        self.down3 = DownBlock(base_channels * 4, base_channels * 8)
        
        # Upsampling (Wiring into the custom UpBlock from residual.py)
        # UpBlock signature: (in_channels, skip_channels, out_channels)
        self.up1 = UpBlock(base_channels * 8, base_channels * 4, base_channels * 4)
        self.up2 = UpBlock(base_channels * 4, base_channels * 2, base_channels * 2)
        self.up3 = UpBlock(base_channels * 2, base_channels, base_channels)
        
        # Final residual prediction (3 channels for RGB)
        self.predict = nn.Conv2d(base_channels, 3, kernel_size=3, padding=1)

    def forward(self, img1, img3, warp1_img, warp3_img, flow0, flow1, mask, warp1_feat, warp3_feat):
        # 1. Base blended image
        # This is what your basic model was outputting. We use it as the starting point.
        base_blend = mask * warp1_img + (1.0 - mask) * warp3_img
        
        # 2. Concatenate all context for the U-Net
        x = torch.cat([
            img1, img3, 
            warp1_img, warp3_img, 
            flow0, flow1, 
            mask, 
            warp1_feat, warp3_feat
        ], dim=1)
        
        # 3. Pass through the Refinement U-Net
        d0 = self.conv_in(x)
        d1 = self.down1(d0)
        d2 = self.down2(d1)
        d3 = self.down3(d2)
        
        u1 = self.up1(d3, d2)
        u2 = self.up2(u1, d1)
        u3 = self.up3(u2, d0)
        
        # 4. Predict the residual
        res = self.predict(u3)
        
        # 5. Final Output
        # Add the learned residual to the base blend to fix artifacts and restore sharpness
        return base_blend + res