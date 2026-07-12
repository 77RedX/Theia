import os
import torch

from models.plus_model import PlusModel

# ---------------- CONFIG ----------------
CHECKPOINT = "/home/akshaygautam4451/Theia/checkpoints/best_plus_model.pth"
OUTPUT_DIR = "/home/akshaygautam4451/Theia/weights"
OUTPUT_FILE = "plus_model.onnx"

HEIGHT = 256
WIDTH = 448
# ----------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

device = torch.device("cpu")

# Load model
model = PlusModel().to(device)

ckpt = torch.load(
    CHECKPOINT,
    map_location=device,
    weights_only=False
)

model.load_state_dict(ckpt["model"])
# Set to eval mode. For PlusModel, this ensures training=False 
# so it returns the final tensor instead of the multi-scale dictionary.
model.eval()

# PlusModel requires two separate inputs (Frame 1 and Frame 3)
dummy_img1 = torch.randn(1, 3, HEIGHT, WIDTH, device=device)
dummy_img3 = torch.randn(1, 3, HEIGHT, WIDTH, device=device)

# Export the model
torch.onnx.export(
    model,
    (dummy_img1, dummy_img3),               # Pass inputs as a tuple
    os.path.join(OUTPUT_DIR, OUTPUT_FILE),
    export_params=True,
    opset_version=17,                       # Opset 17 is great for grid_sample (warp)
    do_constant_folding=True,
    input_names=["img1", "img3"],           # Name the two input nodes
    output_names=["middle_frame"],          # Name the output node
    dynamic_axes={
        "img1": {0: "batch_size"},
        "img3": {0: "batch_size"},
        "middle_frame": {0: "batch_size"}
    },
)

print("ONNX model exported successfully.")
print(f"Saved to: {os.path.join(OUTPUT_DIR, OUTPUT_FILE)}")