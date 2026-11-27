import base64
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                             QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QLabel)
from PyQt6.QtGui import (QPixmap, QPainter, QColor,
                         QPen, QPainterPath, QImage, QTransform)
from PyQt6.QtCore import Qt, QRectF, QBuffer, QIODevice


class VisorCrop(QGraphicsView):
    """Visor personalizado que dibuja la máscara circular y permite arrastrar."""

    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setFixedSize(340, 340)

        # Ocultar barras para un look limpio
        self.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "background-color: #111; border: 2px solid #013B3D; border-radius: 12px;")

    def drawForeground(self, painter, rect):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRect(rect)

        # Círculo central (Radio 125)
        circle = QPainterPath()
        center = QRectF(0, 0, 340, 340).center()
        radius = 125
        circle.addEllipse(center, radius, radius)
        path = path.subtracted(circle)

        # Máscara oscura
        painter.fillPath(path, QColor(0, 0, 0, 200))

        # Borde del círculo
        pen = QPen(QColor("#EFBFBC"), 3)
        painter.setPen(pen)
        painter.drawEllipse(center, radius, radius)
        painter.restore()


class EditorFotoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajustar Foto de Perfil")
        self.setFixedSize(400, 520)

        self.setStyleSheet("""
            QDialog { background-color: #013B3D; }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                color: white;
                border-radius: 6px;
                padding: 8px;
                font: bold 12pt "MS Shell Dlg 2";
                border: 1px solid rgba(255, 255, 255, 50);
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 40); }
            QPushButton#btn_aplicar {
                background-color: #EFBFBC;
                color: #013B3D;
                border: none;
            }
            QPushButton#btn_aplicar:hover { background-color: #E5AFA9; }
            QPushButton#btn_cancelar {
                background-color: #d9534f;
                color: white;
                border: none;
            }
            QPushButton#btn_cancelar:hover { background-color: #c9302c; }
        """)

        self.imagen_b64_resultante = None
        self.current_pixmap = None

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_info = QLabel("Arrastra la foto para centrarla en el círculo.")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        # Configurar escena y visor
        self.scene = QGraphicsScene(self)
        self.scene.setSceneRect(0, 0, 340, 340)
        self.view = VisorCrop(self.scene, self)
        layout.addWidget(self.view, alignment=Qt.AlignmentFlag.AlignCenter)

        self.pixmap_item = QGraphicsPixmapItem()
        self.pixmap_item.setFlag(
            QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        self.scene.addItem(self.pixmap_item)

        # Botones de transformación (Íconos minimalistas)
        transform_layout = QHBoxLayout()
        transform_layout.setSpacing(10)

        self.btn_rotar_izq = QPushButton("↺")
        self.btn_rotar_der = QPushButton("↻")
        self.btn_flip_h = QPushButton("↔")
        self.btn_flip_v = QPushButton("↕")

        for btn in [self.btn_rotar_izq, self.btn_rotar_der, self.btn_flip_h, self.btn_flip_v]:
            btn.setFixedSize(50, 40)
            btn.setToolTip("Transformar imagen")
            transform_layout.addWidget(btn)

        layout.addLayout(transform_layout)
        layout.addStretch()

        # Botones de Acción
        action_layout = QHBoxLayout()

        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setObjectName("btn_cancelar")
        self.btn_cancelar.setFixedHeight(45)
        self.btn_cancelar.clicked.connect(self.reject)

        self.btn_aplicar = QPushButton("Aplicar")
        self.btn_aplicar.setObjectName("btn_aplicar")
        self.btn_aplicar.setFixedHeight(45)
        self.btn_aplicar.clicked.connect(self._guardar)

        action_layout.addWidget(self.btn_cancelar)
        action_layout.addWidget(self.btn_aplicar)
        layout.addLayout(action_layout)

        self.btn_rotar_izq.clicked.connect(lambda: self._rotar_pixmap(-90))
        self.btn_rotar_der.clicked.connect(lambda: self._rotar_pixmap(90))
        self.btn_flip_h.clicked.connect(self._flip_horizontal)
        self.btn_flip_v.clicked.connect(self._flip_vertical)

    def cargar_imagen(self, file_path):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # --- CORRECCIÓN CLAVE: Escalar la imagen si es muy grande ---
            if pixmap.width() > 400 or pixmap.height() > 400:
                pixmap = pixmap.scaled(
                    400, 400, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

            self.current_pixmap = pixmap
            self._actualizar_pixmap_en_escena()
            self.view.centerOn(self.pixmap_item)

    def _actualizar_pixmap_en_escena(self):
        if self.current_pixmap:
            self.pixmap_item.setPixmap(self.current_pixmap)
            self.pixmap_item.setPos(
                (340 - self.current_pixmap.width()) / 2,
                (340 - self.current_pixmap.height()) / 2
            )

    def _rotar_pixmap(self, angulo):
        if self.current_pixmap:
            transform = QTransform().rotate(angulo)
            self.current_pixmap = self.current_pixmap.transformed(transform)
            self._actualizar_pixmap_en_escena()

    def _flip_horizontal(self):
        if self.current_pixmap:
            transform = QTransform().scale(-1, 1)
            self.current_pixmap = self.current_pixmap.transformed(transform)
            self._actualizar_pixmap_en_escena()

    def _flip_vertical(self):
        if self.current_pixmap:
            transform = QTransform().scale(1, -1)
            self.current_pixmap = self.current_pixmap.transformed(transform)
            self._actualizar_pixmap_en_escena()

    def _guardar(self):
        # Área del círculo
        center = QRectF(0, 0, 340, 340).center()
        radius = 125
        source_rect = QRectF(center.x() - radius,
                             center.y() - radius, radius * 2, radius * 2)

        # Lienzo final de 250x250
        image = QImage(250, 250, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Máscara circular
        path = QPainterPath()
        path.addEllipse(0, 0, 250, 250)
        painter.setClipPath(path)

        self.scene.render(painter, QRectF(0, 0, 250, 250), source_rect)
        painter.end()

        # Base64
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        self.imagen_b64_resultante = base64.b64encode(
            buffer.data()).decode('utf-8')
        buffer.close()

        self.accept()
