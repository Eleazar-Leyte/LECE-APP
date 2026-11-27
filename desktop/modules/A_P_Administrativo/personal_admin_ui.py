from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QTableWidget, QLineEdit, QComboBox, QFrame,
                             QGridLayout, QMessageBox)
from PyQt6.QtGui import QPixmap, QIcon, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSignal


class PersonalAdminUI(QMainWindow):
    closing = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def closeEvent(self, event):
        self.closing.emit()
        super().closeEvent(event)

    def setup_ui(self):
        self.setObjectName("PersonalAdmin")
        self.setWindowTitle("Personal Administrativo")
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
        header = QHBoxLayout()

        self.Logo = QLabel()
        self.Logo.setMaximumSize(80, 70)
        self.Logo.setPixmap(QPixmap("assets/images/Nuevo aspecto.png"))
        self.Logo.setScaledContents(True)
        header.addWidget(self.Logo)

        self.btn_regresar = QPushButton()
        self.btn_regresar.setObjectName("btn_regresar")
        self.btn_regresar.setFixedSize(45, 35)
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))
        header.addWidget(self.btn_regresar)

        header.addStretch()
        self.Titulo = QLabel("Personal Administrativo")
        self.Titulo.setFont(QFont("Times New Roman", 26, QFont.Weight.Bold))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.addWidget(self.Titulo)
        header.addStretch()

        self.btn_salir = QPushButton()
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.setFixedSize(45, 35)
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        header.addWidget(self.btn_salir)

        self.main_layout.addLayout(header)

    def setup_body(self):
        body = QHBoxLayout()
        body.setSpacing(15)

        # Tabla
        self.tabla_admin = QTableWidget()
        self.tabla_admin.setAlternatingRowColors(True)
        self.tabla_admin.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        body.addWidget(self.tabla_admin, stretch=1)

        # Formulario
        panel = QFrame()
        panel.setObjectName("right_panel")
        panel.setFixedWidth(350)
        layout_panel = QVBoxLayout(panel)

        lbl_title = QLabel("Alta de Administrativo")
        lbl_title.setObjectName("panel_title")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_panel.addWidget(lbl_title)

        form = QGridLayout()
        form.setSpacing(10)

        form.addWidget(QLabel("Nombre (s):"), 0, 0)
        self.ln_nombre = QLineEdit()
        form.addWidget(self.ln_nombre, 0, 1)

        form.addWidget(QLabel("Apellido Paterno:"), 1, 0)
        self.ln_apaterno = QLineEdit()
        form.addWidget(self.ln_apaterno, 1, 1)

        form.addWidget(QLabel("Apellido Materno:"), 2, 0)
        self.ln_amaterno = QLineEdit()
        form.addWidget(self.ln_amaterno, 2, 1)

        form.addWidget(QLabel("Correo:"), 3, 0)
        self.ln_correo = QLineEdit()
        form.addWidget(self.ln_correo, 3, 1)

        form.addWidget(QLabel("Teléfono:"), 4, 0)
        self.ln_telefono = QLineEdit()
        form.addWidget(self.ln_telefono, 4, 1)

        form.addWidget(QLabel("Área:"), 5, 0)
        self.cb_area = QComboBox()
        form.addWidget(self.cb_area, 5, 1)

        form.addWidget(QLabel("Puesto ID:"), 6, 0)
        self.ln_puesto = QLineEdit()
        self.ln_puesto.setText("1")
        form.addWidget(self.ln_puesto, 6, 1)

        layout_panel.addLayout(form)

        self.btn_guardar = QPushButton(" Guardar")
        self.btn_guardar.setFixedHeight(45)
        self.btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        layout_panel.addWidget(self.btn_guardar)
        layout_panel.addStretch()

        body.addWidget(panel)
        self.main_layout.addLayout(body)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            QLabel#Titulo { color: #EFBFBC; }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QFrame#right_panel { background-color: rgba(255, 255, 255, 15); border-radius: 12px; padding: 15px; border: 1px solid rgba(255, 255, 255, 40); }
            QLabel#panel_title { color: #EFBFBC; font: bold 14pt "MS Shell Dlg 2"; padding-bottom: 10px; border-bottom: 1px solid rgba(255,255,255, 50); }
            QLineEdit, QComboBox { background-color: white; color: black; border-radius: 6px; padding: 6px; font: 11pt "MS Shell Dlg 2"; }
            QPushButton { background-color: rgb(1, 79, 81); color: white; border-radius: 6px; padding: 8px; font: bold 11pt "MS Shell Dlg 2"; }
            QPushButton#btn_guardar { background-color: #EFBFBC; color: #013B3D; border: none; }
            QPushButton#btn_regresar, QPushButton#btn_salir { background-color: rgb(220, 53, 69); border: none; }
            QTableWidget { background-color: white; border-radius: 8px; color: #333; }
            QHeaderView::section { background-color: rgb(1, 59, 61); color: white; padding: 8px; }
        """)
