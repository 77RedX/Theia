#!/usr/bin/env python3

import os
import argparse
from PIL import Image
from tqdm import tqdm


TARGET_SIZE = (448, 256) 


def read_sequence_list(list_path):
    
    with open(list_path, "r") as f:
        return [line.strip() for line in f if line.strip()]


def process_sequence(sequence, input_root, output_root):
    
    input_seq_dir = os.path.join(input_root, "sequences", sequence)
    output_seq_dir = os.path.join(output_root, "sequences", sequence)

    os.makedirs(output_seq_dir, exist_ok=True)

    for img_name in ("im1.png", "im2.png", "im3.png"):
        input_path = os.path.join(input_seq_dir, img_name)
        output_path = os.path.join(output_seq_dir, img_name)

        with Image.open(input_path) as img:
            img = img.convert("RGB")
            resized = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
            resized.save(output_path)


def main():
    parser = argparse.ArgumentParser(
        description="Resize Vimeo-90K triplet images to 256x448."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to original vimeo_triplet directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory to save resized dataset",
    )

    args = parser.parse_args()

    train_list = os.path.join(args.input_dir, "tri_trainlist.txt")
    test_list = os.path.join(args.input_dir, "tri_testlist.txt")
    if not os.path.exists(train_list):
        raise FileNotFoundError(f"tri_trainlist.txt not found in {args.input_dir}. Check your --input_dir path.")

    train_list = os.path.join(args.input_dir, "tri_trainlist.txt")
    test_list = os.path.join(args.input_dir, "tri_testlist.txt")

    sequences = []
    sequences.extend(read_sequence_list(train_list))
    sequences.extend(read_sequence_list(test_list))

    for seq in tqdm(sequences, desc="Preprocessing"):
        try:
            process_sequence(seq, args.input_dir, args.output_dir)
        except Exception as e:
            print(f"\nSkipped {seq}: {e}")


if __name__ == "__main__":
    main()