import tkinter as tk
from pcb_detect.ui.controls import ControlsFrame
from pcb_detect.ui.video_frame import VideoFrame
from pcb_detect.ui.status_frame import StatusFrame
from pcb_detect.ui.status_bar import StatusBar
from pcb_detect.config_manager import ConfigManager

class PCBDetectApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PCB Component Detection GUI")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        self.config_manager = ConfigManager()
        self._setup_ui()
        self._connect_ui()
        # Start camera on launch
        if hasattr(self, 'video_frame') and hasattr(self.video_frame, 'start_camera'):
            self.video_frame.start_camera()

    def _setup_ui(self):
        # Controls (top)
        self.controls = ControlsFrame(self.root, self)
        self.controls.pack(fill=tk.X, padx=5, pady=5)
        # Video and Status (middle)
        self.middle = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.middle.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.video_frame = VideoFrame(self.middle, self)
        self.status_frame = StatusFrame(self.middle, self)
        self.middle.add(self.video_frame, stretch="always")
        self.middle.add(self.status_frame, stretch="always")
        # Status Bar (bottom)
        self.status_bar = StatusBar(self.root, self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def _connect_ui(self):
        # Connect detection results to status frame
        self.video_frame.on_detection = self._on_detection

    def _on_detection(self, results):
        # Get expected components from selected board
        board_name = self.controls.board_combo.get()
        expected = None
        class_names = None
        if hasattr(self.controls, 'detector') and getattr(self.controls.detector, 'model', None):
            class_names = self.controls.detector.model.names if hasattr(self.controls.detector.model, 'names') else None
        if hasattr(self.controls, 'board_manager') and board_name in self.controls.board_manager.sets:
            expected = self.controls.board_manager.sets[board_name]
        self.status_frame.update_results(results, expected)
        # Log event and add to history (filter to only allowed components)
        allowed_components = set(expected.keys()) if expected else set()
        if results and hasattr(results[0], 'boxes'):
            names = []
            for box in results[0].boxes:
                class_id = int(box.cls[0].item())
                label = class_names[class_id] if class_names and class_id in class_names else str(class_id)
                if not allowed_components or label in allowed_components:
                    names.append(label)
            summary = f"Detected: {', '.join(names)}" if names else "No detections"
        else:
            summary = "No detections"
        self.status_frame.log_event(f"Detection run on board '{board_name}': {summary}")
        self.status_frame.add_history(summary)

    def run(self):
        self.root.mainloop()
