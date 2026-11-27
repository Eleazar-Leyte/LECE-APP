from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt


class AdministracionUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Administración y Finanzas")
        self.resize(1000, 600)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        lbl = QLabel("Módulo Financiero - En Construcción")
        lbl.setFont(QFont("Times New Roman", 24, QFont.Weight.Bold))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: #EFBFBC;")

        self.btn_regresar = QPushButton(" Regresar")
        self.btn_regresar.setFixedSize(150, 40)
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))

        layout.addStretch()
        layout.addWidget(lbl)
        layout.addWidget(self.btn_regresar,
                         alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()

        central.setStyleSheet("background: #013B3D;")
