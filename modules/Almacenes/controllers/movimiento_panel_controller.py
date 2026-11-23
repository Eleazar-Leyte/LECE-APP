from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QComboBox
from .base_panel_controller import BasePanelController


class MovimientoPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        self.mov_origen = self.panel.findChild(QComboBox, "mov_origen")
        self.mov_destino = self.panel.findChild(QComboBox, "mov_destino")
        self.ln_serie = self.panel.findChild(QLineEdit, "mov_ln_serie")
        self.ln_cantidad = self.panel.findChild(QLineEdit, "mov_ln_cantidad")
        self.btn_mover = self.panel.findChild(QPushButton, "mov_btn_mover")

        # Llenar combos con las áreas disponibles desde el controlador principal
        if self.mov_origen and self.mov_destino and hasattr(self.main, 'almacen'):
            for i in range(self.main.almacen.str_area.count()):
                txt = self.main.almacen.str_area.itemText(i)
                if txt != "Seleccionar" and txt != "Cargando áreas...":
                    self.mov_origen.addItem(txt)
                    self.mov_destino.addItem(txt)

        if self.btn_mover:
            self.btn_mover.clicked.connect(self._mover)

    def _mover(self):
        if not self.mov_origen or not self.mov_destino or not self.ln_serie or not self.ln_cantidad:
            return

        try:
            cantidad = int(self.ln_cantidad.text().strip())
        except ValueError:
            QMessageBox.warning(self.main.almacen, "Error",
                                "Cantidad inválida")
            return

        datos = {
            "origen": self.mov_origen.currentText(),
            "destino": self.mov_destino.currentText(),
            "numero_serie": self.ln_serie.text().strip(),
            "cantidad": cantidad
        }

        if datos["origen"] == datos["destino"]:
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "El origen y destino no pueden ser iguales")
            return

        self.main._run_api_task(
            method="POST", endpoint="/almacen/movimiento", data=datos,
            callback_success=lambda r: [QMessageBox.information(
                self.main.almacen, "Éxito", "Movimiento exitoso"), self.limpiar_campos()],
            callback_error=lambda err: QMessageBox.critical(
                self.main.almacen, "Error", str(err))
        )

    def limpiar_campos(self):
        if self.ln_serie:
            self.ln_serie.clear()
        if self.ln_cantidad:
            self.ln_cantidad.clear()
