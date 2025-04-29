from PyQt6 import uic


class UpdateProgressWindow():
    def __init__(self):
        self.update = uic.loadUi("modules/actualizando.ui")
        self.update.show()
        self.update.barradeprogreso.setValue(0)

    def update_progress(self, value):
        self.update.barradeprogreso.setValue(value)
