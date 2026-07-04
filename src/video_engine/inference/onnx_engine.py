"""ONNX runtime implementation of InferenceEngine."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort

from .base import InferenceEngine


@dataclass
class ModelSpec:
    """Configuration derived from the ONNX model metadata."""
    input_width: int
    input_height: int
    channels: int


class ONNXInferenceEngine(InferenceEngine):
    """ONNX-backed inference engine."""

    def __init__(self, model_path: str | Path) -> None:
        """Initialize the ONNX inference engine without loading the model.
        
        Args:
            model_path: Path to the .onnx file.
            
        Raises:
            FileNotFoundError: If the model file does not exist.
        """
        super().__init__()
        self._model_path = Path(model_path)
        if not self._model_path.exists():
            raise FileNotFoundError(f"ONNX model not found: {self._model_path}")
            
        self._session: ort.InferenceSession | None = None
        self._input_name: str = ""
        self._output_name: str = ""
        self._input_shape: tuple = ()
        self._output_shape: tuple = ()
        self._model_spec: ModelSpec | None = None

    def load_model(self) -> None:
        """Load the ONNX model and initialize the InferenceSession.
        
        Creates the session, selects the best execution provider, and extracts
        input/output metadata directly from the model.
        """
        if self._session is not None:
            return  # Already loaded
            
        # Detect available providers
        available_providers = ort.get_available_providers()
        providers = []
        if "CUDAExecutionProvider" in available_providers:
            providers.append("CUDAExecutionProvider")
        if "DmlExecutionProvider" in available_providers:
            providers.append("DmlExecutionProvider")
        providers.append("CPUExecutionProvider")
        
        # Create session
        self._session = ort.InferenceSession(str(self._model_path), providers=providers)
        
        # Extract metadata
        session_input = self._session.get_inputs()[0]
        session_output = self._session.get_outputs()[0]
        
        self._input_name = session_input.name
        self._input_shape = tuple(session_input.shape)
        
        self._output_name = session_output.name
        self._output_shape = tuple(session_output.shape)
        
        # Populate model spec (assuming shape is [batch, channels, height, width])
        self._model_spec = ModelSpec(
            input_width=self._input_shape[3],
            input_height=self._input_shape[2],
            channels=self._input_shape[1]
        )

    @property
    def is_loaded(self) -> bool:
        """Return True if the model has been loaded."""
        return self._session is not None
        
    @property
    def input_name(self) -> str:
        """Return the name of the input tensor."""
        return self._input_name
        
    @property
    def output_name(self) -> str:
        """Return the name of the output tensor."""
        return self._output_name
        
    @property
    def input_shape(self) -> tuple:
        """Return the shape of the input tensor."""
        return self._input_shape
        
    @property
    def output_shape(self) -> tuple:
        """Return the shape of the output tensor."""
        return self._output_shape

    @property
    def model_spec(self) -> ModelSpec | None:
        """Return the extracted model configuration."""
        return self._model_spec

    def _preprocess_frames(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Preprocess frames according to model spec and ONNX requirements."""
        import cv2
        from . import preprocessing as P
        
        if not self.model_spec:
            raise RuntimeError("Model spec is not initialized.")
            
        w, h = self.model_spec.input_width, self.model_spec.input_height
        
        # Resize
        left_resized = cv2.resize(left, (w, h))
        right_resized = cv2.resize(right, (w, h))
        
        # BGR -> RGB
        left_rgb = P.bgr_to_rgb(left_resized)
        right_rgb = P.bgr_to_rgb(right_resized)
        
        # Normalize
        left_norm = P.normalize(left_rgb)
        right_norm = P.normalize(right_rgb)
        
        # HWC -> CHW
        left_chw = P.hwc_to_chw(left_norm)
        right_chw = P.hwc_to_chw(right_norm)
        
        # Concat along channels
        tensor = np.concatenate([left_chw, right_chw], axis=0)
        
        # Add batch dim
        return P.add_batch_dim(tensor)

    def _postprocess_frame(self, tensor: np.ndarray, orig_shape: tuple[int, int]) -> np.ndarray:
        """Postprocess the ONNX output tensor back to OpenCV BGR frame."""
        import cv2
        from . import preprocessing as P
        
        # Remove batch dim
        tensor = P.remove_batch_dim(tensor)
        
        # CHW -> HWC
        tensor = P.chw_to_hwc(tensor)
        
        # Denormalize
        tensor_uint8 = P.denormalize(tensor)
        
        # RGB -> BGR
        bgr = P.rgb_to_bgr(tensor_uint8)
        
        # Resize back to original
        h, w = orig_shape
        return cv2.resize(bgr, (w, h))

    def _run_inference(self, input_tensor: np.ndarray) -> np.ndarray:
        """Execute ONNX session run.
        
        Args:
            input_tensor: The fully preprocessed tensor.
            
        Returns:
            The raw output tensor from ONNX Runtime.
            
        Raises:
            RuntimeError: If model is not loaded.
        """
        if not self.is_loaded or self._session is None:
            raise RuntimeError("Model is not loaded.")
            
        outputs = self._session.run(
            [self.output_name],
            {self.input_name: input_tensor}
        )
        return outputs[0]

    def infer(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Run inference using ONNX Runtime.
        
        Args:
            left: The first frame (OpenCV BGR uint8).
            right: The second frame (OpenCV BGR uint8).
            
        Returns:
            The interpolated middle frame.
        """
        if not self.is_loaded:
            raise RuntimeError("Model is not loaded.")
            
        # 1. Record original resolution
        orig_shape = left.shape[:2]
        
        # 2. Preprocess
        input_tensor = self._preprocess_frames(left, right)
        
        # 3. Run Inference
        output_tensor = self._run_inference(input_tensor)
        
        # 4. Postprocess
        result_frame = self._postprocess_frame(output_tensor, orig_shape)
        
        # 5. Return
        return result_frame
