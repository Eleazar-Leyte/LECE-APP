# modules/update_progress.py
from PyQt6.QtWidgets import QMainWindow
from PyQt6 import uic


class UpdateProgressWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("modules/update_manager/actualizando.ui", self)
        self.barradeprogreso.setValue(0)

    def update_progress(self, value):
        self.barradeprogreso.setValue(value)
