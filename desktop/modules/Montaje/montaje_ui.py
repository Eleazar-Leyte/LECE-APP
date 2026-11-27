from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QTableWidget,
                             QListWidget, QSpacerItem, QSizePolicy, QFrame,
                             QSplitter, QDialog, QDateEdit, QGridLayout)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize, QDate, pyqtSignal


class MontajeUI(QMainWindow):
    closing = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def setup_ui(self):
        self.setObjectName("Montaje")
        self.setWindowTitle("Cuadre de Materiales y Montaje")
        self.setWindowIcon(QIcon("assets/icons/layout-fluid.svg"))
        self.resize(1400, 800)

        self.centralwidget = QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.setup_header()
        self.setup_body()
        self.apply_styles()

    def setup_header(self):
        header_layout = QHBoxLayout()

        self.Logo = QLabel()
        self.Logo.setMaximumSize(80, 70)
        self.Logo.setPixmap(QPixmap("assets/images/Nuevo aspecto.png"))
        self.Logo.setScaledContents(True)
        header_layout.addWidget(self.Logo)

        self.btn_regresar = QPushButton()
        self.btn_regresar.setObjectName("btn_regresar")
        self.btn_regresar.setFixedSize(45, 35)
        self.btn_regresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))
        self.btn_regresar.setIconSize(QSize(20, 20))
        header_layout.addWidget(self.btn_regresar)

        header_layout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.Titulo = QLabel("Cuadre de Materiales")
        self.Titulo.setFont(QFont("Times New Roman", 26, QFont.Weight.Bold))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.Titulo)

        header_layout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.btn_salir = QPushButton()
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.setFixedSize(45, 35)
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        self.btn_salir.setIconSize(QSize(20, 20))
        header_layout.addWidget(self.btn_salir)

        self.main_layout.addLayout(header_layout)

    def setup_body(self):
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)

        # ==========================================
        # PANEL IZQUIERDO: FILTROS
        # ==========================================
        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(260)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)
        left_layout.setContentsMargins(20, 20, 20, 20)

        lbl_filtros = QLabel("Filtros de Búsqueda")
        lbl_filtros.setObjectName("panel_title")
        left_layout.addWidget(lbl_filtros)

        left_layout.addWidget(QLabel("Área:"))
        self.str_area = QComboBox()
        self.str_area.setObjectName("str_area")
        self.str_area.addItem("Seleccionar")
        left_layout.addWidget(self.str_area)

        left_layout.addWidget(QLabel("COPE:"))
        self.str_cope = QComboBox()
        self.str_cope.setObjectName("str_cope")
        self.str_cope.addItem("Seleccionar")
        left_layout.addWidget(self.str_cope)

        left_layout.addWidget(QLabel("Técnico:"))
        self.str_exptec = QComboBox()
        self.str_exptec.setObjectName("str_exptec")
        self.str_exptec.addItem("Seleccionar")
        left_layout.addWidget(self.str_exptec)

        left_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.btn_buscar = QPushButton(" Buscar Folios")
        self.btn_buscar.setObjectName("btn_buscar")
        self.btn_buscar.setFixedHeight(40)
        self.btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buscar.setIcon(QIcon("assets/icons/buscar.svg"))
        self.btn_buscar.setIconSize(QSize(18, 18))
        left_layout.addWidget(self.btn_buscar)

        left_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        body_layout.addWidget(left_panel)

        # ==========================================
        # PANEL CENTRAL: LISTA DE FOLIOS Y TABLA
        # ==========================================
        center_panel = QFrame()
        center_panel.setObjectName("center_panel")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Contenedor Izquierdo del Centro (Folios) ---
        folios_container = QFrame()
        folios_container.setObjectName("folios_container")
        folios_layout = QVBoxLayout(folios_container)
        folios_layout.setContentsMargins(0, 0, 10, 0)

        lbl_folios = QLabel("Folios Pendientes")
        lbl_folios.setObjectName("sub_panel_title")
        folios_layout.addWidget(lbl_folios)

        self.lista_instalaciones = QListWidget()
        self.lista_instalaciones.setObjectName("lista_instalaciones")
        folios_layout.addWidget(self.lista_instalaciones)

        self.splitter.addWidget(folios_container)

        # --- Contenedor Derecho del Centro (Tabla Materiales) ---
        tabla_container = QFrame()
        tabla_container.setObjectName("tabla_container")
        tabla_layout = QVBoxLayout(tabla_container)
        tabla_layout.setContentsMargins(10, 0, 0, 0)

        self.lbl_folio_activo = QLabel(
            "Seleccione un folio para ver sus materiales")
        self.lbl_folio_activo.setObjectName("sub_panel_title")
        self.lbl_folio_activo.setStyleSheet("color: #EFBFBC;")  # Color durazno
        tabla_layout.addWidget(self.lbl_folio_activo)

        self.tabla_materiales = QTableWidget()
        self.tabla_materiales.setObjectName("tabla_materiales")
        tabla_layout.addWidget(self.tabla_materiales)

        self.splitter.addWidget(tabla_container)

        # Ajustar proporciones (Folios 30%, Tabla 70%)
        self.splitter.setSizes([280, 650])
        center_layout.addWidget(self.splitter)

        body_layout.addWidget(center_panel)

        # ==========================================
        # PANEL DERECHO: ACCIONES
        # ==========================================
        right_panel = QFrame()
        right_panel.setObjectName("right_panel")
        right_panel.setFixedWidth(180)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(15, 20, 15, 20)

        lbl_acciones = QLabel("Acciones")
        lbl_acciones.setObjectName("panel_title")
        lbl_acciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_acciones)

        right_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.btn_guardar = QPushButton(" Guardar Cuadre")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setFixedHeight(45)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.btn_guardar.setIconSize(QSize(20, 20))
        right_layout.addWidget(self.btn_guardar)

        self.btn_exportar = QPushButton(" Exportar")
        self.btn_exportar.setObjectName("btn_exportar")
        self.btn_exportar.setFixedHeight(40)
        self.btn_exportar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_exportar.setIcon(QIcon("assets/icons/Excel.svg"))
        self.btn_exportar.setIconSize(QSize(18, 18))
        right_layout.addWidget(self.btn_exportar)

        right_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        body_layout.addWidget(right_panel)

        self.main_layout.addLayout(body_layout)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            /* Fondo Principal */
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            
            /* Títulos */
            QLabel#Titulo { 
                color: #EFBFBC; 
            }
            QLabel#panel_title {
                color: white; 
                font: bold 14pt "MS Shell Dlg 2"; 
                padding: 5px 0px 10px 0px; 
                border-bottom: 2px solid rgba(255, 255, 255, 40);
            }
            QLabel#sub_panel_title {
                color: white; 
                font: bold 12pt "MS Shell Dlg 2"; 
                padding: 5px;
            }
            QLabel { 
                color: rgba(255, 255, 255, 200); 
                font: 11pt "MS Shell Dlg 2"; 
            }

            /* Botones del Header */
            QPushButton#btn_salir, QPushButton#btn_regresar { 
                background-color: rgb(220, 53, 69); 
                border-radius: 8px; 
                border: none; 
            }
            QPushButton#btn_salir:hover, QPushButton#btn_regresar:hover { 
                background-color: rgb(200, 35, 51); 
            }

            /* Paneles Laterales */
            QFrame#left_panel, QFrame#right_panel {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 12px;
            }

            /* Inputs */
            QComboBox {
                background-color: white; 
                color: black; 
                border-radius: 6px; 
                padding: 8px 10px; 
                font: 11pt "MS Shell Dlg 2"; 
                border: 2px solid transparent;
            }
            QComboBox:focus { 
                border: 2px solid #EFBFBC; 
            }
            QComboBox QAbstractItemView { 
                background-color: white; 
                color: black; 
                selection-background-color: rgb(1, 59, 61); 
                selection-color: white; 
            }

            /* Botones de Acción */
            QPushButton#btn_buscar {
                background-color: rgb(1, 79, 81); 
                color: white; 
                border-radius: 8px; 
                padding: 10px; 
                font: bold 11pt "MS Shell Dlg 2"; 
                border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton#btn_buscar:hover { 
                background-color: rgb(1, 99, 101); 
            }

            /* Botón Guardar (Destaque en Durazno) */
            QPushButton#btn_guardar {
                background-color: #EFBFBC; 
                color: #013B3D;            
                border-radius: 8px; 
                padding: 12px; 
                font: bold 12pt "MS Shell Dlg 2"; 
                border: 1px solid #E5AFA9;
            }
            QPushButton#btn_guardar:hover { 
                background-color: #E5AFA9; 
            }
            
            /* Botón Exportar (Secundario) */
            QPushButton#btn_exportar {
                background-color: rgba(255, 255, 255, 20); 
                color: white; 
                border-radius: 8px; 
                padding: 10px; 
                font: bold 11pt "MS Shell Dlg 2"; 
                border: 1px solid rgba(255, 255, 255, 80);
            }
            QPushButton#btn_exportar:hover { 
                background-color: rgba(255, 255, 255, 40); 
            }

            /* Lista de Folios (Estilo Tarjetas) */
            QListWidget {
                background-color: transparent; 
                border: none; 
                outline: none;
            }
            QListWidget::item { 
                background-color: white; 
                color: #333;
                padding: 15px 15px; 
                border-radius: 8px; 
                margin-bottom: 8px;
                border: 1px solid #ddd;
                font: 11pt "MS Shell Dlg 2";
            }
            QListWidget::item:hover { 
                background-color: #f0f0f0; 
            }
            QListWidget::item:selected { 
                background-color: rgb(1, 59, 61); 
                color: white; 
                border: 2px solid #EFBFBC;
            }

            /* Tabla de Materiales */
            QTableWidget {
                background-color: white; 
                border-radius: 8px; 
                gridline-color: #e0e0e0; 
                font: 10pt "MS Shell Dlg 2"; 
                color: #333; 
                outline: none;
            }
            QTableWidget::item { 
                padding: 8px; 
            }
            QTableWidget::item:selected { 
                background-color: rgba(1, 79, 81, 180); 
                color: white; 
            }
            QHeaderView::section {
                background-color: rgb(1, 59, 61); 
                color: white; 
                font-weight: bold; 
                padding: 10px; 
                border: none; 
                border-right: 1px solid rgba(255, 255, 255, 30);
            }
            QScrollBar:vertical { 
                background: transparent; 
                width: 10px; 
            }
            QScrollBar::handle:vertical { 
                background: rgba(0, 0, 0, 100); 
                border-radius: 5px; 
            }
        """)


class ExportarDialog(QDialog):
    """Diálogo modal para exportar el reporte de producción"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Reporte de Producción")
        self.setFixedSize(400, 320)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet("""
            QDialog { background: rgb(1, 59, 61); color: white; }
            QLabel { color: white; font: 12pt "MS Shell Dlg 2"; }
            QComboBox, QDateEdit {
                background-color: white; color: black; border-radius: 6px; padding: 6px 10px; font: 11pt "MS Shell Dlg 2";
            }
            QPushButton {
                background-color: #EFBFBC; color: #013B3D; border-radius: 6px; padding: 10px; font: bold 11pt "MS Shell Dlg 2"; border: none;
            }
            QPushButton:hover { background-color: #E5AFA9; }
            QPushButton#btn_cancelar { background-color: rgb(220, 53, 69); color: white;}
            QPushButton#btn_cancelar:hover { background-color: rgb(200, 35, 51); }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)

        lbl_title = QLabel("Seleccione los filtros")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
        layout.addWidget(lbl_title)

        form_layout = QGridLayout()
        form_layout.setSpacing(15)

        form_layout.addWidget(QLabel("Área:"), 0, 0)
        self.str_area_exp = QComboBox()
        form_layout.addWidget(self.str_area_exp, 0, 1)

        form_layout.addWidget(QLabel("COPE:"), 1, 0)
        self.str_cope_exp = QComboBox()
        form_layout.addWidget(self.str_cope_exp, 1, 1)

        form_layout.addWidget(QLabel("Fecha Inicio:"), 2, 0)
        self.fecha_ini = QDateEdit()
        self.fecha_ini.setDate(QDate.currentDate().addMonths(-1))
        self.fecha_ini.setCalendarPopup(True)
        form_layout.addWidget(self.fecha_ini, 2, 1)

        form_layout.addWidget(QLabel("Fecha Fin:"), 3, 0)
        self.fecha_fin = QDateEdit()
        self.fecha_fin.setDate(QDate.currentDate())
        self.fecha_fin.setCalendarPopup(True)
        form_layout.addWidget(self.fecha_fin, 3, 1)

        layout.addLayout(form_layout)
        layout.addStretch()

        btn_layout = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_exportar = QPushButton("Exportar a Excel")
        self.btn_exportar.clicked.connect(self.accept)

        btn_layout.addWidget(self.btn_cancelar)
        btn_layout.addWidget(self.btn_exportar)
        layout.addLayout(btn_layout)
