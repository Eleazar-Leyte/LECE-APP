import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol
from PyQt6.QtCore import QThread, pyqtSignal


class BarcodeScannerThread(QThread):
    code_detected = pyqtSignal(str, np.ndarray)
    frame_captured = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                break
            self.frame_captured.emit(frame)
            decoded_objects = decode(
                frame, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.CODE128])
            for obj in decoded_objects:
                codigo = obj.data.decode("utf-8")
                self.code_detected.emit(codigo, frame)
                self._run_flag = False
                break
        cap.release()
        self.finished.emit()

    def stop(self):
        self._run_flag = False
