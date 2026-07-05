#!/usr/bin/env python3

import os
import random
import argparse
from PIL import Image, ImageDraw, ImageFont
from tqdm import tqdm



TEXT_POOL = [
    "LIVE",
    "HD",
    "BREAKING NEWS",
    "THEIA",
    "Chapter 1",
    "00:42",
    "CC",
    "SANU",
    "Subtitles enabled",
    "AKSHAY",
    "STEVE",
    "JAYES",
    "SAKAMB"
]

AUGMENT_PROB = 0.5

MAX_DRIFT = 4

WIDTH = 448
HEIGHT = 256



def read_list(path):
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def get_font():
    candidates = [
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\Arial.ttf",
        "C:\\Windows\\Fonts\\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  
    ]
    for f in candidates:
        try:
            return ImageFont.truetype(f, 24)
        except:
            pass
    return ImageFont.load_default()



FONT = get_font()


def stamp_text(img, text, x, y):
    draw = ImageDraw.Draw(img)

    # black outline
    for ox in (-1, 0, 1):
        for oy in (-1, 0, 1):
            draw.text((x + ox, y + oy), text, font=FONT, fill="black")

    # white foreground
    draw.text((x, y), text, font=FONT, fill="white")

    return img


def process_sequence(seq, input_root, output_root, augment_prob):
    
    in_dir = os.path.join(input_root, "sequences", seq)
    out_dir = os.path.join(output_root, "sequences", seq)
    

    os.makedirs(out_dir, exist_ok=True)

    imgs = []

    for name in ("im1.png", "im2.png", "im3.png"):
        img = Image.open(os.path.join(in_dir, name)).convert("RGB")
        imgs.append(img)

    augmented = False

    if random.random() < augment_prob:
        augmented = True

        text = random.choice(TEXT_POOL)

        dummy = ImageDraw.Draw(imgs[0])
        bbox = dummy.textbbox((0, 0), text, font=FONT)

        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]

        x = random.randint(0, max(0, WIDTH - tw - 5))
        y = random.randint(0, max(0, HEIGHT - th - 5))

        dx = random.randint(1, MAX_DRIFT)
        dy = random.randint(1, MAX_DRIFT)

        if x + 2 * dx + tw >= WIDTH:
            dx = 0

        if y + 2 * dy + th >= HEIGHT:
            dy = 0

        positions = [
            (x, y),
            (x + dx, y + dy),
            (x + 2 * dx, y + 2 * dy),
        ]

        for img, (px, py) in zip(imgs, positions):
            stamp_text(img, text, px, py)

    for img, name in zip(imgs, ("im1.png", "im2.png", "im3.png")):
        img.save(os.path.join(out_dir, name))

    return augmented



def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input_dir",
        required=True,
        help="Preprocessed Vimeo dataset",
    )

    parser.add_argument(
        "--output_dir",
        required=True,
        help="Augmented dataset",
    )

    parser.add_argument(
        "--prob",
        type=float,
        default=AUGMENT_PROB,
        help="Probability of augmenting a sequence",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed",
    )

    parser.add_argument(
        "--list_file",
        required=True,
        help="Path to train_list.txt — only training sequences should be augmented",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    

    sequences = read_list(args.list_file)

    augmented = 0

    for seq in tqdm(sequences, desc="Augmenting"):
        if process_sequence(seq, args.input_dir, args.output_dir, args.prob):
            augmented += 1

    print(f"\nAugmented {augmented} sequences out of {len(sequences)} total")


if __name__ == "__main__":
    main()