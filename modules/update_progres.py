from PyQt6.QtWidgets import QMainWindow  # <-- Añadir import
from PyQt6 import uic
import os


class UpdateProgressWindow(QMainWindow):  # <-- Heredar de QMainWindow
    def __init__(self):
        super().__init__()
        current_dir = os.path.dirname(__file__)
        ui_path = os.path.join(current_dir, "actualizando.ui")
        self.update = uic.loadUi(ui_path)
        self.update.show()
        self.update.barradeprogreso.setValue(0)

    def update_progress(self, value):
        self.update.barradeprogreso.setValue(value)
