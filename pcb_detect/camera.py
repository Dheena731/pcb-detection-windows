import cv2

class Camera:
    def __init__(self, camera_index=0):
        self.camera_index = camera_index
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.camera_index)
        return self.cap.isOpened()

    def read(self):
        if self.cap:
            ret, frame = self.cap.read()
            return ret, frame
        return False, None

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
