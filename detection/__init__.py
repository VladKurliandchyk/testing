# detection/__init__.py

from .detector import BaseDetector, DetectionResult
from .yolo_detector import YOLODetector

__all__ = [
    "BaseDetector",
    "DetectionResult",
    "YOLODetector",
]