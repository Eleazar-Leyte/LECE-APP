from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

from DatabaseManager import DatabaseManager
from modules.Almacenes.m_almacen import M_Almacen
from modules.Almacenes.r_almacen import R_Almacen
from modules.Almacenes.r_catalogo import R_Catalogo
from modules.Almacenes.r_modem import R_MODEM
from modules.Almacenes.r_ont import R_ont
from modules.Almacenes.surtir_P_O import Surtir_P_O
from TableManager import TableManager


class Almacen():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.almacen = uic.loadUi("modules/Almacenes/Almacen.ui")
        self.almacen.showMaximized()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")

        self.botones()
        self.cargar_areas()

    def botones(self):
        self.almacen.btn_regresar.clicked.connect(self.regresar)
        self.almacen.btn_salir.clicked.connect(self.salir)
        self.almacen.btn_buscar.clicked.connect(self.buscar_tabla)
        self.almacen.btn_ont.clicked.connect(self.ingresar_ONT)
        self.almacen.btn_modem.clicked.connect(self.ingresar_modem)
        self.almacen.btn_almacen.clicked.connect(self.ingresar_almacen)
        self.almacen.btn_catalogo.clicked.connect(self.ver_catalogo)
        self.almacen.btn_movalmacen.clicked.connect(self.mover_almacen)
        self.almacen.btn_almacentecnico.clicked.connect(self.surtir_P_O)
        # self.almacen.btn_guardar.clicked.connect(self.guardar)

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.almacen.close()

    def salir(self):
        """
        Cierra la sesión del usuario actual y regresa a la ventana de inicio de sesión.
        """
        try:
            # Limpiar la variable usuario_actual
            self.usuario_actual.clear()

            # Cerrar la ventana actual
            self.almacen.close()

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
        self.almacen.str_area.clear()
        self.almacen.str_area.currentIndexChanged.connect(self.actualizar_cope)
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
                    self.almacen.str_area.addItem(resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.almacen, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.almacen, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.almacen.str_area.currentText().strip()
        self.almacen.str_cope.clear()

        if not area_seleccionada:
            QMessageBox.warning(
                self.almacen, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.almacen,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.almacen.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.almacen,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.almacen, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def buscar_tabla(self):
        """
        Busca y carga datos en la tabla de la interfaz, aplicando agrupación solo para la tabla 'almacen'.
        """
        area = self.almacen.str_area.currentText().strip()
        cope = self.almacen.str_cope.currentText().strip()
        tabla_combo = self.almacen.str_tabla.currentText().strip()

        # Mapeo de tablas
        tabla_mapeo = {
            "Almacén": "almacen",
            "ONT": "ont",
            "MODEM": "modem"
        }

        COLUMN_MAPPINGS = {
            "Almacén": {
                "Descripción": "descripcion",
                "Código AX": "codigo_ax",
                "Unidad": "unidad",
                "Cantidad": "total_cantidad",
                # Usar MIN para que sea consistente
                "Número de Serie": "numeros_de_serie",
                "Área": "area",
                "COPE": "cope"
            },
            "MODEM": {
                "Número de Serie": "Numero de Serie",
                "Cantidad": "cantidad",
                "Unidad": "unidad",
                "Modelo": "modelo",
                "Área": "area",
                "Centro de Trabajo": "Centro de Trabajo",
                "Ubicación": "ubicacion",
                "Imagen": "imagen"
            },
            "ONT": {
                "Número de Serie": "Numero de Serie",
                "Cantidad": "cantidad",
                "Unidad": "unidad",
                "Modelo": "modelo",
                "Área": "area",
                "Centro de Trabajo": "Centro de Trabajo",
                "Ubicación": "ubicacion",
                "Imagen": "imagen"
            }
        }

        tabla = tabla_mapeo.get(tabla_combo)
        if not tabla or not area or not cope:
            QMessageBox.warning(
                self.almacen,
                "Advertencia",
                "Por favor seleccione un Área, un Copé y una tabla válida.",
            )
            return

        campo_area = '"area"'
        campo_cope = (
            '"Centro de Trabajo"' if tabla in ["ont", "modem"] else '"cope"'
        )

        # Obtener columnas requeridas
        column_mapping = COLUMN_MAPPINGS.get(tabla_combo)
        if not column_mapping:
            QMessageBox.critical(
                self.almacen, "Error", f"Columnas no definidas para la tabla {tabla_combo}."
            )
            return

        columnas = ", ".join(f'"{col}"' for col in column_mapping.values())
        query = ""

        if tabla == "almacen":
            # Agrupación para la tabla Almacén
            query = f"""
                SELECT "descripcion", "unidad", SUM("cantidad") AS total_cantidad, STRING_AGG("Numero de Serie", ', ') AS numeros_de_serie,"area", "cope"
                FROM "{tabla}"
                WHERE {campo_area} = %s AND {campo_cope} = %s
                GROUP BY "descripcion", "unidad", "area", "cope";
            """
        else:
            # Consulta estándar para MODEM y ONT
            query = f"""
                SELECT {columnas}
                FROM "{tabla}"
                WHERE {campo_area} = %s AND {campo_cope} = %s
            """

        try:
            if not self.db_almacen.is_connected():
                self.db_almacen.connect()

            resultados = self.db_almacen.execute_query(query, (area, cope))
            if resultados:
                TableManager.populate_table(
                    self.almacen.tablaalmacen, resultados, tabla_combo
                )
            else:
                QMessageBox.information(
                    self.almacen, "Información", "No se encontraron resultados."
                )
        except Exception as e:
            QMessageBox.critical(
                self.almacen, "Error", f"Error al realizar la búsqueda: {e}"
            )

    def ingresar_ONT(self):
        self.r_ont = R_ont(self.usuario_actual)

    def ingresar_modem(self):
        self.r_modem = R_MODEM(self.usuario_actual)

    def ingresar_almacen(self):
        self.r_almacen = R_Almacen(self.usuario_actual)

    def ver_catalogo(self):
        self.r_catalogo = R_Catalogo(self.usuario_actual)

    def mover_almacen(self):
        self.m_almacen = M_Almacen(self.usuario_actual)

    def surtir_P_O(self):
        self.surtir_p_o = Surtir_P_O(self.usuario_actual)
