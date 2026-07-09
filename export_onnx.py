import os
import torch

from models.basic_flow import BasicFlowInterp

# ---------------- CONFIG ----------------
CHECKPOINT = "/home/akshaygautam4451/Theia/checkpoints/best_model.pth"
OUTPUT_DIR = "/home/akshaygautam4451/Theia/weights"
OUTPUT_FILE = "basic_model.onnx"

HEIGHT = 256
WIDTH = 448
# ----------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

device = torch.device("cpu")

# Load model
model = BasicFlowInterp().to(device)

ckpt = torch.load(
    CHECKPOINT,
    map_location=device,
    weights_only=False
)

model.load_state_dict(ckpt["model"])
model.eval()


# Wrapper because the model returns a dictionary
class ONNXWrapper(torch.nn.Module):
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, x):
        return self.model(x)["pred"]


wrapper = ONNXWrapper(model)

dummy_input = torch.randn(
    1,
    6,
    HEIGHT,
    WIDTH,
    device=device
)

torch.onnx.export(
    wrapper,
    dummy_input,
    os.path.join(OUTPUT_DIR, OUTPUT_FILE),
    export_params=True,
    opset_version=17,
    do_constant_folding=True,
    input_names=["frames"],
    output_names=["middle_frame"],
    dynamic_axes={
        "frames": {
            0: "batch_size"
        },
        "middle_frame": {
            0: "batch_size"
        }
    },
)

print("ONNX model exported successfully.")
print(f"Saved to: {os.path.join(OUTPUT_DIR, OUTPUT_FILE)}")
