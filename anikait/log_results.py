#!/usr/bin/env python3
import argparse
import re
import wandb


def parse_report(report_path):
    with open(report_path, "r") as f:
        text = f.read()

    psnr = re.search(r"Average\s+PSNR\s*:\s*([\d.]+)", text)
    ssim = re.search(r"Average\s+SSIM\s*:\s*([\d.]+)", text)

    if psnr is None:
        raise ValueError("Average PSNR not found in report.")

    if ssim is None:
        raise ValueError("Average SSIM not found in report.")

    return float(psnr.group(1)), float(ssim.group(1))


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--report", required=True)
    parser.add_argument("--run_name", required=True)
    parser.add_argument("--entity", required=True)
    parser.add_argument("--project", default="theia-vfi")

    args = parser.parse_args()

    psnr, ssim = parse_report(args.report)

    wandb.init(
        project=args.project,
        entity=args.entity,
        name=args.run_name,
        config={                          
        "report": args.report,
        "model": args.run_name,
    }
    )

    wandb.log({
        "PSNR": psnr,
        "SSIM": ssim,
    })

    wandb.finish()

    print(f"Logged PSNR={psnr:.4f}, SSIM={ssim:.6f}")


if __name__ == "__main__":
    main()