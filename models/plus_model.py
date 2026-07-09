import torch
import torch.nn as nn
from .modules.feature import FeaturePyramid
from .modules.flow import MultiScaleFlow
from .modules.warp import Warper
from .modules.refinement import RefineUNet

class PlusModel(nn.Module):
    """
    Advanced Video Frame Interpolation Model.
    Predicts the intermediate frame between Frame 1 and Frame 3.
    """
    def __init__(self):
        super(PlusModel, self).__init__()
        
        # 1. Feature Extractor
        self.extractor = FeaturePyramid()
        
        # 2. Multi-Scale Flow & Mask Estimator
        self.flow_estimator = MultiScaleFlow()
        
        # 3. Efficient Warper
        self.warper = Warper()
        
        # 4. Residual U-Net Refinement
        self.refinement = RefineUNet()

    def forward(self, img1, img3, training=False):
        """
        img1, img3: Tensors of shape (B, 3, H, W)
        training: If True, returns multi-scale predictions for hierarchical loss.
        """
        # Step 1: Extract hierarchical features for both frames
        feats1 = self.extractor(img1)
        feats3 = self.extractor(img3)
        
        # Step 2: Estimate flow and masks across all scales
        # flow_preds contains dicts for 'l3', 'l2', 'l1', 'l0'
        flow_preds = self.flow_estimator(feats1, feats3)
        
        # Extract the highest resolution (Level 0) predictions
        flow0 = flow_preds['l0']['flow0']
        flow1 = flow_preds['l0']['flow1']
        mask = flow_preds['l0']['mask']
        
        # Step 3: Warp RGB frames and Level 0 (shallow) features
        # Assuming the network inherently predicts the t=0.5 flow vectors
        warp1_img = self.warper(img1, flow0)
        warp3_img = self.warper(img3, flow1)
        
        warp1_feat = self.warper(feats1['l0'], flow0)
        warp3_feat = self.warper(feats3['l0'], flow1)
        
        # Step 4: Refine the output to restore high-frequency details
        final_pred = self.refinement(
            img1=img1, 
            img3=img3, 
            warp1_img=warp1_img, 
            warp3_img=warp3_img, 
            flow0=flow0, 
            flow1=flow1, 
            mask=mask, 
            warp1_feat=warp1_feat, 
            warp3_feat=warp3_feat
        )
        
        if training:
            # Return all multi-scale outputs so you can calculate loss at every pyramid level
            # This drastically improves flow convergence speed.
            return {
                "pred": final_pred,
                "flows_and_masks": flow_preds,
                "base_blend": mask * warp1_img + (1.0 - mask) * warp3_img
            }
        
        return final_pred
