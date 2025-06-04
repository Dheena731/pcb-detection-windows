import tkinter as tk
from tkinter import ttk

class StatusFrame(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build()

    def _build(self):
        # Mode/FPS/Skipped/Board/Batch labels
        self.mode_label = ttk.Label(self, text="Mode: Idle")
        self.fps_label = ttk.Label(self, text="FPS: 0.00")
        self.skipped_label = ttk.Label(self, text="Skipped Frames: 0")
        self.board_label = ttk.Label(self, text="Board Number: -")
        self.batch_label = ttk.Label(self, text="Current Batch: Default")
        self.mode_label.pack(anchor='w')
        self.fps_label.pack(anchor='w')
        self.skipped_label.pack(anchor='w')
        self.board_label.pack(anchor='w')
        self.batch_label.pack(anchor='w')
        # Detection Results Treeview
        self.results_frame = ttk.LabelFrame(self, text="Detection Results")
        self.results_tree = ttk.Treeview(self.results_frame, columns=("Status", "Component", "Expected", "Detected"), show="headings")
        for col in ("Status", "Component", "Expected", "Detected"):
            self.results_tree.heading(col, text=col)
        self.results_tree.pack(fill=tk.BOTH, expand=True)
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        # Component Summary
        self.summary_label = ttk.Label(self, text="Component Summary: -")
        self.summary_label.pack(anchor='w', pady=2)
        # Detection History
        self.history_frame = ttk.LabelFrame(self, text="Detection History")
        self.history_text = tk.Text(self.history_frame, height=5, wrap=tk.WORD)
        self.history_scroll = ttk.Scrollbar(self.history_frame, command=self.history_text.yview)
        self.history_text.configure(yscrollcommand=self.history_scroll.set)
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        # Status Console
        self.console_frame = ttk.LabelFrame(self, text="Status Console")
        self.console_text = tk.Text(self.console_frame, height=5, wrap=tk.WORD)
        self.console_scroll = ttk.Scrollbar(self.console_frame, command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=self.console_scroll.set)
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.console_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        # Clear Console Button
        self.clear_btn = ttk.Button(self, text="Clear Console", command=self._clear_console)
        self.clear_btn.pack(anchor='e', pady=2)
        # Progress Bar
        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=2)
        self.progress.pack_forget()  # Hide by default

    def _clear_console(self):
        self.console_text.delete('1.0', tk.END)

    def update_results(self, results, expected=None):
        self.results_tree.delete(*self.results_tree.get_children())
        summary = {}
        if results and hasattr(results[0], 'boxes'):
            for box in results[0].boxes:
                label = str(box.cls[0].item())
                summary[label] = summary.get(label, 0) + 1
        if expected:
            for comp, exp_count in expected.items():
                detected = summary.get(comp, 0)
                status = '✔' if detected == exp_count else '✘'
                color = 'green' if detected == exp_count else 'red'
                self.results_tree.insert('', 'end', values=(status, comp, exp_count, detected), tags=(color,))
            self.results_tree.tag_configure('green', foreground='green')
            self.results_tree.tag_configure('red', foreground='red')
        self.summary_label.config(text=f"Component Summary: {', '.join([f'{k}: {v}' for k, v in summary.items()])}")

    def log_event(self, message):
        self.console_text.insert(tk.END, message + '\n')
        self.console_text.see(tk.END)

    def add_history(self, result_summary):
        self.history_text.insert(tk.END, result_summary + '\n')
        self.history_text.see(tk.END)
        # Keep only last 5 entries
        lines = self.history_text.get('1.0', tk.END).splitlines()
        if len(lines) > 5:
            self.history_text.delete('1.0', f'{len(lines)-5}.0')
