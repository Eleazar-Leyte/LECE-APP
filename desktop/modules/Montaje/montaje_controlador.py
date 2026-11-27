import uuid
import json
import os
import base64
import zipfile
import pandas as pd
from PyQt6.QtWidgets import QMessageBox, QTableWidget, QTableWidgetItem, QListWidgetItem, QFileDialog, QProgressDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QColor

from desktop.modules.Montaje.montaje_ui import MontajeUI, ExportarDialog
from desktop.modules.Almacenes.api_worker import ApiWorker
from TableManager import TableManager


class MontajeController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.montaje = MontajeUI()
        # CONECTAR LA SEÑAL DE CIERRE PARA LIMPIAR HILOS
        self.montaje.closing.connect(self.cleanup_workers)
        self.montaje.showMaximized()

        # Validación de token
        if not self.usuario_actual.get("access_token"):
            QMessageBox.critical(
                self.montaje, "Error", "No se encontró la información de autenticación.")
            self.montaje.close()
            return

        # Configuración API
        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        self.active_workers = {}

        self.setup_connections()
        self.configurar_tabla()
        self.cargar_areas()

    # ------------------------------------------LIMPIEZA DE HILOS-------------------------------------------------------------

    def cleanup_workers(self):
        """
        Detiene y espera a que terminen todos los hilos antes de cerrar.
        """
        for worker in list(self.active_workers.values()):
            if worker.isRunning():
                worker.quit()
                worker.wait()
            worker.deleteLater()
        self.active_workers.clear()

    # --------------------------------------CONEXIONES Y CONFIGURACIÓN ------------------------------------------------

    def setup_connections(self):
        # Botones principales
        self.montaje.btn_regresar.clicked.connect(self.regresar)
        self.montaje.btn_salir.clicked.connect(self.salir)

        # Combos en cascada
        self.montaje.str_area.currentIndexChanged.connect(self.actualizar_cope)
        self.montaje.str_cope.currentIndexChanged.connect(
            self.actualizar_exptec)

        # Botones de acción
        self.montaje.btn_buscar.clicked.connect(self.buscar_folios)
        self.montaje.btn_guardar.clicked.connect(self.guardar_cuadre)
        self.montaje.btn_exportar.clicked.connect(self.abrir_exportacion)

        # Lista de folios
        self.montaje.lista_instalaciones.itemClicked.connect(
            self.cargar_materiales_folio)

    def configurar_tabla(self):
        """
        Inicializa la tabla de materiales con TableManager y bloquea columnas.
        """
        TableManager.populate_table(
            self.montaje.tabla_materiales, [], "Consumo")
        # Permitir edición con doble clic o presionando una tecla
        self.montaje.tabla_materiales.setEditTriggers(
            QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.AnyKeyPressed
        )
        self.bloquear_columnas_tabla()
        self.montaje.tabla_materiales.cellChanged.connect(
            self._actualizar_diferencia)

    def bloquear_columnas_tabla(self):
        """
        Bloquea todas las columnas excepto 'Consumido' (índice 4).
        """
        for col in range(self.montaje.tabla_materiales.columnCount()):
            for row in range(self.montaje.tabla_materiales.rowCount()):
                item = self.montaje.tabla_materiales.item(row, col)
                if item:
                    if col == 4:  # Columna Consumido (Editable)
                        # Aseguramos que tenga habilitada la edición y selección
                        item.setFlags(
                            Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
                        # Le damos un fondo ligeramente distinto para indicar que es editable
                        item.setBackground(QColor("#f0fdf4"))
                    else:  # Resto de columnas (Solo lectura)
                        item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                      Qt.ItemFlag.ItemIsSelectable)

    def _run_api_task(self, method, endpoint, data=None, callback_success=None, callback_error=None):
        worker_id = str(uuid.uuid4())
        url = endpoint if endpoint.startswith(
            "http") else f"{self.api_url}{endpoint}"
        worker = ApiWorker(method, url, self.headers, data)
        self.active_workers[worker_id] = worker

        def on_finished(result):
            if callback_success:
                callback_success(result)
            self._cleanup_worker(worker_id)

        def on_error(error_msg):
            if callback_error:
                callback_error(error_msg)
            else:
                QMessageBox.critical(self.montaje, "Error API", error_msg)
            self._cleanup_worker(worker_id)

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def _cleanup_worker(self, worker_id):
        if worker_id in self.active_workers:
            worker = self.active_workers.pop(worker_id)
            worker.deleteLater()

    # ----------------------------------------------COMBOS EN CASCADA---------------------------------------------------------------------

    def cargar_areas(self):
        self.montaje.str_area.blockSignals(True)
        self.montaje.str_area.clear()
        self.montaje.str_area.addItem("Cargando...")

        self._run_api_task(
            method="GET", endpoint="/almacen/areas",
            callback_success=self._on_areas_cargadas,
            callback_error=lambda e: QMessageBox.critical(
                self.montaje, "Error", f"Error: {e}")
        )

    def _on_areas_cargadas(self, areas):
        self.montaje.str_area.blockSignals(False)
        self.montaje.str_area.clear()
        self.montaje.str_area.addItem("Seleccionar", "")
        for area in areas:
            self.montaje.str_area.addItem(
                area.get("nombre", ""), area.get("id"))

    def actualizar_cope(self):
        area_id = self.montaje.str_area.currentData()
        self.montaje.str_cope.blockSignals(True)
        self.montaje.str_cope.clear()
        if not area_id:
            self.montaje.str_cope.blockSignals(False)
            return

        self.montaje.str_cope.addItem("Cargando...")
        self._run_api_task(
            method="GET", endpoint=f"/almacen/areas/{area_id}/copes",
            callback_success=self._on_copes_cargados,
            callback_error=lambda e: print(f"Error copes: {e}")
        )

    def _on_copes_cargados(self, copes):
        self.montaje.str_cope.blockSignals(False)
        self.montaje.str_cope.clear()
        self.montaje.str_cope.addItem("Seleccionar", "")
        for cope in copes:
            self.montaje.str_cope.addItem(cope.get("cope", ""))

    # -----------------------------------------ACTUALIZAR TÉCNICOS------------------------------------------------------

    def actualizar_exptec(self):
        area_id = self.montaje.str_area.currentData()
        cope = self.montaje.str_cope.currentText()

        self.montaje.str_exptec.blockSignals(True)
        self.montaje.str_exptec.clear()
        if not area_id or cope == "Seleccionar":
            self.montaje.str_exptec.blockSignals(False)
            return

        self.montaje.str_exptec.addItem("Cargando...")
        self._run_api_task(
            method="GET", endpoint=f"/personal/?area_id={area_id}&cope={cope}",
            callback_success=self._on_tecnicos_cargados,
            callback_error=lambda e: print(f"Error técnicos: {e}")
        )

    def _on_tecnicos_cargados(self, tecnicos):
        self.montaje.str_exptec.blockSignals(False)
        self.montaje.str_exptec.clear()
        self.montaje.str_exptec.addItem("Seleccionar", "")
        for t in tecnicos:
            nombre = f"{t.get('nombre', '')} {t.get('apellido_paterno', '')} {t.get('apellido_materno', '')}".strip(
            )
            self.montaje.str_exptec.addItem(nombre, t.get("id"))

    # -----------------------------------------LÓGICA DE BÚSQUEDA Y TABLA------------------------------------------------------

    def buscar_folios(self):
        area = self.montaje.str_area.currentText()
        cope = self.montaje.str_cope.currentText()
        tecnico = self.montaje.str_exptec.currentText()

        if not area or area == "Seleccionar" or not cope or cope == "Seleccionar" or not tecnico or tecnico == "Seleccionar":
            QMessageBox.warning(self.montaje, "Atención",
                                "Seleccione Área, COPE y Técnico.")
            return

        self.montaje.lista_instalaciones.clear()
        self.montaje.tabla_materiales.setRowCount(0)

        self._run_api_task(
            method="GET",
            endpoint=f"/montaje/folios?area={area}&cope={cope}&exp_tecnico={tecnico}",
            callback_success=self._on_folios_cargados,
            callback_error=lambda e: QMessageBox.critical(
                self.montaje, "Error", f"Error búsqueda: {e}")
        )

    def _on_folios_cargados(self, folios):
        if not folios:
            self.montaje.lista_instalaciones.addItem(
                "No hay folios pendientes")
            return

        for f in folios:
            nombre_tabla = f.get('tabla', '').replace('_', ' ').title()
            texto = f"📄 {f.get('folio')} ({nombre_tabla})"

            list_item = QListWidgetItem(texto)
            list_item.setData(Qt.ItemDataRole.UserRole, f)

            self.montaje.lista_instalaciones.addItem(list_item)

    def cargar_materiales_folio(self, item):
        datos_folio = item.data(Qt.ItemDataRole.UserRole)
        if not datos_folio:
            return

        # Actualizar el título dinámico de la tabla
        self.montaje.lbl_folio_activo.setText(
            f"Materiales del Folio: {datos_folio.get('folio')} ({datos_folio.get('tabla').replace('_', ' ').title()})")

        area = self.montaje.str_area.currentText()
        cope = self.montaje.str_cope.currentText()
        tecnico = self.montaje.str_exptec.currentText()

        tabla = datos_folio.get("tabla")
        folio = datos_folio.get("folio")

        self.montaje.tabla_materiales.setRowCount(0)

        self._run_api_task(
            method="GET",
            endpoint=f"/montaje/materiales/{tabla}/{folio}?area={area}&cope={cope}&exp_tecnico={tecnico}",
            callback_success=self._on_materiales_cargados,
            callback_error=lambda e: QMessageBox.critical(
                self.montaje, "Error", f"Error carga: {e}")
        )

    def _on_materiales_cargados(self, materiales):
        datos_formateados = []
        for m in materiales:
            datos_formateados.append({
                "Número de Serie": m.get("numero_serie") if m.get("numero_serie") else "S/N",
                "Materiales": m.get("material"),
                "Tipo": m.get("tipo"),
                "Asignado": str(m.get("asignado", 0)),
                "Consumido": "0",
                "Diferencia": str(m.get("asignado", 0))
            })

        TableManager.populate_table(
            self.montaje.tabla_materiales, datos_formateados, "Consumo")
        self.bloquear_columnas_tabla()

    def _actualizar_diferencia(self, row, column):
        if column != 4:
            return

        try:
            item_asignado = self.montaje.tabla_materiales.item(row, 3)
            item_consumido = self.montaje.tabla_materiales.item(row, 4)

            asignado = int(item_asignado.text()) if item_asignado else 0
            consumido = int(item_consumido.text()) if item_consumido else 0

            if consumido < 0 or consumido > asignado:
                raise ValueError(
                    "El consumo no puede ser negativo ni mayor al asignado.")

            diferencia = asignado - consumido

            item_dif = QTableWidgetItem(str(diferencia))
            item_dif.setFlags(item_dif.flags() & ~Qt.ItemFlag.ItemIsEditable)
            if diferencia < 0:
                item_dif.setForeground(QColor(255, 0, 0))
            else:
                item_dif.setForeground(QColor(0, 0, 0))

            self.montaje.tabla_materiales.setItem(row, 5, item_dif)

        except ValueError as e:
            QMessageBox.warning(self.montaje, "Validación", str(e))
            self.montaje.tabla_materiales.item(row, 4).setText("0")

    # -----------------------------------------GUARDAR Y EXPORTAR------------------------------------------------------

    def guardar_cuadre(self):
        item_seleccionado = self.montaje.lista_instalaciones.currentItem()
        if not item_seleccionado or not item_seleccionado.data(Qt.ItemDataRole.UserRole):
            QMessageBox.warning(self.montaje, "Error",
                                "Seleccione un folio válido de la lista.")
            return

        datos_folio = item_seleccionado.data(Qt.ItemDataRole.UserRole)

        area = self.montaje.str_area.currentText()
        cope = self.montaje.str_cope.currentText()
        tecnico = self.montaje.str_exptec.currentText()

        consumos = []
        for row in range(self.montaje.tabla_materiales.rowCount()):
            num_serie_item = self.montaje.tabla_materiales.item(row, 0)
            material_item = self.montaje.tabla_materiales.item(row, 1)
            tipo_item = self.montaje.tabla_materiales.item(row, 2)
            consumido_item = self.montaje.tabla_materiales.item(row, 4)

            consumido = int(consumido_item.text(
            )) if consumido_item and consumido_item.text().isdigit() else 0

            if consumido > 0:
                consumos.append({
                    "tipo": tipo_item.text(),
                    "numero_serie": num_serie_item.text() if num_serie_item.text() != "S/N" else None,
                    "descripcion": material_item.text(),
                    "cantidad": consumido
                })

        if not consumos:
            QMessageBox.warning(self.montaje, "Advertencia",
                                "No ha registrado ningún material consumido.")
            return

        payload = {
            "tabla_origen": datos_folio.get("tabla"),
            "folio": datos_folio.get("folio"),
            "area": area,
            "cope": cope,
            "exp_tecnico": tecnico,
            "consumos": consumos
        }

        if QMessageBox.question(self.montaje, "Confirmar", "¿Desea aplicar este cuadre? El material será descontado del inventario del técnico.",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.No:
            return

        self._run_api_task(
            method="POST",
            endpoint="/montaje/guardar",
            data=payload,
            callback_success=self._on_cuadre_guardado,
            callback_error=lambda e: QMessageBox.critical(
                self.montaje, "Error", f"Error al guardar cuadre: {e}")
        )

    def _on_cuadre_guardado(self, response):
        QMessageBox.information(
            self.montaje, "Éxito", "Cuadre guardado correctamente. El inventario ha sido actualizado.")
        self.buscar_folios()
        self.montaje.tabla_materiales.setRowCount(0)

    def abrir_exportacion(self):
        dialog = ExportarDialog(self.montaje)

        # Llenar combos del diálogo
        dialog.str_area_exp.addItems([self.montaje.str_area.itemText(
            i) for i in range(self.montaje.str_area.count())])
        dialog.str_cope_exp.addItems([self.montaje.str_cope.itemText(
            i) for i in range(self.montaje.str_cope.count())])

        if dialog.exec():
            area = dialog.str_area_exp.currentText()
            cope = dialog.str_cope_exp.currentText()
            fecha_ini = dialog.fecha_ini.date().toString("yyyy-MM-dd")
            fecha_fin = dialog.fecha_fin.date().toString("yyyy-MM-dd")

            # Pedir ruta de guardado
            default_name = f"Produccion_{fecha_ini}_a_{fecha_fin}.xlsx"
            excel_path, _ = QFileDialog.getSaveFileName(
                self.montaje, "Guardar Reporte", default_name, "Excel Files (*.xlsx)"
            )
            if not excel_path:
                return

            # Descargar datos de la API
            params = f"area={area}&fecha_ini={fecha_ini}&fecha_fin={fecha_fin}"
            if cope and cope != "Seleccionar":
                params += f"&cope={cope}"

            self._run_api_task(
                method="GET",
                endpoint=f"/montaje/exportar?{params}",
                callback_success=lambda data: self._iniciar_hilo_exportacion(
                    data, excel_path),
                callback_error=lambda e: QMessageBox.critical(
                    self.montaje, "Error", f"Error al descargar datos: {e}")
            )

    def _iniciar_hilo_exportacion(self, data_json, excel_path):
        if not any(data_json.values()):
            QMessageBox.warning(
                self.montaje, "Sin datos", "No se encontraron registros en las fechas seleccionadas.")
            return

        self.progress_dialog = QProgressDialog(
            "Generando Excel e imágenes...", "Cancelar", 0, 0, self.montaje)
        self.progress_dialog.setWindowTitle("Exportando")
        self.progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress_dialog.show()

        self.export_thread = QThread()
        self.export_worker = ExportWorker(data_json, excel_path)
        self.export_worker.moveToThread(self.export_thread)

        self.export_thread.started.connect(self.export_worker.run)

        def on_finished(success, message):
            self.progress_dialog.close()
            if success:
                QMessageBox.information(
                    self.montaje, "Éxito", f"Reporte exportado correctamente en:\n{message}\n\n(Se generó también un ZIP con las imágenes)")
            self.export_thread.quit()
            self.export_thread.wait()
            self.export_worker.deleteLater()
            self.export_thread.deleteLater()

        def on_error(err):
            self.progress_dialog.close()
            QMessageBox.critical(self.montaje, "Error",
                                 f"Error al generar el Excel: {err}")
            self.export_thread.quit()
            self.export_thread.wait()

        self.export_worker.finished.connect(on_finished)
        self.export_worker.error.connect(on_error)
        self.export_thread.start()

    # ---------------------------------------------NAVEGACIÓN ------------------------------------------------

    def regresar(self):
        """Regresa al menú principal"""
        self.cleanup_workers()
        from desktop.modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.montaje.close()

    def salir(self):
        """Cierra la aplicación"""
        self.cleanup_workers()
        self.montaje.close()

    # ===========================================================================
    # CLASE PARA EXPORTAR
    # ===========================================================================


class ExportWorker(QObject):
    finished = pyqtSignal(bool, str)
    error = pyqtSignal(str)

    def __init__(self, data_json, excel_path):
        super().__init__()
        self.data_json = data_json
        self.excel_path = excel_path

    def run(self):
        try:
            dataframes = {}
            consumo_data = []
            imagenes_zip = {}

            # Procesar cada tabla
            for tabla, registros in self.data_json.items():
                expanded_data = []
                for item in registros:
                    item_copy = item.copy()

                    # Extraer imagen para el ZIP
                    if item_copy.get("imagen_b64") and item_copy.get("numero_serie"):
                        img_name = f"{tabla.upper()}_{item_copy['numero_serie']}.png"
                        try:
                            imagenes_zip[img_name] = base64.b64decode(
                                item_copy["imagen_b64"])
                        except:
                            pass

                    # Procesar JSON de consumo si existe
                    consumo = item_copy.get('consumo', {})
                    if consumo and isinstance(consumo, dict):
                        for consumo_item in consumo.get('items', []):
                            consumo_data.append({
                                'folio_pisa': item_copy.get('folio_pisa'),
                                'telefono_asignado': item_copy.get('telefono_asignado'),
                                'material': consumo_item.get('descripcion'),
                                'tipo_material': consumo_item.get('tipo'),
                                'cantidad': consumo_item.get('cantidad'),
                                'fecha_cuadre': item_copy.get('fecha_cuadre')
                            })

                    # Limpiar columnas que no van al Excel
                    item_copy.pop('consumo', None)
                    item_copy.pop('imagen_b64', None)
                    expanded_data.append(item_copy)

                dataframes[tabla] = pd.DataFrame(expanded_data)

            # Escribir el archivo Excel
            with pd.ExcelWriter(self.excel_path, engine='openpyxl') as writer:
                for tabla, df in dataframes.items():
                    if not df.empty:
                        df.to_excel(writer, index=False, sheet_name=tabla[:31])

                if consumo_data:
                    df_consumo = pd.DataFrame(consumo_data)
                    df_consumo.to_excel(writer, index=False,
                                        sheet_name="Consumo")

            # Crear el ZIP de imágenes
            if imagenes_zip:
                zip_path = f"{os.path.splitext(self.excel_path)[0]}_IMAGENES.zip"
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for img_name, img_data in imagenes_zip.items():
                        zipf.writestr(img_name, img_data)

            self.finished.emit(True, self.excel_path)
        except Exception as e:
            self.error.emit(str(e))
