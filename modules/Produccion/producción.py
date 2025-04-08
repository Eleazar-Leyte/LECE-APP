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


class Producción():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.produccion = uic.loadUi("modules/Produccion/Produccion.ui")
        self.produccion.showMaximized()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")
        self.db_produccion = DatabaseManager("Producción")

        self.filas_recien_creadas = set()
        self.produccion.Multi_carga.setCurrentIndex(0)

        self.iniciar_tablas()
        self.botones()
        self.cargar_areas()
        self.configurar_calendario()
        self.conectar_validaciones()

    def botones(self):
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

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.produccion.close()

    def salir(self):
        """
        Cierra la sesión del usuario actual y regresa a la ventana de inicio de sesión.
        """
        try:
            # Limpiar la variable usuario_actual
            self.usuario_actual.clear()

            # Cerrar la ventana actual
            self.produccion.close()

            # Importar y mostrar la ventana de inicio de sesión
            from modules.login.login import Login
            self.login = Login()

            QMessageBox.information(
                None, "Sesión cerrada", "Se ha cerrado la sesión exitosamente."
            )
        except Exception as e:
            QMessageBox.critical(
                None, "Error", f"Error al cerrar la sesión: {e}"
            )

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.produccion.str_area.clear()
        self.produccion.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
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
                    self.produccion.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.produccion, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.produccion, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.produccion.str_area.currentText().strip()
        self.produccion.str_cope.clear()
        self.produccion.str_cope.currentIndexChanged.connect(
            self.actualizar_exptec)

        if not area_seleccionada:
            QMessageBox.warning(
                self.produccion, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.produccion,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.produccion.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.produccion,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.produccion, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def actualizar_exptec(self):
        """
        Cargar los técnicos en el ComboBox str_expetec según el área y COPE seleccionados.
        """
        try:
            self.produccion.str_exptec.clear()

            # Obtener area y cope seleccionados
            area = self.produccion.str_area.currentText().strip()
            cope = self.produccion.str_cope.currentText().strip()

            if not area or not cope:
                QMessageBox.warning(
                    self.produccion,
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
                query_id_area, (area,))

            if not resultado_id_area:
                QMessageBox.critical(
                    self.produccion,
                    "Error",
                    f"No se encontró el ID para el área: {area}."
                )
                return
            id_area = resultado_id_area[0]["id"]

            query_tecnicos = """
            SELECT id,
            "Apellido Paterno",
            "Apellido Materno",
            "Nombre (s)"
            FROM personal_o
            WHERE "id_area" = %s AND "Cope" = %s
            """
            resultados = self.db_personal.execute_query(
                query_tecnicos, (id_area, cope))

            if resultados:
                for tecnicos in resultados:
                    nombre_completo = (
                        f"{tecnicos['Nombre (s)']} "
                        f"{tecnicos['Apellido Paterno']} "
                        f"{tecnicos['Apellido Materno']}"
                    )
                    self.produccion.str_exptec.addItem(
                        nombre_completo, userData=tecnicos["id"])
            else:
                QMessageBox.information(
                    self.produccion,
                    "Sin técnicos",
                    "No se encontraron técnicos disponibles para esta área y Copé."
                )
        except Exception as e:
            QMessageBox.critical(
                self.produccion, "Error", f"Error al cargar los técnicos: {e}."
            )

    def iniciar_tablas(self):
        """
        Cargar las columnas usando el TableManger.py
        """
        # Tabla Fibra Óptica
        TableManager.populate_table(
            self.produccion.tabla_FO,
            [],
            "Producción F.O."
        )
        # Tabla de Cobre
        TableManager.populate_table(
            self.produccion.tabla_cobre,
            [],
            "Producción Cobre"
        )
        # Tabla de Quejas
        TableManager.populate_table(
            self.produccion.tabla_quejas,
            [],
            "Producción Cobre"
        )  # Tabla de A4
        TableManager.populate_table(
            self.produccion.tabla_a4,
            [],
            "Producción Cobre"
        )

    def cambiar_vista(self, indice):
        self.produccion.Multi_carga.setCurrentIndex(indice)

    def agregar_fila(self):
        """Agrega fila a la tabla visible actualmente"""
        tabla_actual = self.obtener_tabla_actual()
        self._agregar_fila(tabla_actual)

    def eliminar_fila(self):
        """Elimina fila de la tabla visible actualmente"""
        tabla_actual = self.obtener_tabla_actual()
        self._eliminar_fila(tabla_actual)

    def obtener_tabla_actual(self):
        """Devuelve la tabla correspondiente al índice actual del QStackedWidget"""
        indice = self.produccion.Multi_carga.currentIndex()

        mapeo_tablas = {
            0: self.produccion.tabla_FO,     # Fibra Óptica
            1: self.produccion.tabla_cobre,  # Cobre
            2: self.produccion.tabla_quejas,  # Quejas
            3: self.produccion.tabla_a4      # A4
        }

        # Default: Fibra Óptica
        return mapeo_tablas.get(indice, self.produccion.tabla_FO)

    def _agregar_fila(self, tabla):
        """Implementación base para agregar filas"""
        tabla.blockSignals(
            True)  # Bloquear señales para evitar bucles infinitos
        try:
            fila = tabla.rowCount()
            tabla.insertRow(fila)
            for col in range(tabla.columnCount()):
                item = QtWidgets.QTableWidgetItem()
                if col == 7:  # Columnas editables
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                  Qt.ItemFlag.ItemIsSelectable)
                else:
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                  Qt.ItemFlag.ItemIsEditable)
                tabla.setItem(fila, col, item)
        finally:
            tabla.blockSignals(False)

        self.actualizar_estado_combo()  # Actualizar estado de los ComboBoxes

    def _eliminar_fila(self, tabla, row=None):
        """Implementación base para eliminar filas"""
        if row is None:
            row = tabla.currentRow()
        if row != -1:
            tabla.removeRow(row)

        self.actualizar_estado_combo()  # Actualizar estado de los ComboBoxes

    def obtener_total_filas(self) -> int:
        """
        Calcula el total de filas en todas las tablas
        """
        return (
            self.produccion.tabla_FO.rowCount() +
            self.produccion.tabla_cobre.rowCount() +
            self.produccion.tabla_quejas.rowCount() +
            self.produccion.tabla_a4.rowCount()
        )

    def actualizar_estado_combo(self):
        """
        Habilitar/Deshabilitar ComboBoxes según si hay filas
        """
        total = self.obtener_total_filas()
        estado = total == 0

        self.produccion.str_area.setEnabled(estado)
        self.produccion.str_cope.setEnabled(estado)
        self.produccion.str_exptec.setEnabled(estado)

    def configurar_calendario(self):
        """Conectar clics en la columna de fecha para mostrar calendario"""
        self.produccion.tabla_FO.cellClicked.connect(
            lambda row, col: self.mostrar_calendario(row, col))
        self.produccion.tabla_cobre.cellClicked.connect(
            lambda row, col: self.mostrar_calendario(row, col))
        self.produccion.tabla_quejas.cellClicked.connect(
            lambda row, col: self.mostrar_calendario(row, col))
        self.produccion.tabla_a4.cellClicked.connect(
            lambda row, col: self.mostrar_calendario(row, col))

    def mostrar_calendario(self, row: int, col: int):
        """Muestra un diálogo de calendario al hacer clic en la columna 6"""
        if col != 6:
            return

        tabla = self.obtener_tabla_actual()

        # Crear un diálogo que contenga el calendario
        dialog = QtWidgets.QDialog()
        calendario = QtWidgets.QCalendarWidget(dialog)
        dialog.setWindowTitle("Seleccionar Fecha")

        # Configurar el layout del diálogo
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(calendario)
        dialog.setLayout(layout)

        # Conectar la señal de clic en el calendario
        calendario.clicked.connect(
            lambda date: self.actualizar_fecha(row, date, tabla))

        # Mostrar el diálogo modal
        dialog.exec()

    def actualizar_fecha(self, row: int, date: QtCore.QDate, tabla):
        """Actualiza la celda con la fecha seleccionada"""
        fecha_formateada = date.toString("dd/MM/yyyy")
        tabla.setItem(row, 6, QTableWidgetItem(fecha_formateada))

    def consultar_equipo_en_campo(self, numero_serie: str, tipo_equipo: str) -> dict:
        """
        Consulta un equipo (ONT/MODEM) en su tabla correspondiente en campo.
        Filtra por: Número de serie, área, COPE y expediente técnico.
        """
        try:
            # Obtener parámetros de filtrado
            area = self.produccion.str_area.currentText().strip()
            cope = self.produccion.str_cope.currentText().strip()
            nombre_tecnico = self.produccion.str_exptec.currentText().strip()  # ID del técnico
            print(f"ID Técnico: {nombre_tecnico}")

            if not all([area, cope, nombre_tecnico]):
                raise ValueError(
                    "Complete todos los filtros (Área, COPE y Técnico)")

            # Determinar tabla y columnas según el tipo de equipo
            if tipo_equipo == "ONT":
                tabla = "\"ONT en Campo\""
                columna_serie = "\"Numero de Serie\""
            elif tipo_equipo == "MODEM":
                tabla = "modem_en_campo"
                columna_serie = "\"Numero de Serie\""
            else:
                raise ValueError("Tipo de equipo no válido")

            query = f"""
                SELECT modelo, imagen, "Fecha de Registro" 
                FROM {tabla}
                WHERE 
                    {columna_serie} = %s AND
                    area = %s AND
                    "Centro de Trabajo" = %s AND
                    "Expediente Técnico" = %s
            """
            params = (numero_serie, area, cope, nombre_tecnico)

            resultado = self.db_almacen.execute_query(query, params)
            return resultado[0] if resultado else None

        except Exception as e:
            raise RuntimeError(f"Error al consultar {tipo_equipo}: {str(e)}")

    def validar_numero_serie(self, row: int, col: int, tipo_equipo: str):
        """Valida el número de serie y completa datos automáticamente con filtros"""
        if col != 4:  # Solo actuar en columna de número de serie
            return

        tabla = self.obtener_tabla_actual()
        numero_serie = tabla.item(row, col).text().strip()

        try:
            if not numero_serie:
                raise ValueError("Ingrese un número de serie")

            # Consultar equipo con filtros de área, COPE y técnico
            datos = self.consultar_equipo_en_campo(numero_serie, tipo_equipo)

            if not datos:
                raise ValueError(
                    f"{tipo_equipo} no encontrado o no asignado a este técnico/área/COPE"
                )

            # ---- Llenar datos automáticamente ----
            # Columna 5: Modelo
            modelo_item = QTableWidgetItem(datos["modelo"])
            modelo_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Solo lectura
            tabla.setItem(row, 5, modelo_item)

            # Columna 7: Imagen
            if datos["imagen"]:
                label = QtWidgets.QLabel()
                pixmap = QtGui.QPixmap()
                # Convertir desde Binary
                pixmap.loadFromData(datos["imagen"].tobytes())
                label.setPixmap(pixmap.scaled(
                    80, 80, Qt.AspectRatioMode.KeepAspectRatio))
                tabla.setCellWidget(row, 7, label)
            else:
                tabla.setItem(row, 7, QTableWidgetItem("Sin imagen"))

        except Exception as e:
            self._eliminar_fila(tabla, row)
            QMessageBox.warning(self.produccion, "Error", str(e))

    def conectar_validaciones(self):
        """Conectar señales de cambio para cada tipo de tabla"""
        # Fibra Óptica (ONT)
        self.produccion.tabla_FO.cellChanged.connect(
            lambda row, col: self.validar_numero_serie(row, col, "ONT")
        )

        # Cobre (MODEM)
        self.produccion.tabla_cobre.cellChanged.connect(
            lambda row, col: self.validar_numero_serie(row, col, "MODEM")
        )

        # Quejas (Consulta en ambas tablas)
        self.produccion.tabla_quejas.cellChanged.connect(
            self.validar_queja
        )
        self.produccion.tabla_a4.cellChanged.connect(
            lambda row, col: self.validar_numero_serie(row, col, "MODEM")
        )

    def validar_queja(self, row: int, col: int):
        """Validación especial para Quejas (consulta ONT y MODEM)"""
        if col != 4:
            return

        tabla = self.produccion.tabla_quejas
        numero_serie = tabla.item(row, col).text().strip()

        try:
            if not numero_serie:
                raise ValueError("Ingrese un número de serie")

            # Consultar equipo con filtros de área, COPE y técnico
            datos_ont = self.consultar_equipo_en_campo(numero_serie, "ONT")
            datos_modem = self.consultar_equipo_en_campo(numero_serie, "MODEM")

            if not datos_ont and not datos_modem:
                raise ValueError(
                    "Número de serie no encontrado en ONT ni MODEM"
                )

            # ---- Llenar datos automáticamente ----
            # Columna 5: Modelo (ONT o MODEM)
            modelo_item = QTableWidgetItem(
                datos_ont["modelo"] if datos_ont else datos_modem["modelo"])
            modelo_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Solo lectura
            tabla.setItem(row, 5, modelo_item)

            # Columna 7: Imagen (ONT o MODEM)
            imagen = datos_ont["imagen"] if datos_ont else datos_modem["imagen"]
            if imagen:
                label = QtWidgets.QLabel()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(imagen.tobytes())
                label.setPixmap(pixmap.scaled(
                    80, 80, Qt.AspectRatioMode.KeepAspectRatio))
                tabla.setCellWidget(row, 7, label)
            else:
                tabla.setItem(row, 7, QTableWidgetItem("Sin imagen"))
        except Exception as e:
            QMessageBox.warning(self.produccion, "Error", str(e))
            self._eliminar_fila(tabla, row)

    def validar_a4(self, row: int, col: int):
        """Validación especial para A4 (consulta en ambas tablas)"""
        if col != 4:
            return

        tabla = self.produccion.tabla_a4
        numero_serie = tabla.item(row, col).text().strip()

        try:
            if not numero_serie:
                raise ValueError("Ingrese un número de serie")

            # Consultar equipo con filtros de área, COPE y técnico
            datos = self.consultar_equipo_en_campo(numero_serie, "MODEM")

            if not datos:
                raise ValueError(
                    "MODEM no encontrado o no asignado a este Técnico"
                )

            # ---- Llenar datos automáticamente ----
            # Columna 5: Modelo (MODEM)
            modelo_item = QTableWidgetItem(QTableWidgetItem(datos["modelo"]))
            modelo_item.setFlags(Qt.ItemFlag.ItemIsEnabled)  # Solo lectura
            tabla.setItem(row, 5, modelo_item)

            # Columna 7: Imagen (ONT o MODEM)
            imagen = datos["imagen"]
            if imagen:
                label = QtWidgets.QLabel()
                pixmap = QtGui.QPixmap()
                pixmap.loadFromData(imagen.tobytes())
                label.setPixmap(pixmap.scaled(
                    80, 80, Qt.AspectRatioMode.KeepAspectRatio))
                tabla.setCellWidget(row, 7, label)
            else:
                tabla.setItem(row, 7, QTableWidgetItem("Sin imagen"))
        except Exception as e:
            QMessageBox.warning(self.produccion, "Error", str(e))
            self._eliminar_fila(tabla, row)
