import torch
import torch.nn as nn
from torch.utils.checkpoint import checkpoint


class PositionEmbedding2D(nn.Module):
    """
    2D Sinusoidal Positional Encoding for Spatial Feature Maps.
    """
    def __init__(self, channels: int):
        super().__init__()
        self.channels = channels
        half_dim = channels // 4
        inv_freq = 1.0 / (10000 ** (torch.arange(0, half_dim, dtype=torch.float32) / half_dim))
        self.register_buffer("inv_freq", inv_freq)
        self.pos_cache = {}

    def forward(self, B: int, H: int, W: int, device: torch.device) -> torch.Tensor:
        key = f"{H}_{W}_{device}"
        if key not in self.pos_cache:
            pos_x = torch.arange(W, device=device, dtype=torch.float32)
            pos_y = torch.arange(H, device=device, dtype=torch.float32)

            sin_inp_x = torch.einsum("i,j->ij", pos_x, self.inv_freq)
            sin_inp_y = torch.einsum("i,j->ij", pos_y, self.inv_freq)

            emb_x = torch.cat((sin_inp_x.sin(), sin_inp_x.cos()), dim=-1).unsqueeze(0).repeat(H, 1, 1)  # [H, W, C/2]
            emb_y = torch.cat((sin_inp_y.sin(), sin_inp_y.cos()), dim=-1).unsqueeze(1).repeat(1, W, 1)  # [H, W, C/2]

            pos_emb = torch.cat((emb_x, emb_y), dim=-1).permute(2, 0, 1).unsqueeze(0)  # [1, C, H, W]
            self.pos_cache[key] = pos_emb
            
        return self.pos_cache[key].repeat(B, 1, 1, 1)


class TransformerBlock(nn.Module):
    """
    Complete Transformer Encoder Block:
    Norm -> Multihead Cross/Self Attention -> Residual -> Norm -> FFN -> Residual
    """
    def __init__(self, dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn = nn.MultiheadAttention(embed_dim=dim, num_heads=num_heads, dropout=dropout, batch_first=True)
        
        self.norm2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
            nn.Dropout(dropout)
        )

    def forward(self, query: torch.Tensor, key_value: torch.Tensor) -> torch.Tensor:
        # 1. Multi-head Cross/Self Attention with Residual
        norm_q = self.norm1(query)
        norm_kv = self.norm1(key_value)
        
        attn_out, _ = self.attn(query=norm_q, key=norm_kv, value=norm_kv)
        x = query + attn_out

        # 2. Feed-Forward Network with Residual
        x = x + self.ffn(self.norm2(x))
        return x


class CrossAttentionFusion(nn.Module):
    """
    Bidirectional Cross-Attention Fusion for Aligned Features.
    Fuses Frame 1 and Frame 3 features using:
      1. 2D Positional Embeddings
      2. Bidirectional Cross-Attention (Frame 1 -> Frame 3 and Frame 3 -> Frame 1)
      3. Gated Fusion Projection
    """
    def __init__(self, in_channels: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.in_channels = in_channels
        self.pos_embed = PositionEmbedding2D(in_channels)

        # Cross-Attention Transformer Blocks
        self.cross_attn_1to3 = TransformerBlock(dim=in_channels, num_heads=num_heads, dropout=dropout)
        self.cross_attn_3to1 = TransformerBlock(dim=in_channels, num_heads=num_heads, dropout=dropout)

        # Gated blending / feature projection
        self.fusion_gate = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, padding=1),
            nn.PReLU(),
            nn.Conv2d(in_channels, in_channels, kernel_size=1),
            nn.Sigmoid()
        )
        
        self.out_proj = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=3, padding=1),
            nn.PReLU()
        )

    def forward(self, feat1: torch.Tensor, feat3: torch.Tensor) -> torch.Tensor:
        """
        Args:
            feat1: Aligned feature map from Frame 1 [B, C, H, W]
            feat3: Aligned feature map from Frame 3 [B, C, H, W]
        Returns:
            Fused feature representation [B, C, H, W]
        """
        B, C, H, W = feat1.shape
        device = feat1.device

        # Add 2D Positional Encodings
        pos = self.pos_embed(B, H, W, device)
        f1_pos = feat1 + pos
        f3_pos = feat3 + pos

        # Flatten spatial dimensions for Transformer attention: [B, C, H, W] -> [B, H*W, C]
        seq1 = f1_pos.flatten(2).permute(0, 2, 1)
        seq3 = f3_pos.flatten(2).permute(0, 2, 1)

        # Bidirectional Cross-Attention
        fused_seq1 = checkpoint(self.cross_attn_1to3, seq1, seq3, use_reentrant=False)  # Query F1, Key/Val F3
        fused_seq3 = checkpoint(self.cross_attn_3to1, seq3, seq1, use_reentrant=False)  # Query F3, Key/Val F1

        # Reshape tokens back to 2D spatial maps [B, C, H, W]
        f1_attended = fused_seq1.permute(0, 2, 1).reshape(B, C, H, W)
        f3_attended = fused_seq3.permute(0, 2, 1).reshape(B, C, H, W)

        # Adaptive Gated Blending
        gate = self.fusion_gate(torch.cat([f1_attended, f3_attended], dim=1))
        fused_feat = gate * f1_attended + (1.0 - gate) * f3_attended

        # Final projection with residual connection
        base = fused_feat

        out = self.out_proj(
            torch.cat([base, feat1 + feat3], dim=1)
        )

        return base + out