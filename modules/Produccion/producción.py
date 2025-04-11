from functools import partial
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6 import uic, QtWidgets, QtCore, QtGui
from psycopg2 import Binary, sql
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
        self.produccion.btn_guardar.clicked.connect(self.guardar_produccion)

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
        """
        Implementación base para agregar filas
        """
        tabla.blockSignals(True)  # Bloquear señales para evitar bucles
        try:
            row = tabla.rowCount()  # Obtener nueva posición de fila
            tabla.insertRow(row)

            # Crear e inicializar items para todas las columnas
            for col in range(tabla.columnCount()):
                if tabla.item(row, col) is None:
                    item = QTableWidgetItem("")
                    item.setFlags(Qt.ItemFlag.ItemIsEnabled |
                                  Qt.ItemFlag.ItemIsEditable)
                    tabla.setItem(row, col, item)
        finally:
            tabla.blockSignals(False)
        self.actualizar_estado_combo()

    def _eliminar_fila(self, tabla, row=None):
        """Implementación base para eliminar filas"""
        if row is None:
            row = tabla.currentRow()
        if row != -1:
            tabla.blockSignals(True)
            try:
                tabla.removeRow(row)
            finally:
                tabla.blockSignals(False)
        self.actualizar_estado_combo()

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
            nombre_tecnico = self.produccion.str_exptec.currentText().strip()

            if not all([area, cope, nombre_tecnico]):
                raise ValueError(
                    "Complete todos los filtros (Área, COPE y Técnico)")

            # Determinar tabla y columnas según el tipo de equipo
            if tipo_equipo == "ONT":
                return self._consultar_en_tabla(
                    tabla="\"ONT en Campo\"",
                    columna_serie="\"Numero de Serie\"",
                    numero_serie=numero_serie,
                    area=area,
                    cope=cope,
                    tecnico=nombre_tecnico
                )
            elif tipo_equipo == "MODEM":
                return self._consultar_en_tabla(
                    tabla="modem_en_campo",
                    columna_serie="\"Numero de Serie\"",
                    numero_serie=numero_serie,
                    area=area,
                    cope=cope,
                    tecnico=nombre_tecnico
                )
            elif tipo_equipo == "QUEJAS":
                # Busca primero en ONT y despues en MODEM
                return (self._consultar_en_tabla("\"ONT en Campo\"", "\"Numero de Serie\"",
                                                 numero_serie, area, cope, nombre_tecnico) or
                        self._consultar_en_tabla(
                    "modem_en_campo", "\"Numero de Serie\"", numero_serie, area, cope, nombre_tecnico)
                )
            elif tipo_equipo == "A4":
                return self._consultar_en_tabla(
                    tabla="modem_en_campo",
                    columna_serie="\"Numero de Serie\"",
                    numero_serie=numero_serie,
                    area=area,
                    cope=cope,
                    tecnico=nombre_tecnico
                )
            else:
                raise ValueError("Tipo de equipo no válido")

        except Exception as e:
            raise RuntimeError(f"Error al consultar {tipo_equipo}: {str(e)}")

    def _consultar_en_tabla(self, tabla: str, columna_serie: str, numero_serie: str, area: str, cope: str, tecnico: str) -> dict:
        """
        Función auxiliar para consultar un equipo en su tabla correspondiente
        filtrando por número de serie, área, COPE y técnico.
        """

        query = f"""
                SELECT modelo, imagen, "Fecha de Registro" 
                FROM {tabla}
                WHERE 
                    {columna_serie} = %s AND
                    area = %s AND
                    "Centro de Trabajo" = %s AND
                    "Expediente Técnico" = %s
            """
        params = (numero_serie, area, cope, tecnico)

        resultado = self.db_almacen.execute_query(query, params)
        return resultado[0] if resultado else None

    def validar_numero_serie(self, row: int, col: int, tipo_equipo: str):
        """Valida el número de serie y completa datos automáticamente con filtros"""
        if col != 4:  # Solo actuar en columna de número de serie
            return

        tabla = self.obtener_tabla_actual()
        numero_serie = tabla.item(row, col).text().strip()

        try:
            if not numero_serie:
                raise ValueError("Ingrese un número de serie")

            # Mapeo dinámico de tablas
            tabla_bd = {
                "ONT": "fibra_optica",
                "MODEM": "cobre",
                "QUEJAS": "quejas",
                "A4": "a4_incentivos"
            }.get(tipo_equipo, "fibra_optica")

            # Verificar unicidad
            folio = tabla.item(row, 0).text().strip()
            if self.folio_o_serie_existen(folio, numero_serie,  tabla_bd):
                raise ValueError(
                    f"Folio/serie ya existen en {tabla_bd.replace('_', ' ')}")

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
        """Conectar todas las validaciones a las columnas correspondientes"""
        # Conexión para todas las tablas
        tablas = [
            (self.produccion.tabla_FO, "ONT"),
            (self.produccion.tabla_cobre, "MODEM"),
            (self.produccion.tabla_quejas, "QUEJAS"),
            (self.produccion.tabla_a4, "A4")
        ]

        for tabla, tipo in tablas:
            tabla.cellChanged.connect(
                lambda row, col, t=tabla, tt=tipo: self._validar_fila_completa(
                    row, col, t, tt)
            )

    def _validar_fila_completa(self, row: int, col: int, tabla, tipo: str):
        """
        Aplica todas las validaciones para cada edición de celda
        """
        try:
            if row >= tabla.rowCount():
                return

            # Validar teléfono (columna 1)
            if col == 1:
                telefono = tabla.item(row, col).text()
                if not self.validar_telefono(telefono):
                    raise ValueError(
                        "Teléfono debe tener 10 dígitos numéricos")

            # Formatear tipo de tarea (columna 2)
            elif col == 2:
                item = tabla.item(row, col)
                item.setText(self.formatear_tipo_tarea(item.text()))

            # Validar número de serie (columna 4)
            elif col == 4 and tipo in ["ONT", "MODEM", "QUEJAS", "A4"]:
                self.validar_numero_serie(row, col, tipo)

            if col in (0, 4):
                if self.verificar_duplicados_tabla(tabla, row, 0, 4):
                    raise ValueError(
                        "Folio/Serie duplicados en la tabla.")

        except Exception as e:
            QMessageBox.warning(self.produccion, "Error de validación", str(e))
            tabla.item(row, col).setText("")

    def guardar_produccion(self):
        """
        Guardar los datos de todas las tablas en la base de datos
        """
        try:
            # Obtener filas de los ComboBox
            area = self.produccion.str_area.currentText().strip()
            cope = self.produccion.str_cope.currentText().strip()
            exp_tecnico = self.produccion.str_exptec.currentText().strip()

            if not all([area, cope, exp_tecnico]):
                raise ValueError(
                    "Complete todos los filtros (Área, COPE y Técnico)")

            tablas = [
                (self.produccion.tabla_FO, "fibra_optica"),
                (self.produccion.tabla_cobre, "cobre"),
                (self.produccion.tabla_quejas, "quejas"),
                (self.produccion.tabla_a4, "a4_incentivos")
            ]
            errores = []
            for tabla, nombre_bd in tablas:
                try:
                    if tabla.rowCount() > 0:
                        self._guardar_tabla(
                            tabla, nombre_bd, area, cope, exp_tecnico)
                except Exception as e:
                    errores.append(f"Error en {nombre_bd}: {str(e)}")
            if not errores:
                QMessageBox.information(
                    self.produccion, "Éxito", f"La producción del técnico {exp_tecnico} se guardo correctamente")
            self.limpiar_tablas()
        except Exception as e:
            QMessageBox.critical(self.produccion, "Error",
                                 f"Error al guardar: {str(e)}")

    def _guardar_tabla(self, tabla, nombre_tabla: str, area: str, cope: str, exp_tecnico: str):
        """
        Guardar información con implementaciones de seguridad de SQL y una estructura dinámica.
        """
        mapeo_columnas = {
            "fibra_optica": {
                0: "folio_pisa",
                1: "telefono_asignado",
                2: "tipo_tarea",
                3: "cantidad_mts",
                4: "numero_de_serie",
                5: "modelo_ont",
                6: "fecha_posteo",
                7: "imagen"
            },
            "cobre": {
                0: "folio_pisa",
                1: "telefono_asignado",
                2: "tipo_tarea",
                3: "cantidad_mts",
                4: "numero_serie",
                5: "modelo_modem",
                6: "fecha_posteo",
                7: "imagen"
            },
            "quejas": {
                0: "folio_pisa",
                1: "telefono_asignado",
                2: "tipo_tarea",
                3: "cantidad_mts",
                4: "numero_serie",
                5: "modelo",
                6: "fecha_posteo",
                7: "imagen"
            },
            "a4_incentivos": {
                0: "folio_pisa",
                1: "telefono_asignado",
                2: "tipo_tarea",
                3: "cantidad_mts",
                4: "numero_serie",
                5: "modelo_modem",
                6: "fecha_posteo",
                7: "imagen"
            },
        }
        for fila in range(tabla.rowCount()):
            try:
                datos = {}
                for col in mapeo_columnas[nombre_tabla].keys():
                    item = tabla.item(fila, col)
                    # Manejar celdas vacías
                    valor = item.text().strip() if item else ""
                    datos[mapeo_columnas[nombre_tabla][col]] = valor

                # Manejar imagen
                imagen_widget = tabla.cellWidget(fila, 7)
                datos["imagen"] = self._obtener_imagen_bytes(imagen_widget)

                # Añadir campos comunes
                datos.update({
                    "exp_tecnico": exp_tecnico,
                    "area": area,
                    "cope": cope
                })

                # Validar teléfono solo si es obligatorio
                if nombre_tabla == "fibra_optica":
                    if not self.validar_telefono(datos["telefono_asignado"]):
                        raise ValueError(f"Teléfono inválido en fila {fila+1}")

                # Validar duplicados
                serie = datos.get("numero_de_serie") or datos.get(
                    "numero_serie")
                if self.folio_o_serie_existen(datos["folio_pisa"], serie, nombre_tabla):
                    raise ValueError(
                        f"Folio/Serie ya existen en {nombre_tabla}")

                # Construir query
                columns = [sql.Identifier(k) for k in datos.keys()]
                values = [sql.Placeholder() for _ in datos.values()]
                query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
                    table=sql.Identifier(nombre_tabla),
                    fields=sql.SQL(', ').join(columns),
                    values=sql.SQL(', ').join(values)
                )
                self.db_produccion.execute_query(
                    query, tuple(datos.values()), fetch=False)

            except Exception as e:
                raise RuntimeError(f"Fila {fila+1}: {str(e)}")

    def _obtener_imagen_bytes(self, widget: QtWidgets.QLabel) -> bytes:
        """
        Convierte una imagen de un QLabel a bytes para almacenar en la base de datos
        """
        if widget and widget.pixmap():
            pixmap = widget.pixmap()
            buffer = QtCore.QBuffer()
            buffer.open(QtCore.QBuffer.OpenModeFlag.ReadWrite)
            pixmap.save(buffer, "PNG")
            return Binary(buffer.data())
        return None

    def limpiar_tablas(self):
        """
        Limpia todas las tablas y restablece los ComboBoxes
        """
        for tabla in [self.produccion.tabla_FO, self.produccion.tabla_cobre,
                      self.produccion.tabla_quejas, self.produccion.tabla_a4]:
            tabla.setRowCount(0)
        self.actualizar_estado_combo()

    def validar_telefono(self, telefono: str) -> bool:
        """Valida que el teléfono tenga 10 dígitos numéricos."""
        return telefono.isdigit() and len(telefono) == 10

    def folio_o_serie_existen(self, folio: str, serie: str, tabla_bd: str) -> bool:
        """
        Verifica si el folio o serie ya existen en la base de datos.
        """
        tablas_verificar = {
            "fibra_optica": ["fibra_optica", "quejas", "a4_incentivos"],
            "cobre": ["cobre", "a4_incentivos", "quejas"],
            # Verifica en ONT, MODEM y Quejas
            "quejas": ["fibra_optica", "cobre", "quejas"],
            "a4_incentivos": ["a4_incentivos", "fibra_optica", "cobre", "quejas"]
        }.get(tabla_bd, [])

        for tabla in tablas_verificar:
            col_serie = "numero_de_serie" if tabla == "fibra_optica" else "numero_serie"
            query = f"""
                SELECT EXISTS (
                    SELECT 1 FROM {tabla}
                    WHERE folio_pisa = %s OR {col_serie} = %s
                )
            """
            resultado = self.db_produccion.execute_query(query, (folio, serie))
            if resultado[0]['exists']:
                return True
        return False

    def formatear_tipo_tarea(self, texto: str) -> str:
        """Convierte el texto a mayúsculas y elimina caracteres no permitidos."""
        # Permite letras, números y guiones
        texto_limpio = ''.join(c for c in texto.upper()
                               if c.isalnum() or c in ('-', '_'))
        return texto_limpio

    def verificar_duplicados_tabla(self, tabla, fila_actual: int, col_folio: int, col_serie: int) -> bool:
        """Verifica si el folio/serie ya existen en otras filas de la tabla"""
        # Verificar si la fila actual existe
        if fila_actual >= tabla.rowCount():
            return False

        # Obtener items de folio y serie
        folio_item = tabla.item(fila_actual, col_folio)
        serie_item = tabla.item(fila_actual, col_serie)

        # Si alguno de los items no existe, retornar False
        if not folio_item or not serie_item:
            return False

        folio = folio_item.text().strip()
        serie = serie_item.text().strip()

        for fila in range(tabla.rowCount()):
            if fila == fila_actual:
                continue
            # Obtener items de otras filas
            folio_existente_item = tabla.item(fila, col_folio)
            serie_existente_item = tabla.item(fila, col_serie)

            folio_existente = folio_existente_item.text(
            ).strip() if folio_existente_item else ""
            serie_existente = serie_existente_item.text(
            ).strip() if serie_existente_item else ""

            if folio_existente == folio or serie_existente == serie:
                return True
        return False
