from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QAction, QPainter, QColor, QPen
from PyQt6.QtCore import Qt, QSize


class LoginUI(QDialog):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("LoginDialog")
        self.setWindowTitle("Iniciar Sesión")
        self.setWindowIcon(QIcon("assets/images/Nuevo aspecto.png"))
        self.setFixedSize(350, 480)

        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #333333;
                font: 12pt "MS Shell Dlg 2";
            }
            QLineEdit {
                font: 12pt "MS Shell Dlg 2";
                color: #333333;
                padding: 8px 12px;
                padding-right: 30px; /* Espacio extra a la derecha para el ícono */
                border: 1px solid #cccccc;
                border-radius: 6px;
                background-color: #f9f9f9;
            }
            QLineEdit:focus {
                border: 2px solid rgb(0, 175, 255);
                background-color: #ffffff;
            }
            QPushButton {
                font: bold 12pt "MS Shell Dlg 2";
                background-color: rgb(0, 175, 255);
                color: white;
                border-radius: 8px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: rgb(0, 150, 220);
            }
            QPushButton:pressed {
                background-color: rgb(0, 130, 200);
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(40, 30, 40, 30)

        # 1. Logo
        self.logo = QLabel()
        self.logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap("assets/images/Nuevo aspecto.png")
        self.logo.setPixmap(pixmap.scaled(
            100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        main_layout.addWidget(self.logo)

        # 2. Título
        self.lbl_title = QLabel("Inicio de Sesión")
        self.lbl_title.setFont(QFont("Times New Roman", 20, QFont.Weight.Bold))
        self.lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_title.setStyleSheet("color: #013B3D; margin-bottom: 15px;")
        main_layout.addWidget(self.lbl_title)

        # 3. Campo de Usuario
        lbl_user = QLabel("Usuario:")
        self.ln_user = QLineEdit()
        self.ln_user.setPlaceholderText("Ingrese su usuario")
        main_layout.addWidget(lbl_user)
        main_layout.addWidget(self.ln_user)

        # 4. Campo de Contraseña
        lbl_pass = QLabel("Contraseña:")
        self.ln_password = QLineEdit()
        self.ln_password.setPlaceholderText("Ingrese su contraseña")
        self.ln_password.setEchoMode(QLineEdit.EchoMode.Password)

        # --- BOTÓN MOSTRAR/OCULTAR CON ICONO DIBUJADO ---
        self.action_toggle_pass = QAction(self.ln_password)
        self.action_toggle_pass.setIcon(QIcon(self._crear_icono_ojo(False)))
        self.action_toggle_pass.triggered.connect(
            self.toggle_password_visibility)
        self.ln_password.addAction(
            self.action_toggle_pass, QLineEdit.ActionPosition.TrailingPosition)

        main_layout.addWidget(lbl_pass)
        main_layout.addWidget(self.ln_password)

        # 5. Mensaje de Error
        self.error_mesage = QLabel("")
        self.error_mesage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_mesage.setStyleSheet(
            "color: red; font-weight: bold; font-size: 10pt;")
        self.error_mesage.setWordWrap(True)
        main_layout.addWidget(self.error_mesage)

        main_layout.addStretch()

        # 6. Botón Acceder
        self.btn_acceder = QPushButton("Acceder")
        self.btn_acceder.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_acceder.setFixedHeight(45)
        main_layout.addWidget(self.btn_acceder)

    # =========================================================================
    # FUNCIONES PARA DIBUJAR EL ICONO DEL OJO
    # =========================================================================
    def _crear_icono_ojo(self, tachado=False):
        """Dibuja un ícono de ojo (abierto o tachado) usando QPainter"""
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor("#666666")  # Color gris oscuro
        pen = QPen(color, 2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Dibujar el contorno del ojo (una especie de rombo/elipse)
        painter.drawEllipse(4, 7, 16, 10)

        # Dibujar la pupila
        painter.setBrush(color)
        painter.drawEllipse(9, 9, 6, 6)

        # Si está tachado, dibujar una línea diagonal
        if tachado:
            painter.setPen(QPen(QColor("red"), 2))
            painter.drawLine(4, 18, 20, 6)

        painter.end()
        return pixmap

    def toggle_password_visibility(self):
        """Alterna entre mostrar y ocultar la contraseña"""
        if self.ln_password.echoMode() == QLineEdit.EchoMode.Password:
            self.ln_password.setEchoMode(QLineEdit.EchoMode.Normal)
            # Cambia el ícono al ojo tachado
            self.action_toggle_pass.setIcon(
                QIcon(self._crear_icono_ojo(tachado=True)))
        else:
            self.ln_password.setEchoMode(QLineEdit.EchoMode.Password)
            # Cambia el ícono al ojo normal
            self.action_toggle_pass.setIcon(
                QIcon(self._crear_icono_ojo(tachado=False)))
