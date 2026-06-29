#!/usr/bin/env python3

import os
import random
import argparse


def main():
    parser = argparse.ArgumentParser(
        description="Create reproducible train/validation split from Vimeo-90K."
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        required=True,
        help="Path to the original vimeo_triplet directory",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory where train_list.txt and val_list.txt will be saved",
    )

    args = parser.parse_args()

    train_list_path = os.path.join(args.input_dir, "tri_trainlist.txt")

    with open(train_list_path, "r") as f:
        sequences = [line.strip() for line in f if line.strip()]

    random.seed(42)
    random.shuffle(sequences)

    split_idx = int(0.9 * len(sequences))

    train_sequences = sequences[:split_idx]
    val_sequences = sequences[split_idx:]

    os.makedirs(args.output_dir, exist_ok=True)

    train_output = os.path.join(args.output_dir, "train_list.txt")
    val_output = os.path.join(args.output_dir, "val_list.txt")

    with open(train_output, "w") as f:
        f.write("\n".join(train_sequences) + "\n")

    with open(val_output, "w") as f:
        f.write("\n".join(val_sequences) + "\n")

    print(f"Total sequences : {len(sequences)}")
    print(f"Training set    : {len(train_sequences)}")
    print(f"Validation set  : {len(val_sequences)}")
    print(f"Saved train list to: {train_output}")
    print(f"Saved val list to:   {val_output}")


if __name__ == "__main__":
    main()