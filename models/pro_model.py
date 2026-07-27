import torch
import torch.nn as nn
import torch.nn.functional as F

# Keep the proven Flow and Warp modules
from models.modules.flow import MultiScaleFlow
from models.modules.warp import Warper

# Import the new Pro modules
from models.modules.encoder import ResNetSEEncoder
from models.modules.alignment import FlowGuidedAlignment
from models.modules.transformer import DualScaleTransformer
from models.modules.decoder import HierarchicalDecoder

class ProModel(nn.Module):
    """
    Pro Video Frame Interpolation Architecture.
    Features:
      - ResNet-SE Encoder (1x -> 1/2 -> 1/4 -> 1/8)
      - Flow-Guided Deformable Alignment (DCN)
      - Dual-Scale Transformer Bottleneck (Cross-Attn + Global + Swin)
      - Hierarchical Squeeze-and-Excitation Decoder
    """
    def __init__(self):
        super().__init__()
        
        # 1. Proven Motion Estimator (Outputs multi-scale flow)
        self.flow_estimator = MultiScaleFlow(base_channels=64)
        self.warper = Warper()
        
        # 2. Stronger Feature Extraction
        self.encoder = ResNetSEEncoder()
        
        # 3. Flow-Guided Deformable Alignment
        self.align_1x8 = FlowGuidedAlignment(in_channels=512)
        self.align_1x4 = FlowGuidedAlignment(in_channels=256)
        self.align_1x2 = FlowGuidedAlignment(in_channels=128)
        self.align_1x1 = FlowGuidedAlignment(in_channels=64)
        
        # 4. Transformer Bottleneck (Handles 1/8 and 1/4 scales)
        self.transformer = DualScaleTransformer(dim_1x8=512, dim_1x4=256)
        
        # 5. Deep Decoder
        self.decoder = HierarchicalDecoder()

    def forward(self, img1: torch.Tensor, img3: torch.Tensor):
        # --- 1. Multi-Scale Optical Flow Estimation ---
        feat1 = self.encoder(img1)
        feat3 = self.encoder(img3)
        
        # Map encoder keys to flow estimator keys
        flow_feat1 = {
            "l0": feat1["l1"],
            "l1": feat1["l2"],
            "l2": feat1["l3"],
            "l3": feat1["l4"]
        }
        flow_feat3 = {
            "l0": feat3["l1"],
            "l1": feat3["l2"],
            "l2": feat3["l3"],
            "l3": feat3["l4"]
        }
        
        flow_dict = self.flow_estimator(flow_feat1, flow_feat3)
        
        flow_t1 = flow_dict["l0"]["flow1"]  # 1x scale flow from middle to img1
        flow_t3 = flow_dict["l0"]["flow0"]  # 1x scale flow from middle to img3
        base_mask = flow_dict["l0"]["mask"] # 1x scale base blending mask

        # Basic Image Warping
        img1_w = self.warper(img1, flow_t1)
        img3_w = self.warper(img3, flow_t3)

        # --- 2. Feature Extraction ---
        # f_1x1, f_1x2, f_1x4, f_1x8
        f1_1x1 = feat1["l1"]
        f1_1x2 = feat1["l2"]
        f1_1x4 = feat1["l3"]
        f1_1x8 = feat1["l4"]

        f3_1x1 = feat3["l1"]
        f3_1x2 = feat3["l2"]
        f3_1x4 = feat3["l3"]
        f3_1x8 = feat3["l4"]

        # Use optical flows directly from the multi-scale estimator
        flow_t1_half = flow_dict["l1"]["flow1"]
        flow_t3_half = flow_dict["l1"]["flow0"]
        
        flow_t1_quarter = flow_dict["l2"]["flow1"]
        flow_t3_quarter = flow_dict["l2"]["flow0"]
        
        flow_t1_eighth = flow_dict["l3"]["flow1"]
        flow_t3_eighth = flow_dict["l3"]["flow0"]

        # --- 3. Flow-Guided Deformable Alignment ---
        f1_1x8_w = self.align_1x8(f1_1x8, flow_t1_eighth)
        f3_1x8_w = self.align_1x8(f3_1x8, flow_t3_eighth)

        f1_1x4_w = self.align_1x4(f1_1x4, flow_t1_quarter)
        f3_1x4_w = self.align_1x4(f3_1x4, flow_t3_quarter)

        f1_1x2_w = self.align_1x2(f1_1x2, flow_t1_half)
        f3_1x2_w = self.align_1x2(f3_1x2, flow_t3_half)

        f1_1x1_w = self.align_1x1(f1_1x1, flow_t1)
        f3_1x1_w = self.align_1x1(f3_1x1, flow_t3)

        # --- 4. Semantic Reasoning (Transformer Bottleneck) ---
        # Fuses f1_1x4_w and f3_1x4_w as the L3 skip connection
        L3_skip = f1_1x4_w + f3_1x4_w 
        dec_quarter = self.transformer(f1_1x8_w, f3_1x8_w, L3_skip)

        # --- 5. Hierarchical Decoding ---
        skips_half = [f1_1x2_w, f3_1x2_w]
        skips_full = [f1_1x1_w, f3_1x1_w]
        
        ctx = {
            "flow_t1": flow_t1,
            "flow_t3": flow_t3,
            "mask": base_mask,
            "img1_w": img1_w,
            "img3_w": img3_w
        }

        res_rgb, res_mask, out_half, out_quarter = self.decoder(
            dec_quarter, 
            skips_half, 
            skips_full, 
            ctx
        )

        # --- 6. Final Blending ---
        # Refine the base mask with the predicted residual (base_mask is already sigmoided in flow.py)
        final_mask = torch.clamp(base_mask + res_mask, 0.0, 1.0)
        
        # Base linear blend using the refined mask
        blended_img = img1_w * final_mask + img3_w * (1.0 - final_mask)
        
        # Add the RGB residual details
        pred_full = blended_img + res_rgb

        if self.training:
            # During training, return deep supervision outputs
            return {
                "pred_full": pred_full,  # Unclamped during training to prevent dead gradients
                "pred_half": torch.sigmoid(out_half),      # Map 1/2 scale deep supervision to [0, 1]
                "pred_quarter": torch.sigmoid(out_quarter) # Map 1/4 scale deep supervision to [0, 1]
            }
        
        # During inference (and ONNX export), return the clamped final frame
        return torch.clamp(pred_full, 0.0, 1.0)