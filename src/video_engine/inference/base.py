"""Base class for Inference Engines."""

from abc import ABC, abstractmethod

import numpy as np


class InferenceEngine(ABC):
    """Abstract base class for all video interpolation inference engines.
    
    This interface ensures that the orchestration pipeline never needs
    to know about backend-specific details like model shapes, color orders, 
    or normalization requirements.
    """

    @abstractmethod
    def infer(self, left: np.ndarray, right: np.ndarray) -> np.ndarray:
        """Run inference to generate a middle frame between two input frames.
        
        Important Interface Contracts:
        - Inputs are raw OpenCV BGR uint8 arrays.
        - Output is also a raw OpenCV BGR uint8 array.
        - Any preprocessing (e.g., BGR->RGB, normalization, tensor shaping) 
          and postprocessing MUST be handled inside the backend implementations.
        
        Args:
            left: The first frame in the pair (OpenCV BGR uint8).
            right: The second frame in the pair (OpenCV BGR uint8).
                
        Returns:
            The generated middle frame (OpenCV BGR uint8).
        """
        pass
