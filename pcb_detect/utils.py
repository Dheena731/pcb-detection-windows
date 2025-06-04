# Utility functions for color, image, etc.
from PIL import Image, ImageTk
import numpy as np
import cv2

def cv2_to_tk(frame):
    # Convert OpenCV BGR image to Tkinter PhotoImage
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    return ImageTk.PhotoImage(img)

def assign_colors(components):
    # Assign unique colors to each component
    import random
    random.seed(42)
    color_map = {}
    for comp in components:
        color_map[comp] = "#%06x" % random.randint(0, 0xFFFFFF)
    return color_map
