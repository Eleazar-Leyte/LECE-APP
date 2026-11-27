from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QTextEdit, QFrame, QTableWidgetItem, QHeaderView
from PyQt6.QtCore import Qt
from .base_panel_controller import BasePanelController


class CatalogoPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        self.btn_nuevo = self.panel.findChild(
            QPushButton, "catalogo_btn_nuevo")
        self.btn_guardar = self.panel.findChild(
            QPushButton, "catalogo_btn_guardar")
        self.btn_cancelar = self.panel.findChild(
            QPushButton, "catalogo_btn_cancelar")
        self.btn_actualizar = self.panel.findChild(
            QPushButton, "catalogo_btn_actualizar")

        self.ln_buscar = self.panel.findChild(QLineEdit, "catalogo_ln_buscar")
        self.btn_buscar_cat = self.panel.findChild(
            QPushButton, "catalogo_btn_buscar")
        self.ln_codigoax = self.panel.findChild(
            QLineEdit, "catalogo_ln_codigoax")
        self.tex_descripcion = self.panel.findChild(
            QTextEdit, "catalogo_tex_descripcion")

        self.form_container = self.panel.findChild(
            QFrame, "catalogo_form_container")
        self.tabla_principal = self.main.almacen.tablaalmacen

        # Variable para rastrear si estamos editando (None = Modo Creación)
        self.current_codigo_ax = None

        # Conexiones
        if self.btn_nuevo:
            self.btn_nuevo.clicked.connect(self._modo_nuevo)
        if self.btn_cancelar:
            self.btn_cancelar.clicked.connect(self._cerrar_formulario)
        if self.btn_guardar:
            self.btn_guardar.clicked.connect(self._guardar)
        if self.btn_actualizar:
            self.btn_actualizar.clicked.connect(self._modo_edicion)
        if self.ln_buscar:
            self.ln_buscar.textChanged.connect(self._buscar)
        if self.btn_buscar_cat:
            self.btn_buscar_cat.clicked.connect(self._buscar)
        if self.ln_buscar:
            self.ln_buscar.returnPressed.connect(self._buscar)

        self.cargar()

    def _cerrar_formulario(self):
        if not self.form_container:
            return
        self.form_container.setVisible(False)
        self.btn_nuevo.setText(" Nuevo")
        self.current_codigo_ax = None
        self.ln_codigoax.setEnabled(True)
        self.ln_codigoax.clear()
        self.tex_descripcion.clear()

    def _modo_nuevo(self):
        """Prepara el formulario para crear un elemento nuevo."""
        if not self.form_container:
            QMessageBox.critical(self.main.almacen, "Error de UI",
                                 "No se encontró el contenedor del formulario.")
            return

        self.current_codigo_ax = None
        self.ln_codigoax.setEnabled(True)
        self.ln_codigoax.clear()
        self.tex_descripcion.clear()

        self.form_container.setVisible(True)
        self.btn_nuevo.setText(" Ocultar Formulario")
        self.ln_codigoax.setFocus()

    def _modo_edicion(self):
        """Prepara el formulario para editar el elemento seleccionado en la tabla."""
        if not self.form_container:
            QMessageBox.critical(self.main.almacen, "Error de UI",
                                 "No se encontró el contenedor del formulario.")
            return

        row = self.tabla_principal.currentRow()
        if row == -1:
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "Seleccione un material de la tabla para editarlo.")
            return

        # Extraer datos de la fila seleccionada
        codigo_ax = self.tabla_principal.item(row, 0).text()
        descripcion = self.tabla_principal.item(row, 1).text()

        self.current_codigo_ax = codigo_ax

        # Llenar el formulario y bloquear el código AX
        self.ln_codigoax.setText(codigo_ax)
        self.ln_codigoax.setEnabled(False)
        self.tex_descripcion.setPlainText(descripcion)

        self.form_container.setVisible(True)
        self.btn_nuevo.setText(" Ocultar Formulario")
        self.tex_descripcion.setFocus()

    def cargar(self):
        self.main._run_api_task(
            method="GET", endpoint="/almacen/catalogo",
            callback_success=self._on_cargado,
            callback_error=lambda err: QMessageBox.critical(
                self.main.almacen, "Error", str(err))
        )

    def _on_cargado(self, items):
        if not self.tabla_principal:
            return

        self.tabla_principal.clear()
        self.tabla_principal.setColumnCount(4)
        self.tabla_principal.setHorizontalHeaderLabels(
            ["Código AX", "Descripción", "Unidad", "Categoría"])

        self.tabla_principal.verticalHeader().setVisible(False)
        self.tabla_principal.setWordWrap(True)

        header = self.tabla_principal.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_principal.verticalHeader().setDefaultSectionSize(40)
        self.tabla_principal.setRowCount(0)

        for row, item in enumerate(items):
            self.tabla_principal.insertRow(row)
            self.tabla_principal.setItem(
                row, 0, QTableWidgetItem(str(item.get("codigo_ax", ""))))

            desc_item = QTableWidgetItem(str(item.get("nombre_articulo", "")))
            desc_item.setToolTip(str(item.get("nombre_articulo", "")))
            self.tabla_principal.setItem(row, 1, desc_item)

            self.tabla_principal.setItem(
                row, 2, QTableWidgetItem(str(item.get("unidad", ""))))
            self.tabla_principal.setItem(row, 3, QTableWidgetItem(
                str(item.get("categoria", "General"))))

    def _buscar(self):
        """Filtra la tabla según el texto ingresado."""
        if not self.ln_buscar:
            return

        texto = self.ln_buscar.text().strip()

        # Si borra el texto, recarga todo el catálogo
        if not texto:
            self.cargar()
            return

        endpoint = f"/almacen/catalogo?busqueda={texto}"
        self.main._run_api_task(
            method="GET", endpoint=endpoint,
            callback_success=self._on_cargado,
            callback_error=lambda e: QMessageBox.critical(
                self.main.almacen, "Error", f"Error en búsqueda: {e}"))

    def _guardar(self):
        if not self.ln_codigoax or not self.tex_descripcion:
            return

        datos = {
            "codigo_ax": self.ln_codigoax.text().strip(),
            "descripcion": self.tex_descripcion.toPlainText().strip()
        }

        if not datos["codigo_ax"] or not datos["descripcion"]:
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "Código AX y Descripción son obligatorios")
            return

        if self.current_codigo_ax:
            # ES UNA ACTUALIZACIÓN (PUT)
            self.main._run_api_task(
                method="PUT",
                endpoint=f"/almacen/catalogo/{self.current_codigo_ax}",
                data=datos,
                callback_success=lambda r: self._on_guardado_exitoso(
                    "Actualizado"),
                callback_error=lambda err: QMessageBox.critical(
                    self.main.almacen, "Error", str(err))
            )
        else:
            # ES UN NUEVO REGISTRO (POST)
            self.main._run_api_task(
                method="POST",
                endpoint="/almacen/catalogo",
                data=datos,
                callback_success=lambda r: self._on_guardado_exitoso("Creado"),
                callback_error=lambda err: QMessageBox.critical(
                    self.main.almacen, "Error", str(err))
            )

    def _on_guardado_exitoso(self, accion):
        QMessageBox.information(
            self.main.almacen, "Éxito", f"Material {accion} correctamente.")
        self._cerrar_formulario()
        self.cargar()
