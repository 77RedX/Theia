import torch
import torch.nn as nn
import torch.nn.functional as F
from .residual import ResidualBlock
from .feature import BASE_CHANNELS
from .warp import Warper

class FlowBlock(nn.Module):
    # [Same as before]
    def __init__(self, in_channels, hidden_channels=64):
        super(FlowBlock, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, hidden_channels, kernel_size=3, padding=1, bias=False)
        self.act = nn.PReLU(hidden_channels)
        
        self.res1 = ResidualBlock(hidden_channels)
        self.res2 = ResidualBlock(hidden_channels)
        
        self.predict = nn.Conv2d(hidden_channels, 5, kernel_size=3, padding=1)

    def forward(self, x):
        out = self.conv1(x)
        out = self.act(out)
        out = self.res1(out)
        out = self.res2(out)
        return self.predict(out)


class MultiScaleFlow(nn.Module):
    """
    Coarse-to-fine flow estimator that warps features at each level 
    to predict residual corrections.
    """
    def __init__(self, base_channels=BASE_CHANNELS):
        super(MultiScaleFlow, self).__init__()
        
        self.warper = Warper()
        
        c3 = base_channels * 8
        self.block3 = FlowBlock(c3 * 2)
        
        c2 = base_channels * 4
        self.block2 = FlowBlock(c2 * 4 + 5)
        
        c1 = base_channels * 2
        self.block1 = FlowBlock(c1 * 4 + 5)
        
        c0 = base_channels
        self.block0 = FlowBlock(c0 * 4 + 5)

    def _upsample_prediction(self, pred, target_size):
        """Helper to upsample predictions and scale flows safely."""
        up_pred = F.interpolate(
            pred,
            size=target_size,
            mode="bilinear",
            align_corners=False
        )
        flow = up_pred[:, :4, :, :] * 2.0
        mask = up_pred[:, 4:5, :, :]
        return torch.cat([flow, mask], dim=1)

    def forward(self, feats1, feats3):
        # --- Level 3 (Coarse - 1/8) ---
        f3_in = torch.cat([feats1['l3'], feats3['l3']], dim=1)
        pred3 = self.block3(f3_in)
        
        # --- Level 2 (1/4) ---
        up_pred3 = self._upsample_prediction(pred3, feats1['l2'].shape[-2:])
        
        flow0_3 = up_pred3[:, :2, :, :]
        flow1_3 = up_pred3[:, 2:4, :, :]
        
        warp3_l2 = self.warper(feats3['l2'], flow0_3)
        warp1_l2 = self.warper(feats1['l2'], flow1_3)
        
        f2_in = torch.cat([feats1['l2'], feats3['l2'], warp1_l2, warp3_l2, up_pred3], dim=1)
        pred2 = up_pred3 + self.block2(f2_in)
        
        # --- Level 1 (1/2) ---
        up_pred2 = self._upsample_prediction(pred2, feats1['l1'].shape[-2:])
        
        flow0_2 = up_pred2[:, :2, :, :]
        flow1_2 = up_pred2[:, 2:4, :, :]
        
        warp3_l1 = self.warper(feats3['l1'], flow0_2)
        warp1_l1 = self.warper(feats1['l1'], flow1_2)
        
        f1_in = torch.cat([feats1['l1'], feats3['l1'], warp1_l1, warp3_l1, up_pred2], dim=1)
        pred1 = up_pred2 + self.block1(f1_in)
        
        # --- Level 0 (Fine - 1x) ---
        up_pred1 = self._upsample_prediction(pred1, feats1['l0'].shape[-2:])
        
        flow0_1 = up_pred1[:, :2, :, :]
        flow1_1 = up_pred1[:, 2:4, :, :]
        
        warp3_l0 = self.warper(feats3['l0'], flow0_1)
        warp1_l0 = self.warper(feats1['l0'], flow1_1)
        
        f0_in = torch.cat([feats1['l0'], feats3['l0'], warp1_l0, warp3_l0, up_pred1], dim=1)
        pred0 = up_pred1 + self.block0(f0_in)
        
        return {
            "l3": self._format_output(pred3),
            "l2": self._format_output(pred2),
            "l1": self._format_output(pred1),
            "l0": self._format_output(pred0),
        }

    def _format_output(self, pred):
        return {
            "flow0": pred[:, :2, :, :],
            "flow1": pred[:, 2:4, :, :],
            "mask": torch.sigmoid(pred[:, 4:5, :, :])
        }