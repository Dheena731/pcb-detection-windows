import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Label):
    def __init__(self, parent, app):
        super().__init__(parent, text="Ready", relief=tk.SUNKEN, anchor='w')
        self.app = app

    def set_status(self, message):
        self.config(text=message)
