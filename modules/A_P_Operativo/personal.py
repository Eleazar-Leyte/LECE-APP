from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
from DatabaseManager import DatabaseManager
from TableManager import TableManager
from modules.A_P_Operativo.a_personal import A_Personal


class Personal:

    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.personal = uic.loadUi("modules/A_P_Operativo/Personal.ui")
        self.personal.showMaximized()

        # Conexión a la base de datos 'Personal'
        self.db_manager_personal = DatabaseManager('Personal')

        # Conectamos los botones
        self.setup_connections()
        # Cargar áreas en el ComboBox
        self.cargar_areas()

    def setup_connections(self):
        # Conectar señales de botones a métodos correspondientes
        self.personal.btn_agregar.clicked.connect(self.agregarpersonal)
        self.personal.btn_eliminar.clicked.connect(self.eliminarpersonal)
        self.personal.btn_regresar.clicked.connect(self.regresar)
        self.personal.btn_cargarexcel.clicked.connect(self.cargarexcel)
        self.personal.btn_descargarexcel.clicked.connect(self.descargarexcel)
        self.personal.btn_guardar.clicked.connect(self.guardarpersonal)
        self.personal.btn_salir.clicked.connect(self.salir)
        self.personal.btn_buscar.clicked.connect(self.buscar)
        self.personal.btn_sincronizar.clicked.connect(self.sincronizar)
        self.personal.btn_leyaut.clicked.connect(self.descargarexcel_layout)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.personal.str_area.clear()  # Limpiar el ComboBox antes de cargar nuevas áreas
        self.personal.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
        try:
            if self.usuario_actual['rol'] == 'Directivo':
                # Consultar todas las áreas para los administradores
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                resultados = self.db_manager_personal.execute_query(query)
            else:
                # Consultar solo el área asignada para otros roles
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                resultados = self.db_manager_personal.execute_query(
                    query, (self.usuario_actual['area'],)
                )

            # Poblar el ComboBox con las áreas obtenidas
            if resultados:
                for resultado in resultados:
                    self.personal.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.personal, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            print(f"Error al cargar las áreas: {e}")
            QMessageBox.critical(
                self.personal, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.personal.str_area.currentText().strip()
        self.personal.str_cope.clear()  # Limpiar el ComboBox antes de cargar nuevos valores

        if not area_seleccionada or area_seleccionada == "":
            QMessageBox.warning(self.personal, "Advertencia",
                                "Por favor, seleccione un área.")
            return

        try:
            # Crear conexión a la base de datos "Área"
            db_manager_areas = DatabaseManager('Áreas')
            # Construir consulta para la tabla específica del área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = db_manager_areas.execute_query(query)
            # Poblar el ComboBox con los Copé obtenidos
            if resultados:
                for resultado in resultados:
                    self.personal.str_cope.addItem(resultado['Copé'])
            else:
                QMessageBox.information(
                    self.personal, "Información", "No se encontraron Copé disponibles para esta área."
                )

        except Exception as e:
            print(f"Error al actualizar los Copé: {e}")
            QMessageBox.critical(
                self.personal, "Error", f"Error al cargar los datos de Copé: {e}"
            )
        finally:
            # Cerrar la conexion a la base de datos "'Area" si se abrió
            if db_manager_areas and db_manager_areas.is_connected():
                db_manager_areas.close()

    def buscar(self):
        """
        Busca y muestra en la tabla los registros de Personal_O filtrados por Área y Copé,
        utilizando encabezados personalizados para la presentación.
        """
        area = self.personal.str_area.currentText().strip()
        cope = self.personal.str_cope.currentText().strip()

        COLUMN_MAPINGS = {
            "Número de Empleado": "id",
            "Apellido Paterno": "Apellido Paterno",
            "Apellido Materno": "Apellido Materno",
            "Nombre (s)": "Nombre (s)",
            "Expediente Técnico Cobre": "Expediente Técnico Cobre",
            "Expediente Técnico F.O.": "Expediente Técnico F.O.",
            "Área": "id_area",
            "COPE": "Cope",
            "N.S.S.": "N.S.S.",
            "R.F.C.": "R.F.C.",
            "Dirección": "Dirección"
        }
        if not area or not cope:
            QMessageBox.warning(self.personal, "Advertencia",
                                "Por favor, seleccione un Área y un Copé.")
            return

        try:
            # Obtener el id_area correspondiente al nombre del área seleccionada
            query_area_id = """
                SELECT id 
                FROM Areas 
                WHERE "Nombre del Área" = %s
            """
            area_result = self.db_manager_personal.execute_query(
                query_area_id, (area,))
            if not area_result:
                QMessageBox.critical(
                    self.personal, "Error",
                    f"No se encontró el área '{area}' en la base de datos."
                )
                return
            id_area = area_result[0]["id"]

            # Crear la lista de columnas requeridas en la consulta
            columnas = ", ".join(f'"{col}"' for col in COLUMN_MAPINGS.values())

            # Consulta SQL para filtrar por área y cope:
            query = f"""
                SELECT {columnas}
                FROM "personal_o"
                WHERE "id_area" = %s AND "Cope" = %s
            """

            resultados = self.db_manager_personal.execute_query(
                query, (id_area, cope))
            if resultados:
                TableManager.populate_table(
                    self.personal.tablapersonal, resultados, "Personal_O"
                )
            else:
                QMessageBox.information(
                    self.personal, "Información", "No se encontraron reslutados"
                )
        except Exception as e:
            QMessageBox.critical(self.personal, "Error", f"Error al realizar la búsqueda: {e}"
                                 )

    def sincronizar(self):
        try:
            self.buscar()  # Actualizar los datos visibles
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"No se pudo sincronizar los cambios: {e}")

    def cargarexcel(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self.personal, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)"
        )

        if archivo:
            try:
                # Leer el archivo Excel
                datos_excel = pd.read_excel(archivo)

                # Definir las columnas requeridas
                columnas_requeridas = [
                    "Id", "Apellido Paterno", "Apellido Materno", "Nombre", "Puesto"
                    "Expediente Técnico Cobre", "Expediente Técnico F.O.", "id_area",
                    "Cope", "N.S.S.", "R.F.C.", "Dirección"
                ]

                # Verificar que todas las columnas existan en el archivo
                if not all(col in datos_excel.columns for col in columnas_requeridas):
                    QMessageBox.warning(self.personal, "Advertencia",
                                        "El archivo no cumple con el formato requerido.")
                    return

                # Insertar los datos en la base de datos
                query = """
                    INSERT INTO Personal_O (
                        "id", "Apellido Paterno", "Apellido Materno", "Nombre (s)", "id_puesto",
                    "Expediente Técnico Cobre", "Expediente Técnico F.O.", "id_area",
                    "Cope", "N.S.S.", "R.F.C.", "Dirección"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                datos_a_insertar = [
                    (
                        fila["Id"], fila["Apellido Paterno"], fila["Apellido Materno"],
                        fila["Nombre"], fila["Puesto"], fila["Expediente Técnico Cobre"],
                        fila["Expediente Técnico F.O."], fila["id_area"], fila["Cope"],
                        fila["N.S.S."], fila["R.F.C."], fila["Dirección"]
                    )
                    for _, fila in datos_excel.iterrows()
                ]

                self.db_manager_personal.execute_many(query, datos_a_insertar)

                QMessageBox.information(self.personal, "Éxito",
                                        "Datos cargados exitosamente desde el archivo Excel.")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al cargar datos desde Excel: {e}")

    def descargarexcel_layout(self):
        archivo, _ = QFileDialog.getSaveFileName(
            self.personal, "Guardar layout de Excel", "", "Archivo Excel (*.xlsx)"
        )

        if archivo:
            try:
                # Crear un DataFrame con las columnas requeridas y sin datos
                columnas_requeridas = [
                    "Id", "Apellido Paterno", "Apellido Materno", "Nombre", "Puesto"
                    "Expediente Técnico Cobre", "Expediente Técnico F.O.", "id_area",
                    "Cope", "N.S.S.", "R.F.C.", "Dirección"
                ]
                df = pd.DataFrame(columns=columnas_requeridas)

                # Guardar el DataFrame como archivo Excel
                df.to_excel(archivo, index=False)

                QMessageBox.information(self.personal, "Éxito",
                                        "Layout descargado exitosamente.")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al descargar el layout: {e}")

    def descargarexcel(self):
        """
        Exporta los datos filtrados a un archivo Excel.
        """
        area = self.personal.str_area.currentText().strip()
        cope = self.personal.str_cope.currentText().strip()
        archivo, _ = QFileDialog.getSaveFileName(
            self.personal, "Guardar como", "", "Archivo Excel (*.xlsx)")

        if not archivo:
            return  # Usuario canceló la operación

        try:
            query = """
                SELECT "id", "Apellido Paterno", "Apellido Materno", "Nombre (s)", 
                    "Expediente Técnico Cobre", "Expediente Técnico F.O.", "id_area",
                    "COPE", "N.S.S.", "R.F.C.", "Dirección"
                FROM Personal_O
                WHERE id_area = (SELECT id FROM Areas WHERE "Nombre del Área" = %s)
                AND "Cope" = %s
            """
            # Ejecutar consulta para obtener datos filtrados
            resultados = self.db_manager_personal.execute_query(
                query, (area, cope))

            if not resultados:
                QMessageBox.information(self.personal, "Información",
                                        "No hay datos para exportar con los filtros aplicados.")
                return

            # Convertir resultados a DataFrame para exportar a Excel
            columnas = [
                "Número de Empleado", "Apellido Paterno", "Apellido Materno",
                "Nombre (s)", "Expediente Técnico Cobre", "Expediente Técnico F.O.",
                "Área", "Cope", "N.S.S.", "R.F.C.", "Dirección"
            ]
            datos = [list(row.values()) for row in resultados]
            df = pd.DataFrame(datos, columns=columnas)
            df.to_excel(archivo, index=False)

            QMessageBox.information(self.personal, "Éxito",
                                    "Datos exportados correctamente.")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al exportar datos a Excel: {e}")

    def guardarpersonal(self):
        print("Guardando información")

    def eliminarpersonal(self):
        """
        Elimina el registro seleccionado de la tabla y de la base de datos.
        """
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
            try:
                # Ejecutar la consulta de eliminación sin recuperar resultados
                query = "DELETE FROM Personal_O WHERE id = %s"
                self.db_manager_personal.execute_query(
                    query, (numero_empleado,), fetch=False)

                # Eliminar la fila de la tabla en la interfaz
                self.personal.tablapersonal.removeRow(selected_row)
                QMessageBox.information(self.personal, "Éxito",
                                        "Registro eliminado correctamente.")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"No se pudo eliminar el registro: {e}")

    def agregarpersonal(self):
        self.a_personal = A_Personal(self.usuario_actual)

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.personal.close()

    def salir(self):
        """
        Cierra la sesión del usuario actual y regresa a la ventana de inicio de sesión.
        """
        try:
            # Limpiar la variable usuario_actual
            self.usuario_actual.clear()

            # Cerrar la ventana actual
            self.personal.close()

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
