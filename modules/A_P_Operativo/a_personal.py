import sqlite3

from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox

from DatabaseManager import DatabaseManager


class A_Personal():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.a_personal = uic.loadUi("modules/A_P_Operativo/A_personal.ui")
        self.a_personal.show()

        # Conectamos los botones de la Ui
        self.botones()

        # Conexión a la base de datos 'Personal'
        self.db_manager_personal = DatabaseManager('Personal')

        # Conexión a la base de datos áreas
        self.conn_areas = sqlite3.connect("Areas.db")
        self.cursor_areas = self.conn_areas.cursor()

        # Cargamos el ComboBox de Áreas
        self.cargar_areas()

    def botones(self):
        self.a_personal.btn_guardar.clicked.connect(self.agregar_personal_o)
        self.a_personal.btn_regresar.clicked.connect(self.regresar)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.a_personal.str_area.clear()  # Limpiar el ComboBox antes de cargar nuevas áreas
        self.a_personal.str_area.currentIndexChanged.connect(
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
                    self.a_personal.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.a_personal, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            print(f"Error al cargar las áreas: {e}")
            QMessageBox.critical(
                self.a_personal, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.a_personal.str_area.currentText().strip()
        # Limpiar el ComboBox antes de cargar nuevos valores
        self.a_personal.str_cope.clear()

        if not area_seleccionada or area_seleccionada == "":
            QMessageBox.warning(self.a_personal, "Advertencia",
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
                    self.a_personal.str_cope.addItem(resultado['Copé'])
            else:
                QMessageBox.information(
                    self.a_personal, "Información", "No se encontraron Copé disponibles para esta área."
                )

        except Exception as e:
            print(f"Error al actualizar los Copé: {e}")
            QMessageBox.critical(
                self.a_personal, "Error", f"Error al cargar los datos de Copé: {e}"
            )
        finally:
            # Cerrar la conexion a la base de datos "'Area" si se abrió
            if db_manager_areas and db_manager_areas.is_connected():
                db_manager_areas.close()

    def agregar_personal_o(self):
        """
        Agrega un nuevo registro de personal operativo a la base de datos.
        """
        try:
            # Leer datos desde la interfaz gráfica
            a_paterno = self.a_personal.ln_apaterno.text().strip().upper()
            a_materno = self.a_personal.ln_materno.text().strip().upper()
            nombre_s = self.a_personal.ln_nombre.text().strip().upper()
            e_tecnico_c = self.a_personal.ln_expediente_c.text().strip().upper()
            e_tecnico_fo = self.a_personal.ln_expediente_fo.text().strip().upper()
            nss = self.a_personal.ln_nss.text().strip().upper()
            rfc = self.a_personal.ln_rfc.text().strip().upper()
            area = self.a_personal.str_area.currentText()
            cope = self.a_personal.str_cope.currentText()
            direccion = self.a_personal.ln_direccion.toPlainText().strip().upper()

            # Validar datos antes de guardar
            if not a_paterno or not a_materno or not nombre_s or not area or not cope:
                QMessageBox.warning(
                    self.a_personal, "Advertencia", "Por favor, complete todos los campos obligatorios.")
                return

            # Guardar en la base de datos
            if self.guardar_en_base_de_datos(a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo, nss, rfc, area, cope, direccion):
                QMessageBox.information(
                    self.a_personal, "Éxito", "Datos guardados correctamente.")
                self.regresar()
            else:
                QMessageBox.warning(
                    self.a_personal, "Error", "Error al guardar los datos.")
        except Exception as e:
            QMessageBox.critical(
                self.a_personal, "Error", f"Ocurrió un error inesperado: {e}")

    def guardar_en_base_de_datos(self, a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo, nss, rfc, area, cope, direccion):
        """
        Guarda los datos ingresados en la base de datos Personal_O.
        """
        try:
            # Validar que los campos no estén vacíos
            if not a_paterno or not a_materno or not nombre_s or not e_tecnico_c or not e_tecnico_fo:
                QMessageBox.warning(
                    self.a_personal, "Campos incompletos",
                    "Por favor, complete todos los campos obligatorios.")
                return False

            # Verificar si ya existe el registro
            query_check = """
                SELECT COUNT(*)
                FROM Personal_O
                WHERE "Expediente Técnico Cobre" = %s AND "Expediente Técnico F.O." = %s
            """
            existe = self.db_manager_personal.execute_query(
                query_check, (e_tecnico_c, e_tecnico_fo))[0]["count"]

            if existe > 0:
                QMessageBox.warning(
                    self.a_personal, "Registro duplicado",
                    "El expediente técnico ya existe. No se puede guardar datos duplicados.")
                return False

            # Validar el área y obtener su ID
            query_area = """
                SELECT id FROM Areas WHERE "Nombre del Área" = %s
            """
            resultado_area = self.db_manager_personal.execute_query(
                query_area, (area,))
            print(resultado_area)
            if not resultado_area:
                QMessageBox.critical(
                    self.a_personal, "Error",
                    f"El área seleccionada ({area}) no existe en la base de datos."
                )
                return False
            id_area = resultado_area[0]["id"]
            print("id area =", id_area)

            id_puesto = 1
            print("id area =", id_puesto)

            # Insertar datos en la tabla
            query_insert = """
                INSERT INTO Personal_O (
                    "Apellido Paterno", "Apellido Materno", "Nombre (s)",
                    "Expediente Técnico Cobre", "Expediente Técnico F.O.",
                    "id_area", "Cope", "N.S.S.", "R.F.C.", "Dirección", "id_puesto"
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db_manager_personal.execute_query(query_insert, (
                a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo,
                id_area, cope, nss, rfc, direccion, id_puesto
            ), fetch=False)

            QMessageBox.information(
                self.a_personal, "Éxito", "Datos guardados correctamente.")
            return True
        except Exception as e:
            QMessageBox.critical(
                self.a_personal, "Error", f"Error al guardar en la base de datos: {e}")
            return False

    def regresar(self):
        """
        Cierra la ventana actual y regresa a la anterior.
        """
        self.a_personal.close()
