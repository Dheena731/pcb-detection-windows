import tkinter as tk
from tkinter import ttk
import cv2
from PIL import Image, ImageTk, ImageDraw
from pcb_detect.camera import Camera
from pcb_detect.detection import Detector
from pcb_detect.results_manager import ResultsManager
from pcb_detect.utils import cv2_to_tk
import threading
import time
import numpy as np

class VideoFrame(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="Video Feed")
        self.app = app
        self._build()

    def _build(self):
        self.video_label = tk.Label(self, bg="black", width=640, height=480)
        self.video_label.pack(fill=tk.BOTH, expand=True)
        self.camera = Camera()
        self.detector = Detector()
        self.results_manager = ResultsManager()
        self.running = False
        self.paused = False
        self.frame = None
        self._setup_bindings()

    def _setup_bindings(self):
        self.video_label.bind('<Button-1>', self._on_click)
        # Add more bindings for pan/zoom if needed

    def start_camera(self):
        self.stop_camera()  # Always stop previous camera and thread
        if not self.camera.open():
            return False
        self.running = True
        threading.Thread(target=self._update_frame, daemon=True).start()
        return True

    def stop_camera(self):
        self.running = False
        time.sleep(0.1)  # Give time for thread to exit
        self.camera.release()
        self.video_label.config(image=None)
        self.video_label.image = None

    def _update_frame(self):
        while self.running:
            ret, frame = self.camera.read()
            if not ret:
                continue
            self.frame = frame
            img = cv2_to_tk(frame)
            self.video_label.config(image=img)
            self.video_label.image = img
            time.sleep(0.03)

    def capture_image(self):
        if self.frame is not None:
            return self.frame.copy()
        return None

    def _on_click(self, event):
        # Placeholder for pan/zoom
        pass

    def start_detection(self, conf=0.5):
        if self.frame is not None and self.detector.model:
            results = self.detector.detect(self.frame, conf=conf)
            frame_with_boxes = self.draw_bboxes(self.frame, results)
            img = cv2_to_tk(frame_with_boxes)
            self.video_label.config(image=img)
            self.video_label.image = img
            if hasattr(self, 'on_detection'):
                self.on_detection(results)
            return results
        return None

    def save_snapshot(self):
        if self.frame is not None:
            img = Image.fromarray(cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB))
            self.results_manager.save_snapshot(img)

    def run_realtime_detection(self, conf=0.5, delay=0.5):
        if not self.camera.open():
            return False
        self.running = True
        self.paused = False
        def loop():
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                ret, frame = self.camera.read()
                if not ret:
                    continue
                self.frame = frame
                results = self.detector.detect(frame, conf=conf)
                frame_with_boxes = self.draw_bboxes(frame, results)
                img = cv2_to_tk(frame_with_boxes)
                self.video_label.config(image=img)
                self.video_label.image = img
                if hasattr(self, 'on_detection'):
                    self.on_detection(results)
                time.sleep(delay)
        threading.Thread(target=loop, daemon=True).start()
        return True

    def pause_detection(self):
        self.paused = True

    def resume_detection(self):
        self.paused = False

    def stop_detection(self):
        self.running = False
        self.camera.release()

    def draw_bboxes(self, frame, results):
        # Draw bounding boxes and labels on frame using PIL
        if not results or not hasattr(results[0], 'boxes'):
            return frame
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img)
        for box in results[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = str(box.cls[0].item())
            conf = box.conf[0].item()
            draw.rectangle([x1, y1, x2, y2], outline='red', width=2)
            draw.text((x1, y1), f"{label} {conf:.2f}", fill='yellow')
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def draw_detections(self, frame, detections):
        # Draw bounding boxes and labels using persistent colors
        for det in detections:
            x1, y1, x2, y2 = det['bbox']
            label = det['class']
            color = self.controls._get_color_for_class(label) if hasattr(self, 'controls') else (0,255,0)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        return frame

    def switch_camera(self, camera_index):
        # Stop current camera feed
        self.stop_camera()
        # Set new camera index
        self.camera = Camera(camera_index)
        # Start camera feed
        self.start_camera()
