import base64
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QBuffer, QIODevice, Qt


class ImageHandler:
    @staticmethod
    def select_image():
        """Seleccionar imagen desde el sistema de archivos"""
        file_path, _ = QFileDialog.getOpenFileName(
            None,
            "Seleccionar imagen",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        return file_path

    @staticmethod
    def image_to_base64(image_path):
        """Convertir imagen a base64 para enviar a la API"""
        try:
            with open(image_path, "rb") as img_file:
                encoded_string = base64.b64encode(
                    img_file.read()).decode('utf-8')
                # Determinar el tipo MIME
                if image_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif image_path.lower().endswith(('.jpg', '.jpeg')):
                    mime_type = 'image/jpeg'
                elif image_path.lower().endswith('.bmp'):
                    mime_type = 'image/bmp'
                elif image_path.lower().endswith('.gif'):
                    mime_type = 'image/gif'
                else:
                    mime_type = 'image/jpeg'
                return f"data:{mime_type};base64,{encoded_string}"
        except Exception as e:
            raise Exception(f"Error procesando imagen: {str(e)}")

    @staticmethod
    def base64_to_image(base64_string, label):
        """Convertir base64 a imagen para mostrar en QLabel"""
        try:
            if not base64_string:
                return False
            if 'base64,' in base64_string:
                base64_string = base64_string.split('base64,')[1]
            image_data = base64.b64decode(base64_string)
            pixmap = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                label.setPixmap(pixmap.scaled(
                    label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
                return True
        except Exception as e:
            print(f"Error cargando imagen base64: {e}")
        return False

    @staticmethod
    def pixmap_to_base64(pixmap, format='JPG'):
        """Convierte un QPixmap a base64"""
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, format)
        return base64.b64encode(buffer.data()).decode('utf-8')
