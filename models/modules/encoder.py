import torch
import torch.nn as nn

class SEBlock(nn.Module):
    """
    Squeeze-and-Excitation Channel Attention.
    Recalibrates channel-wise feature responses by explicitly 
    modeling interdependencies between channels.
    """
    def __init__(self, channel, reduction=16):
        super(SEBlock, self).__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.fc = nn.Sequential(
            nn.Linear(channel, channel // reduction, bias=False),
            nn.PReLU(),
            nn.Linear(channel // reduction, channel, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        b, c, _, _ = x.size()
        y = self.avg_pool(x).view(b, c)
        y = self.fc(y).view(b, c, 1, 1)
        return x * y.expand_as(x)

class ResBlockSE(nn.Module):
    """
    Standard Residual Block enhanced with Squeeze-and-Excitation.
    Supports spatial downsampling when stride > 1.
    """
    def __init__(self, in_channels, out_channels=None, stride=1):
        super(ResBlockSE, self).__init__()
        if out_channels is None:
            out_channels = in_channels
            
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.act = nn.PReLU()
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1)
        self.se = SEBlock(out_channels)
        
        # Shortcut connection for channel/resolution mismatch
        if stride != 1 or in_channels != out_channels:
            self.shortcut = nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, padding=0)
        else:
            self.shortcut = nn.Identity()

    def forward(self, x):
        res = self.shortcut(x)
        x = self.act(self.conv1(x))
        x = self.se(self.conv2(x))
        return self.act(x + res)

class ResNetSEEncoder(nn.Module):
    """
    Pro-Stage Feature Encoder.
    Extracts deep, semantically rich features at 4 scales:
    1x (64) -> 1/2 (128) -> 1/4 (256) -> 1/8 (512)
    """
    def __init__(self):
        super(ResNetSEEncoder, self).__init__()
        
        # 1x scale (Original Resolution) - 64 Channels
        self.stage1 = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1),
            nn.PReLU(),
            ResBlockSE(64),
            ResBlockSE(64)
        )
        
        # 1/2 scale - 128 Channels
        self.stage2 = nn.Sequential(
            ResBlockSE(64, 128, stride=2),
            ResBlockSE(128),
            ResBlockSE(128)
        )
        
        # 1/4 scale - 256 Channels
        self.stage3 = nn.Sequential(
            ResBlockSE(128, 256, stride=2),
            ResBlockSE(256),
            ResBlockSE(256)
        )
        
        # 1/8 scale - 512 Channels
        self.stage4 = nn.Sequential(
            ResBlockSE(256, 512, stride=2),
            ResBlockSE(512),
            ResBlockSE(512),
            ResBlockSE(512) # Extra depth at the bottleneck
        )

        self._initialize_weights()

    def _initialize_weights(self):
        for m in self.modules():

            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(
                    m.weight,
                    mode="fan_out",
                    nonlinearity="relu"
                )
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

            elif isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)

    def forward(self, x):
        f1 = self.stage1(x)
        f2 = self.stage2(f1)
        f3 = self.stage3(f2)
        f4 = self.stage4(f3)
        return {
            "l1": f1,
            "l2": f2,
            "l3": f3,
            "l4": f4,
        }
    """
    Outputs:

    l1 : [B,64,H,W]

    l2 : [B,128,H/2,W/2]

    l3 : [B,256,H/4,W/4]

    l4 : [B,512,H/8,W/8]
    """