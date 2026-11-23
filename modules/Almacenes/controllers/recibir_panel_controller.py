from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QComboBox, QTableWidget, QTableWidgetItem
from .base_panel_controller import BasePanelController


class RecibirPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        self.str_tecnico = self.panel.findChild(
            QComboBox, "rec_str_tecnico")  # Si se agrega a la UI
        self.ln_serie = self.panel.findChild(QLineEdit, "rec_ln_serie")
        self.btn_add = self.panel.findChild(
            QPushButton, "rec_btn_agregar_item")
        self.btn_guardar = self.panel.findChild(
            QPushButton, "rec_btn_recibir")  # Botón final
        self.tabla = self.panel.findChild(QTableWidget, "tabla_recibir")

        self.items_agregados = []

        if self.btn_add:
            self.btn_add.clicked.connect(self._agregar_item)
        if self.btn_guardar:
            self.btn_guardar.clicked.connect(self._recibir)

    def _agregar_item(self):
        serie = self.ln_serie.text().strip()
        if not serie:
            return

        tipo = "Misceláneo"
        if len(serie) > 10:
            tipo = "ONT"

        self.items_agregados.append(
            {"numero_serie": serie, "tipo": tipo, "cantidad": 1})

        row = self.tabla.rowCount()
        self.tabla.insertRow(row)
        self.tabla.setItem(row, 0, QTableWidgetItem(serie))
        self.tabla.setItem(row, 1, QTableWidgetItem(tipo))
        self.tabla.setItem(row, 2, QTableWidgetItem("1"))
        self.ln_serie.clear()

    def _recibir(self):
        if not self.items_agregados:
            return

        datos = {
            "area": self.main.almacen.str_area.currentText(),
            "cope": self.main.almacen.str_cope.currentText(),
            "exp_tecnico": self.str_tecnico.currentText() if self.str_tecnico else None,
            "items": self.items_agregados
        }

        self.main._run_api_task(
            method="POST", endpoint="/almacen/recibir", data=datos,
            callback_success=lambda r: [QMessageBox.information(
                self.main.almacen, "Éxito", "Material ingresado al almacén"), self._limpiar()],
            callback_error=lambda err: QMessageBox.critical(
                self.main.almacen, "Error", str(err))
        )

    def _limpiar(self):
        self.tabla.setRowCount(0)
        self.items_agregados.clear()
