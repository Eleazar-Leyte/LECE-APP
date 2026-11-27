import base64
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout, QPushButton,
    QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QFont, QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QSize
from desktop.modules.ajustes.settings_manager import SettingsManager


class MainMenuUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Inicio - S.A.P.")
        self.setMinimumSize(800, 600)

        # Widget central con scroll para adaptarse a diferentes tamaños
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(self.scroll_area)

        # Contenedor principal
        self.central_container = QWidget()
        self.scroll_area.setWidget(self.central_container)

        # Layout principal
        self.main_layout = QVBoxLayout(self.central_container)
        self.main_layout.setContentsMargins(20, 20, 20, 20)
        self.main_layout.setSpacing(20)

        # Encabezado
        self.header = QWidget()
        self.header_layout = QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(15, 15, 15, 15)

        # Contenedor de tarjetas (CORREGIDO: usar central_container en lugar de cards_container)
        self.cards_widget = QWidget()
        self.cards_layout = QGridLayout(self.cards_widget)
        self.cards_layout.setSpacing(20)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)

        # Pie de página
        self.footer = QLabel(
            "<p>Sistema de Cuadre de Materiales v1.0 © 2024</p>")
        self.footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.footer.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        # Ensamblar layout
        self.main_layout.addWidget(self.header)
        self.main_layout.addWidget(self.cards_widget)
        self.main_layout.addWidget(self.footer)

        # Componentes que el controlador necesitará acceder
        self.user_icon_label = None
        self.user_info_label = None
        self.btn_logout = None
        self.menu_cards = []

    def setup_header(self, user_name, user_role, user_area):
        """Configura el encabezado con información del usuario"""
        # Limpiar layout existente
        while self.header_layout.count():
            child = self.header_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Crear el QLabel para el avatar
        self.lbl_avatar = QLabel()
        self.lbl_avatar.setFixedSize(60, 60)
        self.lbl_avatar.setStyleSheet(
            "background-color: transparent; border-radius: 30px;")
        self.lbl_avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Cargar foto de perfil si existe
        config = SettingsManager.cargar_config()
        foto_b64 = config.get("perfil_b64")

        if foto_b64:
            pixmap = QPixmap()
            pixmap.loadFromData(base64.b64decode(foto_b64))
            if not pixmap.isNull():
                # Crear imagen circular
                target = QPixmap(60, 60)
                target.fill(Qt.GlobalColor.transparent)
                painter = QPainter(target)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                path = QPainterPath()
                path.addEllipse(0, 0, 60, 60)
                painter.setClipPath(path)
                scaled = pixmap.scaled(
                    60, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
                x = (scaled.width() - 60) // 2
                y = (scaled.height() - 60) // 2
                painter.drawPixmap(0, 0, scaled, x, y, 60, 60)
                painter.end()

                self.lbl_avatar.setPixmap(target)
        else:
            # Si no hay foto, mostrar un ícono por defecto (puedes usar un emoji o un ícono de la carpeta assets)
            self.lbl_avatar.setText("👤")
            self.lbl_avatar.setFont(QFont("Arial", 28))
            self.lbl_avatar.setStyleSheet(
                "background-color: #E0E0E0; border-radius: 30px; color: #333;")

        # Información del usuario
        self.user_info_label = QLabel(
            f"<h2>Bienvenido, <span style='color: #8BC34A;'>{user_name}</span></h2>"
            f"<p>Área: {user_area} | Rol: {user_role}</p>"
        )

        # Botón cerrar sesión
        self.btn_logout = QPushButton(" Cerrar Sesión")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                background-color: #555;
                color: white;
                border: 1px solid #444;
                border-radius: 6px;
                font: 11pt "MS Shell Dlg 2";
            }
            QPushButton:hover {
                background-color: #666;
            }
        """)

        # Agregar componentes al layout
        self.header_layout.addWidget(self.lbl_avatar)
        self.header_layout.addSpacing(15)  # Espacio entre avatar y texto
        self.header_layout.addWidget(self.user_info_label)
        self.header_layout.addStretch()
        self.header_layout.addWidget(self.btn_logout)

    def add_menu_card(self, icon, title, description, card_id):
        """Añade una tarjeta de menú a la interfaz"""
        card = QPushButton()
        card.setObjectName(f"card_{card_id}")

        # Hacer que la tarjeta sea expansible
        card.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)
        card.setMinimumSize(200, 180)
        card.setMaximumSize(300, 220)

        # Usar estilo del sistema
        card.setStyleSheet("""
            QPushButton {
                background: palette(base);
                border: 1px solid palette(mid);
                border-radius: 12px;
                padding: 10px;
            }
            QPushButton:hover {
                background: palette(alternate-base);
                border-color: palette(highlight);
            }
        """)

        # Layout interno de la tarjeta
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(f"<h3>{title}</h3>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setWordWrap(True)

        desc_label = QLabel(f"<p>{description}</p>")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(desc_label)

        # Añadir a la grilla con cálculo dinámico de posición
        position = len(self.menu_cards)

        # Calcular columnas basado en el ancho disponible
        columns = self.calculate_columns()
        row = position // columns
        col = position % columns

        self.cards_layout.addWidget(card, row, col)

        self.menu_cards.append(card)
        return card

    def calculate_columns(self):
        """Calcula el número de columnas según el ancho disponible"""
        # Usar el ancho del widget de tarjetas
        container_width = self.cards_widget.width()
        if container_width <= 0:
            return 2  # Valor por defecto

        # Calcular columnas basado en el ancho (cada columna necesita al menos 250px)
        return max(1, min(4, container_width // 250))

    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana"""
        super().resizeEvent(event)
        self.rearrange_cards()

    def rearrange_cards(self):
        """Reorganiza las tarjetas cuando cambia el tamaño de la ventana"""
        columns = self.calculate_columns()

        # Limpiar el layout actual
        for i in reversed(range(self.cards_layout.count())):
            item = self.cards_layout.itemAt(i)
            if item.widget():
                self.cards_layout.removeWidget(item.widget())

        # Reorganizar las tarjetas
        for i, card in enumerate(self.menu_cards):
            row = i // columns
            col = i % columns
            self.cards_layout.addWidget(card, row, col)
