import sys
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QTableWidgetItem
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from DatabaseManager import DatabaseManager
from TableManager import TableManager


class R_Catalogo:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.ver_catalogo = uic.loadUi("modules/Almacenes/ver_Catalogo.ui")
        self.ver_catalogo.show()

        # Conexión a la base de datos
        self.db_almacen = DatabaseManager("Almacen_construcción")

        # Cargar funcionalidades
        self.cargar_botones()
        self.cargar_catalogo()

    def cargar_botones(self):
        """Conecta los botones a sus respectivas funciones."""
        self.ver_catalogo.btn_regresar.clicked.connect(self.regresar)
        self.ver_catalogo.btn_guardar.clicked.connect(
            self.sincronizar_catalogo)

    def cargar_catalogo(self):
        """Carga los datos del catálogo en la tabla `tabla_catalogo` sin duplicados."""
        try:
            # Consulta para obtener los datos únicos del catálogo
            query = """
                SELECT DISTINCT c.id_producto, c.codigo_ax, c.descripcion
                FROM catalogo c
                ORDER BY c.id_producto
            """
            resultados = self.db_almacen.execute_query(query)

            # Poblar la tabla con los datos obtenidos
            TableManager.populate_table(
                self.ver_catalogo.tabla_catalogo, resultados, "Catalogo"
            )

        except Exception as e:
            QMessageBox.critical(
                self.ver_catalogo, "Error", f"Error al cargar el catálogo: {e}"
            )

    def sincronizar_catalogo(self):
        """
        Sincroniza el catálogo de artículos estándar con la base de datos
        para asegurarse de que todos los modelos de ONT y MODEM estén registrados.
        """
        try:
            # Obtener el máximo codigo_ax actual
            query_max_codigo_ax = """
                SELECT COALESCE(MAX(CAST(codigo_ax AS INTEGER)), 0) AS max_codigo_ax
                FROM articulos_estandar
                WHERE codigo_ax ~ '^\d+$'
            """
            resultado_max = self.db_almacen.execute_query(query_max_codigo_ax)
            max_codigo_ax = int(resultado_max[0]["max_codigo_ax"])

            # Sincronizar ONT
            query_ont = f"""
                INSERT INTO articulos_estandar (codigo_ax, nombre_articulo, unidad)
                SELECT DISTINCT 
                    '{max_codigo_ax}'::INTEGER + ROW_NUMBER() OVER (), 
                    CONCAT('ONT ', modelo), 
                    'pieza'
                FROM "ONT en Campo"
                ON CONFLICT (codigo_ax) DO NOTHING
            """
            self.db_almacen.execute_query(query_ont, fetch=False)

            # Sincronizar MODEM
            query_modem = f"""
                INSERT INTO articulos_estandar (codigo_ax, nombre_articulo, unidad)
                SELECT DISTINCT 
                    '{max_codigo_ax}'::INTEGER + ROW_NUMBER() OVER (), 
                    CONCAT('MODEM ', modelo), 
                    'pieza'
                FROM modem_en_campo
                ON CONFLICT (codigo_ax) DO NOTHING
            """
            self.db_almacen.execute_query(query_modem, fetch=False)

            QMessageBox.information(
                self.ver_catalogo, "Éxito", "El catálogo ha sido sincronizado."
            )
            self.cargar_catalogo()

        except Exception as e:
            QMessageBox.critical(
                self.ver_catalogo, "Error", f"Error al sincronizar el catálogo: {e}"
            )

    def regresar(self):
        """Cierra la ventana del catálogo."""
        self.ver_catalogo.close()
