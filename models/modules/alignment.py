import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint


class ONNXSafeDCN(nn.Module):
    """
    ONNX-Safe Flow-Guided Deformable Convolution.
    Uses 9 explicit F.grid_sample calls centered at standard 3x3 kernel offsets:
      (-1,-1), (-1,0), (-1,1),
      ( 0,-1), ( 0,0), ( 0,1),
      ( 1,-1), ( 1,0), ( 1,1)
    plus learned relative offsets and optical flow.
    """
    def __init__(self, in_channels: int, num_points: int = 9):
        super().__init__()
        self.in_channels = in_channels
        self.num_points = num_points  # 3x3 kernel = 9 sampling points

        # 1. Predict 2*K offsets (x, y per point) and K modulation masks
        self.offset_mask_conv = nn.Sequential(
            nn.Conv2d(in_channels + 2, in_channels, kernel_size=3, padding=1),
            nn.PReLU(),
            nn.Conv2d(in_channels, num_points * 3, kernel_size=3, padding=1)
        )
        
        # Zero-initialize offsets for stable startup
        nn.init.zeros_(self.offset_mask_conv[-1].weight)
        nn.init.zeros_(self.offset_mask_conv[-1].bias)

        # 2. Residual feature projection
        self.project = nn.Sequential(
            nn.Conv2d(in_channels, in_channels, kernel_size=3, padding=1),
            nn.PReLU()
        )

        # 3. Base 3x3 kernel offsets in (dx, dy) pixel coordinates
        base_kernel = torch.tensor([
            [-1, -1], [-1, 0], [-1, 1],
            [ 0, -1], [ 0, 0], [ 0, 1],
            [ 1, -1], [ 1, 0], [ 1, 1]
        ], dtype=torch.float32)  # Shape: (9, 2)
        
        self.register_buffer("base_kernel", base_kernel)
        self.grid_cache = {}
        self.scale_cache = {}

    def forward(self, x: torch.Tensor, flow: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Feature map [B, C, H, W]
            flow: Optical flow map [B, 2, H, W] (dx, dy in pixel space)
        Returns:
            Aligned and refined feature map [B, C, H, W]
        """
        B, C, H, W = x.shape
        device = x.device

        # Predict learned offsets [B, 18, H, W] and raw masks [B, 9, H, W]
        conv_input = torch.cat([x, flow], dim=1)
        out_params = self.offset_mask_conv(conv_input)
        
        learned_offsets = out_params[:, :self.num_points * 2, :, :]  # [B, 18, H, W]
        raw_masks = out_params[:, self.num_points * 2:, :, :]        # [B, 9, H, W]

        # Softmax / sum-normalization across the 9 sampling locations (Normalized Attention Weights)
        masks = torch.softmax(raw_masks, dim=1)     # [B, 9, H, W]

        # Base identity grid in [-1, 1] range (Cached)
        key = f"{H}_{W}_{device}"
        if key not in self.grid_cache:
            grid_y, grid_x = torch.meshgrid(
                torch.linspace(-1.0, 1.0, H, device=device),
                torch.linspace(-1.0, 1.0, W, device=device),
                indexing="ij"
            )
            self.grid_cache[key] = torch.stack([grid_x, grid_y], dim=-1).unsqueeze(0)  # [1, H, W, 2]
            
            # Use torch operations to avoid TracerWarning with Python booleans during ONNX export
            scale_w = torch.clamp(torch.as_tensor(W - 1, device=device, dtype=torch.float32), min=1.0)
            scale_h = torch.clamp(torch.as_tensor(H - 1, device=device, dtype=torch.float32), min=1.0)
            self.scale_cache[key] = torch.stack([scale_w, scale_h])
            
        base_grid = self.grid_cache[key]
        scale = self.scale_cache[key]

        # Scale optical flow to [-1, 1]
        norm_flow = (flow.permute(0, 2, 3, 1) * 2.0) / scale            # [B, H, W, 2]

        # Vectorized 9-point sampling
        # Reshape learned offsets: [B, 18, H, W] -> [B, 9, 2, H, W] -> [B, 9, H, W, 2]
        learned_offsets_reshaped = learned_offsets.view(B, self.num_points, 2, H, W).permute(0, 1, 3, 4, 2)
        
        # Base kernel offsets: [9, 2] -> [1, 9, 1, 1, 2]
        base_offset = self.base_kernel.view(1, self.num_points, 1, 1, 2)
        
        # Total pixel offset: [B, 9, H, W, 2]
        total_pixel_offset = base_offset + learned_offsets_reshaped
        norm_offset = (total_pixel_offset * 2.0) / scale

        # Final sampling grid: [B, 9, H, W, 2]
        sampling_grid = base_grid.unsqueeze(1) + norm_flow.unsqueeze(1) + norm_offset

        # Flatten the 9 grids into the height dimension for a single grid_sample call
        sampling_grid_flat = sampling_grid.contiguous().view(B, self.num_points * H, W, 2)

        # Sample feature via ONNX-supported grid_sample
        # Output shape: [B, C, 9*H, W]
        sampled_feat_flat = F.grid_sample(
            x, sampling_grid_flat, mode='bilinear', padding_mode='border', align_corners=True
        )

        # Reshape back to [B, C, 9, H, W]
        sampled_feat = sampled_feat_flat.view(B, C, self.num_points, H, W)

        # Apply normalized modulation mask weight
        # masks is [B, 9, H, W] -> [B, 1, 9, H, W]
        # Sum over the 9 sampling locations (dim=2) to get [B, C, H, W]
        aligned_feats = torch.sum(sampled_feat * masks.unsqueeze(1), dim=2)

        # Residual Refinement: x + project(aligned_out)
        return x + self.project(aligned_feats)


class FlowGuidedAlignment(nn.Module):
    """
    Wrapper module combining Backward Warp with ONNXSafeDCN refinement.
    """
    def __init__(self, in_channels: int):
        super().__init__()
        self.dcn = ONNXSafeDCN(in_channels)

    def forward(self, x: torch.Tensor, flow: torch.Tensor) -> torch.Tensor:
        # Checkpoint the DCN forward pass to save memory from 9 grid_samples
        return checkpoint(self.dcn, x, flow, use_reentrant=False)