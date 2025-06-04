from ultralytics import YOLO
import torch

class Detector:
    def __init__(self):
        self.model = None
        self.model_path = None

    def load_model(self, path):
        self.model = YOLO(path)
        self.model_path = path

    def unload_model(self):
        self.model = None
        self.model_path = None
        torch.cuda.empty_cache()

    def detect(self, image, conf=0.5):
        if not self.model:
            return []
        results = self.model(image, conf=conf)
        return results
