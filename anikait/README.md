

## What this branch provides

| File | Purpose |
|---|---|
| `preprocess.py` | Resizes all Vimeo-90K images to 256×448 and saves as PNGs |
| `split.py` | Creates reproducible `train_list.txt` and `val_list.txt` from the training sequences |
| `my_dataset.py` | `VimeoTripletDataset` class and `get_dataloaders()` — import this in `train.py` |

---

## Setup

```bash
pip install -r requirements.txt
```

---

## Step 1 — Download the dataset

The dataset is ~32GB and is **not committed to the repo**. Everyone downloads it themselves.

```bash
wget http://data.csail.mit.edu/tofu/dataset/vimeo_triplet.zip
unzip vimeo_triplet.zip
```

This produces a `vimeo_triplet/` folder with:
```
vimeo_triplet/
    sequences/
        00001/0001/im1.png
        00001/0001/im2.png
        00001/0001/im3.png
        ...
    tri_trainlist.txt
    tri_testlist.txt
```

---

## Step 2 — Preprocess (resize all images)

Resizes every image in the dataset to 256×448 and saves to a new directory.  
**Run this once. It takes ~20–40 minutes.**

```bash
python preprocess.py \
    --input_dir /path/to/vimeo_triplet \
    --output_dir /path/to/vimeo_resized
```

---

## Step 3 — Create train/val split

Reads the official training list, shuffles with seed 42, and writes a 90/10 split.

```bash
python split.py \
    --input_dir /path/to/vimeo_triplet \
    --output_dir /path/to/splits
```

Produces:
- `splits/train_list.txt` (~57,000 sequences)
- `splits/val_list.txt` (~6,400 sequences)

---

## Step 4 — Using the dataloader in train.py (Person 1)

Replace the dataset import in `train.py` with:

```python
from my_dataset import get_dataloaders

train_loader, val_loader = get_dataloaders(
    preprocessed_root="/path/to/vimeo_resized",
    train_list="/path/to/splits/train_list.txt",
    val_list="/path/to/splits/val_list.txt",
    batch_size=8,
    num_workers=4,
)
```

Remove `T.Resize((256, 448))` from `dataset.py` — images are already the correct size.

---

## Reproducibility

The train/val split uses `random.seed(42)`. Running `split.py` on any machine produces identical `train_list.txt` and `val_list.txt` files.
