import tkinter as tk
from tkinter import simpledialog, colorchooser, messagebox

class Dialogs:
    @staticmethod
    def error(title, message):
        messagebox.showerror(title, message)

    @staticmethod
    def info(title, message):
        messagebox.showinfo(title, message)

    @staticmethod
    def ask_string(title, prompt, initialvalue=None):
        return simpledialog.askstring(title, prompt, initialvalue=initialvalue)

    @staticmethod
    def ask_color(initialcolor="#ffffff"):
        return colorchooser.askcolor(color=initialcolor)[1]

    @staticmethod
    def confirm(title, message):
        return messagebox.askyesno(title, message)
