# Simple tooltip support for tkinter widgets
import tkinter as tk

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, event=None):
        if self.tipwindow or not self.text:
            return
        # Defensive: bbox may return None for some widgets
        bbox = None
        try:
            bbox = self.widget.bbox("insert")
        except Exception:
            pass
        if bbox is None:
            # Fallback: use mouse pointer position
            x = self.widget.winfo_pointerx() + 20
            y = self.widget.winfo_pointery() + 20
        else:
            x, y, _, cy = bbox
            x = x + self.widget.winfo_rootx() + 20
            y = y + cy + self.widget.winfo_rooty() + 20
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide(self, event=None):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def add_tooltip(widget, text):
    ToolTip(widget, text)
