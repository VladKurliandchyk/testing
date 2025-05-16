# detection/detector.py
from abc import ABC, abstractmethod

class DetectionResult:
    def __init__(self, class_name: str, cx: int, cy: int, score: float):
        self.class_name = class_name
        self.cx = cx
        self.cy = cy
        self.score = score

class BaseDetector(ABC):
    @abstractmethod
    def detect(self, frame) -> list[DetectionResult]:
        """
        Принимает numpy-кадр (H×W×3), возвращает список DetectionResult
        """
        pass
