from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QLineEdit, QComboBox, QFrame,
                             QGridLayout)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class UsuariosUI(QMainWindow):
    closing = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def setup_ui(self):
        self.setObjectName("Usuarios")
        self.setWindowTitle("Gestión de Usuarios")
        self.setWindowIcon(QIcon("assets/icons/profile.gif"))
        self.resize(1200, 700)

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

        header_layout.addStretch()

        self.Titulo = QLabel("Gestión de Usuarios")
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

    def setup_body(self):
        body_layout = QHBoxLayout()
        body_layout.setSpacing(15)

        # --- Tabla Central ---
        self.tabla_usuarios = QTableWidget()
        self.tabla_usuarios.setObjectName("tabla_usuarios")
        self.tabla_usuarios.setAlternatingRowColors(True)
        self.tabla_usuarios.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_usuarios.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection)
        body_layout.addWidget(self.tabla_usuarios, stretch=1)

        # --- Panel Derecho (Formulario) ---
        right_panel = QFrame()
        right_panel.setObjectName("right_panel")
        right_panel.setFixedWidth(340)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        lbl_title = QLabel("Nuevo Usuario")
        lbl_title.setObjectName("panel_title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(lbl_title)

        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        form_layout.addWidget(QLabel("Empleado:"), 0, 0)
        self.cb_personal = QComboBox()
        form_layout.addWidget(self.cb_personal, 0, 1)

        form_layout.addWidget(QLabel("Usuario:"), 1, 0)
        self.ln_usuario = QLineEdit()
        form_layout.addWidget(self.ln_usuario, 1, 1)

        form_layout.addWidget(QLabel("Contraseña:"), 2, 0)
        self.ln_password = QLineEdit()
        self.ln_password.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addWidget(self.ln_password, 2, 1)

        form_layout.addWidget(QLabel("Rol:"), 3, 0)
        self.cb_rol = QComboBox()
        self.cb_rol.addItems(
            ["Admin", "Directivo", "Personal Administrativo", "Personal Técnico"])
        form_layout.addWidget(self.cb_rol, 3, 1)

        right_layout.addLayout(form_layout)

        self.btn_crear = QPushButton(" Crear Usuario")
        self.btn_crear.setFixedHeight(45)
        self.btn_crear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_crear.setIcon(QIcon("assets/icons/plus.svg"))
        right_layout.addWidget(self.btn_crear)

        right_layout.addStretch()

        self.btn_reset_pass = QPushButton(" Resetear Contraseña")
        self.btn_reset_pass.setFixedHeight(40)
        self.btn_reset_pass.setCursor(Qt.CursorShape.PointingHandCursor)
        right_layout.addWidget(self.btn_reset_pass)

        self.btn_toggle_status = QPushButton(" Activar / Desactivar")
        self.btn_toggle_status.setFixedHeight(40)
        self.btn_toggle_status.setCursor(Qt.CursorShape.PointingHandCursor)
        right_layout.addWidget(self.btn_toggle_status)

        body_layout.addWidget(right_panel)
        self.main_layout.addLayout(body_layout)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            QLabel#Titulo { color: #EFBFBC; }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            
            QFrame#right_panel {
                background-color: rgba(255, 255, 255, 15);
                border: 1px solid rgba(255, 255, 255, 40);
                border-radius: 12px;
                padding: 15px;
            }
            QLabel#panel_title {
                color: #EFBFBC; font: bold 14pt "MS Shell Dlg 2"; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255, 50);
            }

            QLineEdit, QComboBox {
                background-color: white; color: black; border-radius: 6px; padding: 6px; font: 11pt "MS Shell Dlg 2";
            }
            
            QPushButton {
                background-color: rgb(1, 79, 81); color: white; border-radius: 6px; padding: 8px; font: bold 11pt "MS Shell Dlg 2"; border: 1px solid rgba(255,255,255, 30);
            }
            QPushButton:hover { background-color: rgb(1, 99, 101); }
            
            QPushButton#btn_crear {
                background-color: #EFBFBC; color: #013B3D; border: none;
            }
            QPushButton#btn_crear:hover { background-color: #E5AFA9; }
            
            QPushButton#btn_regresar, QPushButton#btn_salir { background-color: rgb(220, 53, 69); border: none; }
            
            QTableWidget {
                background-color: white; border-radius: 8px; color: #333; gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: rgb(1, 59, 61); color: white; font-weight: bold; padding: 8px; border: none;
            }
        """)
