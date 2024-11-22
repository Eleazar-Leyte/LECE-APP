import sqlite3
from DatabaseManager import DatabaseManager
from TableManager import TableManager
import pandas as pd
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from modules.a_personal import A_Personal


class Personal:
    def __init__(self):
        self.personal = uic.loadUi("modules/Personal.ui")
        self.personal.show()
        self.bottons()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("personal.db")
        self.db_areas = DatabaseManager("Areas.db")

        # Lista temporal para almacenar IDs de eliminados
        self.eliminados_temporales = []

        # Variable temporal para almacenar los resultados de la búsqueda
        self.resultados_temporales = []

        # Cargar áreas en el ComboBox
        self.cargar_areas()

    def bottons(self):
        # Caramos la botonera de la Ui
        self.personal.btn_agregar.clicked.connect(self.agregarpersonal)
        self.personal.btn_eliminar.clicked.connect(self.eliminarpersonal)
        self.personal.btn_regresar.clicked.connect(self.regresar)
        self.personal.btn_cargarexcel.clicked.connect(self.cargarexcel)
        self.personal.btn_descargarexcel.clicked.connect(self.descargarexcel)
        self.personal.btn_guardar.clicked.connect(self.guardarpersonal)
        self.personal.btn_salir.clicked.connect(self.salir)
        self.personal.btn_buscar.clicked.connect(self.buscar)
        self.personal.btn_sincronizar.clicked.connect(self.sincronizar)
        self.personal.str_area.currentIndexChanged.connect(
            self.actualizar_cope)

    def cargar_areas(self):
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        try:
            tablas = self.db_areas.execute_query(query)
            self.personal.str_area.clear()
            for tabla in tablas:
                self.personal.str_area.addItem(tabla["name"])
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al cargar las áreas: {e}")

    def actualizar_cope(self):
        area_seleccionada = self.personal.str_area.currentText()
        if area_seleccionada:
            query = f"SELECT DISTINCT Copé FROM {area_seleccionada}"
            try:
                resultados = self.db_areas.execute_query(query)
                self.personal.str_cope.clear()
                for resultado in resultados:
                    self.personal.str_cope.addItem(resultado["Copé"])
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al cargar los datos de Cope: {e}")

    def buscar(self):
        area = self.personal.str_area.currentText()
        cope = self.personal.str_cope.currentText()

        if area and cope:
            query = "SELECT * FROM Personal_O WHERE Área = ? AND Cope = ?"
            try:
                self.resultados_temporales = self.db_personal.execute_query(
                    query, (area, cope))
                if self.resultados_temporales:
                    TableManager.populate_table(
                        self.personal.tablapersonal,
                        self.resultados_temporales,
                        "Personal_O"
                    )
                else:
                    QMessageBox.information(self.personal, "Información",
                                            "No se encontraron resultados.")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al realizar la búsqueda: {e}")

    def sincronizar(self):
        try:
            if self.eliminados_temporales:
                query = "DELETE FROM Personal_O WHERE Id = ?"
                for id_empleado in self.eliminados_temporales:
                    self.db_personal.execute_query(query, (id_empleado,))
                self.eliminados_temporales = []  # Limpia los eliminados temporales

            self.buscar()  # Actualizar los datos visibles
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"No se pudo sincronizar los cambios: {e}")

    def cargarexcel(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self.personal, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)")

        if archivo:
            try:
                datos_excel = pd.read_excel(archivo)
                columnas_requeridas = [
                    "Número de Empleado", "Apellido Paterno", "Apellido Materno",
                    "Nombre (s)", "Expediente Técnico Cobre", "Expediente Técnico F.O.",
                    "Área", "Cope", "N.S.S.", "R.F.C.", "Dirección"
                ]

                if not all(col in datos_excel.columns for col in columnas_requeridas):
                    QMessageBox.warning(self.personal, "Advertencia",
                                        "El archivo no cumple con los requisitos.")
                    return

                query = """
                    INSERT INTO Personal_O (
                        Id, `Apellido Paterno`, `Apellido Materno`, `Nombre (s)`,
                        `Expediente Técnico Cobre`, `Expediente Técnico F.O.`,
                        `Área`, `Cope`, `N.S.S.`, `R.F.C.`, `Dirección`
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                for _, fila in datos_excel.iterrows():
                    datos = tuple(fila[col] for col in columnas_requeridas)
                    self.db_personal.execute_query(query, datos)

                QMessageBox.information(self.personal, "Éxito",
                                        "Datos cargados exitosamente desde el archivo Excel.")
                self.sincronizar()
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al cargar datos desde Excel: {e}")

    def descargarexcel(self):
        area = self.personal.str_area.currentText()
        cope = self.personal.str_cope.currentText()
        archivo, _ = QFileDialog.getSaveFileName(
            self.personal, "Guardar como", "", "Archivo Excel (*.xlsx)")

        if archivo:
            try:
                query = "SELECT * FROM Personal_O WHERE Área = ? AND Cope = ?"
                resultados = self.db_personal.execute_query(
                    query, (area, cope)).fetchall()

                if not resultados:
                    QMessageBox.information(self.personal, "Información",
                                            "No hay datos para exportar con los filtros aplicados.")
                    return

                columnas = [
                    "Número de Empleado", "Apellido Paterno", "Apellido Materno",
                    "Nombre (s)", "Expediente Técnico Cobre", "Expediente Técnico F.O.",
                    "Área", "Cope", "N.S.S.", "R.F.C.", "Dirección"
                ]
                df = pd.DataFrame(resultados, columns=columnas)
                df.to_excel(archivo, index=False)

                QMessageBox.information(self.personal, "Éxito",
                                        "Datos exportados correctamente.")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al exportar datos a Excel: {e}")

    def guardarpersonal(self):
        print("Guardando información")

    def eliminarpersonal(self):
        selected_row = self.personal.tablapersonal.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self.personal, "Advertencia",
                                "Por favor, seleccione un registro para eliminar.")
            return

        numero_empleado_item = self.personal.tablapersonal.item(
            selected_row, 0)
        if not numero_empleado_item:
            QMessageBox.warning(self.personal, "Advertencia",
                                "No se pudo obtener la información del empleado.")
            return

        numero_empleado = numero_empleado_item.text()
        confirmacion = QMessageBox.question(
            self.personal, "Eliminar personal",
            f"¿Está seguro de que desea eliminar el registro del empleado con Id: {numero_empleado}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            self.eliminados_temporales.append(numero_empleado)
            self.personal.tablapersonal.removeRow(selected_row)
            QMessageBox.information(self.personal, "Éxito",
                                    "Registro marcado para eliminación. Presione 'Sincronizar' para aplicar los cambios.")

    def agregarpersonal(self):
        self.a_personal = A_Personal()

    def regresar(self):
        from modules.menu import Pestaña1
        self.pestaña1 = Pestaña1()
        self.personal.close()

    def salir(self):
        self.db_personal.close()
        self.db_areas.close()
        self.personal.close()
