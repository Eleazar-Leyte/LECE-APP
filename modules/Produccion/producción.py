from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QMessageBox, QWidget, QVBoxLayout
from DatabaseManager import DatabaseManager
# Importar la clase generada
from modules.Produccion.Produccion_ui import Ui_Produccion


class DynamicRow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        # Configurar todos los campos como en el diseño original
        self.ln_foliopisa = self.create_field(
            "Folio Pisa:", QtWidgets.QLineEdit)
        self.ln_telefono = self.create_field(
            "N° de Telefono:", QtWidgets.QLineEdit)
        self.str_exptec = self.create_combobox(
            "Expediente Técnico:", ["Seleccionar", "Almacén", "ONT", "MODEM"])
        self.ln_metraje = self.create_field("Metraje:", QtWidgets.QLineEdit)
        self.ln_numserie = self.create_field(
            "Número de serie:", QtWidgets.QLineEdit)
        self.ln_modelo = self.create_field("Modelo:", QtWidgets.QLineEdit)
        self.btn_imagen = self.create_image_button()
        self.btn_eliminar = self.create_delete_button()

    def create_field(self, label_text, widget_type):
        container = QtWidgets.QVBoxLayout()
        lbl = QtWidgets.QLabel(label_text)
        lbl.setStyleSheet("color: white; font: 12pt 'MS Shell Dlg 2';")
        widget = widget_type()
        widget.setStyleSheet(
            "font: 12pt 'MS Shell Dlg 2'; background-color: white; border-radius: 10px;")
        widget.setMinimumSize(120, 22)
        container.addWidget(lbl)
        container.addWidget(widget)
        self.layout.addLayout(container)
        return widget

    def create_combobox(self, label_text, items):
        container = QtWidgets.QVBoxLayout()
        lbl = QtWidgets.QLabel(label_text)
        lbl.setStyleSheet("color: white; font: 12pt 'MS Shell Dlg 2';")
        combo = QtWidgets.QComboBox()
        combo.addItems(items)
        combo.setStyleSheet(
            "font: 12pt 'MS Shell Dlg 2'; background-color: white; border-radius: 10px;")
        combo.setMinimumSize(250, 22)
        container.addWidget(lbl)
        container.addWidget(combo)
        self.layout.addLayout(container)
        return combo

    def create_image_button(self):
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtWidgets.QStyle.StandardPixmap.SP_FileIcon)
        btn.setStyleSheet(
            "background-color: #013B3D; color: white; border-radius: 10px;")
        btn.setMinimumSize(120, 22)
        self.layout.addWidget(btn)
        return btn

    def create_delete_button(self):
        btn = QtWidgets.QPushButton()
        btn.setIcon(QtWidgets.QStyle.StandardPixmap.SP_TrashIcon)
        btn.setStyleSheet(
            "background-color: #FF0000; color: white; border-radius: 10px;")
        btn.setMinimumSize(50, 40)
        self.layout.addWidget(btn)
        return btn


class Producción(QtWidgets.QMainWindow):
    def __init__(self, usuario_actual):
        super().__init__()
        self.usuario_actual = usuario_actual

        # Configurar UI
        self.ui = Ui_Produccion()
        self.ui.setupUi(self)

        # Inicialización de variables
        self.filas = []
        self.current_page = 0  # 0: Fibra, 1: Cobre, etc.

        # Configuración inicial
        self.setup_connections()
        self.cargar_areas()
        self.showMaximized()

    def setup_connections(self):
        self.ui.btn_agregar.clicked.connect(self.agregar_fila)
        self.ui.btn_ont.clicked.connect(lambda: self.cambiar_pagina(0))
        self.ui.btn_modem.clicked.connect(lambda: self.cambiar_pagina(1))
        self.ui.btn_almacen.clicked.connect(lambda: self.cambiar_pagina(2))
        self.ui.btn_catalogo.clicked.connect(lambda: self.cambiar_pagina(3))

    def cambiar_pagina(self, index):
        self.current_page = index
        self.ui.Multi_carga.setCurrentIndex(index)
        self.actualizar_interfaz()

    def actualizar_interfaz(self):
        # Limpiar filas al cambiar de página
        self.limpiar_filas()

        # Obtener referencia al contenedor actual
        contenedores = [
            self.ui.Fibra_Optica,
            self.ui.COBRE,
            self.ui.Quejas,
            self.ui.A4
        ]
        self.current_container = contenedores[self.current_page].findChild(
            QtWidgets.QWidget, "filas_contenedor")

        # Configurar layout dinámico si no existe
        if not self.current_container.layout():
            layout = QVBoxLayout(self.current_container)
            layout.setContentsMargins(0, 0, 0, 0)

    def limpiar_filas(self):
        for fila in self.filas:
            fila.setParent(None)
            fila.deleteLater()
        self.filas.clear()

    def agregar_fila(self):
        nueva_fila = DynamicRow()

        # Configurar eliminación
        nueva_fila.btn_eliminar.clicked.connect(
            lambda _, f=nueva_fila: self.eliminar_fila(f)
        )

        # Añadir al layout correspondiente
        layout = self.current_container.layout()
        layout.addWidget(nueva_fila)

        self.filas.append(nueva_fila)

        # Mostrar contenedor si está oculto
        if not self.current_container.isVisible():
            self.current_container.show()

    def eliminar_fila(self, fila):
        if fila in self.filas:
            self.filas.remove(fila)
            fila.setParent(None)
            fila.deleteLater()

            # Ocultar contenedor si no hay filas
            if not self.filas:
                self.current_container.hide()

    def cargar_areas(self):
        try:
            self.ui.str_area.clear()

            if self.usuario_actual["rol"] == "Directivo":
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                params = None
            else:
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                params = (self.usuario_actual['area'],)

            resultados = DatabaseManager(
                "Personal").execute_query(query, params)

            if resultados:
                self.ui.str_area.addItems(
                    [r['Nombre del Área'] for r in resultados])
                self.ui.str_area.currentIndexChanged.connect(
                    self.actualizar_cope)
            else:
                QMessageBox.warning(self, "Advertencia",
                                    "No se encontraron áreas disponibles")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al cargar áreas: {str(e)}")

    def actualizar_cope(self):
        try:
            area = self.ui.str_area.currentText()
            self.ui.str_cope.clear()

            if not area or area == "Seleccionar":
                return

            query = f"SELECT DISTINCT \"Copé\" FROM \"{area}\""
            resultados = DatabaseManager("Áreas").execute_query(query)

            if resultados:
                self.ui.str_cope.addItems([r["Copé"] for r in resultados])
            else:
                QMessageBox.information(
                    self, "Información", "No hay COPE disponibles")

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Error al cargar COPE: {str(e)}")


# Uso
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    usuario_ejemplo = {"rol": "Usuario", "area": "Fibra Óptica"}
    ventana = Producción(usuario_ejemplo)
    app.exec()
