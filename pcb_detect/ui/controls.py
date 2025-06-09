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
import json
import threading
import time
import datetime

class ControlsFrame(ttk.LabelFrame):
    def __init__(self, parent, app):
        super().__init__(parent, text="Controls")
        self.app = app
        self._load_component_colors()
        self._build()

    def _build(self):
        # Model Controls
        self.model_label = ttk.Label(self, text="Model:")
        self.model_label.grid(row=0, column=0, padx=5, pady=2, sticky='w')
        self.model_combo = ttk.Combobox(self, values=[], width=25)
        self.model_combo.grid(row=0, column=1, padx=5, pady=2)
        self.load_btn = ttk.Button(self, text="Load")
        self.upload_btn = ttk.Button(self, text="Upload model")
        self.unload_btn = ttk.Button(self, text="Unload model")
        self.delete_btn = ttk.Button(self, text="Delete model")
        self.load_btn.grid(row=0, column=2, padx=2)
        self.upload_btn.grid(row=0, column=3, padx=2)
        self.unload_btn.grid(row=0, column=4, padx=2)
        self.delete_btn.grid(row=0, column=5, padx=2)
        add_tooltip(self.model_combo, "Select a model from the list.")
        add_tooltip(self.upload_btn, "Upload a new model (.pt file).")
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
        self.colors_btn.config(command=self._on_colors)

    def _get_camera_list(self):
        # Try to find available cameras (0-4)
        available = []
        for idx in range(5):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
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
            if hasattr(self.app, 'status_frame') and self.detector.model:
                self.app.status_frame.log_event(f"[INFO] Model '{model_name}' loaded from '{model_path}'")
                try:
                    class_names = self.detector.model.names if hasattr(self.detector.model, 'names') else None
                    if class_names:
                        self.app.status_frame.log_event(f"[INFO] Model classes: {', '.join([f'{i}: {c}' for i, c in class_names.items()])}")
                    else:
                        self.app.status_frame.log_event("[WARN] Model loaded, but class names could not be determined.")
                except Exception as e:
                    self.app.status_frame.log_event(f"[ERROR] Error reading model classes: {e}")
        except Exception as e:
            Dialogs.error("Model Load Error", str(e))
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event(f"[ERROR] Model load failed: {e}")

    def _on_upload_model(self):
        file_path = filedialog.askopenfilename(title="Select Model", filetypes=[("PyTorch Model", "*.pt")])
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
        # Open a single dialog for set name and component editing
        editor = tk.Toplevel(self)
        editor.title("Create New Board Set")
        editor.geometry("420x400")
        # Set name
        tk.Label(editor, text="Set Name:").pack(anchor='w', padx=10, pady=(10,2))
        set_name_var = tk.StringVar()
        set_name_entry = tk.Entry(editor, textvariable=set_name_var, width=30)
        set_name_entry.pack(anchor='w', padx=10, pady=(0,8))
        # Table for components
        columns = ("Component", "Quantity")
        comp_tree = ttk.Treeview(editor, columns=columns, show="headings", height=8)
        for col in columns:
            comp_tree.heading(col, text=col)
            comp_tree.column(col, width=150, anchor='center')
        comp_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # Entry for component name and quantity
        entry_frame = tk.Frame(editor)
        entry_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(entry_frame, text="Component:").pack(side=tk.LEFT)
        comp_entry = tk.Entry(entry_frame, width=15)
        comp_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(entry_frame, text="Qty:").pack(side=tk.LEFT)
        qty_entry = tk.Entry(entry_frame, width=5)
        qty_entry.pack(side=tk.LEFT, padx=2)
        # Add/Update button
        components = {}
        def add_or_update():
            comp = comp_entry.get().strip()
            try:
                qty = int(qty_entry.get())
            except Exception:
                Dialogs.error("Invalid Quantity", "Enter a valid integer quantity.")
                return
            if not comp or qty < 1:
                Dialogs.error("Invalid Input", "Component name and quantity required.")
                return
            components[comp] = qty
            refresh_table()
            comp_entry.delete(0, tk.END)
            qty_entry.delete(0, tk.END)
        def refresh_table():
            comp_tree.delete(*comp_tree.get_children())
            for c, q in components.items():
                comp_tree.insert('', tk.END, values=(c, q))
        add_btn = tk.Button(editor, text="Add/Update Component", command=add_or_update)
        add_btn.pack(pady=2)
        # Delete button
        def del_comp():
            sel = comp_tree.selection()
            if not sel:
                return
            comp = comp_tree.item(sel[0])['values'][0]
            if comp in components:
                del components[comp]
                refresh_table()
        del_btn = tk.Button(editor, text="Delete Selected Component", command=del_comp)
        del_btn.pack(pady=2)
        # Save button
        def save_set():
            set_name = set_name_var.get().strip()
            if not set_name:
                Dialogs.error("No Name", "Enter a set name.")
                return
            if not components:
                Dialogs.error("No Components", "Add at least one component.")
                return
            self.board_manager.add_set(set_name, components)
            self._refresh_boards()
            Dialogs.info("Set Created", f"Board set '{set_name}' created.")
            editor.destroy()
        save_btn = tk.Button(editor, text="Save Set", command=save_set)
        save_btn.pack(pady=5)

    def _on_edit_set(self):
        name = self.board_combo.get()
        if not name:
            Dialogs.error("No Set Selected", "Please select a set to edit.")
            return
        # Get current components
        components_orig = self.board_manager.sets.get(name, {})
        editor = tk.Toplevel(self)
        editor.title(f"Edit Board Set: {name}")
        editor.geometry("420x400")
        # Set name
        tk.Label(editor, text="Set Name:").pack(anchor='w', padx=10, pady=(10,2))
        set_name_var = tk.StringVar(value=name)
        set_name_entry = tk.Entry(editor, textvariable=set_name_var, width=30)
        set_name_entry.pack(anchor='w', padx=10, pady=(0,8))
        # Table for components
        columns = ("Component", "Quantity")
        comp_tree = ttk.Treeview(editor, columns=columns, show="headings", height=8)
        for col in columns:
            comp_tree.heading(col, text=col)
            comp_tree.column(col, width=150, anchor='center')
        comp_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        # Populate with existing components
        components = dict(components_orig)
        def refresh_table():
            comp_tree.delete(*comp_tree.get_children())
            for c, q in components.items():
                comp_tree.insert('', tk.END, values=(c, q))
        refresh_table()
        # Double-click to edit component name or quantity
        def on_double_click(event):
            item = comp_tree.identify_row(event.y)
            col = comp_tree.identify_column(event.x)
            if not item:
                return
            values = comp_tree.item(item, 'values')
            if col == '#1':  # Component name
                x, y, width, height = comp_tree.bbox(item, 'Component')
                entry = tk.Entry(comp_tree, width=15)
                entry.insert(0, values[0])
                entry.place(x=x, y=y, width=width, height=height)
                entry.focus()
                def save_edit(event=None):
                    new_name = entry.get().strip()
                    if not new_name:
                        entry.destroy()
                        return
                    old_name = values[0]
                    qty = int(values[1])
                    if new_name != old_name and new_name in components:
                        Dialogs.error("Exists", "A component with this name already exists.")
                        entry.destroy()
                        return
                    del components[old_name]
                    components[new_name] = qty
                    refresh_table()
                    entry.destroy()
                entry.bind('<Return>', save_edit)
                entry.bind('<FocusOut>', save_edit)
            elif col == '#2':  # Quantity
                x, y, width, height = comp_tree.bbox(item, 'Quantity')
                entry = tk.Entry(comp_tree, width=5)
                entry.insert(0, values[1])
                entry.place(x=x, y=y, width=width, height=height)
                entry.focus()
                def save_edit(event=None):
                    try:
                        v = int(entry.get())
                        if v < 1:
                            raise ValueError
                        comp_name = values[0]
                        components[comp_name] = v
                        refresh_table()
                    except Exception:
                        pass
                    entry.destroy()
                entry.bind('<Return>', save_edit)
                entry.bind('<FocusOut>', save_edit)
        comp_tree.bind('<Double-1>', on_double_click)
        # Entry for component name and quantity
        entry_frame = tk.Frame(editor)
        entry_frame.pack(fill=tk.X, padx=10, pady=2)
        tk.Label(entry_frame, text="Component:").pack(side=tk.LEFT)
        comp_entry = tk.Entry(entry_frame, width=15)
        comp_entry.pack(side=tk.LEFT, padx=2)
        tk.Label(entry_frame, text="Qty:").pack(side=tk.LEFT)
        qty_entry = tk.Entry(entry_frame, width=5)
        qty_entry.pack(side=tk.LEFT, padx=2)
        # Add/Update button
        def add_or_update():
            comp = comp_entry.get().strip()
            try:
                qty = int(qty_entry.get())
            except Exception:
                Dialogs.error("Invalid Quantity", "Enter a valid integer quantity.")
                return
            if not comp or qty < 1:
                Dialogs.error("Invalid Input", "Component name and quantity required.")
                return
            components[comp] = qty
            refresh_table()
            comp_entry.delete(0, tk.END)
            qty_entry.delete(0, tk.END)
        add_btn = tk.Button(editor, text="Add/Update Component", command=add_or_update)
        add_btn.pack(pady=2)
        # Delete button
        def del_comp():
            sel = comp_tree.selection()
            if not sel:
                return
            comp = comp_tree.item(sel[0])['values'][0]
            if comp in components:
                del components[comp]
                refresh_table()
        del_btn = tk.Button(editor, text="Delete Selected Component", command=del_comp)
        del_btn.pack(pady=2)
        # Save button
        def save_set():
            set_name = set_name_var.get().strip()
            if not set_name:
                Dialogs.error("No Name", "Enter a set name.")
                return
            if not components:
                Dialogs.error("No Components", "Add at least one component.")
                return
            # If renaming, check for conflicts
            if set_name != name and set_name in self.board_manager.sets:
                Dialogs.error("Exists", "A set with this name already exists.")
                return
            # Remove old set if renamed
            if set_name != name:
                self.board_manager.delete_set(name)
            self.board_manager.add_set(set_name, components)
            self._refresh_boards()
            Dialogs.info("Set Edited", f"Board set '{set_name}' updated.")
            editor.destroy()
        save_btn = tk.Button(editor, text="Save Changes", command=save_set)
        save_btn.pack(pady=5)
        set_name_entry.focus()

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
        from pcb_detect.ui import setup_components
        import tkinter as tk
        from tkinter import simpledialog, filedialog
        print("[DEBUG] _on_setup_set called")
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'stop_camera'):
            print("[DEBUG] Stopping main video feed for setup dialog")
            self.app.video_frame.stop_camera()
        name = self.board_combo.get()
        if not name:
            print("[ERROR] No board set selected for setup dialog")
            Dialogs.error("No Set Selected", "Please select a board set before setup.")
            return
        # Call the new setup dialog
        setup_components.setup_component_dialog(
            parent=self,
            app=self.app,
            model_name=self.model_combo.get(),
            board_name=name,
            camera_name=self.camera_combo.get(),
            board_manager=self.board_manager,
            detector=getattr(self, 'detector', None),
            video_frame=getattr(self.app, 'video_frame', None),
            add_tooltip=add_tooltip,
            Dialogs=Dialogs
        )

    def _get_color_for_class(self, label):
        if not hasattr(self, '_component_colors'):
            self._load_component_colors()
        color = self._component_colors.get(label)
        if color:
            if isinstance(color, str) and color.startswith('#'):
                # Convert hex to BGR
                h = color.lstrip('#')
                return tuple(int(h[i:i+2], 16) for i in (4,2,0))  # hex to BGR
            elif isinstance(color, (list, tuple)):
                return tuple(int(x) for x in color)
        # fallback
        import random
        random.seed(label)
        return tuple(random.randint(0,255) for _ in range(3))

    def _on_capture(self):
        # PCB QA: Freeze, detect, overlay, auto-save, log, update UI, robust error handling
        import datetime
        import random
        import cv2
        from pcb_detect.utils import cv2_to_tk
        # 1. Check camera and capture frame
        if not (hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'capture_image')):
            Dialogs.error("Camera Error", "Camera is not initialized.")
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event("[ERROR] Camera is not initialized for capture.")
            return
        # Stop the video feed for a stable image
        if hasattr(self.app.video_frame, 'stop_camera'):
            self.app.video_frame.stop_camera()
        frame = self.app.video_frame.capture_image()
        if frame is None:
            Dialogs.error("Camera Error", "No frame available from camera.")
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event("[ERROR] No frame available from camera during capture.")
            return
        # 2. Run detection
        if not (hasattr(self, 'detector') and getattr(self.detector, 'model', None)):
            Dialogs.error("No Model Loaded", "Please load a detection model before capturing.")
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event("[ERROR] No model loaded for detection during capture.")
            return
        class_names = self.detector.model.names if hasattr(self.detector.model, 'names') else None
        conf = self.confidence_slider.get() if hasattr(self, 'confidence_slider') else 0.5
        results = self.detector.detect(frame, conf=conf)
        # 3. Only keep detections for components in the current set
        board_name = self.board_combo.get()
        expected = None
        if hasattr(self, 'board_manager') and board_name in self.board_manager.sets:
            expected = self.board_manager.sets[board_name]
        allowed_components = set(expected.keys()) if expected else set()
        color_map = {}
        if class_names:
            for i in class_names:
                random.seed(i)
                color_map[i] = tuple([random.randint(0,255) for _ in range(3)])
        detected_components = {}
        filtered_boxes = []
        if results and hasattr(results[0], 'boxes'):
            for box in results[0].boxes:
                x1, y1, x2, y2 = [int(float(v)) for v in box.xyxy[0]]
                class_id = int(box.cls[0].item())
                label = class_names[class_id] if class_names and class_id in class_names else str(class_id)
                if label not in allowed_components:
                    continue  # Ignore components not in the set
                color = color_map[class_id] if class_names and class_id in color_map else (0,255,0)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
                detected_components[label] = detected_components.get(label, 0) + 1
                filtered_boxes.append(box)
        # 4. Update video frame with overlay
        img = cv2_to_tk(frame)
        self.app.video_frame.video_label.config(image=img)
        self.app.video_frame.video_label.image = img
        # 5. Assign/increment board number for each capture
        if not hasattr(self, '_board_number'):
            self._board_number = 1
        else:
            self._board_number += 1
        board_number = self._board_number
        if hasattr(self.app, 'status_frame') and hasattr(self.app.status_frame, 'board_label'):
            self.app.status_frame.board_label.config(text=f"Board Number: {board_number}")
        # 6. Update detection results table and status
        batch_name = None
        if hasattr(self, 'batch_proc_var') and self.batch_proc_var.get():
            batch_name = getattr(self, 'current_batch', None)
        # Pass/fail logic: all expected components present in correct quantity
        pass_fail = "PASS"
        missing = []
        if expected:
            for comp, qty in expected.items():
                if detected_components.get(comp, 0) < qty:
                    pass_fail = "FAIL"
                    missing.append(f"{comp} (expected {qty}, found {detected_components.get(comp,0)})")
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_msg = f"[QA] {ts} | Board: {board_name} | Board# {board_number} | Batch: {batch_name or '-'} | Result: {pass_fail}"
        if missing:
            log_msg += f" | Missing: {', '.join(missing)}"
        if hasattr(self.app, 'status_frame'):
            self.app.status_frame.log_event(log_msg)
        if hasattr(self.app, 'status_frame') and hasattr(self.app.status_frame, 'update_results'):
            # Patch results to only include filtered boxes
            class DummyResult:
                def __init__(self, boxes):
                    self.boxes = boxes
            filtered_results = [DummyResult(filtered_boxes)]
            self.app.status_frame.update_results(filtered_results, expected)
        # 7. Save image and results for traceability
        ts_file = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        fname = f"snapshots/{board_name}_board{board_number}_batch{batch_name or 'NA'}_{ts_file}_{pass_fail}.png"
        try:
            cv2.imwrite(fname, frame)
            self._last_snapshot_path = fname  # Store for export
        except Exception as e:
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event(f"[ERROR] Failed to save image: {e}")
            return
        # Save detection results as JSON for traceability
        import json
        results_fname = fname.replace('.png', '.json')
        try:
            with open(results_fname, 'w') as f:
                json.dump({
                    'timestamp': ts,
                    'board': board_name,
                    'board_number': board_number,
                    'batch': batch_name,
                    'result': pass_fail,
                    'missing': missing,
                    'detected': detected_components,
                    'expected': expected
                }, f, indent=2)
            self._last_json_path = results_fname  # Store for export
        except Exception as e:
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event(f"[ERROR] Failed to save detection results: {e}")
        # 8. No pass/fail dialog popups, only table and status update
        # 9. Require user to press Continue to resume camera preview
        self._capture_paused = True
        self.capture_btn.config(state=tk.DISABLED)
        self.continue_btn.config(state=tk.NORMAL)

    def _on_continue(self):
        # Resume camera preview after capture/detection
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'start_camera'):
            self.app.video_frame.start_camera()
        self._capture_paused = False
        self.capture_btn.config(state=tk.NORMAL)
        self.continue_btn.config(state=tk.DISABLED)

    def _on_start_realtime(self):
        # Use the main video_frame's run_realtime_detection for real-time detection
        if not hasattr(self, 'detector') or not getattr(self.detector, 'model', None):
            Dialogs.error("No Model Loaded", "Please load a detection model before starting real-time detection.")
            return
        conf = self.confidence_slider.get() if hasattr(self, 'confidence_slider') else 0.5
        delay = self.delay_slider.get() if hasattr(self, 'delay_slider') else 0.5
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'run_realtime_detection'):
            self.app.video_frame.detector = self.detector  # Ensure detector is set
            started = self.app.video_frame.run_realtime_detection(conf=conf, delay=delay)
            if started:
                if hasattr(self.app, 'status_frame'):
                    self.app.status_frame.log_event("[INFO] Real-time detection started. Use Stop to end.")
            else:
                Dialogs.error("Camera Error", "Failed to start real-time detection.")
        else:
            Dialogs.error("Camera Error", "Camera is not initialized.")

    def _on_pause(self):
        # Pause real-time detection
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'pause_detection'):
            self.app.video_frame.pause_detection()
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event("[INFO] Real-time detection paused.")
        self.pause_btn.config(state=tk.DISABLED)
        self.continue_btn.config(state=tk.NORMAL)

    def _on_stop(self):
        # Stop real-time detection and resume normal camera feed
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'stop_detection'):
            self.app.video_frame.stop_detection()
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event("[INFO] Real-time detection stopped.")
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'start_camera'):
            self.app.video_frame.start_camera()
        self.pause_btn.config(state=tk.NORMAL)
        self.continue_btn.config(state=tk.DISABLED)

    def _on_export_snapshot(self):
        import shutil
        from tkinter import filedialog
        # Find the last saved snapshot and JSON result
        if not hasattr(self, '_last_snapshot_path') or not hasattr(self, '_last_json_path'):
            Dialogs.error("No Snapshot", "No snapshot available to export. Please capture an image first.")
            return
        img_path = self._last_snapshot_path
        json_path = self._last_json_path
        if not (os.path.exists(img_path) and os.path.exists(json_path)):
            Dialogs.error("File Not Found", "Snapshot or result file not found. Please capture again.")
            return
        # Ask user for export directory
        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            return
        try:
            shutil.copy2(img_path, export_dir)
            shutil.copy2(json_path, export_dir)
            Dialogs.info("Exported", f"Snapshot and results exported to {export_dir}")
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event(f"[INFO] Exported snapshot and results to {export_dir}")
        except Exception as e:
            Dialogs.error("Export Error", f"Failed to export: {e}")
            if hasattr(self.app, 'status_frame'):
                self.app.status_frame.log_event(f"[ERROR] Failed to export snapshot/results: {e}")

    def _on_camera_selected(self, event=None):
        # Switch the camera feed to the selected camera
        selected = self.camera_combo.get()
        try:
            if selected.startswith("Camera "):
                cam_idx = int(selected.split(" ")[-1])
            else:
                cam_idx = 0
        except Exception:
            cam_idx = 0
        print(f"[DEBUG] (main window) Camera selected: {selected}, index: {cam_idx}")
        # Set camera_index on video_frame for consistency
        if hasattr(self.app, 'video_frame'):
            self.app.video_frame.camera_index = cam_idx
            print(f"[DEBUG] (main window) Set video_frame.camera_index = {cam_idx}")
        # Stop current camera if running
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'stop_camera'):
            self.app.video_frame.stop_camera()
        # Start new camera
        if hasattr(self.app, 'video_frame') and hasattr(self.app.video_frame, 'start_camera'):
            started = self.app.video_frame.start_camera()
            print(f"[DEBUG] (main window) start_camera() returned: {started}")
        if hasattr(self.app, 'status_frame'):
            self.app.status_frame.log_event(f"[INFO] Switched to camera index {cam_idx}")

    def _on_batches(self):
        pass

    def _on_batch_toggle(self):
        pass

    def _on_capture(self):
        pass

    def _on_start_realtime(self):
        pass

    def _on_pause(self):
        pass

    def _on_stop(self):
        pass

    def _on_export_snapshot(self):
        pass

    def _on_continue(self):
        pass

    def _on_camera_selected(self, event=None):
        pass

    def _on_colors(self):
        pass

    def _load_component_colors(self):
        self._component_colors_path = os.path.join('config', 'component_colors.json')
        if not os.path.exists(self._component_colors_path):
            self._component_colors = {}
            return
        try:
            with open(self._component_colors_path, 'r') as f:
                self._component_colors = json.load(f)
        except Exception:
            self._component_colors = {}
