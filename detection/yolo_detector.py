# detection/yolo_detector.py
import numpy as np
from ultralytics import YOLO
from .detector import BaseDetector, DetectionResult

class YOLODetector(BaseDetector):
    def __init__(self, weights_path: str, class_names: list[str]):
        self.model = YOLO(weights_path)
        self.class_names = class_names

    def detect(self, frame: np.ndarray) -> list[DetectionResult]:
        results = self.model(frame)[0]
        dets = []
        for cls, box, conf in zip(results.boxes.cls, results.boxes.xyxy, results.boxes.conf):
            name = self.model.names[int(cls)]
            if name in self.class_names:
                x1, y1, x2, y2 = box
                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)
                dets.append(DetectionResult(name, cx, cy, float(conf)))
        return dets
