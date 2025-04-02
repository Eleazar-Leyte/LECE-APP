from PyQt6.QtWidgets import QApplication
from modules.login.login import Login


class Constructora():
    def __init__(self):
        self.app = QApplication([])
        self.login = Login()
        self.app.exec()
