import tkinter as tk
from tkinter import simpledialog, filedialog
import threading, time, os, json, datetime, cv2
from pcb_detect.utils import cv2_to_tk

def setup_component_dialog(parent, app, model_name, board_name, camera_name, board_manager, detector, video_frame, add_tooltip, Dialogs):
    print("[DEBUG] setup_component_dialog called")
    setup_win = tk.Toplevel(parent)
    setup_win.title("Component Set Setup")
    setup_win.geometry("1100x650")
    setup_win.minsize(1100, 650)
    setup_win.resizable(True, True)
    setup_win.grab_set()
    setup_win.configure(bg="#f4f4f4")
    grid = tk.Frame(setup_win, bg="#f4f4f4")
    grid.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
    # Adjust grid weights for better expansion
    for i in range(13):
        grid.grid_columnconfigure(i, weight=1 if i in [0,1,2,3,4,5,6,7,8,9,10,11,12] else 0, minsize=60)
    for i in range(10):
        grid.grid_rowconfigure(i, weight=1 if i in [4,5,6] else 0)
    # Row 0: Model and Camera controls
    tk.Label(grid, text="Model:", font=("Segoe UI", 10), bg="#f4f4f4").grid(row=0, column=0, padx=5, pady=2, sticky='w')
    model_entry = tk.Entry(grid, width=25, font=("Segoe UI", 10))
    model_entry.insert(0, model_name)
    model_entry.config(state='disabled')
    model_entry.grid(row=0, column=1, padx=8, pady=2, sticky='ew')
    tk.Label(grid, text="Camera:", font=("Segoe UI", 10), bg="#f4f4f4").grid(row=0, column=2, padx=10, pady=2, sticky='w')
    camera_entry = tk.Entry(grid, width=10, font=("Segoe UI", 10))
    camera_entry.insert(0, camera_name)
    camera_entry.config(state='disabled')
    camera_entry.grid(row=0, column=3, padx=8, pady=2, sticky='ew')
    # Row 1: Help
    help_btn = tk.Button(grid, text="?", font=("Segoe UI", 10, "bold"), width=2, command=lambda: Dialogs.info("Setup Help", "1. Use Capture to freeze a frame.\n2. Edit, add, or remove components in the table.\n3. Use Save & Continue to finish."))
    help_btn.grid(row=1, column=8, padx=8, pady=2, sticky='e')
    # Error label
    error_var = tk.StringVar(value="")
    error_label = tk.Label(grid, textvariable=error_var, font=("Segoe UI", 10, "bold"), fg="red", bg="#f4f4f4")
    error_label.grid(row=10, column=0, columnspan=12, sticky="ew", padx=8, pady=4)
    # Row 2: Action buttons
    capture_btn = tk.Button(grid, text="Capture", width=12)
    resume_btn = tk.Button(grid, text="Continue", width=12, state=tk.DISABLED)
    capture_btn.grid(row=2, column=0, padx=8, pady=8, sticky='ew')
    resume_btn.grid(row=2, column=1, padx=8, pady=8, sticky='ew')
    # Row 3: (Removed settings_frame for zoom and threshold)
    # Row 4: Status/info label
    status_var = tk.StringVar(value="Ready.")
    status_label = tk.Label(grid, textvariable=status_var, font=("Segoe UI", 8), bg="#f4f4f4", fg="#444")
    status_label.grid(row=4, column=0, columnspan=4, sticky="ew", padx=8, pady=(0,2))
    # Row 5: Video feed (left) and table (right)
    video_label = tk.Label(grid, bg="#222", width=640, height=480, relief=tk.SUNKEN)
    video_label.grid(row=5, column=0, columnspan=4, rowspan=2, sticky="nsew", padx=8, pady=8)

    # Set Name above the table (right side)
    tk.Label(grid, text="Set Name:", font=("Segoe UI", 10), bg="#f4f4f4").grid(row=4, column=4, padx=10, pady=2, sticky='w')
    set_name_var = tk.StringVar(value=board_name)
    set_name_entry = tk.Entry(grid, textvariable=set_name_var, width=20, font=("Segoe UI", 10))
    set_name_entry.grid(row=4, column=5, padx=8, pady=2, sticky='ew', columnspan=3)

    # Table to the right
    tk.Label(grid, text="Components in Set", font=("Segoe UI", 10, "bold"), bg="#f4f4f4").grid(row=5, column=4, columnspan=4, sticky='w', pady=(0,2))
    columns = ("Class", "Mapped Name", "Quantity")
    comp_tree = tk.ttk.Treeview(grid, columns=columns, show="headings", height=12)
    for col in columns:
        comp_tree.heading(col, text=col)
        comp_tree.column(col, width=100, anchor='center')
    comp_tree.grid(row=6, column=4, columnspan=8, rowspan=2, sticky="nsew", padx=8, pady=8)

    # Table controls below table (row 8)
    table_ctrls = tk.Frame(grid, bg="#f4f4f4")
    table_ctrls.grid(row=8, column=4, columnspan=8, sticky="ew", pady=2, padx=8)
    add_frame = tk.Frame(table_ctrls, bg="#f4f4f4")
    add_frame.pack(side=tk.LEFT)
    tk.Label(add_frame, text="Add Component:", bg="#f4f4f4", font=("Segoe UI", 8)).pack(side=tk.LEFT)
    add_name = tk.Entry(add_frame, width=10, font=("Segoe UI", 8))
    add_name.pack(side=tk.LEFT, padx=1)
    add_qty = tk.Entry(add_frame, width=4, font=("Segoe UI", 8))
    add_qty.pack(side=tk.LEFT, padx=1)
    tk.Button(add_frame, text="Add", command=lambda: add_manual(), font=("Segoe UI", 8), width=6).pack(side=tk.LEFT, padx=1)
    tk.Button(table_ctrls, text="Remove Selected", command=lambda: remove_selected(), font=("Segoe UI", 8), width=12).pack(side=tk.LEFT, padx=4)
    tk.Button(table_ctrls, text="Clear Table", command=lambda: clear_table(), font=("Segoe UI", 8), width=10).pack(side=tk.LEFT, padx=4)
    # Row 9: Save/Export controls (bottom right)
    save_ctrls = tk.Frame(grid, bg="#f4f4f4")
    save_ctrls.grid(row=9, column=4, columnspan=8, sticky="ew", pady=4, padx=8)
    tk.Button(save_ctrls, text="Save & Continue", font=("Segoe UI", 9, "bold"), bg="#4caf50", fg="white", command=lambda: save_and_close(), width=14).pack(side=tk.LEFT, padx=4)
    tk.Button(save_ctrls, text="Export Set", command=lambda: export_set(), font=("Segoe UI", 8), width=10).pack(side=tk.LEFT, padx=4)

    # --- Modern UI Layout ---
    # Main horizontal split: left (video), right (controls)
    main_frame = tk.Frame(grid, bg="#f4f4f4")
    main_frame.grid(row=0, column=0, rowspan=11, columnspan=13, sticky="nsew")
    main_frame.grid_columnconfigure(0, weight=1, minsize=660)
    main_frame.grid_columnconfigure(1, weight=0, minsize=420)
    main_frame.grid_rowconfigure(0, weight=1)

    # --- Left: Video Feed ---
    video_frame = tk.Frame(main_frame, bg="#222", bd=2, relief=tk.SUNKEN)
    video_frame.grid(row=0, column=0, sticky="nsew", padx=(0,16), pady=8)
    video_label = tk.Label(video_frame, bg="#222", width=640, height=480)
    video_label.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")
    video_frame.grid_rowconfigure(0, weight=1)
    video_frame.grid_columnconfigure(0, weight=1)

    # --- Right: Controls ---
    controls_frame = tk.Frame(main_frame, bg="#f4f4f4")
    controls_frame.grid(row=0, column=1, sticky="nsew", padx=(0,8), pady=8)
    controls_frame.grid_columnconfigure(0, weight=1)

    # Set Name at the top
    setname_section = tk.Frame(controls_frame, bg="#f4f4f4")
    setname_section.grid(row=0, column=0, sticky="ew", pady=(0,8))
    tk.Label(setname_section, text="Set Name:", font=("Segoe UI", 11, "bold"), bg="#f4f4f4").grid(row=0, column=0, padx=(0,6), sticky='w')
    set_name_var = tk.StringVar(value=board_name)
    set_name_entry = tk.Entry(setname_section, textvariable=set_name_var, width=22, font=("Segoe UI", 11))
    set_name_entry.grid(row=0, column=1, padx=(0,6), sticky='ew')
    help_btn = tk.Button(setname_section, text="?", font=("Segoe UI", 10, "bold"), width=2, command=lambda: Dialogs.info("Setup Help", "1. Use Capture to freeze a frame.\n2. Edit, add, or remove components in the table.\n3. Use Save & Continue to finish."))
    help_btn.grid(row=0, column=2, padx=(6,0), sticky='e')
    setname_section.grid_columnconfigure(1, weight=1)

    # Model and Camera info
    info_section = tk.Frame(controls_frame, bg="#f4f4f4")
    info_section.grid(row=1, column=0, sticky="ew", pady=(0,8))
    tk.Label(info_section, text="Model:", font=("Segoe UI", 10), bg="#f4f4f4").grid(row=0, column=0, padx=(0,4), sticky='w')
    model_entry = tk.Entry(info_section, width=18, font=("Segoe UI", 10))
    model_entry.insert(0, model_name)
    model_entry.config(state='disabled')
    model_entry.grid(row=0, column=1, padx=(0,8), sticky='w')
    tk.Label(info_section, text="Camera:", font=("Segoe UI", 10), bg="#f4f4f4").grid(row=0, column=2, padx=(0,4), sticky='w')
    camera_entry = tk.Entry(info_section, width=10, font=("Segoe UI", 10))
    camera_entry.insert(0, camera_name)
    camera_entry.config(state='disabled')
    camera_entry.grid(row=0, column=3, padx=(0,4), sticky='w')
    info_section.grid_columnconfigure(4, weight=1)

    # Action buttons
    btn_section = tk.Frame(controls_frame, bg="#f4f4f4")
    btn_section.grid(row=2, column=0, sticky="ew", pady=(0,8))
    capture_btn = tk.Button(btn_section, text="Capture", width=14)
    resume_btn = tk.Button(btn_section, text="Continue", width=14, state=tk.DISABLED)
    capture_btn.grid(row=0, column=0, padx=(0,8), pady=4)
    resume_btn.grid(row=0, column=1, padx=(0,8), pady=4)
    btn_section.grid_columnconfigure(2, weight=1)

    # Status/info label
    status_var = tk.StringVar(value="Ready.")
    status_label = tk.Label(controls_frame, textvariable=status_var, font=("Segoe UI", 9), bg="#f4f4f4", fg="#444")
    status_label.grid(row=3, column=0, sticky="ew", pady=(0,8))

    # Table section
    table_section = tk.LabelFrame(controls_frame, text="Components in Set", font=("Segoe UI", 10, "bold"), bg="#f4f4f4")
    table_section.grid(row=4, column=0, sticky="nsew", pady=(0,8))
    table_section.grid_rowconfigure(0, weight=1)
    table_section.grid_columnconfigure(0, weight=1)
    columns = ("Class", "Mapped Name", "Quantity")
    comp_tree = tk.ttk.Treeview(table_section, columns=columns, show="headings", height=10)
    for col in columns:
        comp_tree.heading(col, text=col)
        comp_tree.column(col, width=110, anchor='center')
    comp_tree.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    # Table controls
    table_ctrls = tk.Frame(controls_frame, bg="#f4f4f4")
    table_ctrls.grid(row=5, column=0, sticky="ew", pady=(0,8))
    add_frame = tk.Frame(table_ctrls, bg="#f4f4f4")
    add_frame.grid(row=0, column=0, sticky='w')
    tk.Label(add_frame, text="Add Component:", bg="#f4f4f4", font=("Segoe UI", 8)).grid(row=0, column=0)
    add_name = tk.Entry(add_frame, width=10, font=("Segoe UI", 8))
    add_name.grid(row=0, column=1, padx=1)
    add_qty = tk.Entry(add_frame, width=4, font=("Segoe UI", 8))
    add_qty.grid(row=0, column=2, padx=1)
    tk.Button(add_frame, text="Add", command=lambda: add_manual(), font=("Segoe UI", 8), width=6).grid(row=0, column=3, padx=1)
    tk.Button(table_ctrls, text="Remove Selected", command=lambda: remove_selected(), font=("Segoe UI", 8), width=12).grid(row=0, column=1, padx=4)
    tk.Button(table_ctrls, text="Clear Table", command=lambda: clear_table(), font=("Segoe UI", 8), width=10).grid(row=0, column=2, padx=4)
    table_ctrls.grid_columnconfigure(3, weight=1)

    # Save/Export controls
    save_ctrls = tk.Frame(controls_frame, bg="#f4f4f4")
    save_ctrls.grid(row=6, column=0, sticky="ew", pady=(0,8))
    tk.Button(save_ctrls, text="Save & Continue", font=("Segoe UI", 9, "bold"), bg="#4caf50", fg="white", command=lambda: save_and_close(), width=16).grid(row=0, column=0, padx=4, pady=4)
    tk.Button(save_ctrls, text="Export Set", command=lambda: export_set(), font=("Segoe UI", 8), width=12).grid(row=0, column=1, padx=4, pady=4)
    save_ctrls.grid_columnconfigure(2, weight=1)

    # Error label at the bottom
    error_label.grid(row=7, column=0, sticky="ew", pady=(0,4))
    controls_frame.grid_rowconfigure(4, weight=1)
    # ...existing code...
    # --- Logic ---
    stop_event = threading.Event()
    video_paused = [False]
    last_frame = [None]
    detected_boxes = []
    detected_components = {}
    class_names = []
    set_name_entry.focus()
    # Tooltips
    add_tooltip(capture_btn, "Freeze the current frame for annotation.")
    add_tooltip(resume_btn, "Resume the live camera feed.")
    add_tooltip(save_ctrls, "Save or export the current set.")
    add_tooltip(status_label, "Status and info messages.")
    # --- Table logic and handlers ---
    def add_manual():
        n = add_name.get().strip()
        try:
            q = int(add_qty.get())
        except Exception:
            q = 1
        if n:
            comp_tree.insert('', tk.END, values=(n, n, q))
            add_name.delete(0, tk.END)
            add_qty.delete(0, tk.END)
    def remove_selected():
        sel = comp_tree.selection()
        for s in sel:
            comp_tree.delete(s)
    def clear_table():
        for s in comp_tree.get_children():
            comp_tree.delete(s)
    def save_and_close():
        set_name = set_name_var.get().strip()
        if not set_name:
            set_name = simpledialog.askstring("Set Name Required", "Enter a name for this board set:")
            if not set_name:
                Dialogs.error("No Name", "Enter a set name.")
                return
            set_name_var.set(set_name)
        components = {}
        for row in comp_tree.get_children():
            mapped = comp_tree.set(row, "Mapped Name")
            qty = comp_tree.set(row, "Quantity")
            if not mapped:
                mapped = comp_tree.set(row, "Class")
            try:
                qty = int(qty)
            except Exception:
                qty = 1
            components[mapped] = qty
        if not components:
            Dialogs.error("No Components", "Add at least one component.")
            return
        board_manager.add_set(set_name, components)
        if hasattr(parent, '_refresh_boards'):
            parent._refresh_boards()
        Dialogs.info("Set Saved", f"Board set '{set_name}' saved.")
        stop_event.set()
        setup_win.destroy()
        if hasattr(app, 'video_frame') and hasattr(app.video_frame, 'start_camera'):
            app.video_frame.start_camera()
    def export_set():
        set_name = set_name_var.get().strip()
        if not set_name:
            Dialogs.error("No Name", "Enter a set name before export.")
            return
        components = {}
        for row in comp_tree.get_children():
            mapped = comp_tree.set(row, "Mapped Name")
            qty = comp_tree.set(row, "Quantity")
            if not mapped:
                mapped = comp_tree.set(row, "Class")
            try:
                qty = int(qty)
            except Exception:
                qty = 1
            components[mapped] = qty
        if not components:
            Dialogs.error("No Components", "Add at least one component.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            with open(file_path, 'w') as f:
                json.dump({set_name: components}, f, indent=2)
            Dialogs.info("Exported", f"Component set exported to {file_path}")
    # --- Camera/video feed logic ---
    cam_idx = 0
    if camera_name and camera_name.startswith('Camera '):
        try:
            cam_idx = int(camera_name.split(' ')[-1])
        except Exception:
            cam_idx = 0
    elif hasattr(video_frame, 'camera_index'):
        cam_idx = video_frame.camera_index
    print(f"[DEBUG] (setup dialog) Using camera index: {cam_idx}")

    # Stop main window camera if running (before opening dialog)
    if hasattr(app, 'video_frame') and hasattr(app.video_frame, 'stop_camera'):
        try:
            app.video_frame.stop_camera()
        except Exception as e:
            print(f"[WARN] Could not stop main window camera: {e}")

    # State for preview/detection
    preview_running = [True]
    last_detection = [None]

    def run_camera():
        print("[DEBUG] run_camera thread started (setup dialog)")
        try:
            from pcb_detect.camera import Camera
            cam = Camera(cam_idx)
            if not cam.open():
                print("[ERROR] Could not open camera in setup dialog")
                error_var.set("Could not open camera. It may be in use or unavailable.")
                return
            while not stop_event.is_set():
                if not preview_running[0]:
                    time.sleep(0.05)
                    continue
                ret, frame = cam.read()
                if not ret:
                    error_var.set("Camera read failed. Check camera connection.")
                    time.sleep(0.5)
                    continue
                last_frame[0] = frame.copy()
                img = cv2_to_tk(frame)
                def update_video():
                    if video_label.winfo_exists():
                        video_label.config(image=img)
                        video_label.image = img
                video_label.after(0, update_video)
                error_var.set("")
                time.sleep(0.05)
        except Exception as e:
            print(f"[ERROR] Exception in run_camera: {e}")
            error_var.set(f"Camera thread error: {e}")
    cam_thread = threading.Thread(target=run_camera, daemon=True)
    cam_thread.start()

    def draw_bboxes_on_frame(frame, results, class_names):
        # Draw bounding boxes and labels on frame
        if not results or not hasattr(results[0], 'boxes'):
            return frame, []
        boxes = []
        for box in results[0].boxes:
            x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]
            h, w, _ = frame.shape
            nx1, ny1, nx2, ny2 = x1/w, y1/h, x2/w, y2/h
            label = str(box.cls[0].item())
            if class_names:
                try:
                    label = class_names[int(box.cls[0].item())]
                except Exception:
                    pass
            boxes.append((nx1, ny1, nx2, ny2, label))
            color = (0, 255, 0)
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
            cv2.putText(frame, label, (int(x1), int(y1)-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        return frame, boxes

    def do_capture():
        # Freeze preview
        preview_running[0] = False
        video_paused[0] = True
        capture_btn.config(state=tk.DISABLED)
        resume_btn.config(state=tk.NORMAL)
        status_var.set("Frame captured. Running detection...")
        # Run detection on last frame
        frame = last_frame[0]
        if frame is None:
            error_var.set("No frame to capture.")
            return
        try:
            from pcb_detect.detection import Detector
            local_detector = Detector()
            model_path = None
            if detector and hasattr(detector, 'model_path') and detector.model_path:
                model_path = detector.model_path
            elif hasattr(video_frame, 'detector') and hasattr(video_frame.detector, 'model_path'):
                model_path = video_frame.detector.model_path
            if not model_path or not os.path.isfile(model_path):
                error_var.set("No model loaded or model file missing. Please load a detection model.")
                return
            local_detector.load_model(model_path)
            nonlocal class_names
            if hasattr(local_detector, 'model') and hasattr(local_detector.model, 'names'):
                class_names = list(local_detector.model.names.values())
            results = local_detector.detect(frame, conf=0.5)  # Fixed confidence value
            frame_with_boxes, boxes = draw_bboxes_on_frame(frame.copy(), results, class_names)
            detected_boxes.clear()
            detected_boxes.extend(boxes)
            last_detection[0] = results
            # Show frame with boxes
            img = cv2_to_tk(frame_with_boxes)
            def update_video():
                if video_label.winfo_exists():
                    video_label.config(image=img)
                    video_label.image = img
            video_label.after(0, update_video)
            # Update table with detected components
            detected_components.clear()
            comp_tree.delete(*comp_tree.get_children())  # Ensure table is cleared before inserting
            if results and hasattr(results[0], 'boxes'):
                for box in results[0].boxes:
                    label = str(box.cls[0].item())
                    if class_names:
                        try:
                            label = class_names[int(box.cls[0].item())]
                        except Exception:
                            pass
                    detected_components[label] = detected_components.get(label, 0) + 1
                for label, qty in detected_components.items():
                    comp_tree.insert('', tk.END, values=(label, label, qty))
            status_var.set("Detection complete. Edit table or save as needed.")
        except Exception as e:
            error_var.set(f"Detection failed: {e}")
            print(f"[ERROR] Detection failed: {e}")

    def do_resume():
        preview_running[0] = True
        video_paused[0] = False
        capture_btn.config(state=tk.NORMAL)
        resume_btn.config(state=tk.DISABLED)
        status_var.set("Live feed resumed.")
        # Optionally clear table or keep last detection

    capture_btn.config(command=do_capture)
    resume_btn.config(command=do_resume)

    # Video click for crop
    def on_video_click(event):
        pass  # No snapshot/crop logic
    video_label.bind('<Button-1>', on_video_click)

    # On close
    def on_close():
        stop_event.set()
        setup_win.destroy()
        # Wait a moment to ensure camera is released before restarting main feed
        time.sleep(0.2)
        # Ensure main window's video_frame is reset and camera is started
        if hasattr(app, 'video_frame'):
            if hasattr(app.video_frame, 'paused'):
                app.video_frame.paused = False
            if hasattr(app.video_frame, 'running'):
                app.video_frame.running = False
            if hasattr(app.video_frame, 'start_camera'):
                app.video_frame.start_camera()
    setup_win.protocol("WM_DELETE_WINDOW", on_close)

    return setup_win