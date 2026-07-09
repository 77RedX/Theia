import torch
import torch.nn as nn
import torch.nn.functional as F

class Warper(nn.Module):
    """
    Efficient optical flow warper.
    Caches the base meshgrids to prevent recreating them on every forward pass.
    """
    def __init__(self):
        super(Warper, self).__init__()
        self.grid_cache = {}

    def forward(self, img, flow):
        """
        Warps an image or feature map using optical flow.
        img: Tensor of shape (B, C, H, W) - Can be RGB or feature maps
        flow: Tensor of shape (B, 2, H, W) - Flow vectors
        """
        B, C, H, W = img.size()
        device = img.device
        
        # Create a unique key for the grid size and device
        key = f"{H}_{W}_{device}"

        # Create or fetch the base meshgrid
        if key not in self.grid_cache:
            # We use indexing='ij' but explicitly assign to y and x 
            # to match the (X, Y) structure of optical flow
            grid_y, grid_x = torch.meshgrid(
                torch.arange(0, H, device=device),
                torch.arange(0, W, device=device),
                indexing='ij'
            )
            # Stack into (1, H, W, 2)
            base_grid = torch.stack((grid_x, grid_y), dim=-1).float().unsqueeze(0)
            self.grid_cache[key] = base_grid

        # Expand base grid to match the batch size
        base_grid = self.grid_cache[key].expand(B, -1, -1, -1)
        
        # Add flow to the grid
        # flow is (B, 2, H, W) -> permute to (B, H, W, 2)
        vgrid = base_grid + flow.permute(0, 2, 3, 1)
        
        # Normalize grid to [-1, 1] for grid_sample
        # Scale factors to convert pixel coordinates to normalized coordinates
        scale = torch.tensor([max(W - 1, 1), max(H - 1, 1)], device=device).float()
        
        vgrid = 2.0 * vgrid / scale - 1.0
        
        # Warp the tensor
        # padding_mode='border' is critical for VFI to prevent black edges bleeding in
        # align_corners=True ensures exact pixel alignment
        return F.grid_sample(img, vgrid, padding_mode='border', align_corners=True)

# Functional wrapper if you ever need to call it without instantiating the class
_global_warper = Warper()

def backwarp(img, flow):
    """Convenience function for one-off warping without tracking state."""
    return _global_warper(img, flow)