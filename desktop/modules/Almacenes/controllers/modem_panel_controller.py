from PyQt6.QtWidgets import QMessageBox, QPushButton, QLineEdit, QComboBox, QLabel
from .base_panel_controller import BasePanelController


class ModemPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        # Buscar widgets específicos del panel MODEM
        self.ln_ns = self.panel.findChild(QLineEdit, "modem_ln_ns")
        self.ln_modelo = self.panel.findChild(QLineEdit, "modem_ln_modelo")
        self.str_proyecto = self.panel.findChild(
            QLineEdit, "modem_str_proyecto")
        self.str_ubicacion = self.panel.findChild(
            QComboBox, "modem_str_ubicacion")
        self.str_exptec = self.panel.findChild(QComboBox, "modem_str_exptec")
        self.label_imagen = self.panel.findChild(QLabel, "modem_label_imagen")
        self.btn_imagen = self.panel.findChild(QPushButton, "modem_btn_imagen")
        self.btn_codebar = self.panel.findChild(
            QPushButton, "modem_btn_codebar")
        self.btn_guardar = self.panel.findChild(
            QPushButton, "modem_btn_guardar")

        # Buscar la etiqueta del Expediente Técnico por su texto
        self.label_exptec = None
        for lbl in self.panel.findChildren(QLabel):
            if "Expediente Técnico" in lbl.text():
                self.label_exptec = lbl
                break

        # Conectar señales
        if self.btn_imagen:
            self.btn_imagen.clicked.connect(
                lambda: self._seleccionar_imagen(self.label_imagen))
        if self.btn_codebar:
            self.btn_codebar.clicked.connect(self._leer_codigo_barras)
        if self.btn_guardar:
            self.btn_guardar.clicked.connect(self._guardar)

        # Conectar ubicación para mostrar/ocultar combo de expediente
        if self.str_ubicacion:
            self.str_ubicacion.currentIndexChanged.connect(
                self._actualizar_visibilidad_exptec)

        # Conectar cambios de área/cope para recargar técnicos en segundo plano
        if hasattr(self.main, 'almacen'):
            self.main.almacen.str_area.currentIndexChanged.connect(
                self._cargar_tecnicos)
            self.main.almacen.str_cope.currentIndexChanged.connect(
                self._cargar_tecnicos)

        # Inicializar visibilidad y precargar técnicos si ya hay área y cope
        self._actualizar_visibilidad_exptec()
        if self.main.almacen.str_area.currentData() and self.main.almacen.str_cope.currentText() not in ("", "Seleccionar"):
            self._cargar_tecnicos()

    # =========================================================================
    # VISIBILIDAD DEL EXPEDIENTE TÉCNICO
    # =========================================================================
    def _actualizar_visibilidad_exptec(self):
        """Muestra u oculta el combo y la etiqueta de Expediente Técnico según la ubicación."""
        if not self.str_ubicacion or not self.str_exptec:
            return

        ubicacion = self.str_ubicacion.currentText()
        visible = (ubicacion == "En campo")

        # Ocultar/mostrar el combo
        self.str_exptec.setVisible(visible)

        # Ocultar/mostrar la etiqueta (si se encontró)
        if self.label_exptec:
            self.label_exptec.setVisible(visible)

        # Si se hace visible, aseguramos que los técnicos estén cargados
        if visible and self.str_exptec.count() <= 1:
            self._cargar_tecnicos()

    # =========================================================================
    # CARGA DE TÉCNICOS (EXPEDIENTES)
    # =========================================================================
    def _cargar_tecnicos(self):
        """Carga los técnicos desde la API de personal según área y cope."""
        area_id = self.main.almacen.str_area.currentData()
        cope = self.main.almacen.str_cope.currentText()
        if not area_id or not cope or cope == "Seleccionar":
            return

        endpoint = f"/personal/?area_id={area_id}&cope={cope}"
        self.main._run_api_task(
            method="GET",
            endpoint=endpoint,
            data=None,
            callback_success=self._on_tecnicos_cargados,
            callback_error=lambda err: None  # Silencioso si falla
        )

    def _on_tecnicos_cargados(self, data):
        """Llena el combo de expedientes con los técnicos obtenidos."""
        if not self.str_exptec:
            return
        self.str_exptec.clear()
        self.str_exptec.addItem("Seleccionar")
        if not data:
            return
        for persona in data:
            nombre = persona.get("nombre", "")
            apellido_paterno = persona.get("apellido_paterno", "")
            apellido_materno = persona.get("apellido_materno", "")
            nombre_completo = f"{nombre} {apellido_paterno} {apellido_materno}".strip(
            )
            if nombre_completo:
                self.str_exptec.addItem(nombre_completo)

    # =========================================================================
    # GUARDAR
    # =========================================================================
    def _guardar(self):
        if not self.ln_ns or not self.ln_modelo:
            QMessageBox.critical(
                self.main.almacen, "Error", "Error de interfaz")
            return

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

        ubicacion = self.str_ubicacion.currentText() if self.str_ubicacion else "Almacén"
        if ubicacion not in ["Almacén", "En campo"]:
            ubicacion = "Almacén"

        datos = {
            "numero_serie": self.ln_ns.text().strip(),
            "modelo": self.ln_modelo.text().strip(),
            "cantidad": 1,
            "unidad": "Pieza",
            "area": area,
            "centro_trabajo": cope,
            "ubicacion": ubicacion,
            "proyecto": self.str_proyecto.text().strip() if self.str_proyecto else "",
            "expediente_tecnico": self.str_exptec.currentText() if self.str_exptec and self.str_exptec.isVisible() else "",
            "imagen": self.current_image_data
        }

        if not datos["numero_serie"]:
            QMessageBox.warning(self.main.almacen,
                                "Advertencia", "Número de serie obligatorio")
            return
        if not datos["modelo"]:
            QMessageBox.warning(self.main.almacen,
                                "Advertencia", "Modelo obligatorio")
            return
        if ubicacion == "En campo" and (not datos["expediente_tecnico"] or datos["expediente_tecnico"] == "Seleccionar"):
            QMessageBox.warning(self.main.almacen, "Advertencia",
                                "Seleccione un expediente técnico")
            return

        if QMessageBox.question(self.main.almacen, "Confirmar", "¿Guardar MODEM?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        print("Datos a enviar:", datos)  # Depuración

        self.main._run_api_task(
            method="POST",
            endpoint="/almacen/modem",
            data=datos,
            callback_success=self._on_guardado,
            callback_error=lambda err: QMessageBox.critical(
                self.main.almacen, "Error", f"Error al guardar: {err}")
        )

    def _on_guardado(self, response):
        QMessageBox.information(
            self.main.almacen, "Éxito", "MODEM guardado correctamente")
        self.limpiar_campos()
        self.main.almacen.hide_panel()
        self.main.buscar_tabla()

    def limpiar_campos(self):
        if self.ln_ns:
            self.ln_ns.clear()
        if self.ln_modelo:
            self.ln_modelo.clear()
        if self.str_proyecto:
            self.str_proyecto.clear()
        if self.str_ubicacion:
            self.str_ubicacion.setCurrentIndex(0)
        if self.str_exptec:
            self.str_exptec.clear()
            self.str_exptec.addItem("Seleccionar")
        if self.label_imagen:
            self.label_imagen.clear()
            self.label_imagen.setText("Vista previa de imagen/etiqueta")
        self.current_image_data = None
