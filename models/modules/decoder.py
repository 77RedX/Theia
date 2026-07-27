import torch
import torch.nn as nn
import torch.nn.functional as F

from models.modules.encoder import ResBlockSE

class DecoderLevel(nn.Module):
    """
    A single hierarchical step in the decoder.
    Upsamples the previous feature map, concatenates skip connections from 
    both Frame 1 and Frame 3, and fuses them using SE-enhanced residual blocks.
    """
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int, use_se: bool = True):
        super().__init__()
        
        # Replace ConvTranspose2d with Bilinear Upsample + 3x3 Conv to avoid checkerboard artifacts
        self.up = nn.Sequential(
            nn.Upsample(scale_factor=2.0, mode='bilinear', align_corners=False),
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1),
            nn.PReLU()
        )
        
        # Fusion handles: upsampled features + f1_skip + f3_skip
        self.fusion = nn.Sequential(
            nn.Conv2d(out_channels + skip_channels * 2, out_channels, kernel_size=3, padding=1),
            nn.PReLU(),
            ResBlockSE(out_channels) if use_se else nn.Identity()
        )
        
    def forward(self, x: torch.Tensor, skip1: torch.Tensor, skip3: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        
        # Guard against minor shape mismatches due to pooling/padding during encoder downsampling
        if x.shape[2:] != skip1.shape[2:]:
            x = F.interpolate(x, size=skip1.shape[2:], mode='bilinear', align_corners=False)
            
        # Concatenate upsampled features with aligned encoder skip connections
        x_cat = torch.cat([x, skip1, skip3], dim=1)
        return self.fusion(x_cat)

class HierarchicalDecoder(nn.Module):
    """
    Decodes features from the DualScaleTransformer back to full resolution.
    - Deep Supervision: Outputs intermediate predictions at 1/4 and 1/2 scales.
    - Final Output: Predicts RGB Residuals and a Blending Mask Residual.
    """
    def __init__(self):
        super().__init__()
        
        # Up2: 1/4 scale (256ch) -> 1/2 scale (128ch)
        self.up2 = DecoderLevel(in_channels=256, skip_channels=128, out_channels=128)
        
        # Up1: 1/2 scale (128ch) -> 1x scale (64ch)
        self.up1 = DecoderLevel(in_channels=128, skip_channels=64, out_channels=64)
        
        # --- Deep Supervision Heads ---
        # Predicting intermediate RGB representations directly from the feature maps
        self.out_quarter = nn.Conv2d(256, 3, kernel_size=3, padding=1)
        self.out_half = nn.Conv2d(128, 3, kernel_size=3, padding=1)
        
        # --- Final Context Fusion ---
        # Fuses the 1x decoded features (64) + warped img1 (3) + warped img3 (3) 
        # + flow1 (2) + flow3 (2) + base_mask (1) = 75 channels
        self.final_fusion = nn.Sequential(
            nn.Conv2d(75, 64, kernel_size=3, padding=1),
            nn.PReLU(),
            ResBlockSE(64),
            nn.Conv2d(64, 32, kernel_size=3, padding=1),
            nn.PReLU(),
            # Output 4 channels: 3 for RGB residual, 1 for Mask residual
            nn.Conv2d(32, 4, kernel_size=3, padding=1) 
        )

        # Weight Initialization
        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode="fan_out", nonlinearity="relu")
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(
        self, 
        dec_quarter: torch.Tensor, 
        skips_half: list[torch.Tensor], 
        skips_full: list[torch.Tensor], 
        ctx: dict[str, torch.Tensor]
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Args:
            dec_quarter: 1/4 scale refined features from DualScaleTransformer [B, 256, H/4, W/4]
            skips_half: [f1_1x2, f3_1x2] aligned features at 1/2 scale
            skips_full: [f1_1x1, f3_1x1] aligned features at 1x scale
            ctx: [flow_t1, flow_t3, base_mask, img1_w, img3_w] at 1x scale
        """
        
        # 1. Deep Supervision at 1/4 Scale
        out_quarter = self.out_quarter(dec_quarter)
        
        # 2. Decode to 1/2 Scale
        d2 = self.up2(dec_quarter, skips_half[0], skips_half[1])
        out_half = self.out_half(d2)  # Deep Supervision at 1/2 Scale
        
        # 3. Decode to Full 1x Scale
        d1 = self.up1(d2, skips_full[0], skips_full[1])
        
        # 4. Final Contextual Fusion
        flow_t1 = ctx["flow_t1"]
        flow_t3 = ctx["flow_t3"]
        mask    = ctx["mask"]
        img1_w  = ctx["img1_w"]
        img3_w  = ctx["img3_w"]
        full_ctx = torch.cat([d1, img1_w, img3_w, flow_t1, flow_t3, mask], dim=1)
        
        res = self.final_fusion(full_ctx)
        
        # Split the 4-channel prediction into RGB and Mask
        res_rgb = res[:, :3, :, :]
        res_mask = res[:, 3:4, :, :]
        
        return res_rgb, res_mask, out_half, out_quarter