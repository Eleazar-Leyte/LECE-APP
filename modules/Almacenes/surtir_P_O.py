from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6 import uic, QtWidgets, QtCore, QtGui
from psycopg2 import Binary
from datetime import datetime
import os
import uuid
import subprocess

from DatabaseManager import DatabaseManager
from TableManager import TableManager
from Documents.documentación.latex_report_generator import escape_latex


class ReportGenerationThread(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, data, template_path, output_dir):
        super().__init__()
        self.data = data
        self.template_path = template_path
        self.output_dir = output_dir

    def run(self):
        try:
            from Documents.documentación.latex_report_generator import generar_reporte_entrega_latex, limpiar_archivos_temporales
            success, log = generar_reporte_entrega_latex(
                self.data, self.template_path, self.output_dir
            )

            if not success:
                self.error.emit(f"Error LaTeX:\n{log}")
                return

            limpiar_archivos_temporales(self.output_dir)

            pdf_path = os.path.join(
                self.output_dir, f"reporte_{self.data['id_entrega']}.pdf")
            self.finished.emit(self.data['id_entrega'], pdf_path)

        except Exception as e:
            self.error.emit(f"Error inesperado:\n{str(e)}")


class Surtir_P_O():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        # Cargamos la interfaz de usuario mover a almacen
        self.surtir_p_o = uic.loadUi("modules/Almacenes/Entrega.ui")
        self.surtir_p_o.show()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")

        self.filas_recien_creadas = set()
        self.surtir_p_o.multi_tablas.setCurrentIndex(0)

        self.iniciar_tablas()
        self.cargar_botones()
        self.cargar_areas()

    def cargar_botones(self):
        # Conexiones únicas de señales
        self.surtir_p_o.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
        self.surtir_p_o.str_cope.currentIndexChanged.connect(
            self.actualizar_exptec)
        self.surtir_p_o.btn_agregar.clicked.connect(self.agregar_fila_po)
        self.surtir_p_o.tabla_a_p_o.itemChanged.connect(
            self.buscar_codigo_barras_po)
        self.surtir_p_o.tabla_a_p_o.itemChanged.connect(
            self.validar_cantidad_po)
        self.surtir_p_o.btn_eliminar.clicked.connect(self.eliminar_fila_po)
        self.surtir_p_o.btn_enviar.clicked.connect(self.procesar_entrega)
        self.surtir_p_o.btn_imprimir.clicked.connect(self.imprimir_reporte)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.surtir_p_o.str_area.clear()
        try:
            if self.usuario_actual["rol"] == "Directivo":
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(query)
            else:
                query = query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(
                    query, (self.usuario_actual['area'],)
                )

            if resultados:
                for resultado in resultados:
                    self.surtir_p_o.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.surtir_p_o, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.surtir_p_o, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.surtir_p_o.str_area.currentText().strip()
        self.surtir_p_o.str_cope.clear()

        if not area_seleccionada:
            QMessageBox.warning(
                self.surtir_p_o, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.surtir_p_o,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.surtir_p_o.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.surtir_p_o,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.surtir_p_o, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def actualizar_exptec(self):
        """
        Cargar los técnicos en el ComboBox str_expetec según el área y COPE seleccionados.
        """
        try:
            self.surtir_p_o.str_exptec.clear()

            # Obtenemos area y cope seleccionados
            area_seleccionada = self.surtir_p_o.str_area.currentText().strip()
            cope_seleccionado = self.surtir_p_o.str_cope.currentText().strip()

            if not area_seleccionada or not cope_seleccionado:
                QMessageBox.warning(
                    self.surtir_p_o,
                    "Datos incompletos",
                    "Por favor, seleccione un área y un Copé."
                )
                return

            # Obtener el id_area correspondiente al nombre del área
            query_id_area = """
            SELECT id FROM areas
            WHERE "Nombre del Área" = %s
            """
            resultado_id_area = self.db_personal.execute_query(
                query_id_area, (area_seleccionada,))

            if not resultado_id_area:
                QMessageBox.critical(
                    self.surtir_p_o,
                    "Error",
                    f"No se encontró el ID para el área: {area_seleccionada}."
                )
                return
            id_area = resultado_id_area[0]["id"]

            # Consultar los técnicos disponibles para el área y Copé seleccionados
            query_tecnicos = """
            SELECT id,
            "Apellido Paterno",
            "Apellido Materno",
            "Nombre (s)"
            FROM personal_o
            WHERE "id_area" = %s AND "Cope" = %s
            """
            resultados = self.db_personal.execute_query(query_tecnicos,
                                                        (id_area, cope_seleccionado))
            if resultados:
                for tecnico in resultados:
                    nombre_completo = (
                        f"{tecnico['Nombre (s)']} "
                        f"{tecnico['Apellido Paterno']} "
                        f"{tecnico['Apellido Materno']}"
                    )
                    self.surtir_p_o.str_exptec.addItem(
                        nombre_completo, userData=tecnico["id"])
            else:
                QMessageBox.information(
                    self.surtir_p_o,
                    "Sin técnicos",
                    "No se encontraron técnicos disponibles para esta área y Copé."
                )
        except Exception as e:
            QMessageBox.critical(
                self.surtir_p_o, "Error", f"Error al cargar los técnicos: {e}"
            )

    def iniciar_tablas(self):
        """
        Configurar las columnas deseadas en la tabla 'tabla_a_p_o'.
        """
        TableManager.populate_table(
            self.surtir_p_o.tabla_a_p_o,
            [],
            "Asignacion_PO"
        )

    def agregar_fila_po(self):
        """
        Agrega una nueva fila en la tabla 'tabla_a_p_o'.
        """
        self.surtir_p_o.tabla_a_p_o.blockSignals(True)
        try:
            filas_totales = self.surtir_p_o.tabla_a_p_o.rowCount()
            if filas_totales == 0:
                self.surtir_p_o.str_area.setEnabled(False)
                self.surtir_p_o.str_cope.setEnabled(False)
                self.surtir_p_o.str_exptec.setEnabled(False)

            # Eliminar conexiones redundantes de itemChanged
            self.surtir_p_o.tabla_a_p_o.blockSignals(True)
            self.surtir_p_o.tabla_a_p_o.insertRow(filas_totales)

            for col in range(self.surtir_p_o.tabla_a_p_o.columnCount()):
                item = QTableWidgetItem()
                if col in [0, 7]:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                  Qt.ItemFlag.ItemIsEditable)
                else:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)

                self.surtir_p_o.tabla_a_p_o.setItem(filas_totales, col, item)

                self.filas_recien_creadas.add(filas_totales)

        finally:
            self.surtir_p_o.tabla_a_p_o.blockSignals(False)

    def eliminar_fila_po(self):
        """Elimina la fila seleccionada de la tabla."""
        fila = self.surtir_p_o.tabla_a_p_o.currentRow()
        if fila == -1:
            QMessageBox.warning(self.surtir_p_o, "Error",
                                "Seleccione una fila")
            return

        confirmacion = QMessageBox.question(
            self.surtir_p_o,
            "Confirmar",
            "¿Eliminar esta fila?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            self.surtir_p_o.tabla_a_p_o.removeRow(fila)

    def buscar_codigo_barras_po(self, item):
        """
        Busca equipos/misceláneos por número de serie y carga datos en la tabla
        """
        if item.column() != 0 or not item.text():
            return
        # Bloquear señales antes de modificar la tabla
        self.surtir_p_o.tabla_a_p_o.blockSignals(True)
        try:

            numero_serie = item.text().strip()
            if self.verificar_duplicados(numero_serie, item.row()):
                QMessageBox.warning(self.surtir_p_o, "Error",
                                    f"El número de serie {numero_serie} ya está registrado en otra fila.")
                self.limpiar_fila_po(item.row())
                return

            area = self.surtir_p_o.str_area.currentText().strip()
            cope = self.surtir_p_o.str_cope.currentText().strip()

            # Consulta unificada que incluye misceláneos
            query = """
                SELECT
                    "Numero de Serie",
                    SUM(cantidad) AS total_cantidad,
                    unidad,
                    modelo,
                    tipo,
                    imagen,
                    MAX("Fecha de Registro") AS "Fecha de Registro"
                FROM (
                    SELECT
                        "Numero de Serie", cantidad, unidad, descripcion AS modelo,
                        'Misceláneo' AS tipo, NULL AS imagen, "Fecha de Registro"
                    FROM almacen
                    WHERE area = %s AND cope = %s
                    UNION ALL
                    SELECT
                        "Numero de Serie", cantidad, unidad, modelo,
                        'ONT' AS tipo, imagen, "Fecha de Registro"
                    FROM ont
                    WHERE area = %s AND "Centro de Trabajo" = %s
                    UNION ALL
                    SELECT
                        "Numero de Serie", cantidad, unidad, modelo,
                        'MODEM' AS tipo, imagen, "Fecha de Registro"
                    FROM modem
                    WHERE area = %s AND "Centro de Trabajo" = %s
                ) AS datos
                WHERE "Numero de Serie" = %s
                GROUP BY "Numero de Serie", unidad, modelo, tipo, imagen
            """

            params = [
                area, cope,  # Almacén (Misceláneo)
                area, cope,  # ONT
                area, cope,  # MODEM
                numero_serie
            ]

            resultados = self.db_almacen.execute_query(query, params)

            if resultados:
                datos = resultados[0]
                if int(datos["total_cantidad"]) <= 0:
                    QMessageBox.warning(self.surtir_p_o, "Error",
                                        "No hay stock disponible")
                    self.limpiar_fila_po(item.row())
                    return

                # Llenar la columna 1 con el stock disponible
                item_stock = QTableWidgetItem(str(datos["total_cantidad"]))
                item_stock.setFlags(Qt.ItemFlag.ItemIsEnabled)
                self.surtir_p_o.tabla_a_p_o.setItem(item.row(), 1, item_stock)
                self.actualizar_fila_po(item.row(), datos)

                # Eliminar fila de recién creadas si ya se encontró el equipo
                if item.row() in self.filas_recien_creadas:
                    self.filas_recien_creadas.remove(item.row())
            else:
                QMessageBox.warning(self.surtir_p_o, "Error",
                                    "Equipo no encontrado")
                self.limpiar_fila_po(item.row())

        except Exception as e:
            print(f"Error en búsqueda: {str(e)}")
        finally:
            self.surtir_p_o.tabla_a_p_o.blockSignals(False)

    def verificar_duplicados(self, numero_serie, fila_actual):
        for row in range(self.surtir_p_o.tabla_a_p_o.rowCount()):
            if row == fila_actual:  # Excluir la fila actual
                continue
            item = self.surtir_p_o.tabla_a_p_o.item(row, 0)
            if item and item.text() == numero_serie:
                return True
        return False

    def actualizar_fila_po(self, row, datos):
        """
        Actualiza la fila con datos obtenidos de la consulta
        """
        try:
            columnas = ["total_cantidad", "unidad", "modelo", "imagen",
                        "tipo", "Fecha de Registro"]

            for col_index, col_name in enumerate(columnas, start=1):
                # Obtener valor mapeado o directo
                valor = (datos.get(col_name, ""))
                if col_name == "imagen":
                    self.surtir_p_o.tabla_a_p_o.removeCellWidget(row, 4)
                    self.surtir_p_o.tabla_a_p_o.removeCellWidget(row, 4)
                    # Guardar los bytes de la imagen en el item (Rol UserRole)
                    item_imagen = QTableWidgetItem()
                    # Almacenar bytes aquí
                    item_imagen.setData(Qt.ItemDataRole.UserRole, valor)
                    self.surtir_p_o.tabla_a_p_o.setItem(row, 4, item_imagen)
                    if valor:
                        pixmap = QtGui.QPixmap()
                        pixmap.loadFromData(valor)
                        label = QtWidgets.QLabel()
                        label.setPixmap(pixmap.scaled(
                            80, 80, Qt.AspectRatioMode.KeepAspectRatio))
                        self.surtir_p_o.tabla_a_p_o.setCellWidget(
                            row, 4, label)
                    else:
                        self.surtir_p_o.tabla_a_p_o.setItem(
                            row, col_index, QTableWidgetItem("Sin imagen"))
                else:
                    item = QTableWidgetItem(str(valor))
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    self.surtir_p_o.tabla_a_p_o.setItem(row, col_index, item)

            # Agregar fecha de registro (Columna 6)
            fecha = datos.get("Fecha de Registro", "")
            fecha_item = QTableWidgetItem(str(fecha))
            fecha_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.surtir_p_o.tabla_a_p_o.setItem(row, 6, fecha_item)
        except Exception as e:
            print(f"Error al actualizar fila: {str(e)}")

    def validar_cantidad_po(self, item):
        """
        Valida la cantidad ingresada contra el stock disponible (almacenado internamente).
        """
        if item.column() != 7 or item.row() in self.filas_recien_creadas:
            return

        fila = item.row()
        try:
            cantidad_solicitada = item.text().strip()
            if not cantidad_solicitada.isdigit() or int(cantidad_solicitada) <= 0:
                QMessageBox.warning(self.surtir_p_o, "Advertencia",
                                    "Por favor, Ingrese una cantidad válida.")
                self.surtir_p_o.tabla_a_p_o.blockSignals(True)
                item.setText("")
                self.surtir_p_o.tabla_a_p_o.blockSignals(False)
                return
            cantidad_solicitada = int(cantidad_solicitada)

            # Obtener la cantidad en Stock
            item_stock = self.surtir_p_o.tabla_a_p_o.item(fila, 1)
            if not item_stock:
                QMessageBox.warning(self.surtir_p_o, "Error",
                                    "No hay stock disponible")
                self.limpiar_fila_po(fila)
                return
            # Convertir texto a entero
            cantidad_stock = int(item_stock.text())

            if cantidad_solicitada > cantidad_stock:
                QMessageBox.warning(self.surtir_p_o, "Advertencia",
                                    f"La cantidad solicitada excede el stock disponible ({cantidad_stock}).")
                self.surtir_p_o.tabla_a_p_o.blockSignals(True)
                # Ajustar a la cantidad máxima disponible
                item.setText(str(cantidad_stock))
                self.surtir_p_o.tabla_a_p_o.blockSignals(False)
                return

        except ValueError:
            QMessageBox.warning(self.surtir_p_o, "Error",
                                "Ingrese un número válido.")
            item.setText("")

    def limpiar_fila_po(self, row):
        for col in range(self.surtir_p_o.tabla_a_p_o.columnCount()):
            self.surtir_p_o.tabla_a_p_o.setItem(
                row, col, QTableWidgetItem())

    def procesar_entrega(self):
        if not self.validar_surtido():
            return

        try:
            id_entrega = str(uuid.uuid4())
            area = self.surtir_p_o.str_area.currentText().strip()
            cope = self.surtir_p_o.str_cope.currentText().strip()
            id_tecnico = self.surtir_p_o.str_exptec.currentData()
            materiales = self.obtener_materiales_interfaz()

            # Generar filas separadas para cada tipo de material
            filas_ont = []
            filas_modem = []
            filas_misceláneos = []

            for m in materiales:
                print(f"Material: {m['numero_serie']}, Tipo: {m['tipo']}")
                fila = self.generar_fila_reporte_entrega(m)
                if m["tipo"] == "ONT":
                    filas_ont.append(fila)
                elif m["tipo"] == "MODEM":
                    filas_modem.append(fila)
                elif m["tipo"] == "Misceláneo":
                    filas_misceláneos.append(fila)

            # Generar reporte
            data_reporte = {
                "id_entrega": id_entrega,
                "area": escape_latex(area),
                "cope": escape_latex(cope),
                "fecha": escape_latex(datetime.now().strftime("%d/%m/%Y")),
                "exptec": escape_latex(self.surtir_p_o.str_exptec.currentText()),
                "usuario": escape_latex(self.usuario_actual["nombre"]),
                "tecnico": escape_latex(self.surtir_p_o.str_exptec.currentText()),
                "administrador": escape_latex(self.usuario_actual["nombre"]),
                "miscelaneos": filas_misceláneos,  # Lista de filas
                "ont": filas_ont,  # Lista de filas
                "modem": filas_modem  # Lista de filas
            }

            thread = ReportGenerationThread(
                data_reporte,
                "Documents/documentación/REntregaMateriales.tex",
                "Entregas"
            )
            thread.finished.connect(self.on_reporte_generado)
            thread.error.connect(self.on_reporte_error)
            thread.start()

            # Registrar en base de datos
            self.registrar_entrega(id_entrega, area, cope, id_tecnico)
            self.procesar_entrega_campo(
                area, cope, materiales, id_entrega, id_tecnico)

            QMessageBox.information(
                self.surtir_p_o, "Éxito", "Entrega registrada correctamente")
            self.limpiar_ui()

        except Exception as e:
            QMessageBox.critical(self.surtir_p_o, "Error",
                                 f"Error al procesar entrega: {str(e)}")

    def registrar_entrega(self, id_entrega, area, cope, id_tecnico):
        """Registra la entrega en la tabla 'entregas'"""
        query = """
            INSERT INTO entregas
            (id_entrega, area, cope, expediente_tecnico, "Fecha de Entrega")
            VALUES (%s, %s, %s, %s, NOW())
        """
        expediente_tecnico = self.surtir_p_o.str_exptec.currentText().strip()

        params = (id_entrega, area, cope, expediente_tecnico)

        self.db_almacen.execute_query(query, params, fetch=False)

    def validar_surtido(self):
        """Valida que los datos para el surtido sean correctos"""
        if self.surtir_p_o.tabla_a_p_o.rowCount() == 0:
            QMessageBox.warning(self.surtir_p_o, "Error",
                                "Agregue al menos un material a la entrega")
            return False

        if not self.surtir_p_o.str_exptec.currentText():
            QMessageBox.warning(self.surtir_p_o, "Error",
                                "Seleccione un técnico")
            return False

        for row in range(self.surtir_p_o.tabla_a_p_o.rowCount()):
            if not self.surtir_p_o.tabla_a_p_o.item(row, 7).text().isdigit():
                QMessageBox.warning(self.surtir_p_o, "Error",
                                    f"Cantidad inválida en fila {row+1}")
                return False

        return True

    def procesar_entrega_campo(self, area, cope, materiales, id_entrega, id_tecnico):
        try:
            expte_tecnico = self.surtir_p_o.str_exptec.currentText().strip()

            for material in materiales:
                # Obtener datos comunes
                tipo = material["tipo"].lower()
                imagen = material.get("imagen")
                params_common = (
                    material['numero_serie'],
                    material['cantidad'],
                    material['unidad'],
                    area,
                    cope,
                    expte_tecnico
                )
                # Determinar nombre de columna y valor
                if tipo in ["ONT", "MODEM"]:
                    columna = "modelo"
                    valor = material["modelo"]
                else:  # Misceláneo
                    columna = "descripcion"
                    valor = material["descripcion"]

                if material['tipo'] == 'ONT':
                    query = """
                        INSERT INTO "ONT en Campo" (
                            "Numero de Serie", cantidad, unidad, modelo, area,
                            "Centro de Trabajo", "Expediente Técnico", imagen,
                            "Fecha de Registro", "Fecha de Movimiento"
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    imagen = Binary(material['imagen']) if material.get(
                        'imagen') else None
                    params = (
                        material['numero_serie'],
                        material['cantidad'],
                        material['unidad'],
                        material['modelo'],
                        area,
                        cope,
                        expte_tecnico,
                        imagen,
                        material['fecha_registro']
                    )

                elif material['tipo'] == 'MODEM':
                    query = """
                            INSERT INTO modem_en_campo (
                                "Numero de Serie", cantidad, unidad, modelo, area,
                                "Centro de Trabajo", "Expediente Técnico", imagen,
                                "Fecha de Registro", "Fecha de Movimiento"
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                    # Asegurar que la imagen se maneje como Binary o None
                    imagen = Binary(material['imagen']) if material.get(
                        'imagen') else None
                    params = (
                        material['numero_serie'],
                        material['cantidad'],
                        material['unidad'],
                        material.get('modelo', ''),
                        area,
                        cope,
                        expte_tecnico,
                        imagen,
                        material['fecha_registro']
                    )

                else:  # Misceláneo
                    query = query = f"""
                        INSERT INTO miselaneo_en_campo (
                            "Numero de Serie", cantidad, unidad, {columna}, area,
                            "Centro de Trabajo", "Expediente Técnico", "Fecha de surtido"
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    params = (
                        material['numero_serie'],  # "Numero de Serie"
                        material['cantidad'],  # cantidad
                        material['unidad'],  # unidad
                        valor,  # descripción
                        area,
                        cope,
                        expte_tecnico
                    )

                # Ejecutar inserción
                self.db_almacen.execute_query(query, params, fetch=False)

                # Actualizar inventario origen
                self.actualizar_inventario_origen(
                    material['tipo'],
                    material['numero_serie'],
                    material['cantidad'],
                    area,
                    cope
                )

        except Exception as e:
            error_msg = f"""
            Error al procesar {material.get('numero_serie', 'material desconocido')}:
            {str(e)}
            Query: {query}
            Params: {params}
            """
            raise RuntimeError(error_msg)

    def actualizar_inventario_origen(self, tipo, numero_serie, cantidad, area, cope):
        tabla = "almacen" if tipo == "Misceláneo" else "ont" if tipo == "ONT" else "modem"
        columna = "cope" if tipo == "Misceláneo" else "\"Centro de Trabajo\""

        # Paso 1: Descontar la cantidad entregada
        query_update = f"""
            UPDATE {tabla}
            SET cantidad = cantidad - %s
            WHERE "Numero de Serie" = %s
            AND area = %s
            AND {columna} = %s
        """
        self.db_almacen.execute_query(
            query_update, [cantidad, numero_serie, area, cope], fetch=False)

        # Paso 2: Eliminar registros con cantidad = 0
        query_delete = f"""
            DELETE FROM {tabla}
            WHERE "Numero de Serie" = %s
            AND area = %s
            AND {columna} = %s
            AND cantidad <= 0
        """
        self.db_almacen.execute_query(
            query_delete, [numero_serie, area, cope], fetch=False)

    def obtener_materiales_interfaz(self):
        materiales = []
        for row in range(self.surtir_p_o.tabla_a_p_o.rowCount()):
            try:
                # Obtener datos de la fila
                numero_serie = self.surtir_p_o.tabla_a_p_o.item(
                    row, 0).text().strip()
                cantidad = int(self.surtir_p_o.tabla_a_p_o.item(row, 7).text())
                unidad = self.surtir_p_o.tabla_a_p_o.item(
                    row, 2).text().strip()
                modelo_desc = self.surtir_p_o.tabla_a_p_o.item(
                    row, 3).text().strip()  # Columna 3 = Modelo o descripción
                tipo = self.surtir_p_o.tabla_a_p_o.item(row, 5).text().strip()
                fecha_registro = self.surtir_p_o.tabla_a_p_o.item(
                    row, 6).text().strip()

                # Obtener imagen (si existe)
                imagen = None
                imagen_item = self.surtir_p_o.tabla_a_p_o.item(
                    row, 4)  # Columna oculta 4
                if imagen_item and imagen_item.data(Qt.ItemDataRole.UserRole):
                    imagen = imagen_item.data(
                        Qt.ItemDataRole.UserRole) if imagen_item else None

                materiales.append({
                    "numero_serie": numero_serie,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "modelo": modelo_desc if tipo in ["ONT", "MODEM"] else None,
                    "descripcion": modelo_desc if tipo == "Misceláneo" else None,
                    "tipo": tipo,
                    "fecha_registro": fecha_registro,
                    "imagen": imagen
                })
            except Exception as e:
                print(f"Error en fila {row}: {str(e)}")
        return materiales

    def generar_fila_reporte_entrega(self, material):
        """Genera filas LaTeX con campos escapados y un solo \\ al final."""
        escaped_serie = escape_latex(material['numero_serie'])
        escaped_cantidad = escape_latex(
            str(material['cantidad']))  # Convertir a string
        escaped_unidad = escape_latex(material['unidad'])

        if material['tipo'] == 'ONT':
            modelo = escape_latex(material['modelo'])
            return f"{escaped_serie} & {escaped_cantidad} & {escaped_unidad} & {modelo} \\\\ \hline"
        elif material['tipo'] == 'MODEM':
            modelo = escape_latex(material['modelo'])
            return f"{escaped_serie} & {escaped_cantidad} & {escaped_unidad} & {modelo} \\\\ \hline"
        else:
            descripcion = escape_latex(material['descripcion'])
            return f"{escaped_serie} & {escaped_cantidad} & {escaped_unidad} & {descripcion} \\\\ \hline"

    def on_reporte_generado(self, id_entrega, pdf_path):
        """Manejador de la señal finished: recibe id_movimiento y pdf_path"""
        try:
            self.db_almacen.execute_query(
                "UPDATE entregas SET reporte_path = %s WHERE id_entrega = %s",
                [pdf_path, id_entrega],
                fetch=False
            )

            # Verificar que el PDF existe antes de abrirlo
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"El archivo {pdf_path} no existe.")

            # Abrir el PDF
            if os.name == 'nt':
                os.startfile(pdf_path)
            else:
                subprocess.run(['xdg-open', pdf_path] if os.name ==
                               'posix' else ['open', pdf_path], check=True)

        except FileNotFoundError as e:
            QMessageBox.critical(self.surtir_p_o, "Error",
                                 f"Archivo no encontrado: {str(e)}")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self.surtir_p_o, "Error",
                                 f"No se pudo abrir el PDF: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self.surtir_p_o, "Error",
                                 f"Error inesperado: {str(e)}")

    def on_reporte_error(self, error_msg):
        """Maneja errores durante la generación del reporte"""
        QMessageBox.critical(
            self.surtir_p_o,
            "Error en reporte",
            f"Error al generar el documento:\n{error_msg}"
        )
        self.surtir_p_o.lbl_estado.setText("Error en generación de reporte")
        self.surtir_p_o.btn_enviar.setEnabled(True)

    def limpiar_ui(self):
        """Restablece la interfaz a su estado inicial"""
        self.surtir_p_o.tabla_a_p_o.setRowCount(0)
        self.surtir_p_o.str_area.setEnabled(True)
        self.surtir_p_o.str_cope.setEnabled(True)
        self.surtir_p_o.str_exptec.setEnabled(True)
        self.surtir_p_o.str_area.setCurrentIndex(0)
        self.surtir_p_o.str_cope.setCurrentIndex(0)
        self.surtir_p_o.str_exptec.setCurrentIndex(0)

    def imprimir_reporte(self):
        """
        Alternar entre las páginas de la tabla y el reporte.
        """

        indice_actual = self.surtir_p_o.multi_tablas.currentIndex()

        nuevo_indice = 1 if indice_actual == 0 else 0
        self.surtir_p_o.multi_tablas.setCurrentIndex(nuevo_indice)

        if nuevo_indice == 1:
            self.cargar_reporte_entrega()

        icon = QtGui.QIcon(
            "assets/icons/arrow-left.svg" if nuevo_indice == 1 else "assets/icons/imprimir.svg"
        )
        self.surtir_p_o.btn_imprimir.setIcon(icon)

    def cargar_reporte_entrega(self):
        """
        Cargar los movimientos almacenados y los muestra en la tabla.
        """
        exp_tec = self.surtir_p_o.str_exptec.currentText().strip()
        try:
            query = """
                SELECT id_entrega, area, cope, "Fecha de Entrega", "expediente_tecnico", "reporte_path"
                FROM entregas
                WHERE expediente_tecnico = %s
                ORDER BY "Fecha de Entrega" DESC
            """
            params = (exp_tec,)
            resultados = self.db_almacen.execute_query(query, params)

            if resultados:
                TableManager.populate_table(
                    self.surtir_p_o.tabla_reportes,
                    resultados,
                    "Entregas"
                )
                self.surtir_p_o.tabla_reportes.cellClicked.connect(
                    self.abrir_pdf)
            else:
                QMessageBox.information(
                    self.surtir_p_o, "Información", "No se encontraron reportes para este técnico."
                )
        except Exception as e:
            QMessageBox.critical(
                self.surtir_p_o, "Error", f"Error al cargar los reportes: {e}"
            )

    def abrir_pdf(self, row, column):
        """
        Abre el PDF del reporte seleccionado en la tabla de reportes.
        """
        if column == 5:
            # Obtener la ruta del PDF desde la tabla
            ruta_item = self.surtir_p_o.tabla_reportes.item(row, column)
            if ruta_item and ruta_item.text():
                ruta_pdf = ruta_item.text()
                if os.path.exists(ruta_pdf):
                    try:
                        if os.name == 'nt':
                            os.startfile(ruta_pdf)
                        else:
                            subprocess.run(
                                ['xdg-open' if os.name == 'posix' else 'open', ruta_pdf], check=True)
                    except Exception as e:
                        QMessageBox.critical(
                            self.surtir_p_o, "Error", f"No se pudo abrir el PDF: {str(e)}")
                else:
                    QMessageBox.warning(
                        self.surtir_p_o, "Advertencia", "El archivo PDF no existe.")
            else:
                QMessageBox.warning(
                    self.surtir_p_o, "Advertencia", "No hay ruta de PDF registrada.")
