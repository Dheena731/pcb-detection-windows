import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from pcb_detect.model_manager import ModelManager
from pcb_detect.detection import Detector
from pcb_detect.board_manager import BoardManager
from pcb_detect.batch_manager import BatchManager
from pcb_detect.ui.dialogs import Dialogs
from pcb_detect.ui.tooltips import add_tooltip
import cv2

class ControlsFrame(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="Controls")
        self.app = app
        self._build()

    def _build(self):
        # Model Controls
        self.model_label = ttk.Label(self, text="Model:")
        self.model_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.model_combo = ttk.Combobox(self, values=[], width=25)
        self.model_combo.grid(row=0, column=1, padx=5, pady=2)
        self.load_btn = ttk.Button(self, text="Load")
        self.upload_btn = ttk.Button(self, text="Upload")
        self.unload_btn = ttk.Button(self, text="Unload")
        self.delete_btn = ttk.Button(self, text="Delete")
        self.load_btn.grid(row=0, column=2, padx=2)
        self.upload_btn.grid(row=0, column=3, padx=2)
        self.unload_btn.grid(row=0, column=4, padx=2)
        self.delete_btn.grid(row=0, column=5, padx=2)
        add_tooltip(self.model_combo, "Select a YOLO model from the list.")
        add_tooltip(self.upload_btn, "Upload a new YOLO model (.pt file).")
        # Board Controls
        self.board_label = ttk.Label(self, text="Board Type:")
        self.board_label.grid(row=0, column=6, padx=10, pady=2, sticky='w')
        self.board_combo = ttk.Combobox(self, values=[], width=25)
        self.board_combo.grid(row=0, column=7, padx=5, pady=2)
        self.new_set_btn = ttk.Button(self, text="New Set")
        self.edit_set_btn = ttk.Button(self, text="Edit Set")
        self.delete_set_btn = ttk.Button(self, text="Delete Set")
        self.setup_btn = ttk.Button(self, text="Setup")
        self.new_set_btn.grid(row=0, column=8, padx=2)
        self.edit_set_btn.grid(row=0, column=9, padx=2)
        self.delete_set_btn.grid(row=0, column=10, padx=2)
        self.setup_btn.grid(row=0, column=11, padx=2)
        add_tooltip(self.board_combo, "Select a board type or configure a new one.")
        # Camera Controls
        self.camera_label = ttk.Label(self, text="Camera:")
        self.camera_label.grid(row=0, column=12, padx=10, pady=2, sticky='w')
        self.camera_combo = ttk.Combobox(self, values=self._get_camera_list(), width=10)
        self.camera_combo.grid(row=0, column=13, padx=5, pady=2)
        self.camera_combo.bind("<<ComboboxSelected>>", self._on_camera_selected)
        # Action Buttons (Row 1)
        self.capture_btn = ttk.Button(self, text="Capture Image")
        self.start_btn = ttk.Button(self, text="Start Real-time")
        self.pause_btn = ttk.Button(self, text="Pause")
        self.stop_btn = ttk.Button(self, text="Stop")
        self.export_btn = ttk.Button(self, text="Export Snapshot")
        self.continue_btn = ttk.Button(self, text="Continue")
        self.capture_btn.grid(row=1, column=0, padx=2, pady=4)
        self.start_btn.grid(row=1, column=1, padx=2)
        self.pause_btn.grid(row=1, column=2, padx=2)
        self.stop_btn.grid(row=1, column=3, padx=2)
        self.export_btn.grid(row=1, column=4, padx=2)
        self.continue_btn.grid(row=1, column=5, padx=2)
        add_tooltip(self.capture_btn, "Capture a single image for detection.")
        add_tooltip(self.start_btn, "Start real-time detection mode.")
        # Settings (Row 2)
        self.zoom_in_btn = ttk.Button(self, text="Zoom In")
        self.zoom_out_btn = ttk.Button(self, text="Zoom Out")
        self.colors_btn = ttk.Button(self, text="Colors")
        self.batches_btn = ttk.Button(self, text="Batches")
        self.auto_save_var = tk.BooleanVar(value=True)
        self.batch_proc_var = tk.BooleanVar(value=False)
        self.auto_save_chk = ttk.Checkbutton(self, text="Auto-save Snapshots", variable=self.auto_save_var)
        self.batch_proc_chk = ttk.Checkbutton(self, text="Batch Processing", variable=self.batch_proc_var)
        self.zoom_in_btn.grid(row=2, column=0, padx=2, pady=2)
        self.zoom_out_btn.grid(row=2, column=1, padx=2)
        self.colors_btn.grid(row=2, column=2, padx=2)
        self.batches_btn.grid(row=2, column=3, padx=2)
        self.auto_save_chk.grid(row=2, column=4, padx=2)
        self.batch_proc_chk.grid(row=2, column=5, padx=2)
        # Sliders (Row 3)
        self.confidence_label = ttk.Label(self, text="Confidence:")
        self.confidence_slider = ttk.Scale(self, from_=0.1, to=1.0, orient=tk.HORIZONTAL)
        self.confidence_slider.set(0.5)
        self.delay_label = ttk.Label(self, text="Delay (s):")
        self.delay_slider = ttk.Scale(self, from_=0.1, to=2.0, orient=tk.HORIZONTAL)
        self.delay_slider.set(0.5)
        self.confidence_label.grid(row=3, column=0, padx=2, pady=2)
        self.confidence_slider.grid(row=3, column=1, padx=2, pady=2)
        self.delay_label.grid(row=3, column=2, padx=2, pady=2)
        self.delay_slider.grid(row=3, column=3, padx=2, pady=2)
        self._refresh_models()
        self.load_btn.config(command=self._on_load_model)
        self.upload_btn.config(command=self._on_upload_model)
        self.unload_btn.config(command=self._on_unload_model)
        self.delete_btn.config(command=self._on_delete_model)
        self._refresh_boards()
        self.new_set_btn.config(command=self._on_new_set)
        self.edit_set_btn.config(command=self._on_edit_set)
        self.delete_set_btn.config(command=self._on_delete_set)
        self.setup_btn.config(command=self._on_setup_set)
        self.batches_btn.config(command=self._on_batches)
        self.batch_proc_chk.config(command=self._on_batch_toggle)
        self.capture_btn.config(command=self._on_capture)
        self.start_btn.config(command=self._on_start_realtime)
        self.pause_btn.config(command=self._on_pause)
        self.stop_btn.config(command=self._on_stop)
        self.export_btn.config(command=self._on_export_snapshot)
        self.continue_btn.config(command=self._on_continue)

    def _get_camera_list(self):
        # Try to find available cameras (0-4)
        available = []
        for idx in range(5):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                available.append(f"Camera {idx}")
                cap.release()
        return available if available else ["Camera 0"]

    def _refresh_models(self):
        models = ModelManager.list_models()
        self.model_combo['values'] = models
        if models:
            self.model_combo.current(0)

    def _on_load_model(self):
        model_name = self.model_combo.get()
        if not model_name:
            Dialogs.error("No Model Selected", "Please select a model to load.")
            return
        model_path = os.path.join(ModelManager.MODELS_DIR, model_name)
        if not hasattr(self, 'detector'):
            self.detector = Detector()
        try:
            self.detector.load_model(model_path)
            Dialogs.info("Model Loaded", f"Model '{model_name}' loaded successfully.")
        except Exception as e:
            Dialogs.error("Model Load Error", str(e))

    def _on_upload_model(self):
        file_path = filedialog.askopenfilename(title="Select YOLO Model", filetypes=[("PyTorch Model", "*.pt")])
        if file_path:
            try:
                ModelManager.upload_model(file_path)
                self._refresh_models()
                Dialogs.info("Model Uploaded", "Model uploaded successfully.")
            except Exception as e:
                Dialogs.error("Upload Error", str(e))

    def _on_unload_model(self):
        if hasattr(self, 'detector') and self.detector.model:
            self.detector.unload_model()
            Dialogs.info("Model Unloaded", "Model unloaded from memory.")
        else:
            Dialogs.info("No Model Loaded", "No model is currently loaded.")

    def _on_delete_model(self):
        model_name = self.model_combo.get()
        if not model_name:
            Dialogs.error("No Model Selected", "Please select a model to delete.")
            return
        if Dialogs.confirm("Delete Model", f"Are you sure you want to delete '{model_name}'?"):
            if ModelManager.delete_model(model_name):
                self._refresh_models()
                Dialogs.info("Model Deleted", f"Model '{model_name}' deleted.")
            else:
                Dialogs.error("Delete Error", "Model could not be deleted.")

    def _refresh_boards(self):
        self.board_manager = BoardManager()
        boards = list(self.board_manager.sets.keys())
        self.board_combo['values'] = boards
        if boards:
            self.board_combo.current(0)

    def _on_new_set(self):
        name = Dialogs.ask_string("New Board Set", "Enter new board set name:")
        if name:
            if name in self.board_manager.sets:
                Dialogs.error("Exists", "A set with this name already exists.")
                return
            self.board_manager.add_set(name, {})
            self._refresh_boards()
            Dialogs.info("Set Created", f"Board set '{name}' created.")

    def _on_edit_set(self):
        name = self.board_combo.get()
        if not name:
            Dialogs.error("No Set Selected", "Please select a set to edit.")
            return
        # For demo: just edit as empty dict
        self.board_manager.edit_set(name, {})
        Dialogs.info("Set Edited", f"Board set '{name}' updated.")

    def _on_delete_set(self):
        name = self.board_combo.get()
        if not name:
            Dialogs.error("No Set Selected", "Please select a set to delete.")
            return
        if Dialogs.confirm("Delete Set", f"Are you sure you want to delete '{name}'?"):
            self.board_manager.delete_set(name)
            self._refresh_boards()
            Dialogs.info("Set Deleted", f"Board set '{name}' deleted.")

    def _on_setup_set(self):
        Dialogs.info("Setup", "Custom board setup not yet implemented.")

    def _on_batches(self):
        bm = BatchManager()
        name = Dialogs.ask_string("New Batch", "Enter batch name:")
        if name:
            bm.create_batch(name)
            Dialogs.info("Batch Created", f"Batch '{name}' created.")

    def _on_batch_toggle(self):
        enabled = self.batch_proc_var.get()
        Dialogs.info("Batch Processing", f"Batch processing {'enabled' if enabled else 'disabled'}.")

    def _on_capture(self):
        frame = self.app.video_frame.capture_image()
        if frame is not None:
            results = self.app.video_frame.start_detection(conf=self.confidence_slider.get())
            if results is not None and hasattr(results[0], 'boxes'):
                num_objs = len(results[0].boxes)
            else:
                num_objs = 0
            Dialogs.info("Detection", f"Detected {num_objs} objects.")
        else:
            Dialogs.error("No Frame", "No image to capture.")

    def _on_start_realtime(self):
        conf = self.confidence_slider.get()
        delay = self.delay_slider.get()
        self.app.video_frame.run_realtime_detection(conf=conf, delay=delay)
        Dialogs.info("Real-time", "Started real-time detection.")

    def _on_pause(self):
        self.app.video_frame.pause_detection()
        Dialogs.info("Paused", "Detection paused.")

    def _on_stop(self):
        self.app.video_frame.stop_detection()
        Dialogs.info("Stopped", "Detection stopped.")

    def _on_export_snapshot(self):
        self.app.video_frame.save_snapshot()
        Dialogs.info("Snapshot", "Snapshot exported.")

    def _on_continue(self):
        self.app.video_frame.resume_detection()
        Dialogs.info("Continue", "Detection resumed.")

    def _on_camera_selected(self, event=None):
        cam_idx = self.camera_combo.current()
        if hasattr(self.app.video_frame, 'camera'):
            self.app.video_frame.camera.camera_index = cam_idx
            self.app.video_frame.stop_camera()
            self.app.video_frame.start_camera()
        # Optionally, show a message or log event
