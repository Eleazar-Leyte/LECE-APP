import sqlite3

from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox


class A_Personal():
    def __init__(self):
        self.a_personal = uic.loadUi("modules/A_personal.ui")
        self.a_personal.show()

        # Conectamos los botones de la Ui
        self.botones()

        # Conectamos la base de datos:
        self.conn = sqlite3.connect("personal.db")
        self.cursor = self.conn.cursor()

        # Conexión a la base de datos áreas
        self.conn_areas = sqlite3.connect("Areas.db")
        self.cursor_areas = self.conn_areas.cursor()

        # Ejecutamos la fucnion para crar la tabla en caso de que no exista
        self.crear_tab_P_O()

        # Cargamos el ComboBox de Áreas
        self.cargar_areas()

    def botones(self):
        self.a_personal.btn_guardar.clicked.connect(self.agregar_personal_o)
        self.a_personal.btn_regresar.clicked.connect(self.regresar)
        self.a_personal.str_area.currentIndexChanged.connect(
            self.actualizar_cope)

    def crear_tab_P_O(self):
        # Crear la tabla si no existe:
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Personal_O (
            "Id"	INTEGER NOT NULL,
            "Apellido Paterno"	TEXT NOT NULL,
            "Apellido Materno"	TEXT NOT NULL,
            "Nombre (s)"	TEXT NOT NULL,
            "Expediente Técnico Cobre"	TEXT NOT NULL,
            "Expediente Técnico F.O."	TEXT NOT NULL,
            "Área"	TEXT NOT NULL,
            "Cope"	TEXT NOT NULL,
            "N.S.S."	TEXT NOT NULL,
            "R.F.C."	TEXT NOT NULL,
            "Dirección"	TEXT NOT NULL,
            PRIMARY KEY("Id" AUTOINCREMENT))''')
        self.conn.commit()

    def cargar_areas(self):
        # Ploblar el CoboBox de áreas con los nombre de las tablas en la base de datos
        self.cursor_areas.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")
        tablas = self.cursor_areas.fetchall()

        self.a_personal.str_area.clear()
        for tabla in tablas:
            self.a_personal.str_area.addItem(tabla[0])

    def actualizar_cope(self):
        # Cargar el ComboBox de cope basado en el área seleccionada
        area_seleccionada = self.a_personal.str_area.currentText()

        if area_seleccionada:
            self.a_personal.str_cope.clear()
            try:
                consulta = f"SELECT DISTINCT Copé FROM {area_seleccionada}"
                self.cursor_areas.execute(consulta)
                valores_cope = self.cursor_areas.fetchall()

                for valor in valores_cope:
                    self.a_personal.str_cope.addItem(valor[0])
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self.a_personal, "Error", f"Error al cargar los datos de Cope: {e}")

    def agregar_personal_o(self):
        try:
            # Registrar los datos desde la interfaz gráfica
            a_paterno = self.a_personal.ln_apaterno.text()
            a_materno = self.a_personal.ln_materno.text()
            nombre_s = self.a_personal.ln_nombre.text()
            e_tecnico_c = self.a_personal.ln_expediente_c.text()
            e_tecnico_fo = self.a_personal.ln_expediente_fo.text()
            nss = self.a_personal.ln_nss.text()
            rfc = self.a_personal.ln_rfc.text()
            area = self.a_personal.str_area.currentText()
            cope = self.a_personal.str_cope.currentText()
            direccion = self.a_personal.ln_direccion.toPlainText()

            # Intentar guardar en la base de datos
            if self.guardar_en_base_de_datos(a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo, nss, rfc, area, cope, direccion):
                QMessageBox.information(
                    self.a_personal, "Éxito", "Datos guardados correctamente.")
                self.regresar()
            else:
                QMessageBox.warning(
                    self.a_personal, "Error", "Error al guardar los datos.")
        except Exception as e:
            QMessageBox.critical(
                self.a_personal, "Error", f"Ocurrió un error inesperado: {str(e)}")

    def guardar_en_base_de_datos(self, a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo, nss, rfc, area, cope, direccion):
        try:
            # Verificar si ya existe el registro con los expedientes técnicos usando el cursor global
            self.cursor.execute(
                "SELECT COUNT(*) FROM Personal_O WHERE `Expediente Técnico Cobre` = ? AND `Expediente Técnico F.O.` = ?",
                (e_tecnico_c, e_tecnico_fo)
            )
            existe = self.cursor.fetchone()[0]

            if existe > 0:
                QMessageBox.warning(
                    self.a_personal, "Registro duplicado", "El expediente técnico ya existe. \n No se puede guardar datos duplicados")
                return False

            # Insertar datos en la tabla 'Personal_O' usando el cursor global
            self.cursor.execute('''INSERT INTO Personal_O 
                ("Apellido Paterno", "Apellido Materno", "Nombre (s)", "Expediente Técnico Cobre", "Expediente Técnico F.O.", "Área", "Cope", "N.S.S.", "R.F.C.", "Dirección") 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (a_paterno, a_materno, nombre_s, e_tecnico_c, e_tecnico_fo, area, cope, nss, rfc, direccion))

            self.conn.commit()  # Guardar los cambios en la base de datos

            # Cerrar la conexión a la base de datos después de guardar
            self.cerrar_db()

            return True

        except sqlite3.Error as e:
            QMessageBox.critical(
                self.a_personal, "Error", f"Error al guardar en la base de datos: {str(e)}")
            return False

    def cerrar_db(self):
        try:
            if self.conn:            # Cerrar la conexión de la base de datos antes de cerrar la ventana
                self.conn.close()
                print("Conexión a la base de datos 'personal.db' cerrada.")
            if self.conn_areas:
                self.conn_areas.close()
                print("Conexión a la base de datos 'Álmacen.db' cerrada.")
        except Exception as e:
            print(f"Error al cerrar la conexión de la base de datos: {e}")

    def regresar(self):
        self.cerrar_db()
        self.a_personal.close()
