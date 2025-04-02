from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

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

        self.botones()
        self.cargar_areas()

    def botones(self):
        self.produccion.btn_regresar.clicked.connect(self.regresar)
        self.produccion.btn_salir.clicked.connect(self.salir)

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

    def iniciar_tablas(self):
        """
        Cargar las columnas usando el TableManger.py
        """
        TableManager.populate_table(
            self.produccion.tabla_FO,
            []
            "Producción F.O."
        )
