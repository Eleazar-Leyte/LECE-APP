from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QLineEdit,
                             QTabWidget, QFormLayout, QFrame, QSpacerItem, QSizePolicy, QCheckBox)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QSize


class AjustesUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("Ajustes")
        self.setWindowTitle("Configuración del Sistema")
        self.setWindowIcon(QIcon("assets/icons/cogwheel.png"))
        self.resize(1000, 700)

        self.centralwidget = QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(20, 20, 20, 20)

        self.setup_header()
        self.setup_tabs()
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

        header_layout.addStretch()

        self.Titulo = QLabel("Configuración")
        self.Titulo.setFont(QFont("Times New Roman", 26, QFont.Weight.Bold))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.Titulo)

        header_layout.addStretch()

        self.btn_salir = QPushButton()
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.setFixedSize(45, 35)
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        self.btn_salir.setIconSize(QSize(20, 20))
        header_layout.addWidget(self.btn_salir)

        self.main_layout.addLayout(header_layout)

    def setup_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setObjectName("tabs")

        # --- Pestaña 1: Apariencia ---
        tab_apariencia = QWidget()
        layout_ap = QFormLayout(tab_apariencia)
        layout_ap.setSpacing(20)
        layout_ap.setContentsMargins(30, 30, 30, 30)

        self.str_tema = QComboBox()
        self.str_tema.addItems(["Oscuro", "Claro", "Del Sistema"])

        self.chk_notificaciones = QCheckBox(
            "Habilitar notificaciones de escritorio")

        layout_ap.addRow(QLabel("Modo de la aplicación:"), self.str_tema)
        layout_ap.addRow(QLabel("Notificaciones:"), self.chk_notificaciones)
        self.tabs.addTab(tab_apariencia, "Apariencia")

        # --- Pestaña 2: Perfil ---
        tab_perfil = QWidget()
        layout_perfil = QVBoxLayout(tab_perfil)
        layout_perfil.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_perfil.setSpacing(15)
        layout_perfil.setContentsMargins(30, 30, 30, 30)

        # Foto
        foto_layout = QHBoxLayout()
        self.lbl_foto = QLabel()
        self.lbl_foto.setFixedSize(120, 120)
        self.lbl_foto.setStyleSheet(
            "background-color: white; border-radius: 60px; border: 2px solid #ccc;")
        self.lbl_foto.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_foto.setText("Sin Foto")

        btn_foto_layout = QVBoxLayout()
        self.btn_subir_foto = QPushButton("Cambiar Foto de Perfil")
        self.btn_subir_foto.setFixedSize(200, 35)
        self.btn_subir_foto.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_foto_layout.addWidget(self.btn_subir_foto)
        btn_foto_layout.addStretch()

        foto_layout.addWidget(self.lbl_foto)
        foto_layout.addSpacing(20)
        foto_layout.addLayout(btn_foto_layout)

        layout_perfil.addLayout(foto_layout)

        # Datos de usuario
        self.lbl_info_usuario = QLabel("Información del Usuario")
        self.lbl_info_usuario.setStyleSheet(
            "font-weight: bold; margin-top: 20px;")
        layout_perfil.addWidget(self.lbl_info_usuario)

        self.lbl_nombre = QLabel("Nombre: -")
        self.lbl_rol = QLabel("Rol: -")
        self.lbl_area = QLabel("Área: -")
        layout_perfil.addWidget(self.lbl_nombre)
        layout_perfil.addWidget(self.lbl_rol)
        layout_perfil.addWidget(self.lbl_area)

        self.tabs.addTab(tab_perfil, "Mi Perfil")

        # --- Pestaña 3: Sistema ---
        tab_sistema = QWidget()
        layout_sis = QFormLayout(tab_sistema)
        layout_sis.setSpacing(20)
        layout_sis.setContentsMargins(30, 30, 30, 30)

        self.ln_api_url = QLineEdit()
        self.ln_api_url.setPlaceholderText("http://localhost:8000")
        self.ln_api_url.setFixedWidth(300)

        self.btn_test_conexion = QPushButton("Probar Conexión")
        self.btn_test_conexion.setCursor(Qt.CursorShape.PointingHandCursor)

        layout_sis.addRow(QLabel("URL de la API:"), self.ln_api_url)
        layout_sis.addRow("", self.btn_test_conexion)
        self.tabs.addTab(tab_sistema, "Sistema Avanzado")

        self.main_layout.addWidget(self.tabs)

        # Botón de Guardar Global
        btn_save_layout = QHBoxLayout()
        btn_save_layout.addStretch()
        self.btn_guardar_ajustes = QPushButton(" Guardar Cambios")
        self.btn_guardar_ajustes.setFixedSize(200, 45)
        self.btn_guardar_ajustes.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar_ajustes.setObjectName("btn_guardar_ajustes")
        self.btn_guardar_ajustes.setIcon(QIcon("assets/icons/Guardar.svg"))
        btn_save_layout.addWidget(self.btn_guardar_ajustes)
        self.main_layout.addLayout(btn_save_layout)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QLabel#Titulo { color: #EFBFBC; }
            
            QTabWidget::pane {
                border: 1px solid rgba(255,255,255, 40);
                background-color: rgba(255, 255, 255, 15);
                border-radius: 10px;
            }
            QTabBar::tab {
                background: rgba(0,0,0, 50);
                color: white;
                padding: 10px 20px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: rgba(255,255,255, 20);
                color: #EFBFBC;
                font-weight: bold;
            }
            
            QComboBox, QLineEdit {
                background-color: white; color: black; border-radius: 6px; padding: 6px; font: 11pt "MS Shell Dlg 2";
            }
            QCheckBox { color: white; font: 11pt "MS Shell Dlg 2"; }
            
            QPushButton {
                background-color: rgb(1, 79, 81); color: white; border-radius: 6px; padding: 8px; font: bold 11pt "MS Shell Dlg 2";
            }
            QPushButton:hover { background-color: rgb(1, 99, 101); }
            
            QPushButton#btn_guardar_ajustes {
                background-color: #EFBFBC; color: #013B3D;
            }
            QPushButton#btn_guardar_ajustes:hover { background-color: #E5AFA9; }
            
            QPushButton#btn_regresar, QPushButton#btn_salir { background-color: rgb(220, 53, 69); border-radius: 8px; }
        """)
