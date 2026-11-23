# almacen_panel_controller.py
from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QComboBox, QTextEdit
from .base_panel_controller import BasePanelController


class AlmacenPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        self.ln_ns = self.panel.findChild(QLineEdit, "almacen_ln_ns")
        self.ln_cantidad = self.panel.findChild(
            QLineEdit, "almacen_ln_cantidad")
        self.str_unidad = self.panel.findChild(QComboBox, "almacen_str_unidad")
        self.str_codigoax = self.panel.findChild(
            QComboBox, "almacen_str_codigoax")
        self.str_codigosap = self.panel.findChild(
            QLineEdit, "almacen_str_codigosap")
        self.str_proyecto = self.panel.findChild(
            QLineEdit, "almacen_str_proyecto")
        self.texedit_descripcion = self.panel.findChild(
            QTextEdit, "almacen_texedit_descripcion")
        self.btn_guardar = self.panel.findChild(
            QPushButton, "almacen_btn_guardar")

        if self.btn_guardar:
            self.btn_guardar.clicked.connect(self._guardar)
        self._cargar_codigos_ax()

    def _cargar_codigos_ax(self):
        """Obtiene el catálogo de la API y llena el ComboBox."""
        if not self.str_codigoax:
            return

        self.str_codigoax.clear()
        self.str_codigoax.addItem("Cargando...")

        self.main._run_api_task(
            method="GET",
            endpoint="/almacen/catalogo",
            callback_success=self._on_ax_cargados,
            callback_error=lambda e: print(f"Error al cargar AX: {e}")
        )

    def _on_ax_cargados(self, data):
        self.str_codigoax.clear()
        self.str_codigoax.addItem("Seleccionar", "")
        for item in data:
            codigo = item.get("codigo_ax", "")
            nombre = item.get("nombre_articulo", "")
            # Mostramos "Código - Nombre" en el combo, pero guardamos solo el código internamente
            self.str_codigoax.addItem(f"{codigo} - {nombre}", codigo)

    def _guardar(self):
        area = self.main.almacen.str_area.currentText()
        cope = self.main.almacen.str_cope.currentText()
        if not area or area == "Seleccionar":
            QMessageBox.warning(self.main.almacen,
                                "Advertencia", "Seleccione un área válida")
            return
        if not cope or cope == "Seleccionar":
            QMessageBox.warning(self.main.almacen,
                                "Advertencia", "Seleccione un cope válido")
            return
        if not self.ln_cantidad or not self.str_unidad or not self.texedit_descripcion:
            QMessageBox.critical(
                self.main.almacen, "Error", "Error de interfaz")
            return

        try:
            cantidad = int(self.ln_cantidad.text().strip())
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            QMessageBox.warning(self.main.almacen,
                                "Advertencia", "La cantidad debe ser un número positivo")
            return

        datos = {
            "numero_serie": self.ln_ns.text().strip() if self.ln_ns else "",
            "descripcion": self.texedit_descripcion.toPlainText().strip(),
            "codigo_ax": self.str_codigoax.currentData() if self.str_codigoax else "",
            "codigo_catalogo": self.str_codigosap.text().strip() if self.str_codigosap else "",
            "cantidad": cantidad,
            "unidad": self.str_unidad.currentText(),
            "area": self.main.almacen.str_area.currentText(),
            "cope": self.main.almacen.str_cope.currentText(),
            "proyecto": self.str_proyecto.text().strip() if self.str_proyecto else ""
        }

        if not datos["descripcion"]:
            QMessageBox.warning(self.main.almacen, "Advertencia",
                                "La descripción es obligatoria")
            return

        if QMessageBox.question(self.main.almacen, "Confirmar", "¿Guardar en almacén?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        self.main._run_api_task(
            method="POST",
            endpoint="/almacen/almacen",
            data=datos,
            callback_success=self._on_guardado,
            callback_error=lambda err: QMessageBox.critical(
                self.panel, "Error", f"Error al guardar: {err}")
        )

    def _on_guardado(self, response):
        QMessageBox.information(self.main.almacen, "Éxito",
                                "Registro guardado correctamente")
        self.limpiar_campos()
        self.main.almacen.hide_panel()
        self.main.buscar_tabla()

    def limpiar_campos(self):
        if self.ln_ns:
            self.ln_ns.clear()
        if self.ln_cantidad:
            self.ln_cantidad.clear()
        if self.str_unidad:
            self.str_unidad.setCurrentIndex(0)
        if self.str_codigoax:
            self.str_codigoax.setCurrentIndex(0)
        if self.str_codigosap:
            self.str_codigosap.clear()
        if self.str_proyecto:
            self.str_proyecto.clear()
        if self.texedit_descripcion:
            self.texedit_descripcion.clear()
