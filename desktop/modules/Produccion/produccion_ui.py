from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QStackedWidget,
                             QTableWidget, QSpacerItem, QSizePolicy, QFrame,
                             QButtonGroup, QGroupBox, QGridLayout)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QSize


class ProduccionUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("Produccion")
        self.setWindowTitle("Carga de Producción (Supervisión)")
        self.setWindowIcon(QIcon("assets/icons/desk.svg"))
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

        self.Titulo = QLabel("Carga de Producción por Tecnología")
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
        # PANEL IZQUIERDO: FILTROS (Sin Técnico global)
        # ==========================================
        left_panel = QFrame()
        left_panel.setObjectName("left_panel")
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(15)

        lbl_filtros = QLabel("Filtros Base")
        lbl_filtros.setObjectName("panel_title")
        left_layout.addWidget(lbl_filtros)

        filter_group = QGroupBox()
        filter_grid = QGridLayout(filter_group)
        filter_grid.setSpacing(15)

        # Área
        filter_grid.addWidget(QLabel("Área:"), 0, 0)
        self.str_area = QComboBox()
        self.str_area.setObjectName("str_area")
        self.str_area.addItem("Seleccionar")
        filter_grid.addWidget(self.str_area, 1, 0)

        # COPE
        filter_grid.addWidget(QLabel("COPE:"), 2, 0)
        self.str_cope = QComboBox()
        self.str_cope.setObjectName("str_cope")
        self.str_cope.addItem("Seleccionar")
        filter_grid.addWidget(self.str_cope, 3, 0)

        left_layout.addWidget(filter_group)

        # Nota informativa para el usuario
        lbl_info = QLabel(
            "Seleccione Área y COPE.\nLuego asigne un Técnico\na cada fila en la tabla.")
        lbl_info.setWordWrap(True)
        lbl_info.setStyleSheet(
            "color: rgba(255,255,255,150); font: italic 10pt 'MS Shell Dlg 2'; margin-top: 20px;")
        left_layout.addWidget(lbl_info)

        left_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        body_layout.addWidget(left_panel)

        # ==========================================
        # PANEL CENTRAL: PESTAÑAS Y TABLAS
        # ==========================================
        center_panel = QFrame()
        center_panel.setObjectName("center_panel")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(10)

        # Barra de Navegación
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(5)

        self.btn_F_O = QPushButton("Fibra Óptica")
        self.btn_cobre = QPushButton("Cobre")
        self.btn_quejas = QPushButton("Quejas")
        self.btn_a4 = QPushButton("A4")

        for btn in [self.btn_F_O, self.btn_cobre, self.btn_quejas, self.btn_a4]:
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            nav_layout.addWidget(btn)

        self.btn_F_O.setChecked(True)

        self.nav_group = QButtonGroup(self)
        self.nav_group.addButton(self.btn_F_O, 0)
        self.nav_group.addButton(self.btn_cobre, 1)
        self.nav_group.addButton(self.btn_quejas, 2)
        self.nav_group.addButton(self.btn_a4, 3)

        nav_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        center_layout.addLayout(nav_layout)

        # Stacked Widget
        self.Multi_carga = QStackedWidget()
        self.Multi_carga.setObjectName("Multi_carga")

        self.tabla_FO = QTableWidget()
        self.tabla_cobre = QTableWidget()
        self.tabla_quejas = QTableWidget()
        self.tabla_a4 = QTableWidget()

        self.tabla_FO.setObjectName("tabla_FO")
        self.tabla_cobre.setObjectName("tabla_cobre")
        self.tabla_quejas.setObjectName("tabla_quejas")
        self.tabla_a4.setObjectName("tabla_a4")

        # Contenedores para las tablas
        for tabla in [self.tabla_FO, self.tabla_cobre, self.tabla_quejas, self.tabla_a4]:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(tabla)
            self.Multi_carga.addWidget(page)

        center_layout.addWidget(self.Multi_carga)
        body_layout.addWidget(center_panel)

        # ==========================================
        # PANEL DERECHO: ACCIONES
        # ==========================================
        right_panel = QFrame()
        right_panel.setObjectName("right_panel")
        right_panel.setFixedWidth(120)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        lbl_acciones = QLabel("Acciones")
        lbl_acciones.setObjectName("panel_title")
        lbl_acciones.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_acciones)

        right_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        self.btn_agregar = QPushButton(" Agregar")
        self.btn_agregar.setObjectName("btn_agregar")
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.setIcon(QIcon("assets/icons/plus.svg"))
        self.btn_agregar.setIconSize(QSize(18, 18))
        right_layout.addWidget(self.btn_agregar)

        self.btn_eliminar = QPushButton(" Eliminar")
        self.btn_eliminar.setObjectName("btn_eliminar")
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setIcon(QIcon("assets/icons/trash.png"))
        self.btn_eliminar.setIconSize(QSize(18, 18))
        right_layout.addWidget(self.btn_eliminar)

        right_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.btn_guardar = QPushButton(" Guardar")
        self.btn_guardar.setObjectName("btn_guardar")
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.btn_guardar.setIconSize(QSize(18, 18))
        right_layout.addWidget(self.btn_guardar)

        right_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        body_layout.addWidget(right_panel)
        self.main_layout.addLayout(body_layout)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            QLabel#Titulo { color: rgba(239, 191, 188, 255); }
            QPushButton#btn_salir, QPushButton#btn_regresar { background-color: rgb(220, 53, 69); border-radius: 8px; border: none; }
            QPushButton#btn_salir:hover, QPushButton#btn_regresar:hover { background-color: rgb(200, 35, 51); }

            QFrame#left_panel, QFrame#right_panel {
                background-color: rgba(255, 255, 255, 20);
                border: 1px solid rgba(255, 255, 255, 50);
                border-radius: 12px;
            }
            QFrame#center_panel { background-color: transparent; }
            
            QLabel#panel_title {
                color: white; font: bold 14pt "MS Shell Dlg 2"; padding: 10px 0px; border-bottom: 2px solid rgba(255, 255, 255, 50);
            }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QGroupBox { border: none; }

            QComboBox {
                background-color: white; color: black; border-radius: 8px; padding: 6px 10px; font: 11pt "MS Shell Dlg 2"; border: 2px solid transparent;
            }
            QComboBox:focus { border: 2px solid rgba(239, 191, 188, 255); }
            QComboBox QAbstractItemView { background-color: white; color: black; selection-background-color: rgb(1, 59, 61); selection-color: white; }

            QPushButton[objectName^="btn_"] {
                background-color: transparent; color: rgba(255, 255, 255, 150); border: none; border-bottom: 3px solid transparent; padding: 10px 20px; font: bold 12pt "MS Shell Dlg 2";
            }
            QPushButton[objectName^="btn_"]:hover { color: white; background-color: rgba(255, 255, 255, 10); }
            QPushButton[objectName^="btn_"]:checked { color: white; border-bottom: 3px solid rgba(239, 191, 188, 255); }

            QPushButton#btn_agregar, QPushButton#btn_eliminar, QPushButton#btn_guardar {
                background-color: rgb(1, 79, 81); color: white; border-radius: 8px; padding: 12px; font: bold 11pt "MS Shell Dlg 2"; border: 1px solid rgba(255, 255, 255, 30);
            }
            QPushButton#btn_agregar:hover, QPushButton#btn_eliminar:hover, QPushButton#btn_guardar:hover {
                background-color: rgb(1, 99, 101); border: 1px solid rgba(255, 255, 255, 80);
            }

            QTableWidget {
                background-color: white; border-radius: 8px; gridline-color: #e0e0e0; font: 10pt "MS Shell Dlg 2"; color: #333; outline: none;
            }
            QTableWidget::item { padding: 8px; }
            QTableWidget::item:selected { background-color: rgba(1, 59, 61, 200); color: white; }
            QHeaderView::section {
                background-color: rgb(1, 59, 61); color: white; font-weight: bold; padding: 10px; border: none; border-right: 1px solid rgba(255, 255, 255, 20);
            }
            QScrollBar:vertical { background: transparent; width: 10px; }
            QScrollBar::handle:vertical { background: rgba(0, 0, 0, 100); border-radius: 5px; }
        """)
