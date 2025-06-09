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
        self.conf = 0.5  # Default confidence
        self.delay = 0.5  # Default delay
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
        self.conf = conf
        self.delay = delay
        if not self.camera.open():
            return False
        self.running = True
        self.paused = False
        # Disable capture button during real-time detection
        if hasattr(self.app, 'controls'):
            self.app.controls.capture_btn.config(state='disabled')
        def loop():
            class_names = None
            color_map = {}
            set_components = []
            skipped_frames = 0
            last_time = time.time()
            frame_count = 0
            fps = 0.0
            if hasattr(self.app, 'controls') and hasattr(self.app.controls, 'detector') and getattr(self.app.controls.detector, 'model', None):
                class_names = self.app.controls.detector.model.names if hasattr(self.app.controls.detector.model, 'names') else None
            board_name = self.app.controls.board_combo.get() if hasattr(self.app, 'controls') else None
            if hasattr(self.app.controls, 'board_manager') and board_name in self.app.controls.board_manager.sets:
                set_components = list(self.app.controls.board_manager.sets[board_name].keys())
            component_colors = getattr(self.app.controls, '_component_colors', {})
            for comp in set_components:
                c = component_colors.get(comp)
                if c:
                    if isinstance(c, str) and c.startswith('#'):
                        h = c.lstrip('#')
                        color_map[comp] = tuple(int(h[i:i+2], 16) for i in (0,2,4))
                    elif isinstance(c, (list, tuple)):
                        color_map[comp] = tuple(int(x) for x in c)
            import random
            for comp in set_components:
                if comp not in color_map:
                    random.seed(comp)
                    color_map[comp] = tuple(random.randint(0,255) for _ in range(3))
            def get_label(class_id):
                if class_names and class_id in class_names:
                    return class_names[class_id]
                return str(class_id)
            while self.running:
                if self.paused:
                    time.sleep(0.1)
                    continue
                # Always fetch latest confidence and delay values from sliders
                if hasattr(self.app, 'controls'):
                    self.conf = self.app.controls.confidence_slider.get()
                    self.delay = self.app.controls.delay_slider.get()
                start_time = time.time()
                ret, frame = self.camera.read()
                if not ret:
                    skipped_frames += 1
                    if hasattr(self.app, 'status_frame'):
                        self.app.status_frame.update_skipped(skipped_frames)
                    continue
                self.frame = frame
                results = self.detector.detect(frame, conf=self.conf)
                frame_with_boxes = frame.copy()
                if results and hasattr(results[0], 'boxes'):
                    filtered_boxes = []
                    for box in results[0].boxes:
                        class_id = int(box.cls[0].item())
                        label = get_label(class_id)
                        if label not in set_components:
                            continue
                        x1, y1, x2, y2 = [int(float(v)) for v in box.xyxy[0]]
                        color = color_map.get(label, (0,255,0))
                        cv2.rectangle(frame_with_boxes, (x1, y1), (x2, y2), color, 2)
                        cv2.putText(frame_with_boxes, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                        filtered_boxes.append(box)
                img = cv2_to_tk(frame_with_boxes)
                self.video_label.config(image=img)
                self.video_label.image = img
                if hasattr(self, 'on_detection'):
                    self.on_detection(results)
                # FPS calculation
                frame_count += 1
                now = time.time()
                elapsed = now - last_time
                if elapsed >= 1.0:
                    fps = frame_count / elapsed
                    frame_count = 0
                    last_time = now
                    if hasattr(self.app, 'status_frame'):
                        self.app.status_frame.update_fps(fps)
                # Wait for the full delay interval before updating the frame again
                total_wait = 0
                while total_wait < self.delay and self.running and not self.paused:
                    time.sleep(0.05)
                    total_wait += 0.05
        threading.Thread(target=loop, daemon=True).start()
        # Set mode label
        if hasattr(self.app, 'status_frame'):
            self.app.status_frame.update_mode('Real-time')
        return True

    def pause_detection(self):
        self.paused = True

    def resume_detection(self):
        self.paused = False

    def stop_detection(self):
        self.running = False
        self.camera.release()
        # Re-enable capture button after stopping real-time detection
        if hasattr(self.app, 'controls'):
            self.app.controls.capture_btn.config(state='normal')

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
