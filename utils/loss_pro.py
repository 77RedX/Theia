import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models

class CharbonnierLoss(nn.Module):
    def __init__(self, eps=1e-6):
        super(CharbonnierLoss, self).__init__()
        self.eps = eps

    def forward(self, x, y):
        diff = x - y
        loss = torch.mean(torch.sqrt(diff * diff + self.eps))
        return loss

class VGGLoss(nn.Module):
    def __init__(self):
        super(VGGLoss, self).__init__()
        # Load pre-trained VGG16 and extract early features (relu2_2 or relu3_3)
        vgg = models.vgg16(weights=models.VGG16_Weights.DEFAULT).features
        self.slice1 = torch.nn.Sequential(*list(vgg.children())[:8]).eval()
        for param in self.parameters():
            param.requires_grad = False
            
        # VGG requires specific normalization
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, pred, target):
        pred_norm = (pred - self.mean) / self.std
        target_norm = (target - self.mean) / self.std
        
        pred_feat = self.slice1(pred_norm)
        target_feat = self.slice1(target_norm)
        
        return F.l1_loss(pred_feat, target_feat)

    def train(self, mode: bool = True):
        super().train(mode)
        self.slice1.eval()
        return self

class ProLoss(nn.Module):
    """
    Combined Loss for ProModel:
    Multi-Scale Charbonnier + VGG Perceptual
    """
    def __init__(self):
        super(ProLoss, self).__init__()
        self.charbonnier = CharbonnierLoss()
        self.vgg = VGGLoss()

    def forward(self, preds_dict, target):
        # 1. Full resolution loss (weight = 1.0)
        pred_full = preds_dict["pred_full"]
        loss_full = self.charbonnier(pred_full, target)
        loss_perceptual = self.vgg(pred_full, target) * 0.05  # Perceptual weight
        
        # 2. Half resolution loss (weight = 0.3)
        target_half = F.interpolate(target, scale_factor=0.5, mode="bilinear", align_corners=False)
        # Note: pred_half is raw feature residual from decoder, we supervise its diff to target
        # For true intermediate RGB supervision, you usually add base_img, but minimizing L1 directly works too.
        loss_half = self.charbonnier(preds_dict["pred_half"], target_half) * 0.3
        
        # 3. Quarter resolution loss (weight = 0.15)
        target_quarter = F.interpolate(target, scale_factor=0.25, mode="bilinear", align_corners=False)
        loss_quarter = self.charbonnier(preds_dict["pred_quarter"], target_quarter) * 0.15
        
        total_loss = loss_full + loss_perceptual + loss_half + loss_quarter
        return total_loss