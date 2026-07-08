#!/usr/bin/env python3

import os
import argparse
import numpy as np
import torch
from torch.utils.data import DataLoader
from tqdm import tqdm
from skimage.metrics import peak_signal_noise_ratio as psnr
from skimage.metrics import structural_similarity as ssim
from models.basic_flow import BasicFlowInterp
from dataset import VimeoTripletDataset



def tensor_to_numpy(tensor):
    """
    Convert a tensor of shape (1,3,H,W) to a numpy array (H,W,3).
    """
    img = (
        tensor.squeeze(0)
        .permute(1, 2, 0)
        .detach()
        .cpu()
        .numpy()
        .astype(np.float32)
    )

    return np.clip(img, 0.0, 1.0)


def main():

    parser = argparse.ArgumentParser(
        description="Evaluate BasicFlowInterp on Vimeo-90K."
    )

    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to trained .pth checkpoint",
    )

    parser.add_argument(
        "--data_root",
        required=True,
        help="Path to resized Vimeo dataset",
    )

    parser.add_argument(
        "--test_list",
        required=True,
        help="Path to test_list.txt",
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Path to save evaluation report",
    )

    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = BasicFlowInterp()

    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=False)
    model.load_state_dict(checkpoint["model"])


    model.to(device)
    model.eval()

    dataset = VimeoTripletDataset(
    root=args.data_root,
    list_file=args.test_list,
    )

    loader = DataLoader(
        dataset,
        batch_size=1,
        shuffle=False,
        num_workers=0,
    )

    psnr_scores = []
    ssim_scores = []
    with torch.no_grad():

        for batch in tqdm(loader, desc="Evaluating"):

            x, y = batch

            x = x.to(device)
            y = y.to(device)

            output = model(x)

            pred = output["pred"]

            pred_np = tensor_to_numpy(pred)
            gt_np = tensor_to_numpy(y)

            psnr_value = psnr(
                gt_np,
                pred_np,
                data_range=1.0,
            )

            ssim_value = ssim(
                gt_np,
                pred_np,
                channel_axis=2,
                data_range=1.0,
            )

            psnr_scores.append(psnr_value)
            ssim_scores.append(ssim_value)

    avg_psnr = float(np.mean(psnr_scores))
    avg_ssim = float(np.mean(ssim_scores))

    print("\n========== Evaluation ==========")
    print(f"Average PSNR : {avg_psnr:.4f} dB")
    print(f"Average SSIM : {avg_ssim:.6f}")

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(args.output, "w") as f:
        f.write("Evaluation Report\n")
        f.write("=================\n")
        f.write(f"Checkpoint : {args.checkpoint}\n")
        f.write(f"Dataset    : {args.data_root}\n")
        f.write(f"Test List  : {args.test_list}\n\n")
        f.write(f"Average PSNR : {avg_psnr:.4f} dB\n")
        f.write(f"Average SSIM : {avg_ssim:.6f}\n")

    print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()