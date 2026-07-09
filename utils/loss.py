import torch
import torch.nn as nn
import torch.nn.functional as F

class CharbonnierLoss(nn.Module):
    """
    Charbonnier Loss: sqrt((x - y)^2 + epsilon^2)
    Acts like L2 for small errors and L1 for large errors.
    """
    def __init__(self, epsilon=1e-6):
        super(CharbonnierLoss, self).__init__()
        self.epsilon = epsilon

    def forward(self, pred, target):
        return torch.mean(torch.sqrt((pred - target) ** 2 + self.epsilon ** 2))

class VFILoss(nn.Module):
    """
    Combines final Refinement Loss with Multi-Scale Flow Alignment Loss.
    """
    def __init__(self):
        super(VFILoss, self).__init__()
        self.charbonnier = CharbonnierLoss()
        
        # Optional: Add SSIM here. 
        # from pytorch_msssim import ssim
        # self.ssim_weight = 0.1

    def forward(self, model_output, gt_img, img1, img3, warper):
        """
        model_output: Dictionary returned from PlusModel(training=True)
        gt_img: Ground truth intermediate frame
        """
        final_pred = model_output["pred"]
        flows_and_masks = model_output["flows_and_masks"]
        
        # 1. Final Refinement Loss
        total_loss = self.charbonnier(final_pred, gt_img)
        
        # Optional SSIM Loss:
        # ssim_loss = 1 - ssim(final_pred, gt_img, data_range=1.0, size_average=True)
        # total_loss += self.ssim_weight * ssim_loss

        # 2. Multi-Scale Base Alignment Loss (Deep Supervision)
        # We downscale the ground truth and input images to match the pyramid levels
        weights = {'l0': 1.0, 'l1': 0.5, 'l2': 0.25, 'l3': 0.125}
        
        for level, weight in weights.items():
            preds = flows_and_masks[level]
            flow0 = preds['flow0']
            flow1 = preds['flow1']
            mask = preds['mask']
            
            # Target dimensions for this pyramid level
            _, _, H, W = flow0.shape
            
            # Downscale frames
            gt_scaled = F.interpolate(gt_img, size=(H, W), mode='area')
            img1_scaled = F.interpolate(img1, size=(H, W), mode='area')
            img3_scaled = F.interpolate(img3, size=(H, W), mode='area')
            
            # Warp scaled inputs
            warp1 = warper(img1_scaled, flow0)
            warp3 = warper(img3_scaled, flow1)
            
            # Base blend at this scale
            blend = mask * warp1 + (1.0 - mask) * warp3
            
            # Add to total loss
            total_loss += weight * self.charbonnier(blend, gt_scaled)
            
        return total_loss