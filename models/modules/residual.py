import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    """
    Standard Residual Block with activation after the addition.
    Maintains spatial dimensions and channel counts.
    """
    def __init__(self, channels):
        super(ResidualBlock, self).__init__()
        self.conv1 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)
        self.act = nn.PReLU(channels)
        self.conv2 = nn.Conv2d(channels, channels, kernel_size=3, padding=1, bias=False)

    def forward(self, x):
        out = self.conv1(x)
        out = self.act(out)
        out = self.conv2(out)
        
        # Activation after addition
        out = out + x
        out = self.act(out)
        
        return out


class DownBlock(nn.Module):
    """
    Downsampling block for the Multi-Scale/U-Net pyramids.
    Uses strided convolution for spatial reduction followed by a ResidualBlock.
    """
    def __init__(self, in_channels, out_channels):
        super(DownBlock, self).__init__()
        self.down = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=2, padding=1, bias=False),
            nn.PReLU(out_channels),
            ResidualBlock(out_channels)
        )

    def forward(self, x):
        return self.down(x)


class UpBlock(nn.Module):
    """
    Upsampling block for the U-Net refinement.
    Order: Upsample -> Concat Skip -> Conv -> PReLU -> ResidualBlock
    """
    def __init__(self, in_channels, skip_channels, out_channels):
        super(UpBlock, self).__init__()
        self.up = nn.Upsample(scale_factor=2, mode='bilinear', align_corners=False)
        
        # Convolution takes the sum of upsampled channels and skip channels
        self.conv = nn.Conv2d(in_channels + skip_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.act = nn.PReLU(out_channels)
        self.res = ResidualBlock(out_channels)

    def forward(self, x1, x2):
        # 1. Upsample
        out = self.up(x1)
        
        # Pad if spatial dimensions don't match exactly (due to odd input sizes)
        diffY = x2.size()[2] - out.size()[2]
        diffX = x2.size()[3] - out.size()[3]
        if diffY > 0 or diffX > 0:
            out = F.pad(out, [diffX // 2, diffX - diffX // 2,
                              diffY // 2, diffY - diffY // 2])
            
        # 2. Concatenate Skip
        out = torch.cat([x2, out], dim=1)
        
        # 3. Conv 3x3
        out = self.conv(out)
        
        # 4. PReLU
        out = self.act(out)
        
        # 5. Residual Block
        out = self.res(out)
        
        return out