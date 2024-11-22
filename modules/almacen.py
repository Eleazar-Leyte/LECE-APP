import sqlite3
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QMessageBox

from DatabaseManager import DatabaseManager
from modules.r_almacen import R_Almacen
from modules.r_modem import R_MODEM
from modules.r_ont import R_ont
from TableManager import TableManager  # Importar el nuevo módulo


class Almacen():
    def __init__(self):
        self.almacen = uic.loadUi("modules/Almacen.ui")
        self.almacen.show()
        self.botones()

        # Inicializamos las conexiones a las bases de datos
        self.db_areas = DatabaseManager("Areas.db")
        self.db_tablas = DatabaseManager("Almacen_construcción.db")

        self.cargar_areas()

    def botones(self):
        self.almacen.btn_regresar.clicked.connect(self.regresar)
        self.almacen.btn_salir.clicked.connect(self.salir)
        self.almacen.btn_buscar.clicked.connect(self.buscar_tabla)
        self.almacen.btn_ont.clicked.connect(self.ingresar_ONT)
        self.almacen.btn_modem.clicked.connect(self.ingresar_modem)
        self.almacen.btn_almacen.clicked.connect(self.ingresar_almacen)
        # self.almacen.btn_catalogo.clicked.connect(self.ver_catalogo)
        # self.almacen.btn_movalmacen.clicked.connect(self.moveralmacen)
        # self.almacen.btn_almacentecnico.clicked.connect(self.surtir_P_O)
        # self.almacen.btn_guardar.clicked.connect(self.guardar)
        self.almacen.str_area.currentIndexChanged.connect(self.actualizar_cope)

    def regresar(self):
        from modules.menu import Pestaña1

        self.pestaña1 = Pestaña1()
        self.almacen.show()
        self.almacen.close()

    def salir(self):
        self.almacen.close()

    def cargar_areas(self):
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        try:
            tablas = self.db_areas.execute_query(query).fetchall()
            self.almacen.str_area.clear()
            for tabla in tablas:
                self.almacen.str_area.addItem(tabla[0])
        except sqlite3.Error as e:
            QMessageBox.critical(
                self.almacen, "Error", f"Error al cargar las áreas: {e}")

    def actualizar_cope(self):
        area_seleccionada = self.almacen.str_area.currentText()
        if area_seleccionada:
            query = f"SELECT DISTINCT Copé FROM {area_seleccionada}"
            try:
                resultados = self.db_areas.execute_query(query).fetchall()
                self.almacen.str_cope.clear()
                for resultado in resultados:
                    self.almacen.str_cope.addItem(resultado[0])
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self.almacen, "Error", f"Error al cargar los copes: {e}")

    def buscar_tabla(self):
        area = self.almacen.str_area.currentText()
        cope = self.almacen.str_cope.currentText()
        tabla = self.almacen.str_tabla.currentText()

        if not tabla:
            QMessageBox.warning(
                self.almacen, "Advertencia", "Por favor seleccione una tabla válida"
            )
            return
        # Escapamos las nombres de las columnas y tablas en comillas dobles
        if tabla in ["ONT", "MODEM"]:
            campo_area = '"Area"'
            campo_cope = '"Centro de trabajo"'
        elif tabla == "Almacén":
            campo_area = '"Area"'
            campo_cope = '"Cope"'
        elif tabla == "Catalogo":
            campo_area = '"Area"'
            campo_cope = '"Cope"'
        elif tabla == "ONT en campo":
            campo_area = '"Area"'
            campo_cope = '"Centro de Trabajo"'
        else:
            QMessageBox.warning(
                self.almacen, "Advertencia", "Tabla seleccionada no válida"
            )
            return

        query = f'SELECT * FROM "{tabla}" WHERE {campo_area} = ? AND {campo_cope} = ?'
        try:
            resultados = self.db_tablas.execute_query(
                query, (area, cope)).fetchall()

            # Usar TableManager para dibujar la tabla
            TableManager.populate_table(
                self.almacen.tablaalmacen, resultados, tabla)
        except sqlite3.Error as e:
            QMessageBox.critical(
                self.almacen, "Error", f"Error al realizar la búsqueda: {e}"
            )

    def ingresar_ONT(self):
        self.r_ont = R_ont()

    def ingresar_modem(self):
        self.r_modem = R_MODEM()

    def ingresar_almacen(self):
        self.r_almacen = R_Almacen()
