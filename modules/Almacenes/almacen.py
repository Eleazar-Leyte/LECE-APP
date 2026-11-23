from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import QComboBox, QMessageBox
import uuid

from modules.Almacenes.almacen_ui import AlmacenUI
from modules.Almacenes.api_worker import ApiWorker
from modules.Almacenes.image_handler import ImageHandler
from TableManager import TableManager

# Importar controladores de paneles
from modules.Almacenes.controllers.ont_panel_controller import OntPanelController
from modules.Almacenes.controllers.modem_panel_controller import ModemPanelController
from modules.Almacenes.controllers.almacen_panel_controller import AlmacenPanelController
from modules.Almacenes.controllers.catalogo_panel_controller import CatalogoPanelController
from modules.Almacenes.controllers.movimiento_panel_controller import MovimientoPanelController
from modules.Almacenes.controllers.entrega_panel_controller import EntregaPanelController
from modules.Almacenes.controllers.recibir_panel_controller import RecibirPanelController


class AreaLoaderWorker(ApiWorker):
    """Worker específico para cargar áreas (señales personalizadas)"""
    areas_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, headers):
        super().__init__("GET", url, headers)
        self.finished.connect(self._on_finished)
        self.error.connect(self._on_error)

    def _on_finished(self, result):
        self.areas_loaded.emit(result)

    def _on_error(self, error_msg):
        self.error_occurred.emit(error_msg)


class CopeLoaderWorker(ApiWorker):
    copes_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, url, headers):
        super().__init__("GET", url, headers)
        self.finished.connect(self._on_finished)
        self.error.connect(self._on_error)

    def _on_finished(self, result):
        self.copes_loaded.emit(result)

    def _on_error(self, error_msg):
        self.error_occurred.emit(error_msg)


class AlmacenController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.almacen = AlmacenUI()
        self.almacen.showMaximized()

        if not self.usuario_actual.get("access_token"):
            QMessageBox.critical(self.almacen, "Error",
                                 "No se encontró autenticación.")
            self.almacen.close()
            return

        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        self.panel_controllers = {}  # panel_index -> controller
        self.active_workers = {}     # worker_id -> worker

        self.setup_connections()
        self.cargar_areas_background()

    def setup_connections(self):
        # Botones principales
        self.almacen.btn_regresar.clicked.connect(self.regresar)
        self.almacen.btn_salir.clicked.connect(self.salir)
        self.almacen.btn_buscar.clicked.connect(self.buscar_tabla)

        # Botones de submódulos
        self.almacen.btn_ont.clicked.connect(
            lambda: self.mostrar_panel(0, "Registro de ONT"))
        self.almacen.btn_modem.clicked.connect(
            lambda: self.mostrar_panel(1, "Registro de MODEM"))
        self.almacen.btn_almacen.clicked.connect(
            lambda: self.mostrar_panel(2, "Registro en Almacén"))
        self.almacen.btn_catalogo.clicked.connect(
            lambda: self.mostrar_panel(3, "Catálogo de Materiales"))
        self.almacen.btn_movalmacen.clicked.connect(
            lambda: self.mostrar_panel(4, "Movimiento entre Almacenes"))
        self.almacen.btn_almacentecnico.clicked.connect(
            lambda: self.mostrar_panel(5, "Entrega a Personal Operativo"))
        self.almacen.btn_recibir.clicked.connect(
            lambda: self.mostrar_panel(6, "Recibir Material"))

        # ComboBox signals
        self.almacen.str_area.currentIndexChanged.connect(self.actualizar_cope)
        self.almacen.btn_close_panel.clicked.connect(self.almacen.hide_panel)

    # === Carga de áreas y copes (similar a antes) ===

    def cargar_areas_background(self):
        self.almacen.str_area.clear()
        self.almacen.str_area.addItem("Cargando áreas...")
        self.almacen.str_area.setEnabled(False)

        worker = AreaLoaderWorker(
            f"{self.api_url}/almacen/areas", self.headers)
        worker.areas_loaded.connect(self.on_areas_loaded)
        worker.error_occurred.connect(self.on_area_load_error)
        self._track_worker(worker)
        worker.start()

    def on_areas_loaded(self, areas):
        self.almacen.str_area.clear()
        self.almacen.str_area.setEnabled(True)
        self.areas_cache = areas

        if self.usuario_actual.get('rol') == 'Admin':
            self.almacen.str_area.addItem("Seleccionar", "")
            for area in areas:
                self.almacen.str_area.addItem(
                    area.get("nombre", f"Área {area.get('id')}"), area.get("id"))
        else:
            area_id = self.usuario_actual.get(
                'area_id') or self.usuario_actual.get('area')
            area_name = self.usuario_actual.get(
                'area_nombre', f'Área {area_id}')
            self.almacen.str_area.addItem(area_name, area_id)

        QTimer.singleShot(100, self.cargar_copes_automatico)

    def on_area_load_error(self, error_msg):
        self.almacen.str_area.clear()
        self.almacen.str_area.setEnabled(True)
        self.almacen.str_area.addItem("Error al cargar áreas")
        QMessageBox.critical(self.almacen, "Error",
                             f"Error cargando áreas: {error_msg}")

    def actualizar_cope(self):
        if self.usuario_actual.get('rol') == 'Admin':
            area_id = self.almacen.str_area.currentData()
        else:
            area_id = self.usuario_actual.get(
                'area_id') or self.usuario_actual.get('area')

        self.almacen.str_cope.clear()
        if not area_id:
            return

        self.almacen.str_cope.addItem("Cargando copes...")
        self.almacen.str_cope.setEnabled(False)

        worker = CopeLoaderWorker(
            f"{self.api_url}/almacen/areas/{area_id}/copes", self.headers)
        worker.copes_loaded.connect(self.on_copes_loaded)
        worker.error_occurred.connect(self.on_cope_load_error)
        self._track_worker(worker)
        worker.start()

    def on_copes_loaded(self, copes):
        self.almacen.str_cope.clear()
        self.almacen.str_cope.setEnabled(True)
        self.almacen.str_cope.addItem("Seleccionar", "")
        for cope in copes:
            self.almacen.str_cope.addItem(cope.get("cope", ""), cope.get("id"))

    def on_cope_load_error(self, error_msg):
        self.almacen.str_cope.clear()
        self.almacen.str_cope.setEnabled(True)
        self.almacen.str_cope.addItem("Error al cargar copes")
        QMessageBox.critical(self.almacen, "Error",
                             f"Error cargando copes: {error_msg}")

    def cargar_copes_automatico(self):
        if self.almacen.str_area.count() > 0 and self.almacen.str_area.currentData():
            self.actualizar_cope()

    # === Búsqueda en tabla ===

    def buscar_tabla(self):
        area = self.almacen.str_area.currentText()
        cope = self.almacen.str_cope.currentText()
        tabla = self.almacen.str_tabla.currentText()

        if not area or area == "Seleccionar":
            QMessageBox.warning(self.almacen, "Advertencia",
                                "Seleccione un área")
            return
        if not cope or cope == "Seleccionar":
            QMessageBox.warning(self.almacen, "Advertencia",
                                "Seleccione un cope")
            return
        if not tabla or tabla == "Seleccionar":
            QMessageBox.warning(self.almacen, "Advertencia",
                                "Seleccione un tipo de inventario")
            return

        endpoint_map = {
            "Almacén": "/almacen/almacen",
            "ONT": "/almacen/ont",
            "MODEM": "/almacen/modem"
        }
        endpoint = endpoint_map.get(tabla)
        if not endpoint:
            QMessageBox.warning(self.almacen, "Error",
                                "Tipo de tabla no válido")
            return

        params = {"area": area, "cope": cope}
        url = f"{self.api_url}{endpoint}?" + \
            "&".join(f"{k}={v}" for k, v in params.items())

        self._run_api_task(
            method="GET",
            endpoint=url,  # ya incluye parámetros
            data=None,
            callback_success=lambda datos: self._on_busqueda_exitosa(
                datos, tabla),
            callback_error=lambda err: QMessageBox.critical(
                self.almacen, "Error", f"Error en búsqueda: {err}")
        )

    def _on_busqueda_exitosa(self, datos, tabla):
        if datos:
            mapeados = self._mapear_datos(datos, tabla)
            TableManager.populate_table(
                self.almacen.tablaalmacen, mapeados, tabla, on_image_click=self.mostrar_imagen)
        else:
            QMessageBox.information(
                self.almacen, "Información", "No se encontraron resultados")

    def _mapear_datos(self, datos, tabla):
        if tabla == "ONT":
            return [{
                "Número de Serie": i.get("numero_serie", ""),
                "Cantidad": i.get("cantidad", 1),
                "Unidad": i.get("unidad", "Pieza"),
                "Modelo": i.get("modelo", ""),
                "Área": i.get("area", ""),
                "Centro de Trabajo": i.get("centro_trabajo", ""),
                "Ubicación": i.get("ubicacion", ""),
                "Fecha de Registro": i.get("fecha_registro", ""),
                "Imagen": i.get("numero_serie") if i.get("imagen") else ""
            } for i in datos]
        elif tabla == "MODEM":
            return [{
                "Número de Serie": i.get("numero_serie", ""),
                "Cantidad": i.get("cantidad", 1),
                "Unidad": i.get("unidad", "Pieza"),
                "Modelo": i.get("modelo", ""),
                "Área": i.get("area", ""),
                "Centro de Trabajo": i.get("centro_trabajo", ""),
                "Ubicación": i.get("ubicacion", ""),
                "Fecha de Registro": i.get("fecha_registro", ""),
                "Imagen": i.get("numero_serie") if i.get("imagen") else ""
            } for i in datos]
        elif tabla == "Almacén":
            return [{
                "ID": i.get("id", ""),
                "Descripción": i.get("descripcion", ""),
                "Código AX": i.get("codigo_ax", ""),
                "Código Catálogo": i.get("codigo_catalogo", ""),
                "Número de Serie": i.get("numero_serie", ""),
                "Cantidad": i.get("cantidad", 0),
                "Unidad": i.get("unidad", ""),
                "Área": i.get("area", ""),
                "COPE": i.get("cope", ""),
                "Proyecto": i.get("proyecto", ""),
                "Fecha de Registro": i.get("fecha_registro", "")
            } for i in datos]
        return []

    def mostrar_imagen(self, identificador, tipo_tabla):
        """Callback cuando se hace clic en el ícono de imagen"""
        if tipo_tabla == "ONT":
            endpoint = f"/almacen/ont/{identificador}/imagen"
        elif tipo_tabla == "MODEM":
            endpoint = f"/almacen/modem/{identificador}/imagen"
        else:
            return

        self._run_api_task(
            method="GET",
            endpoint=endpoint,
            data=None,
            binary=True,
            callback_success=lambda img_bytes: self._mostrar_dialogo_imagen(
                img_bytes, identificador),
            callback_error=lambda err: QMessageBox.warning(
                self.almacen, "Error", f"No se pudo cargar la imagen: {err}")
        )

    def _mostrar_dialogo_imagen(self, img_data, identificador):
        """Muestra la imagen en un diálogo modal"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel
        from PyQt6.QtGui import QPixmap
        from PyQt6.QtCore import Qt

        if not img_data:
            QMessageBox.information(
                self.almacen, "Información", "Este registro no tiene imagen.")
            return

        dialog = QDialog(self.almacen)
        dialog.setWindowTitle(f"Imagen - {identificador}")
        layout = QVBoxLayout(dialog)
        label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(img_data)  # img_data debe ser bytes
        if not pixmap.isNull():
            # Escalar para que no sea enorme, manteniendo proporción
            pixmap = pixmap.scaled(
                600, 600, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            label.setPixmap(pixmap)
        else:
            label.setText("No se pudo cargar la imagen")
        layout.addWidget(label)
        dialog.exec()

    # === Gestión de paneles ===

    def mostrar_panel(self, panel_index, titulo):
        self.almacen.show_panel(panel_index, titulo)
        widget = self.almacen.stacked_panels.widget(panel_index)

        if panel_index == 0 and "ont" not in self.panel_controllers:
            self.panel_controllers["ont"] = OntPanelController(widget, self)
        elif panel_index == 1 and "modem" not in self.panel_controllers:
            self.panel_controllers["modem"] = ModemPanelController(
                widget, self)
        elif panel_index == 2 and "almacen" not in self.panel_controllers:
            self.panel_controllers["almacen"] = AlmacenPanelController(
                widget, self)
        elif panel_index == 3 and "catalogo" not in self.panel_controllers:
            self.panel_controllers["catalogo"] = CatalogoPanelController(
                widget, self)
        elif panel_index == 4 and "movimiento" not in self.panel_controllers:
            self.panel_controllers["movimiento"] = MovimientoPanelController(
                widget, self)
        elif panel_index == 5 and "entrega" not in self.panel_controllers:
            self.panel_controllers["entrega"] = EntregaPanelController(
                widget, self)
        elif panel_index == 6 and "recibir" not in self.panel_controllers:
            self.panel_controllers["recibir"] = RecibirPanelController(
                widget, self)

        if panel_index == 5 and "entrega" in self.panel_controllers:
            self.panel_controllers["entrega"].configurar_tabla()
        elif panel_index == 3 and "catalogo" in self.panel_controllers:
            self.panel_controllers["catalogo"].cargar()
        elif panel_index == 0:
            self.buscar_tabla()  # Si es el panel de ONT, puedes recargar la búsqueda

        self._sincronizar_combos_panel(widget)

    def _sincronizar_combos_panel(self, panel_widget):
        area_combo = panel_widget.findChild(QComboBox, "str_area")
        if area_combo:
            area_combo.clear()
            for i in range(self.almacen.str_area.count()):
                area_combo.addItem(self.almacen.str_area.itemText(
                    i), self.almacen.str_area.itemData(i))
            area_combo.setCurrentIndex(self.almacen.str_area.currentIndex())
        cope_combo = panel_widget.findChild(QComboBox, "str_cope")
        if cope_combo:
            cope_combo.clear()
            for i in range(self.almacen.str_cope.count()):
                cope_combo.addItem(self.almacen.str_cope.itemText(i))
            cope_combo.setCurrentIndex(self.almacen.str_cope.currentIndex())

    # === Método genérico para tareas API ===

    def _run_api_task(self, method, endpoint, data=None, callback_success=None, callback_error=None, binary=False):
        worker_id = str(uuid.uuid4())
        # Asegurar que endpoint sea URL completa
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
                QMessageBox.critical(self.almacen, "Error", error_msg)
            self._cleanup_worker(worker_id)

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def _track_worker(self, worker):
        worker_id = str(uuid.uuid4())
        self.active_workers[worker_id] = worker
        worker.finished.connect(lambda: self._cleanup_worker(worker_id))
        worker.error.connect(lambda: self._cleanup_worker(worker_id))

    def _cleanup_worker(self, worker_id):
        if worker_id in self.active_workers:
            worker = self.active_workers.pop(worker_id)
            worker.deleteLater()

    # === Navegación ===

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.almacen.close()

    def salir(self):
        confirm = QMessageBox.question(self.almacen, "Confirmar", "¿Salir del módulo almacén?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.almacen.close()
