
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6 import uic, QtWidgets, QtCore, QtGui
from psycopg2 import Binary
from datetime import datetime
import os
import uuid

from DatabaseManager import DatabaseManager
from TableManager import TableManager
from Documents.documentación.latex_report_generator import escape_latex


class ReportGenerationThread(QThread):
    finished = pyqtSignal(str, str)
    error = pyqtSignal(str)

    def __init__(self, data, template_path, output_dir):  # ← Constructor corregido
        super().__init__()
        self.data = data
        self.template_path = template_path
        self.output_dir = output_dir

    def run(self):
        try:
            from Documents.documentación.latex_report_generator import generar_reporte_latex, limpiar_archivos_temporales
            success, log = generar_reporte_latex(
                self.data, self.template_path, self.output_dir
            )

            if not success:
                self.error.emit(f"Error LaTeX:\n{log}")
                return

            limpiar_archivos_temporales(self.output_dir)

            pdf_path = os.path.join(
                self.output_dir, f"reporte_{self.data['id_movimiento']}.pdf")
            self.finished.emit(self.data['id_movimiento'], pdf_path)

        except Exception as e:
            self.error.emit(f"Error inesperado:\n{str(e)}")


class M_Almacen():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        # Cargamos la interfaz de usuario mover a almacen
        self.m_almacen = uic.loadUi("modules/Almacenes/mover a almacen.ui")
        self.m_almacen.show()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")

        self.filas_recien_creadas = set()
        self.m_almacen.multi_tablas.setCurrentIndex(0)

        self.cargar_botones()
        self.cargar_areas()
        self.cargar_areas_destino()
        self.inicializar_tabla()

    def cargar_botones(self):
        # Conexiones únicas de señales
        self.m_almacen.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
        self.m_almacen.str_area_destino.currentIndexChanged.connect(
            self.actualizar_cope_destino)
        self.m_almacen.tabla_mov_almacen.itemChanged.connect(
            self.buscar_codigo_barras)
        self.m_almacen.tabla_mov_almacen.itemChanged.connect(
            self.validar_cantidad)
        self.m_almacen.btn_agregar.clicked.connect(self.agregar_fila)
        self.m_almacen.btn_eliminar.clicked.connect(self.eliminar_fila)
        self.m_almacen.btn_enviar.clicked.connect(
            self.procesar_envio_materiales)
        self.m_almacen.btn_imprimir.clicked.connect(self.imprimir_reporte)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.m_almacen.str_area.clear()
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
                    self.m_almacen.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.m_almacen, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.m_almacen, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.m_almacen.str_area.currentText().strip()
        self.m_almacen.str_cope.clear()

        if not area_seleccionada:
            QMessageBox.warning(
                self.m_almacen, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.m_almacen,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.m_almacen.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.m_almacen,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.m_almacen, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def cargar_areas_destino(self):
        """
        Carga todas las áreas disponibles en el ComboBox de destino sin restricciones.
        """
        self.m_almacen.str_area_destino.clear()
        try:
            query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
            resultados = self.db_personal.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.m_almacen.str_area_destino.addItem(
                        resultado['Nombre del Área']
                    )
            else:
                QMessageBox.information(
                    self.m_almacen,
                    "Información",
                    "No se encontraron áreas disponibles para el destino."
                )
        except Exception as e:
            QMessageBox.critical(
                self.m_almacen,
                "Error",
                f"Error al cargar las áreas de destino: {e}"
            )

    def actualizar_cope_destino(self):
        """
        Actualiza los valores del ComboBox de Copé destino basándose en el área seleccionada.
        """
        area_destino_seleccionada = self.m_almacen.str_area_destino.currentText().strip()
        cope_origen = self.m_almacen.str_cope.currentText().strip()
        self.m_almacen.str_cope_destino.clear()

        if not area_destino_seleccionada:
            QMessageBox.warning(
                self.m_almacen,
                "Advertencia",
                "Por favor, seleccione un área de destino."
            )
            return

        try:
            # Consultar los Copé para el área destino seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_destino_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    cope_destino = resultado["Copé"]
                    if cope_destino != cope_origen:
                        self.m_almacen.str_cope_destino.addItem(cope_destino)
            else:
                QMessageBox.information(
                    self.m_almacen,
                    "Información",
                    "No se encontraron Copé disponibles para esta área de destino.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.m_almacen,
                "Error",
                f"Error al cargar los datos de Copé destino: {e}"
            )

    def inicializar_tabla(self):
        """
        Configura las columnas deseadas en la tabla 'tabla_mov_almacen' usando TableManager.
        """
        headers = TableManager.TABLE_HEADERS.get(
            "M_Almacen") + ["Ubicación", "Imagen"]
        self.m_almacen.tabla_mov_almacen.setColumnCount(len(headers))
        self.m_almacen.tabla_mov_almacen.setHorizontalHeaderLabels(headers)
        self.m_almacen.tabla_mov_almacen.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )
        # Ocultar columnas de ubicación e imagen
        self.m_almacen.tabla_mov_almacen.setColumnHidden(
            len(headers)-2, True)  # Ubicación
        self.m_almacen.tabla_mov_almacen.setColumnHidden(
            len(headers)-1, True)  # Imagen

    def agregar_fila(self):
        """
        Agrega una nueva fila en la tabla 'tabla_mov_almacen'.
        La primera columna se habilita para ingresar o buscar el código de barras.
        """
        filas_totales = self.m_almacen.tabla_mov_almacen.rowCount()

        if filas_totales == 0:
            self.m_almacen.str_area.setEnabled(False)
            self.m_almacen.str_cope.setEnabled(False)
            self.m_almacen.str_area_destino.setEnabled(False)
            self.m_almacen.str_cope_destino.setEnabled(False)

        # Eliminadas conexiones redundantes de itemChanged
        self.m_almacen.tabla_mov_almacen.blockSignals(True)
        self.m_almacen.tabla_mov_almacen.insertRow(filas_totales)

        item = QTableWidgetItem()
        item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
        self.m_almacen.tabla_mov_almacen.setItem(filas_totales, 0, item)

        for col in range(1, self.m_almacen.tabla_mov_almacen.columnCount()):
            item = QTableWidgetItem()
            if col == 5:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                              Qt.ItemFlag.ItemIsEditable)
            else:
                item.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.m_almacen.tabla_mov_almacen.setItem(filas_totales, col, item)

        self.filas_recien_creadas.add(filas_totales)
        self.m_almacen.tabla_mov_almacen.blockSignals(False)

    def buscar_codigo_barras(self, item):
        # Desconectar la señal temporalmente para evitar recursión
        self.m_almacen.tabla_mov_almacen.blockSignals(True)

        try:
            if item.column() != 0 or not item.text():
                return

            numero_serie = item.text().strip()
            if self.verificar_duplicados(numero_serie, item.row()):
                QMessageBox.warning(self.m_almacen, "Error",
                                    f"El número de serie {numero_serie} ya está registrado en otra fila.")
                self.limpiar_fila(item.row())
                return

            area_origen = self.m_almacen.str_area.currentText().strip()
            cope_origen = self.m_almacen.str_cope.currentText().strip()

            # Consulta corregida (agregar UNION ALL después de la primera subconsulta)
            query = f"""
                    SELECT
                        "Numero de Serie",
                        SUM(cantidad) AS total_cantidad,
                        unidad,
                        modelo,
                        area,
                        "Centro de Trabajo" AS cope,
                        tipo,
                        ubicacion,
                        imagen
                    FROM (
                        -- Primera subconsulta: almacen
                        SELECT
                            "Numero de Serie", cantidad, unidad, descripcion AS modelo,
                            area, cope AS "Centro de Trabajo", 'almacen' AS tipo,
                            NULL AS ubicacion, NULL AS imagen
                        FROM almacen
                        WHERE area = %s AND cope = %s
                        UNION ALL  -- ← ¡Agregar aquí!
                        -- Segunda subconsulta: ont
                        SELECT
                            "Numero de Serie", cantidad, unidad, modelo,
                            area, "Centro de Trabajo", 'ont' AS tipo,
                            ubicacion, imagen
                        FROM ont
                        WHERE area = %s AND "Centro de Trabajo" = %s
                        UNION ALL
                        -- Tercera subconsulta: modem
                        SELECT
                            "Numero de Serie", cantidad, unidad, modelo,
                            area, "Centro de Trabajo", 'modem' AS tipo,
                            ubicacion, imagen
                        FROM modem
                        WHERE area = %s AND "Centro de Trabajo" = %s
                    ) AS datos
                    WHERE "Numero de Serie" = %s
                    GROUP BY "Numero de Serie", unidad, modelo, area, "Centro de Trabajo", tipo, ubicacion, imagen
                """

            # Ejecutar consulta con parámetros adicionales para ubicacion
            params = [
                area_origen, cope_origen,  # Almacén
                area_origen, cope_origen,  # ONT
                area_origen, cope_origen,  # MODEM
                numero_serie  # Número de serie
            ]

            resultado = self.db_almacen.execute_query(query, params)
            if resultado:
                datos = resultado[0]
                if int(datos["total_cantidad"]) <= 0:
                    QMessageBox.warning(
                        self.m_almacen, "Advertencia", "No hay suficientes unidades disponibles en el almacén.")
                    self.limpiar_fila(item.row())
                    return
                ubicacion = datos.get("ubicacion", "")
                imagen = datos.get("imagen", None)
                # Llenar columna 6 (Ubicación)
                item_ubicacion = QTableWidgetItem(ubicacion)
                self.m_almacen.tabla_mov_almacen.setItem(
                    item.row(), 6, item_ubicacion)

                # Llenar columna 7 (Imagen) con datos binarios
                item_imagen = QTableWidgetItem()
                if imagen is not None:
                    # Almacenar binario
                    item_imagen.setData(Qt.ItemDataRole.UserRole, imagen)
                else:
                    print("[DEBUG] No hay imagen en el registro original")
                self.m_almacen.tabla_mov_almacen.setItem(
                    item.row(), 7, item_imagen)

                # Llenar columnas principales (sin incluir ubicación/imagen)
                tipo_mapeo = {'almacen': 'Misceláneo',
                              'ont': 'ONT', 'modem': 'MODEM'}
                columnas = ["total_cantidad", "unidad", "modelo", "tipo"]

                for col_index, col_name in enumerate(columnas, start=1):
                    valor = tipo_mapeo.get(
                        datos.get(col_name, ""), "") if col_name == "tipo" else datos.get(col_name, "")
                    celda = QTableWidgetItem(str(valor))

                    if col_index == 5:  # Columna "Cantidad a enviar"
                        celda.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                       Qt.ItemFlag.ItemIsEditable)
                    else:
                        celda.setFlags(Qt.ItemFlag.ItemIsEnabled)

                    self.m_almacen.tabla_mov_almacen.setItem(
                        item.row(), col_index, celda)

                # Ocultar columnas de ubicación e imagen (no necesitan manipulación)
                self.m_almacen.tabla_mov_almacen.setColumnHidden(
                    6, True)  # Columna 6: ubicacion
                self.m_almacen.tabla_mov_almacen.setColumnHidden(
                    7, True)  # Columna 7: imagen

            else:
                QMessageBox.warning(self.m_almacen, "Advertencia",
                                    "No se encontraron datos para el número de serie ingresado.")
                self.limpiar_fila(item.row())

        except Exception as e:
            print(f"Error al buscar código de barras: {str(e)}")
        finally:
            self.m_almacen.tabla_mov_almacen.blockSignals(False)

    def verificar_duplicados(self, numero_serie, fila_actual):
        for row in range(self.m_almacen.tabla_mov_almacen.rowCount()):
            if row == fila_actual:  # Excluir la fila actual
                continue
            item = self.m_almacen.tabla_mov_almacen.item(row, 0)
            if item and item.text() == numero_serie:
                return True
        return False

    def limpiar_fila(self, row):
        for col in range(self.m_almacen.tabla_mov_almacen.columnCount()):
            self.m_almacen.tabla_mov_almacen.setItem(
                row, col, QTableWidgetItem())

    def validar_cantidad(self, item):
        """
        Valida y corrige la cantidad ingresada en la columna 'Cantidad a enviar'.
        Si el valor excede la cantidad disponible, lo ajusta automáticamente.
        """
        columna = item.column()
        fila = item.row()

        if columna != 5:  # Validar solo la columna "Cantidad a enviar"
            return

        cantidad_enviar = item.text().strip()

        # Validar que la cantidad sea un número entero positivo}
        if not cantidad_enviar.isdigit() or int(cantidad_enviar) <= 0:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "Por favor, ingrese una cantidad válida.")
            self.m_almacen.tabla_mov_almacen.blockSignals(True)
            item.setText("")
            self.m_almacen.tabla_mov_almacen.blockSignals(False)
            return

        cantidad_enviar = int(cantidad_enviar)

        # Ignorar la validación si es una fila recién creada
        if fila in self.filas_recien_creadas:
            if cantidad_enviar > 0:
                self.filas_recien_creadas.remove(fila)
            return

        # Obtener la cantidad disponible
        cantidad_disponible_item = self.m_almacen.tabla_mov_almacen.item(
            fila, 1)  # Columna 1 es "Cantidad disponible"
        if not cantidad_disponible_item:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "No se encontró la cantidad disponible.")
            return

        cantidad_disponible = cantidad_disponible_item.text().strip()
        if not cantidad_disponible.isdigit():
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "La cantidad disponible no es válida.")
            return

        cantidad_disponible = int(cantidad_disponible)

        # Validar si la cantidad a enviar excede la cantidad disponible
        if cantidad_enviar > cantidad_disponible:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                f"La cantidad a enviar ({cantidad_enviar}) excede la cantidad disponible ({cantidad_disponible}). Se ajustará automáticamente.")
            self.m_almacen.tabla_mov_almacen.blockSignals(True)
            # Ajustar a la cantidad máxima disponible
            item.setText(str(cantidad_disponible))
            self.m_almacen.tabla_mov_almacen.blockSignals(False)

    def eliminar_fila(self):
        fila_seleccionada = self.m_almacen.tabla_mov_almacen.currentRow()
        if fila_seleccionada == -1:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "Por favor, seleccione una fila para eliminar.")
            return

        respuesta = QMessageBox.question(
            self.m_almacen, "Confirmación",
            "¿Está seguro que desea eliminar la fila seleccionada?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if respuesta == QMessageBox.StandardButton.Yes:
            self.m_almacen.tabla_mov_almacen.removeRow(fila_seleccionada)
            # Habilitar todos los ComboBox si no hay filas
            if self.m_almacen.tabla_mov_almacen.rowCount() == 0:
                self.m_almacen.str_area.setEnabled(True)
                self.m_almacen.str_cope.setEnabled(True)
                self.m_almacen.str_area_destino.setEnabled(True)
                self.m_almacen.str_cope_destino.setEnabled(True)
        else:
            QMessageBox.information(
                self.m_almacen, "Cancelado", "La fila no ha sido eliminada.")

    def validar_datos_movimiento(self):
        """Valida los datos del movimiento antes de registrarlos."""
        if self.m_almacen.tabla_mov_almacen.rowCount() == 0:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "Por favor, agregue al menos un artículo a la lista.")
            return False

        area_origen = self.m_almacen.str_area.currentText().strip()
        cope_origen = self.m_almacen.str_cope.currentText().strip()
        area_destino = self.m_almacen.str_area_destino.currentText().strip()
        cope_destino = self.m_almacen.str_cope_destino.currentText().strip()

        if not area_destino or not cope_destino:
            QMessageBox.warning(self.m_almacen, "Advertencia",
                                "Por favor, seleccione un área y Copé de destino.")
            return False

        for row in range(self.m_almacen.tabla_mov_almacen.rowCount()):
            cantidad = self.m_almacen.tabla_mov_almacen.item(row, 5)
            if not cantidad or not cantidad.text().isdigit():
                QMessageBox.warning(self.m_almacen, "Advertencia",
                                    f"Fila {row+1}: Cantidad inválida o vacía.")
                return False
        return True

    def obtener_materiales_interfaz(self):
        """
        Obtiene los materiales ingresados en la tabla 'tabla_mov_almacen'.
        : return: Lista de diccionarios con los detalles de los materiales.
        """
        materiales = []
        for row in range(self.m_almacen.tabla_mov_almacen.rowCount()):
            try:
                numero_serie_item = self.m_almacen.tabla_mov_almacen.item(
                    row, 0)
                cantidad_item = self.m_almacen.tabla_mov_almacen.item(row, 5)
                unidad_item = self.m_almacen.tabla_mov_almacen.item(row, 2)
                descripcion_item = self.m_almacen.tabla_mov_almacen.item(
                    row, 3)
                tipo_item = self.m_almacen.tabla_mov_almacen.item(row, 4)

                if not (numero_serie_item and cantidad_item and unidad_item and tipo_item):
                    print(f"Error en la fila {row}: Datos incompletos.")
                    continue

                numero_serie = numero_serie_item.text().strip()
                cantidad = int(cantidad_item.text().strip(
                )) if cantidad_item.text().strip().isdigit() else 0
                unidad = unidad_item.text().strip()
                descripcion = descripcion_item.text().strip()
                tipo = tipo_item.text().strip()

                print(f"""
                    Filas {row}:
                    Serie: {numero_serie}
                    Cantidad: {cantidad}
                    Tipo: {tipo}
                """)

                materiales.append({
                    "numero_serie": numero_serie,
                    "Numero de Serie": numero_serie,
                    "cantidad": cantidad,
                    "unidad": unidad,
                    "descripcion": descripcion,
                    "tipo": tipo
                })

            except Exception as e:
                print(f"Error en al fila {row}: {str(e)}")
        return materiales

    def registrar_movimiento_general(self, id_movimiento, area_origen, cope_origen, area_destino, cope_destino):
        """Registra un movimiento en la base de datos."""
        origen = f"{area_origen} - {cope_origen}"
        destino = f"{area_destino} - {cope_destino}"
        query_mov = """
            INSERT INTO movimientos (id_movimiento, origen, destino, "Tipo de Movimiento")
            VALUES (%s, %s, %s, 'Envío')
        """
        self.db_almacen.execute_query(
            query_mov, [id_movimiento, origen, destino], fetch=False)

    def registrar_movimiento_materiales(self, id_movimiento, material, cantidad_a_mover):
        query = """
            INSERT INTO movimientos_materiales 
            (id_movimiento, "Numero de Serie", cantidad, unidad, descripcion, imagen, tipo)
            VALUES (%s, %s, %s, %s, %s, %s,%s)
        """
        # Usar la clave corregida
        params = [
            id_movimiento,
            material["Numero de Serie"],  # ← Clave corregida
            cantidad_a_mover,
            material["unidad"],
            material["descripcion"],
            Binary(material.get("imagen")) if material.get("imagen") else None,
            material["tipo"]
        ]
        self.db_almacen.execute_query(query, params, fetch=False)

    def procesar_actualizacion_almacen(self, area_origen, cope_origen, materiales, id_movimiento):
        try:
            area_destino = self.m_almacen.str_area_destino.currentText().strip()
            cope_destino = self.m_almacen.str_cope_destino.currentText().strip()

            # Iterar por cada fila de la tabla (no por la lista materiales)
            for row in range(self.m_almacen.tabla_mov_almacen.rowCount()):
                numero_serie_item = self.m_almacen.tabla_mov_almacen.item(
                    row, 0)
                if not numero_serie_item:
                    continue  # Saltar filas vacías

                numero_serie = numero_serie_item.text().strip()

                # Buscar el material correspondiente en la lista
                material = next(
                    (m for m in materiales if m.get("numero_serie") == numero_serie), None)
                if not material:
                    continue  # Si no existe, continuar

                cantidad = material["cantidad"]
                tipo = material["tipo"].lower()

                # Obtener datos de la UI usando el row real
                unidad = self.m_almacen.tabla_mov_almacen.item(
                    row, 2).text().strip()
                modelo = self.m_almacen.tabla_mov_almacen.item(
                    row, 3).text().strip()
                ubicacion = self.m_almacen.tabla_mov_almacen.item(
                    row, 6).text().strip()
                imagen_item = self.m_almacen.tabla_mov_almacen.item(
                    row, 7)  # Usar row real

                # Convertir la imagen
                imagen = None
                if imagen_item:
                    imagen_data = imagen_item.data(Qt.ItemDataRole.UserRole)
                    if isinstance(imagen_data, memoryview):
                        # Convertir a bytes
                        imagen = Binary(imagen_data.tobytes())
                    elif imagen_data is not None:
                        imagen = Binary(imagen_data)
                    else:
                        print(f"[DEBUG] Imagen es None para {numero_serie}")

                if tipo in ["ont", "modem"]:
                    tabla_traslado = "ont_en_traslado" if tipo == "ont" else "modem_en_traslado"
                    query_traslado = f"""
                        INSERT INTO {tabla_traslado}
                        ("Numero de Serie", cantidad, unidad, modelo, area,
                         "Centro de Trabajo", ubicacion, imagen, id_movimiento)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    params_traslado = (
                        numero_serie,
                        cantidad,
                        unidad,
                        modelo,
                        area_destino,
                        cope_destino,
                        "En tránsito",
                        imagen,  # Ahora imagen no será None si existe
                        id_movimiento
                    )
                    print(f"[DEBUG] Parámetros: {params_traslado}")
                    self.db_almacen.execute_query(
                        query_traslado, params_traslado, fetch=False)

                # 2. Actualizar/Eliminar en tabla origen
                tabla_origen = "ont" if tipo == "ont" else "modem" if tipo == "modem" else "almacen"
                columna_trabajo = '"Centro de Trabajo"' if tipo in [
                    "ont", "modem"] else "cope"

                # Obtener cantidad actual
                query_cantidad = f"""
                    SELECT cantidad FROM {tabla_origen}
                    WHERE "Numero de Serie" = %s
                    AND area = %s
                    AND {columna_trabajo} = %s
                """
                resultado = self.db_almacen.execute_query(
                    query_cantidad,
                    [numero_serie, area_origen, cope_origen]
                )

                if not resultado:
                    raise Exception(
                        f"Material {numero_serie} no encontrado en {tabla_origen}")

                cantidad_actual = resultado[0]["cantidad"]
                nueva_cantidad = cantidad_actual - cantidad

                if nueva_cantidad <= 0:
                    # Eliminar registro si la cantidad llega a 0
                    query_delete = f"""
                        DELETE FROM {tabla_origen}
                        WHERE "Numero de Serie" = %s
                        AND area = %s
                        AND {columna_trabajo} = %s
                    """
                    self.db_almacen.execute_query(
                        query_delete,
                        [numero_serie, area_origen, cope_origen],
                        fetch=False
                    )
                    print(
                        f"Eliminado {numero_serie} de {tabla_origen} (cantidad 0)")
                else:
                    # Actualizar cantidad en origen
                    query_update = f"""
                        UPDATE {tabla_origen}
                        SET cantidad = %s
                        WHERE "Numero de Serie" = %s
                        AND area = %s
                        AND {columna_trabajo} = %s
                    """
                    self.db_almacen.execute_query(
                        query_update,
                        [nueva_cantidad, numero_serie, area_origen, cope_origen],
                        fetch=False
                    )
                    print(
                        f"Actualizado {numero_serie} en {tabla_origen}: {nueva_cantidad} unidades")

        except Exception as e:
            print(f"Error crítico al procesar actualización: {str(e)}")
            raise

    def registrar_ont_traslado(self, id_movimiento):
        """Registra ONTs desde ont_en_traslado a movimientos_materiales"""
        query = """
            INSERT INTO movimientos_materiales
            (id_movimiento, "Numero de Serie", cantidad, unidad, descripcion, tipo)
            SELECT %s, "Numero de Serie", cantidad, unidad, modelo, 'ONT'
            FROM ont_en_traslado
            WHERE id_movimiento = %s
        """
        self.db_almacen.execute_query(
            query, [id_movimiento, id_movimiento], fetch=False)
        print(f"ONTs del movimiento {id_movimiento} registrados")

    def registrar_modem_traslado(self, id_movimiento):
        """Registra MODEMs desde modem_en_traslado a movimientos_materiales"""
        query = """
            INSERT INTO movimientos_materiales
            (id_movimiento, "Numero de Serie", cantidad, unidad, descripcion, tipo)
            SELECT %s, "Numero de Serie", cantidad, unidad, modelo, 'MODEM'
            FROM modem_en_traslado
            WHERE id_movimiento = %s
        """
        self.db_almacen.execute_query(
            query, [id_movimiento, id_movimiento], fetch=False)
        print(f"MODEMs del movimiento {id_movimiento} registrados")

    def registrar_miscelaneos(self, id_movimiento, materiales):
        for material in materiales:
            if material["tipo"] == "Misceláneo":
                query_insert_misc = """
                INSERT INTO movimientos_materiales (id_movimiento, "Numero de Serie", cantidad, unidad, descripcion, tipo)
                VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.db_almacen.execute_query(
                    query_insert_misc, [
                        id_movimiento,
                        material["numero_serie"],
                        material["cantidad"],
                        material["unidad"],
                        material["descripcion"],
                        material["tipo"]
                    ],
                    fetch=False
                )
        print(
            f"Registrados {len(materiales)} misceláneos en el movimiento {id_movimiento}.")

    def registrar_materiales_traslado(self, id_movimiento, materiales):
        """Registra los materiales en movimientos_materiales con su tipo correspondiente"""
        try:
            # Contadores para ONT y MODEM
            cont_ont = 0
            cont_modem = 0

            for material in materiales:
                tipo = material["tipo"].lower()

                if tipo == "misceláneo":
                    # Insertar misceláneo con su número de serie real
                    query = """
                        INSERT INTO movimientos_materiales
                        (id_movimiento, "Numero de Serie",
                         cantidad, unidad, descripcion, tipo)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    params = (
                        id_movimiento,
                        material["numero_serie"],
                        material["cantidad"],
                        material["unidad"],
                        material["descripcion"],
                        "MISCELÁNEO"
                    )
                    self.db_almacen.execute_query(query, params, fetch=False)

                elif tipo == "ont":
                    cont_ont += material["cantidad"]

                elif tipo == "modem":
                    cont_modem += material["cantidad"]

            # Registrar ONTs y MODEMs como resumen grupal
            if cont_ont > 0:
                query = """
                    INSERT INTO movimientos_materiales
                    (id_movimiento, "Numero de Serie",
                     cantidad, unidad, descripcion, tipo)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                self.db_almacen.execute_query(query, (
                    id_movimiento,
                    id_movimiento,  # Usar el ID de movimiento como referencia
                    cont_ont,
                    "Pieza(s)",
                    f"Resumen de ONTs enviadas",
                    "ONT"
                ), fetch=False)

            if cont_modem > 0:
                self.db_almacen.execute_query(query, (
                    id_movimiento,
                    id_movimiento,  # Mismo ID de movimiento
                    cont_modem,
                    "Pieza(s)",
                    f"Resumen de MODEMs enviados",
                    "MODEM"
                ), fetch=False)

        except Exception as e:
            print(f"Error al registrar: {e}")
            raise

    def procesar_envio_materiales(self):
        if not self.validar_datos_movimiento():
            return

        try:
            # Obtener datos del movimiento UNA SOLA VEZ
            area_origen, cope_origen, area_destino, cope_destino = self.obtener_datos_movimiento()
            origen = f"{area_origen} - {cope_origen}"
            destino = f"{area_destino} - {cope_destino}"

            # Generar ID de movimiento único
            id_movimiento = str(uuid.uuid4())

            # Obtener los materiales de la tabla
            materiales = self.obtener_materiales_interfaz()

            # Preparar datos para el reporte (usar variables ya calculadas)
            data_reporte = {
                "id_movimiento": id_movimiento,
                "origen": origen,
                "destino": destino,
                "fecha": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "tabla_datos": "\n".join([self.generar_fila_tabla(m) for m in materiales]),
                "nombre_usuario": self.usuario_actual["nombre"]
            }

            # Crear el hilo para generar el reporte
            thread = ReportGenerationThread(
                data_reporte,
                "Documents/documentación/RMovimiento de material.tex",
                "reports"
            )
            thread.finished.connect(self.on_reporte_generado)
            thread.error.connect(self.on_reporte_error)
            thread.start()

            # Registrar el movimiento GENERAL con TODOS los parámetros <-- Clave
            self.registrar_movimiento_general(
                id_movimiento,
                area_origen,
                cope_origen,
                area_destino,
                cope_destino
            )

            # Registrar cada material
            for material in materiales:
                cantidad = material["cantidad"]
                material["Numero de Serie"] = material.get("numero_serie", "")
                self.registrar_movimiento_materiales(
                    id_movimiento, material, cantidad)

            # Actualizar el almacenamiento físico
            self.procesar_actualizacion_almacen(
                area_origen,
                cope_origen,
                materiales,
                id_movimiento
            )
            # 2. Registrar resúmenes en movimientos_materiales
            self.registrar_ont_traslado(id_movimiento)  # Resumen ONT
            self.registrar_modem_traslado(id_movimiento)  # Resumen MODEM
            self.registrar_miscelaneos(
                id_movimiento, materiales)  # Misceláneos

            self.limpiar_ui()

            QMessageBox.information(
                self.m_almacen,
                "Éxito",
                "El movimiento se ha registrado correctamente."
            )

        except Exception as e:
            QMessageBox.critical(
                self.m_almacen,
                "Error",
                f"Error al procesar el movimiento:\n{str(e)}"
            )

    def obtener_datos_movimiento(self):
        return (
            self.m_almacen.str_area.currentText().strip(),
            self.m_almacen.str_cope.currentText().strip(),
            self.m_almacen.str_area_destino.currentText().strip(),
            self.m_almacen.str_cope_destino.currentText().strip()
        )

    def obtener_datos_origen(self):
        return (
            self.m_almacen.str_area.currentText().strip(),
            self.m_almacen.str_cope.currentText().strip()
        )

    def generar_id_movimiento(self):
        return f"MV-{uuid.uuid4().hex[:8].upper()}"

    def iniciar_generacion_reporte(self, id_movimiento, materiales):
        if hasattr(self, 'report_thread') and self.report_thread.isRunning():
            self.report_thread.terminate()

        try:
            report_data = self.preparar_datos_reporte(
                id_movimiento, materiales)
            template_path = "Documents/documentación/RMovimiento de material.tex"
            output_dir = "reports"
            # Crear instancia sin parámetros opcionales incorrectos
            self.report_thread = ReportGenerationThread(
                data=report_data,
                template_path=template_path,
                output_dir=output_dir
            )

            self.report_thread.finished.connect(self.on_reporte_generado)
            self.report_thread.error.connect(self.on_reporte_error)
            self.report_thread.start()
        except Exception as e:
            self.manejar_error(e)

    def preparar_datos_reporte(self, id_movimiento, materiales):
        origen, _, destino, _ = self.obtener_datos_movimiento()
        nombre_usuario = escape_latex(self.usuario_actual["nombre"])

        filas_tabla = []
        for m in materiales:
            fila = self.generar_fila_tabla(m)
            filas_tabla.append(fila)

        return {
            'id_movimiento': escape_latex(id_movimiento),
            'origen': escape_latex(f"{origen}"),
            'destino': escape_latex(f"{destino}"),
            'fecha': escape_latex(datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
            'tabla_datos': "\n".join(filas_tabla),
            'nombre_usuario': nombre_usuario
        }

    def generar_fila_tabla(self, material):
        return rf"{escape_latex(material['numero_serie'])} & "rf"{escape_latex(material['descripcion'])} & "rf"{material['cantidad']} & "rf"{escape_latex(material['unidad'])} \\\\"

    def mostrar_estado_proceso(self, mostrar):
        texto = "Generando reporte..." if mostrar else ""
        self.m_almacen.lbl_estado.setText(texto)
        self.m_almacen.lbl_estado.setVisible(mostrar)
        self.m_almacen.btn_enviar.setEnabled(not mostrar)

    def on_reporte_generado(self, id_movimiento, pdf_path):
        """Manejador de la señal finished: recibe id_movimiento y pdf_path"""
        try:
            # 1. Guardar ruta en la BD
            query = "UPDATE movimientos SET reporte_path = %s WHERE id_movimiento = %s"
            self.db_almacen.execute_query(
                query, [pdf_path, id_movimiento], fetch=False)

            # 2. Abrir el PDF automáticamente
            if os.path.exists(pdf_path):
                if os.name == 'nt':  # Windows
                    os.startfile(pdf_path)
                else:  # Linux/macOS
                    subprocess.run(
                        ['xdg-open' if os.name == 'posix' else 'open', pdf_path])

            QMessageBox.information(
                self.m_almacen,
                "Éxito",
                f"Reporte generado: {pdf_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self.m_almacen,
                "Error",
                f"No se pudo guardar la ruta del PDF: {str(e)}"
            )

    def on_reporte_error(self, error_msg):
        QMessageBox.critical(
            self.m_almacen,
            "Error",
            f"Error durante la generación del reporte:\n{error_msg}"
        )

    def manejar_error(self, error):
        self.mostrar_estado_proceso(False)
        QMessageBox.critical(
            self.m_almacen,
            "Error",
            f"Error crítico: {str(error)}"
        )

    def limpiar_ui(self):
        """Restablece la tabla y los ComboBox a su estado inicial"""
        # Limpiar tabla
        self.m_almacen.tabla_mov_almacen.setRowCount(0)

        # Habilitar ComboBox
        self.m_almacen.str_area.setEnabled(True)
        self.m_almacen.str_cope.setEnabled(True)
        self.m_almacen.str_area_destino.setEnabled(True)
        self.m_almacen.str_cope_destino.setEnabled(True)

    def imprimir_reporte(self):
        """
        Alterna entre las páginas del QStackedWidget y carga los reportes al mostrar la tabla.
        """
        # Obtener el índice actual
        indice_actual = self.m_almacen.multi_tablas.currentIndex()

        # Determinar el nuevo índice
        nuevo_indice = 1 if indice_actual == 0 else 0

        # Cambiar de página
        self.m_almacen.multi_tablas.setCurrentIndex(nuevo_indice)

        # Cargar datos solo si se está mostrando la página de reportes
        if nuevo_indice == 1:
            self.cargar_reportes()

        # Opcional: Cambiar el texto del botón según la página
        icon = QtGui.QIcon(
            "assets/icons/arrow-left.svg" if nuevo_indice == 1 else "assets/icons/imprimir.svg")
        self.m_almacen.btn_imprimir.setIcon(icon)

    def cargar_reportes(self):
        """
        Carga los movimientos almacenados y los muestra en la tabla.
        """
        try:
            # Consulta para obtener los movimientos
            query = """
            SELECT 
                id_movimiento, origen, destino, 
                "Fecha de Movimiento", "Tipo de Movimiento", reporte_path
            FROM movimientos
            ORDER BY "Fecha de Movimiento" DESC;
            """
            resultados = self.db_almacen.execute_query(query)

            # Mostrar datos en la tabla
            if resultados:
                TableManager.populate_table(
                    self.m_almacen.tabla_reportes,  # Asegúrate que el QTableWidget se llame así
                    resultados,
                    "Reportes"  # Nombre clave definido en TableManager
                )
                self.m_almacen.tabla_reportes.cellClicked.connect(
                    self.abrir_pdf)
            else:
                QtWidgets.QMessageBox.information(
                    self.m_almacen,
                    "Información",
                    "No hay movimientos registrados."
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self.m_almacen,
                "Error",
                f"Error al cargar movimientos: {str(e)}"
            )

    def abrir_pdf(self, row, column):
        """
        Abre el PDF asociado a un movimiento al hacer clic en la celda correspondiente.
        """
        if column == 5:

            # Obtener la ruta del PDF
            ruta_item = self.m_almacen.tabla_reportes.item(row, column)
            if ruta_item:
                ruta_pdf = ruta_item.text()
                if ruta_pdf:
                    # Abrir el PDF con el visor predeterminado del sistema
                    QtGui.QDesktopServices.openUrl(
                        QtCore.QUrl.fromLocalFile(ruta_pdf))
