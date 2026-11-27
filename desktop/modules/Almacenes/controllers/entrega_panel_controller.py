import os
import subprocess
import tempfile
import base64

from PyQt6.QtWidgets import (QMessageBox, QPushButton, QLineEdit, QComboBox, QTableWidgetItem,
                             QLabel, QDialog, QVBoxLayout, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon
from datetime import datetime

from .base_panel_controller import BasePanelController
from .entrega_report_thread import ReportGenerationThread
from Documents.documentación.latex_report_generator import escape_latex
from TableManager import TableManager


class EntregaPanelController(BasePanelController):
    def __init__(self, panel_widget, main_controller):
        super().__init__(panel_widget, main_controller)

        # Inicialización de widgets
        self.str_tecnico = self.panel.findChild(
            QComboBox, "entrega_str_tecnico")
        self.ln_serie = self.panel.findChild(QLineEdit, "entrega_ln_serie")
        self.ln_cantidad = self.panel.findChild(
            QLineEdit, "entrega_ln_cantidad")
        self.btn_add = self.panel.findChild(
            QPushButton, "entrega_btn_agregar_item")
        self.btn_eliminar = self.panel.findChild(
            QPushButton, "entrega_btn_eliminar")
        self.btn_guardar = self.panel.findChild(
            QPushButton, "entrega_btn_guardar")
        self.btn_imprimir = self.panel.findChild(
            QPushButton, "entrega_btn_imprimir")

        self.tabla = self.main.almacen.tablaalmacen

        # Lista en memoria para persistir los items
        self.items_pendientes = []

        # Conexiones de botones
        if self.btn_add:
            self.btn_add.clicked.connect(self._agregar_item)
        if self.btn_eliminar:
            self.btn_eliminar.clicked.connect(self._eliminar_item)
        if self.btn_guardar:
            self.btn_guardar.clicked.connect(self._guardar_entrega)
        if self.btn_imprimir:
            self.btn_imprimir.clicked.connect(self._abrir_historial_reportes)

        self.configurar_tabla()
        self._sincronizar_tecnicos()

        # Sincronizar técnicos al cambiar área o cope
        self.main.almacen.str_area.currentIndexChanged.connect(
            self._sincronizar_tecnicos)
        self.main.almacen.str_cope.currentIndexChanged.connect(
            self._sincronizar_tecnicos)

    def configurar_tabla(self):
        """Inicializa la tabla con los encabezados de Asignacion_PO."""
        TableManager.populate_table(self.tabla, [], "Asignacion_PO")
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setWordWrap(True)
        self.tabla.setStyleSheet("""
            QTableWidget {
                font: 10pt "MS Shell Dlg 2";
                color: rgb(1, 59, 61);
                background-color: white;
                gridline-color: #d0d0d0;
                border: 2px solid #cccccc;
                border-radius: 8px;
            }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #e0e0e0; }
            QTableWidget::item:selected { background-color: rgb(1, 59, 61); color: white; }
            QHeaderView::section { background-color: rgb(1, 59, 61); color: white; font-weight: bold; padding: 8px; border: none; font-size: 11pt; }
        """)
        self._redibujar_items()

    def _sincronizar_tecnicos(self):
        area_id = self.main.almacen.str_area.currentData()
        cope = self.main.almacen.str_cope.currentText()

        if not self.str_tecnico:
            return

        self.str_tecnico.clear()
        if not area_id or cope == "Seleccionar":
            self.str_tecnico.addItem("Seleccione Área y COPE primero")
            return

        self.str_tecnico.addItem("Cargando técnicos...")
        self.main._run_api_task(
            method="GET", endpoint=f"/personal/?area_id={area_id}&cope={cope}",
            callback_success=self._on_tecnicos_cargados,
            callback_error=lambda e: self.str_tecnico.addItem(
                "Error al cargar")
        )

    def _on_tecnicos_cargados(self, tecnicos):
        self.str_tecnico.clear()
        self.str_tecnico.addItem("Seleccionar", None)
        for t in tecnicos:
            nombre = f"{t.get('nombre', '')} {t.get('apellido_paterno', '')} {t.get('apellido_materno', '')}".strip(
            )
            self.str_tecnico.addItem(nombre, t.get("id"))

    def _agregar_item(self):
        serie = self.ln_serie.text().strip()
        try:
            cantidad = int(self.ln_cantidad.text().strip())
        except ValueError:
            QMessageBox.warning(self.main.almacen, "Error",
                                "Cantidad inválida")
            return

        if not serie:
            return

        self.btn_add.setEnabled(False)
        self.btn_add.setText(" Buscando...")

        area = self.main.almacen.str_area.currentText()
        cope = self.main.almacen.str_cope.currentText()

        self.main._run_api_task(
            method="GET", endpoint=f"/almacen/buscar_global?area={area}&cope={cope}&numero_serie={serie}",
            callback_success=lambda data: self._on_item_encontrado(
                data, serie, cantidad),
            callback_error=lambda e: self._on_error_busqueda(e)
        )

    def _on_item_encontrado(self, result, serie, cantidad):
        self.btn_add.setEnabled(True)
        self.btn_add.setText(" Agregar a la lista")

        if not result or "tipo" not in result:
            QMessageBox.warning(self.main.almacen, "No encontrado",
                                f"El equipo {serie} no está disponible.")
            return

        item_data = result["data"]
        tipo = result["tipo"]

        # Verificar duplicados
        for item in self.items_pendientes:
            if item["numero_serie"] == serie:
                QMessageBox.warning(self.main.almacen, "Aviso",
                                    "Este número de serie ya está en la lista.")
                return

        nuevo_item = {
            "numero_serie": serie,
            "cantidad_almacen": str(item_data.get("cantidad", 0)),
            "unidad": item_data.get("unidad", "Pieza"),
            "modelo_desc": item_data.get("descripcion", ""),
            "tipo": tipo,
            "imagen": item_data.get("imagen"),
            "cantidad_entregar": cantidad
        }
        self.items_pendientes.append(nuevo_item)

        self._redibujar_items()
        self.ln_serie.clear()
        self.ln_cantidad.setText("1")

    def _redibujar_items(self):
        """Dibuja los items guardados en la tabla, con las celdas bloqueadas."""
        self.tabla.setRowCount(0)

        for row, item in enumerate(self.items_pendientes):
            self.tabla.insertRow(row)

            # Col 0: Serie
            it_serie = QTableWidgetItem(item["numero_serie"])
            it_serie.setFlags(Qt.ItemFlag.ItemIsEnabled |
                              Qt.ItemFlag.ItemIsSelectable)
            self.tabla.setItem(row, 0, it_serie)

            # Col 1: Cantidad Almacén
            it_cant = QTableWidgetItem(item["cantidad_almacen"])
            it_cant.setFlags(Qt.ItemFlag.ItemIsEnabled |
                             Qt.ItemFlag.ItemIsSelectable)
            self.tabla.setItem(row, 1, it_cant)

            # Col 2: Unidad
            it_uni = QTableWidgetItem(item["unidad"])
            it_uni.setFlags(Qt.ItemFlag.ItemIsEnabled |
                            Qt.ItemFlag.ItemIsSelectable)
            self.tabla.setItem(row, 2, it_uni)

            # Col 3: Modelo/Desc
            it_mod = QTableWidgetItem(item["modelo_desc"])
            it_mod.setFlags(Qt.ItemFlag.ItemIsEnabled |
                            Qt.ItemFlag.ItemIsSelectable)
            self.tabla.setItem(row, 3, it_mod)

            # Col 4: Imagen
            if item["imagen"] == "Si":
                btn_img = QPushButton()
                btn_img.setIcon(QIcon("assets/icons/eye.svg"))
                btn_img.setIconSize(QSize(20, 15))
                btn_img.setFlat(True)
                btn_img.setCursor(Qt.CursorShape.PointingHandCursor)
                btn_img.clicked.connect(
                    lambda checked, s=item["numero_serie"], t=item["tipo"]: self._ver_imagen(s, t))
                self.tabla.setCellWidget(row, 4, btn_img)
            else:
                it_img = QTableWidgetItem("Sin imagen")
                it_img.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.tabla.setItem(row, 4, it_img)

            # Col 5: Tipo
            it_tipo = QTableWidgetItem(item["tipo"])
            it_tipo.setFlags(Qt.ItemFlag.ItemIsEnabled |
                             Qt.ItemFlag.ItemIsSelectable)
            self.tabla.setItem(row, 5, it_tipo)

            # Col 6: Fecha
            it_fecha = QTableWidgetItem(datetime.now().strftime("%d/%m/%Y"))
            it_fecha.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.tabla.setItem(row, 6, it_fecha)

            # Col 7: Cantidad a Entregar (Editable)
            it_cant_ent = QTableWidgetItem(str(item["cantidad_entregar"]))
            it_cant_ent.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable)
            it_cant_ent.setBackground(Qt.GlobalColor.white)
            self.tabla.setItem(row, 7, it_cant_ent)

    def _ver_imagen(self, serie, tipo):
        self.main.mostrar_imagen(serie, tipo)

    def _on_error_busqueda(self, error):
        self.btn_add.setEnabled(True)
        self.btn_add.setText(" Agregar a la lista")
        QMessageBox.warning(self.main.almacen, "No encontrado", str(error))

    def _eliminar_item(self):
        row = self.tabla.currentRow()
        if row >= 0:
            del self.items_pendientes[row]
            self._redibujar_items()

    # =========================================================================
    # MÉTODOS PARA GUARDAR Y GENERAR PDF
    # =========================================================================

    def _guardar_entrega(self):
        if not self.items_pendientes:
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "No hay equipos en la lista")
            return

        tecnico = self.str_tecnico.currentText()
        tecnico_id = self.str_tecnico.currentData()

        if not tecnico_id:
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "Seleccione un técnico válido")
            return

        # Sincronizar los cambios que el usuario haya hecho en la columna editable
        for row, item in enumerate(self.items_pendientes):
            try:
                item["cantidad_entregar"] = int(self.tabla.item(row, 7).text())
            except (ValueError, AttributeError):
                QMessageBox.warning(self.main.almacen, "Error",
                                    f"Cantidad inválida en la fila {row+1}")
                return

        items = []
        for item in self.items_pendientes:
            items.append({
                "numero_serie": item["numero_serie"],
                "modelo_desc": item["modelo_desc"],
                "tipo": item["tipo"],
                "unidad": item["unidad"],
                "cantidad": item["cantidad_entregar"]
            })

        payload = {
            "area": self.main.almacen.str_area.currentText(),
            "cope": self.main.almacen.str_cope.currentText(),
            "exp_tecnico": tecnico,
            "items": items
        }

        self.btn_guardar.setEnabled(False)
        self.btn_guardar.setText(" Procesando...")

        self.main._run_api_task(
            method="POST", endpoint="/almacen/entrega", data=payload,
            callback_success=self._on_entrega_guardada,
            callback_error=lambda e: self._on_error_guardado(e)
        )

    def _on_entrega_guardada(self, response):
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText(" Guardar Entrega")

        QMessageBox.information(
            self.main.almacen, "Éxito", "Entrega registrada. Preparando reporte...")
        self._generar_pdf(response["id_entrega"])

        # Limpiar la tabla y la lista
        self.items_pendientes.clear()
        self.configurar_tabla()

    def _on_error_guardado(self, error):
        self.btn_guardar.setEnabled(True)
        self.btn_guardar.setText(" Guardar Entrega")
        QMessageBox.critical(self.main.almacen, "Error al guardar", error)

    def _generar_pdf(self, id_entrega):
        """
        Prepara los datos y lanza el hilo de LaTeX.
        """

        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.setText(" Generando PDF...")

        # Armar los datos separando por tipo
        filas_ont = []
        filas_modem = []
        filas_misc = []

        for item in self.items_pendientes:
            serie = escape_latex(item["numero_serie"])
            cant = escape_latex(str(item["cantidad_entregar"]))
            unidad = escape_latex(item["unidad"])
            modelo = escape_latex(item["modelo_desc"])
            fila_str = f"{serie} & {cant} & {unidad} & {modelo} \\\\"

            # Separar según el tipo
            if item["tipo"] == "ONT":
                filas_ont.append(fila_str)
            elif item["tipo"] == "MODEM":
                filas_modem.append(fila_str)
            else:
                filas_misc.append(fila_str)

        nombre_usuario = self.main.usuario_actual.get("name") or self.main.usuario_actual.get(
            "username") or self.main.usuario_actual.get("nombre", "Sistema")
        nombre_tecnico = self.str_tecnico.currentText()

        data_reporte = {
            "id_entrega": id_entrega,
            "area": escape_latex(self.main.almacen.str_area.currentText()),
            "cope": escape_latex(self.main.almacen.str_cope.currentText()),
            "fecha": escape_latex(datetime.now().strftime("%d/%m/%Y")),
            "exptec": escape_latex(self.str_tecnico.currentText()),
            "usuario": escape_latex(str(nombre_usuario)),
            "tecnico": escape_latex(nombre_tecnico),
            "administrador": escape_latex(str(nombre_usuario)),
            "miscelaneos": filas_misc,  # <-- Separados
            "ont": filas_ont,            # <-- Separados
            "modem": filas_modem         # <-- Separados
        }

        self.thread = ReportGenerationThread(
            data_reporte,
            "Documents/documentación/REntregaMateriales.tex",
            "Entregas"
        )
        self.thread.finished.connect(self._on_pdf_generado)
        self.thread.error.connect(self._on_pdf_error)
        self.thread.start()

    def _on_pdf_generado(self, id_entrega, pdf_path):
        self.btn_imprimir.setEnabled(True)
        self.btn_imprimir.setText(" Imprimir Reporte")

        if not os.path.exists(pdf_path):
            QMessageBox.warning(self.main.almacen, "Error",
                                "El PDF no se generó correctamente.")
            return

        # 1. Leer el PDF y codificarlo en Base64
        try:
            with open(pdf_path, "rb") as f:
                pdf_b64 = base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            QMessageBox.critical(self.main.almacen, "Error",
                                 f"No se pudo leer el PDF: {e}")
            return

        # 2. Subirlo al servidor (esto actualiza la BD)
        payload = {"pdf_b64": pdf_b64}

        def subida_exitosa(res):
            # 3. Si se subió bien, lo abrimos localmente
            try:
                os.startfile(pdf_path) if os.name == 'nt' else subprocess.run(
                    ['xdg-open', pdf_path])
            except Exception:
                pass

        self.main._run_api_task(
            method="POST",
            endpoint=f"/almacen/entregas/{id_entrega}/guardar_reporte",
            data=payload,
            callback_success=lambda res: subida_exitosa(res),
            callback_error=lambda e: QMessageBox.warning(
                self.main.almacen, "Aviso", f"PDF generado localmente, pero no se subió al servidor: {e}")
        )

    def _on_pdf_error(self, error):
        self.btn_imprimir.setEnabled(True)
        self.btn_imprimir.setText(" Imprimir Reporte")
        QMessageBox.critical(self.main.almacen, "Error de Reporte", error)

    def _abrir_historial_reportes(self):
        """Consulta los reportes anteriores del técnico seleccionado."""
        tecnico = self.str_tecnico.currentText()

        if not tecnico or tecnico == "Seleccionar":
            QMessageBox.warning(self.main.almacen, "Aviso",
                                "Seleccione un técnico para ver su historial.")
            return

        self.btn_imprimir.setEnabled(False)
        self.btn_imprimir.setText(" Cargando...")

        self.main._run_api_task(
            method="GET",
            endpoint=f"/almacen/entregas?tecnico={tecnico}",
            callback_success=self._mostrar_dialogo_historial,
            callback_error=self._on_error_historial
        )

    def _on_error_historial(self, error):
        self.btn_imprimir.setEnabled(True)
        self.btn_imprimir.setText(" Imprimir Reporte")
        QMessageBox.critical(self.main.almacen, "Error",
                             f"No se pudo cargar el historial: {error}")

    def _mostrar_dialogo_historial(self, entregas):
        """Crea y muestra la ventana modal con la lista de reportes."""
        self.btn_imprimir.setEnabled(True)
        self.btn_imprimir.setText(" Imprimir Reporte")

        if not entregas:
            QMessageBox.information(
                self.main.almacen, "Sin registros", "No hay entregas registradas para este técnico.")
            return

        # Crear la ventana modal
        dialog = QDialog(self.main.almacen)
        dialog.setWindowTitle(
            f"Historial de Entregas - {self.str_tecnico.currentText()}")
        dialog.resize(550, 400)

        layout = QVBoxLayout(dialog)

        lbl_info = QLabel("Seleccione un reporte de la lista para abrirlo:")
        layout.addWidget(lbl_info)

        lista = QListWidget()
        for e in entregas:
            # Formatear la fecha
            fecha_str = "Fecha desconocida"
            if e.get("Fecha de Entrega"):
                try:
                    fecha_str = e["Fecha de Entrega"].strftime('%d/%m/%Y %H:%M') if hasattr(
                        e["Fecha de Entrega"], 'strftime') else str(e["Fecha de Entrega"])
                except:
                    fecha_str = str(e["Fecha de Entrega"])

            texto = f"📅 {fecha_str} | Área: {e.get('area')} | Folio: {e.get('id_entrega')[:8]}"
            item = QListWidgetItem(texto)

            # AQUÍ EL CAMBIO: Guardamos el ID de la entrega, no la ruta del PDF
            item.setData(Qt.ItemDataRole.UserRole, e.get("id_entrega"))
            lista.addItem(item)

        layout.addWidget(lista)

        # Botones de la ventana modal
        btn_layout = QHBoxLayout()

        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.reject)

        btn_abrir = QPushButton(" Abrir PDF")
        btn_abrir.setIcon(QIcon("assets/icons/imprimir.svg"))
        btn_abrir.setStyleSheet(
            "background-color: #28a745; color: white; padding: 5px 15px; border-radius: 5px;")
        # Doble clic o clic en abrir
        btn_abrir.clicked.connect(
            lambda: self._abrir_pdf_historial(lista, dialog))
        lista.itemDoubleClicked.connect(
            lambda: self._abrir_pdf_historial(lista, dialog))

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        btn_layout.addWidget(btn_abrir)

        layout.addLayout(btn_layout)

        # Aplicar un estilo básico al diálogo
        dialog.setStyleSheet("""
            QDialog { background-color: rgb(1, 59, 61); }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QListWidget { 
                background-color: white; 
                border-radius: 5px; 
                padding: 5px;
                font: 10pt "MS Shell Dlg 2";
            }
            QListWidget::item { padding: 8px; border-bottom: 1px solid #ddd; }
            QListWidget::item:selected { background-color: rgb(1, 79, 81); color: white; }
            QPushButton#btn_cerrar { background-color: rgb(220, 53, 69); color: white; padding: 5px 15px; border-radius: 5px; }
        """)

        dialog.exec()

    def _abrir_pdf_historial(self, lista, dialog):
        """Solicita el PDF a la API, lo guarda temporalmente y lo abre."""
        item = lista.currentItem()
        if not item:
            QMessageBox.warning(
                dialog, "Aviso", "Por favor, seleccione un reporte de la lista.")
            return

        id_entrega = item.data(Qt.ItemDataRole.UserRole)
        if not id_entrega:
            QMessageBox.warning(
                dialog, "Error", "No se encontró el ID de esta entrega.")
            return

        # Deshabilitar botón temporalmente mientras descarga
        dialog.setEnabled(False)

        def on_pdf_descargado(pdf_bytes):
            dialog.setEnabled(True)
            if not pdf_bytes:
                QMessageBox.critical(
                    dialog, "Error", "El servidor no devolvió un archivo válido.")
                return

            # Guardar en la carpeta temporal del sistema (funciona en Windows, Mac y Linux)
            ruta_temp = os.path.join(
                tempfile.gettempdir(), f"reporte_{id_entrega}.pdf")

            try:
                with open(ruta_temp, "wb") as f:
                    f.write(pdf_bytes)

                # Abrir el archivo
                if os.name == 'nt':  # Windows
                    os.startfile(ruta_temp)
                else:  # Linux / Mac
                    subprocess.run(['xdg-open', ruta_temp], check=True)

                dialog.accept()  # Cerrar la ventana modal tras abrir el PDF
            except Exception as e:
                QMessageBox.critical(
                    dialog, "Error", f"No se pudo abrir el archivo descargado: {str(e)}")

        def on_error_descarga(error_msg):
            dialog.setEnabled(True)
            QMessageBox.critical(dialog, "Error de descarga",
                                 f"No se pudo descargar el PDF:\n{error_msg}")

        # Llamada a la API pidiendo el archivo binario
        self.main._run_api_task(
            method="GET",
            endpoint=f"/almacen/entregas/{id_entrega}/descargar_reporte",
            binary=True,  # IMPORTANTE: Indica al ApiWorker que reciba bytes
            data=None,
            callback_success=on_pdf_descargado,
            callback_error=on_error_descarga
        )
