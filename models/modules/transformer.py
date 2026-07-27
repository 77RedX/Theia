import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint
from models.modules.fusion import (
    PositionEmbedding2D,
    TransformerBlock,
    CrossAttentionFusion,
)

class LocalWindowTransformer(nn.Module):
    """
    Applies Self-Attention to local non-overlapping windows (e.g. 8x8 patches).
    Operates at higher resolutions to restore fine texture efficiently.
    Includes positional encoding injection.
    """
    def __init__(self, dim: int, num_heads: int = 8, window_size: int = 8, depth: int = 2, dropout: float = 0.1):
        super().__init__()
        self.window_size = window_size
        self.pos_embed = PositionEmbedding2D(dim)
        self.blocks = nn.ModuleList([
            TransformerBlock(dim=dim, num_heads=num_heads, dropout=dropout)
            for _ in range(depth)
        ])

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x
        B, C, H, W = x.shape
        
        # Inject positional encoding before partitioning
        x = x + self.pos_embed(B, H, W, x.device)

        # Pad to ensure divisibility by window_size
        pad_h = (self.window_size - H % self.window_size) % self.window_size
        pad_w = (self.window_size - W % self.window_size) % self.window_size
        if pad_h > 0 or pad_w > 0:
            x = F.pad(x, (0, pad_w, 0, pad_h))
            
        _, _, Hp, Wp = x.shape
        
        # Partition into non-overlapping windows
        # [B, C, Hp, Wp] -> [B, C, Hp/Ws, Ws, Wp/Ws, Ws]
        windows = x.reshape(B, C, Hp // self.window_size, self.window_size, Wp // self.window_size, self.window_size)
        # Permute and reshape to sequence: [B * (Hp/Ws) * (Wp/Ws), Ws * Ws, C]
        windows = windows.permute(0, 2, 4, 3, 5, 1).contiguous().reshape(-1, self.window_size * self.window_size, C)
        
        # Apply Self-Attention blocks
        for block in self.blocks:
            windows = block(query=windows, key_value=windows)
            
        # Reverse Partitioning
        out = windows.reshape(B, Hp // self.window_size, Wp // self.window_size, self.window_size, self.window_size, C)
        out = out.permute(0, 5, 1, 3, 2, 4).contiguous().reshape(B, C, Hp, Wp)
        
        # Unpad
        if pad_h > 0 or pad_w > 0:
            out = out[:, :, :H, :W]
            
        # Residual refinement
        return identity + out

class DualScaleTransformer(nn.Module):
    """
    Unified Semantic Reasoning Stage.
    1. Cross-Attention Fusion (1/8 scale)
    2. Global Self-Attention (1/8 scale, Depth 6)
    3. Residual Upsampling to 1/4 scale
    4. Fuse with 1/4 Encoder Features
    5. Local Window Self-Attention (1/4 scale, Depth 2)
    """
    def __init__(self, dim_1x8: int = 512, dim_1x4: int = 256, heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.cross_fusion = CrossAttentionFusion(in_channels=dim_1x8)

        # 2. Global Self-Attention (Depth 6)
        self.global_blocks = nn.ModuleList([
            TransformerBlock(dim=dim_1x8, num_heads=heads, dropout=dropout)
            for _ in range(6)
        ])

        # 3. Upsample & Projection (1/8 -> 1/4)
        self.up_proj = nn.Sequential(
            nn.ConvTranspose2d(dim_1x8, dim_1x4, kernel_size=2, stride=2),
            nn.PReLU()
        )

        # 4. Local Window Self-Attention (Depth 2)
        self.window_transformer = LocalWindowTransformer(dim=dim_1x4, num_heads=heads, window_size=8, depth=2, dropout=dropout)

        self.skip_fusion = nn.Sequential(
            nn.Conv2d(
                dim_1x4 * 2,
                dim_1x4,
                kernel_size=3,
                padding=1
            ),
            nn.PReLU()
        )

    def forward(self, f1_1x8: torch.Tensor, f3_1x8: torch.Tensor, L3_skip: torch.Tensor) -> torch.Tensor:
        """
        Args:
            f1_1x8: Aligned Frame 1 features at 1/8 scale [B, 512, H/8, W/8]
            f3_1x8: Aligned Frame 3 features at 1/8 scale [B, 512, H/8, W/8]
            L3_skip: Fused encoder features at 1/4 scale [B, 256, H/4, W/4]
        Returns:
            Refined features at 1/4 scale ready for the Hierarchical Decoder
        """
        B, C, H, W = f1_1x8.shape

        # --- PART 1: Cross-Attention Fusion ---
        identity_1x8 = self.cross_fusion(f1_1x8, f3_1x8)
        
        # --- PART 2: Global Self-Attention ---
        seq_global = identity_1x8.flatten(2).permute(0, 2, 1)
        for block in self.global_blocks:
            seq_global = checkpoint(block, seq_global, seq_global, use_reentrant=False)
            
        global_out = seq_global.permute(0, 2, 1).reshape(B, C, H, W)
        
        # Residual wrap around the global blocks
        global_out = identity_1x8 + global_out

        # --- PART 3 & 4: Upsample and Local Window Attention ---
        up_feat = self.up_proj(global_out)
        
        # Fuse with 1/4 scale skip connection before local attention
        fused_1x4 = self.skip_fusion(
            torch.cat(
                [up_feat, L3_skip],
                dim=1
            )
        )
        
        final_out = self.window_transformer(fused_1x4)

        return final_out