from PyQt6.QtWidgets import QMainWindow
from PyQt6 import uic
import os
import sys


class UpdateProgressWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Manejar rutas para producción/desarrollo
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        ui_path = os.path.join(base_dir, "actualizando.ui")
        self.ui = uic.loadUi(ui_path)
        self.setCentralWidget(self.ui)
        self.ui.barradeprogreso.setValue(0)
        self.show()

    def update_progress(self, value):
        self.ui.barradeprogreso.setValue(value)
