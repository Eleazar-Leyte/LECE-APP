import uuid
from PyQt6.QtWidgets import (QMessageBox, QCalendarWidget, QDialog, QVBoxLayout,
                             QTableWidgetItem, QLabel, QComboBox, QSizePolicy, QPushButton)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon

from modules.Produccion.produccion_ui import ProduccionUI
from TableManager import TableManager
from modules.Almacenes.api_worker import ApiWorker


class ProduccionController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.produccion = ProduccionUI()
        self.produccion.showMaximized()

        if not self.usuario_actual.get("access_token"):
            QMessageBox.critical(
                self.produccion, "Error", "No se encontró la información de autenticación.")
            self.produccion.close()
            return

        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        self.active_workers = {}
        self.tecnicos_cache = []  # Guardar técnicos cargados para inyectarlos en las tablas

        self.produccion.Multi_carga.setCurrentIndex(0)
        self.setup_connections()
        self.iniciar_tablas()
        self.configurar_calendario()
        self.cargar_areas()

    def setup_connections(self):
        self.produccion.btn_regresar.clicked.connect(self.regresar)
        self.produccion.btn_salir.clicked.connect(self.salir)

        self.produccion.btn_F_O.clicked.connect(lambda: self.cambiar_vista(0))
        self.produccion.btn_cobre.clicked.connect(
            lambda: self.cambiar_vista(1))
        self.produccion.btn_quejas.clicked.connect(
            lambda: self.cambiar_vista(2))
        self.produccion.btn_a4.clicked.connect(lambda: self.cambiar_vista(3))

        self.produccion.btn_agregar.clicked.connect(self.agregar_fila)
        self.produccion.btn_eliminar.clicked.connect(self.eliminar_fila)
        self.produccion.btn_guardar.clicked.connect(self.guardar_produccion)

        self.produccion.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
        self.produccion.str_cope.currentIndexChanged.connect(
            self.cargar_tecnicos)

        self.conectar_validaciones()

    def iniciar_tablas(self):
        """Iniciamos las tablas añadiendo una columna extra para el Técnico."""
        for tabla, nombre in [
            (self.produccion.tabla_FO, "Producción F.O."),
            (self.produccion.tabla_cobre, "Producción Cobre"),
            (self.produccion.tabla_quejas, "Producción Cobre"),
            (self.produccion.tabla_a4, "Producción Cobre")
        ]:
            TableManager.populate_table(tabla, [], nombre)

            # Insertar columna "Técnico" al principio (índice 0)
            tabla.insertColumn(0)
            tabla.setHorizontalHeaderItem(
                0, QTableWidgetItem("Técnico Asignado"))
            tabla.horizontalHeader().setSectionResizeMode(
                0, tabla.horizontalHeader().ResizeMode.ResizeToContents)

    def _run_api_task(self, method, endpoint, data=None, callback_success=None, callback_error=None, binary=False):
        worker_id = str(uuid.uuid4())
        url = endpoint if endpoint.startswith(
            "http") else f"{self.api_url}{endpoint}"
        worker = ApiWorker(method, url, self.headers, data, binary=binary)
        self.active_workers[worker_id] = worker

        def on_finished(result):
            if callback_success:
                callback_success(result)
            self._cleanup_worker(worker_id)

        def on_error(error_msg):
            if callback_error:
                callback_error(error_msg)
            else:
                QMessageBox.critical(self.produccion, "Error API", error_msg)
            self._cleanup_worker(worker_id)

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def _cleanup_worker(self, worker_id):
        if worker_id in self.active_workers:
            worker = self.active_workers.pop(worker_id)
            worker.deleteLater()

    # --- COMBOS GLOBALES ---
    def cargar_areas(self):
        self.produccion.str_area.blockSignals(True)
        self.produccion.str_area.clear()
        self.produccion.str_area.addItem("Cargando áreas...")

        self._run_api_task(
            method="GET", endpoint="/almacen/areas",
            callback_success=self._on_areas_cargadas,
            callback_error=lambda e: QMessageBox.critical(
                self.produccion, "Error", f"Error al cargar áreas: {e}")
        )

    def _on_areas_cargadas(self, areas):
        self.produccion.str_area.blockSignals(False)
        self.produccion.str_area.clear()
        self.produccion.str_area.addItem("Seleccionar", "")
        for area in areas:
            self.produccion.str_area.addItem(
                area.get("nombre", ""), area.get("id"))

    def actualizar_cope(self):
        area_id = self.produccion.str_area.currentData()
        self.produccion.str_cope.blockSignals(True)
        self.produccion.str_cope.clear()
        if not area_id:
            self.produccion.str_cope.blockSignals(False)
            return

        self.produccion.str_cope.addItem("Cargando copes...")
        self._run_api_task(
            method="GET", endpoint=f"/almacen/areas/{area_id}/copes",
            callback_success=self._on_copes_cargados,
            callback_error=lambda e: QMessageBox.critical(
                self.produccion, "Error", f"Error al cargar copes: {e}")
        )

    def _on_copes_cargados(self, copes):
        self.produccion.str_cope.blockSignals(False)
        self.produccion.str_cope.clear()
        self.produccion.str_cope.addItem("Seleccionar", "")
        for cope in copes:
            self.produccion.str_cope.addItem(cope.get("cope", ""))

    def cargar_tecnicos(self):
        """Carga los técnicos del COPE actual y los guarda en caché."""
        area_id = self.produccion.str_area.currentData()
        cope = self.produccion.str_cope.currentText()

        self.tecnicos_cache = []
        if not area_id or cope == "Seleccionar":
            return

        self._run_api_task(
            method="GET", endpoint=f"/personal/?area_id={area_id}&cope={cope}",
            callback_success=self._on_tecnicos_cargados,
            callback_error=lambda e: print(f"Error al cargar técnicos: {e}")
        )

    def _on_tecnicos_cargados(self, tecnicos):
        self.tecnicos_cache = tecnicos
        # Actualizar combos existentes en las filas que no tengan técnico seleccionado
        for tabla in [self.produccion.tabla_FO, self.produccion.tabla_cobre, self.produccion.tabla_quejas, self.produccion.tabla_a4]:
            for row in range(tabla.rowCount()):
                combo = tabla.cellWidget(row, 0)
                if isinstance(combo, QComboBox):
                    self._llenar_combo_tecnico(combo)

    def _llenar_combo_tecnico(self, combo):
        current_text = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("Seleccionar Técnico", None)
        for t in self.tecnicos_cache:
            # CORRECCIÓN AQUÍ: Agregamos t.get('apellido_materno', '')
            nombre = f"{t.get('nombre', '')} {t.get('apellido_paterno', '')} {t.get('apellido_materno', '')}".strip(
            )
            combo.addItem(nombre, t.get("id"))
        idx = combo.findText(current_text)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        combo.blockSignals(False)

    # --- TABLAS ---
    def cambiar_vista(self, indice):
        self.produccion.Multi_carga.setCurrentIndex(indice)

    def obtener_tabla_actual(self):
        mapeo = {0: self.produccion.tabla_FO, 1: self.produccion.tabla_cobre,
                 2: self.produccion.tabla_quejas, 3: self.produccion.tabla_a4}
        return mapeo.get(self.produccion.Multi_carga.currentIndex(), self.produccion.tabla_FO)

    def agregar_fila(self):
        tabla = self.obtener_tabla_actual()
        tabla.blockSignals(True)
        row = tabla.rowCount()
        tabla.insertRow(row)

        # 1. Insertar ComboBox de Técnico en la columna 0
        combo = QComboBox()
        # Altura fija para asegurar que el texto quepa
        combo.setMinimumHeight(30)
        combo.setSizePolicy(QSizePolicy.Policy.Expanding,
                            QSizePolicy.Policy.Fixed)

        # Estilo limpio y directo sin margin, usando padding
        combo.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #b0b0b0;
                border-radius: 4px;
                padding: 2px 6px; /* Espacio interno para el texto */
                font: 10pt "MS Shell Dlg 2";
            }
            QComboBox:hover {
                border: 1px solid #80bdff;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                color: black;
                selection-background-color: rgb(1, 59, 61);
                selection-color: white;
            }
        """)
        self._llenar_combo_tecnico(combo)
        tabla.setCellWidget(row, 0, combo)

        # 2. Inicializar el resto de celdas (a partir de la columna 1)
        for col in range(1, tabla.columnCount()):
            item = QTableWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                          Qt.ItemFlag.ItemIsEditable)
            tabla.setItem(row, col, item)

        # 3. Ajustar la altura de la fila
        tabla.setRowHeight(row, 36)

        tabla.blockSignals(False)

    def eliminar_fila(self):
        tabla = self.obtener_tabla_actual()
        row = tabla.currentRow()
        if row != -1:
            tabla.removeRow(row)

    def configurar_calendario(self):
        for tabla in [self.produccion.tabla_FO, self.produccion.tabla_cobre, self.produccion.tabla_quejas, self.produccion.tabla_a4]:
            tabla.cellClicked.connect(
                lambda r, c, t=tabla: self.mostrar_calendario(r, c, t))

    def mostrar_calendario(self, row, col, tabla):
        # La columna de fecha ahora es la 7 (porque insertamos la 0 del técnico)
        if col != 7:
            return

        dialog = QDialog(self.produccion)
        calendario = QCalendarWidget(dialog)
        dialog.setWindowTitle("Seleccionar Fecha")
        layout = QVBoxLayout(dialog)
        layout.addWidget(calendario)
        dialog.setLayout(layout)

        calendario.clicked.connect(
            lambda date: self.actualizar_fecha(row, date, tabla, dialog))
        dialog.exec()

    def actualizar_fecha(self, row, date, tabla, dialog):
        tabla.setItem(row, 7, QTableWidgetItem(date.toString("dd/MM/yyyy")))
        dialog.accept()

    # --- VALIDACIONES ---
    def conectar_validaciones(self):
        tablas = [
            (self.produccion.tabla_FO, "ONT"),
            (self.produccion.tabla_cobre, "MODEM"),
            (self.produccion.tabla_quejas, "QUEJAS"),
            (self.produccion.tabla_a4, "A4")
        ]
        for tabla, tipo in tablas:
            tabla.cellChanged.connect(
                lambda r, c, t=tabla, tt=tipo: self._validar_fila_completa(r, c, t, tt))

    def _validar_fila_completa(self, row, col, tabla, tipo):
        try:
            if row >= tabla.rowCount():
                return

            # Columnas desplazadas +1 por el combo del técnico
            if col == 2:  # Teléfono
                telefono = tabla.item(row, col).text()
                if telefono and not (telefono.isdigit() and len(telefono) == 10):
                    raise ValueError(
                        "El teléfono debe tener 10 dígitos numéricos")

            elif col == 3:  # Tipo Tarea
                item = tabla.item(row, col)
                item.setText(''.join(c for c in item.text().upper()
                             if c.isalnum() or c in ('-', '_')))

            elif col == 5:  # Número de Serie
                self.validar_numero_serie(row, col, tabla, tipo)

        except Exception as e:
            QMessageBox.warning(self.produccion, "Error de validación", str(e))
            tabla.item(row, col).setText("")

    def validar_numero_serie(self, row, col, tabla, tipo):
        # Validar que haya un técnico seleccionado en la fila
        combo = tabla.cellWidget(row, 0)
        if not combo or combo.currentData() is None:
            raise ValueError("Primero seleccione un Técnico para esta fila.")

        tecnico_asignado = combo.currentText()

        numero_serie = tabla.item(row, col).text().strip()
        if not numero_serie:
            return

        # Determinar endpoint (apuntando a /campo/)
        if tipo in ["ONT", "QUEJAS"]:
            ep_eq = f"/almacen/campo/ont/{numero_serie}"
            ep_img = f"/almacen/campo/ont/{numero_serie}/imagen"
        elif tipo in ["MODEM", "A4"]:
            ep_eq = f"/almacen/campo/modem/{numero_serie}"
            ep_img = f"/almacen/campo/modem/{numero_serie}/imagen"
        else:
            return

        self._run_api_task(
            method="GET", endpoint=ep_eq,
            callback_success=lambda data: self._on_equipo_encontrado(
                data, row, tabla, tipo, ep_img, tecnico_asignado),
            callback_error=lambda err: self._on_equipo_no_encontrado(
                row, tabla, err)
        )

    def _on_equipo_encontrado(self, data, row, tabla, tipo, endpoint_imagen, tecnico_asignado):
        try:
            # VALIDACIÓN DE SEGURIDAD: ¿El equipo pertenece al técnico?
            expediente_db = data.get("expediente_tecnico", "")

            # Comparamos si el nombre del técnico seleccionado está contenido en el expediente de la DB.
            # Usamos .lower() para evitar problemas de mayúsculas/minúsculas.
            if tecnico_asignado.lower() not in expediente_db.lower():
                raise ValueError(
                    f"El equipo está a nombre de '{expediente_db}', no de '{tecnico_asignado}'.")

            # Columna de Modelo ahora es la 6
            modelo_item = QTableWidgetItem(data.get("modelo", ""))
            modelo_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            tabla.setItem(row, 6, modelo_item)

            # Configurar celda de imagen (Columna 8)
            if data.get("imagen") == "Si":
                btn = QPushButton()
                # Asegúrate de tener este ícono
                btn.setIcon(QIcon("assets/icons/eye.svg"))
                btn.setIconSize(QSize(24, 24))
                btn.setFlat(True)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setToolTip("Ver imagen del equipo")

                # Guardamos la URL de la imagen en el botón para saber qué descargar
                btn.setProperty("endpoint_imagen", endpoint_imagen)
                btn.setProperty("numero_serie", data.get("numero_serie", ""))

                # Conectar clic a la función que descarga y muestra
                btn.clicked.connect(
                    lambda checked, b=btn: self._mostrar_imagen_desde_api(b))

                tabla.setCellWidget(row, 8, btn)
            else:
                tabla.setItem(row, 8, QTableWidgetItem("Sin imagen"))

        except Exception as e:
            self._on_equipo_no_encontrado(row, tabla, str(e))

    def _on_equipo_no_encontrado(self, row, tabla, err):
        QMessageBox.warning(
            self.produccion, "Error de Validación", f"Equipo no válido: {err}")
        # Limpiar las celdas de la fila para evitar guardar basura
        tabla.item(row, 5).setText("")  # Limpiar número de serie
        tabla.setItem(row, 6, QTableWidgetItem(""))  # Limpiar modelo
        tabla.setItem(row, 8, QTableWidgetItem(""))  # Limpiar imagen

    def _mostrar_imagen_desde_api(self, button):
        """Descarga la imagen binaria de la API y la muestra en un diálogo."""
        endpoint = button.property("endpoint_imagen")
        serie = button.property("numero_serie")

        self._run_api_task(
            method="GET",
            endpoint=endpoint,
            binary=True,
            callback_success=lambda img_bytes: self._abrir_dialogo_imagen(
                img_bytes, serie),
            callback_error=lambda err: QMessageBox.warning(
                self.produccion, "Error", f"No se pudo cargar la imagen: {err}")
        )

    def _abrir_dialogo_imagen(self, img_bytes, identificador):
        """Muestra la imagen en un QDialog modal."""
        if not img_bytes:
            QMessageBox.information(
                self.produccion, "Información", "Este registro no tiene imagen.")
            return

        dialog = QDialog(self.produccion)
        dialog.setWindowTitle(f"Imagen - {identificador}")
        layout = QVBoxLayout(dialog)

        label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(img_bytes)

        if not pixmap.isNull():
            # Escalar para que no sea enorme
            pixmap = pixmap.scaled(
                600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            label.setText("No se pudo cargar la imagen")

        layout.addWidget(label)
        dialog.exec()

    # --- GUARDAR ---
    def guardar_produccion(self):
        area = self.produccion.str_area.currentText()
        cope = self.produccion.str_cope.currentText()

        if not area or area == "Seleccionar" or not cope or cope == "Seleccionar":
            QMessageBox.warning(self.produccion, "Atención",
                                "Seleccione Área y COPE")
            return

        payload = {"area": area, "cope": cope, "registros": []}
        tablas_mapeo = {"tabla_FO": "fibra_optica", "tabla_cobre": "cobre",
                        "tabla_quejas": "quejas", "tabla_a4": "a4_incentivos"}

        for ui_nombre, db_nombre in tablas_mapeo.items():
            tabla = getattr(self.produccion, ui_nombre)
            for row in range(tabla.rowCount()):
                combo_tec = tabla.cellWidget(row, 0)
                tecnico_nombre = combo_tec.currentText() if combo_tec else ""
                tecnico_id = combo_tec.currentData() if combo_tec else None

                # Validar que no esté vacía
                folio_item = tabla.item(row, 1)  # Folio ahora es col 1
                if not folio_item or not folio_item.text().strip():
                    continue

                if not tecnico_id:
                    QMessageBox.warning(
                        self.produccion, "Atención", f"Falta asignar técnico en la fila {row+1} de {ui_nombre}")
                    return

                registro = {
                    "tipo_produccion": db_nombre,
                    "exp_tecnico": tecnico_nombre,
                    "tecnico_id": tecnico_id,
                    "folio_pisa": folio_item.text(),
                    "telefono": tabla.item(row, 2).text() if tabla.item(row, 2) else "",
                    "tipo_tarea": tabla.item(row, 3).text() if tabla.item(row, 3) else "",
                    "cantidad_mts": tabla.item(row, 4).text() if tabla.item(row, 4) else "",
                    "numero_serie": tabla.item(row, 5).text() if tabla.item(row, 5) else "",
                    "modelo": tabla.item(row, 6).text() if tabla.item(row, 6) else "",
                    "fecha_posteo": tabla.item(row, 7).text() if tabla.item(row, 7) else ""
                }
                payload["registros"].append(registro)

        if not payload["registros"]:
            QMessageBox.information(
                self.produccion, "Información", "No hay registros con folio para guardar.")
            return

        self._run_api_task(
            method="POST", endpoint="/produccion/guardar", data=payload,
            callback_success=self._on_guardado_exitoso,
            callback_error=lambda err: QMessageBox.critical(
                self.produccion, "Error al Guardar", err)
        )

    def _on_guardado_exitoso(self, response):
        QMessageBox.information(self.produccion, "Éxito", response.get(
            "message", "Producción guardada."))
        for t in [self.produccion.tabla_FO, self.produccion.tabla_cobre, self.produccion.tabla_quejas, self.produccion.tabla_a4]:
            t.setRowCount(0)

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.produccion.close()

    def salir(self):
        self.produccion.close()
