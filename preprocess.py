#!/usr/bin/env python3

import os
from PIL import Image
from tqdm import tqdm

INPUT_DIR = "/home/akshaygautam4451/Theia/data/vimeo_triplet"
OUTPUT_DIR = "/home/akshaygautam4451/Theia/data/vimeo_triplet_256"

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

    train_list = os.path.join(INPUT_DIR, "tri_trainlist.txt")
    test_list = os.path.join(INPUT_DIR, "tri_testlist.txt")
    
    if not os.path.exists(train_list):
        raise FileNotFoundError(f"tri_trainlist.txt not found in {args.input_dir}. Check your --input_dir path.")

    train_list = os.path.join(INPUT_DIR, "tri_trainlist.txt")
    test_list = os.path.join(INPUT_DIR, "tri_testlist.txt")

    sequences = []
    sequences.extend(read_sequence_list(train_list))
    sequences.extend(read_sequence_list(test_list))

    for seq in tqdm(sequences, desc="Preprocessing"):
        try:
            process_sequence(seq, INPUT_DIR, OUTPUT_DIR)
        except Exception as e:
            print(f"\nSkipped {seq}: {e}")


if __name__ == "__main__":
    main()