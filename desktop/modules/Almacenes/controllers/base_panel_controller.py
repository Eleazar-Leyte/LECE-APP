import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol

from PyQt6.QtCore import QObject, Qt
from PyQt6.QtWidgets import (
    QMessageBox, QPushButton, QLabel, QLineEdit,
    QComboBox, QDialog, QVBoxLayout
)
from PyQt6.QtGui import QPixmap, QImage

from ..image_handler import ImageHandler


class BasePanelController(QObject):
    """
    Controlador base para todos los paneles laterales.
    Incluye manejo de imágenes, detección de código de barras y autollenado.
    """

    def __init__(self, panel_widget, main_controller):
        super().__init__()
        self.panel = panel_widget
        self.main = main_controller  # Referencia al AlmacenController
        self.current_image_data = None

        # Inicializar referencias a widgets comunes para que limpiar_campos no falle
        self.ln_ns = None
        self.label_imagen = None

    # =========================================================================
    # DETECCIÓN DE CÓDIGO DE BARRAS DESDE IMAGEN (FUNCIONALIDAD 2)
    # =========================================================================
    def _detectar_codigo_en_imagen(self, image_path):
        """
        Detecta un código de barras en una imagen estática.
        Retorna el código como string o None.
        """
        image = cv2.imread(image_path)
        if image is None:
            return None

        # Decodificar usando pyzbar
        decoded_objects = decode(
            image,
            symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.CODE128]
        )
        if decoded_objects:
            return decoded_objects[0].data.decode("utf-8")
        return None

    def _seleccionar_imagen(self, label_widget):
        """
        Selecciona una imagen, detecta el código de barras automáticamente,
        lo asigna al campo de número de serie y dispara la búsqueda.
        """
        path = ImageHandler.select_image()
        if not path:
            return

        try:
            # 1. Detectar código de barras en la imagen seleccionada
            codigo = self._detectar_codigo_en_imagen(path)
            if codigo and hasattr(self, 'ln_ns') and self.ln_ns:
                self.ln_ns.setText(codigo)
                # Disparar la búsqueda automática (si la subclase la implementa)
                self._buscar_por_serie()

            # 2. Cargar la imagen en base64 y mostrarla en el QLabel
            self.current_image_data = ImageHandler.image_to_base64(path)
            pixmap = QPixmap(path)
            if label_widget:
                label_widget.setPixmap(pixmap.scaled(
                    label_widget.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))

        except Exception as e:
            QMessageBox.warning(
                self.main.almacen,  # Usamos la ventana principal para mantener el estilo
                "Error",
                f"Error al procesar la imagen: {e}"
            )

    # =========================================================================
    # ESCÁNER CON CÁMARA (FUNCIONALIDAD 1)
    # =========================================================================
    def _leer_codigo_barras(self):
        """
        Inicia el escáner de código de barras con la cámara.
        """
        self._iniciar_scanner_camara()

    def _iniciar_scanner_camara(self):
        """
        Abre un diálogo con la cámara para escanear código de barras en tiempo real.
        """
        # Importamos el hilo del escáner aquí para evitar dependencias circulares
        from ..barcode_scanner import BarcodeScannerThread

        self.scanner_dialog = QDialog(self.main.almacen)
        self.scanner_dialog.setWindowTitle("Escáner de código de barras")
        self.scanner_dialog.resize(640, 480)

        layout = QVBoxLayout(self.scanner_dialog)
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("background-color: black;")
        layout.addWidget(self.video_label)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.scanner_dialog.reject)
        layout.addWidget(btn_cancelar)

        # Iniciar el hilo de la cámara
        self.scanner_thread = BarcodeScannerThread()
        self.scanner_thread.frame_captured.connect(self._mostrar_frame_camara)
        self.scanner_thread.code_detected.connect(self._on_codigo_detectado)
        self.scanner_thread.finished.connect(self.scanner_dialog.accept)
        self.scanner_thread.start()

        # Ejecutar el diálogo (bloquea hasta que se cierre)
        self.scanner_dialog.exec()

    def _mostrar_frame_camara(self, frame):
        """Muestra el frame de la cámara en el QLabel del diálogo."""
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line,
                      QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.video_label.setPixmap(
            pixmap.scaled(
                self.video_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        )

    def _on_codigo_detectado(self, codigo, frame):
        """
        Callback cuando se detecta un código en la cámara.
        Asigna el código al campo de número de serie y dispara la búsqueda.
        """
        if hasattr(self, 'ln_ns') and self.ln_ns:
            self.ln_ns.setText(codigo)
            # Disparar la búsqueda automática
            self._buscar_por_serie()

        # Detener el hilo y cerrar el diálogo
        if hasattr(self, 'scanner_thread'):
            self.scanner_thread.stop()
        if hasattr(self, 'scanner_dialog'):
            self.scanner_dialog.accept()

    # =========================================================================
    # AUTOLLENADO POR NÚMERO DE SERIE (FUNCIONALIDAD 1 y 3)
    # =========================================================================
    def _buscar_por_serie(self):
        """
        Método a sobrescribir en cada subclase (ONT, MODEM, Almacén).
        Debe consultar la API con el número de serie y llenar los campos.
        """
        pass

    # =========================================================================
    # LIMPIEZA Y UTILIDADES
    # =========================================================================
    def limpiar_campos(self):
        """
        Limpia los campos básicos. Usa hasattr para evitar errores si
        la subclase no ha definido algún widget.
        """
        if hasattr(self, 'ln_ns') and self.ln_ns:
            self.ln_ns.clear()
        if hasattr(self, 'label_imagen') and self.label_imagen:
            self.label_imagen.clear()
            self.label_imagen.setText("Vista previa de imagen/etiqueta")
        self.current_image_data = None

    # =========================================================================
    # HELPERS (SIN CAMBIOS)
    # =========================================================================
    def _get_combo_text(self, combo_name):
        combo = self.panel.findChild(QComboBox, combo_name)
        return combo.currentText() if combo else ""

    def _get_lineedit_text(self, lineedit_name):
        le = self.panel.findChild(QLineEdit, lineedit_name)
        return le.text().strip() if le else ""

    def _get_combobox(self, name):
        return self.panel.findChild(QComboBox, name)

    def _get_lineedit(self, name):
        return self.panel.findChild(QLineEdit, name)
