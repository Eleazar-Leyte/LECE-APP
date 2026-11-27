import base64
import requests
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QFileDialog, QDialog
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QPainterPath
from PyQt6.QtCore import Qt

from desktop.modules.ajustes.ajustes_ui import AjustesUI
from desktop.modules.ajustes.settings_manager import SettingsManager
from desktop.modules.ajustes.editor_foto import EditorFotoDialog


class AjustesController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.ajustes = AjustesUI()
        self.ajustes.showMaximized()

        self.config = SettingsManager.cargar_config()

        self.setup_connections()
        self.cargar_datos_actuales()

    def setup_connections(self):
        self.ajustes.btn_regresar.clicked.connect(self.regresar)
        self.ajustes.btn_salir.clicked.connect(self.salir)
        self.ajustes.btn_subir_foto.clicked.connect(self._cambiar_foto)
        self.ajustes.btn_test_conexion.clicked.connect(self._probar_conexion)
        self.ajustes.btn_guardar_ajustes.clicked.connect(self._guardar_ajustes)

    def cargar_datos_actuales(self):
        index_tema = self.ajustes.str_tema.findText(
            self.config.get("tema", "Oscuro"))
        if index_tema >= 0:
            self.ajustes.str_tema.setCurrentIndex(index_tema)

        self.ajustes.ln_api_url.setText(
            self.config.get("api_url", "http://localhost:8000"))
        self.ajustes.chk_notificaciones.setChecked(
            self.config.get("notificaciones", True))

        # Mapeo rápido de áreas (o podrías consultarlo a la API)
        AREAS = {1: "Administración", 2: "Producción",
                 3: "Almacén", 4: "Montaje", 5: "Recursos Humanos"}

        nombre = self.usuario_actual.get("name", "Usuario")
        rol = self.usuario_actual.get("rol", "Sin Rol")
        area_id = self.usuario_actual.get("area", 0)
        area_nombre = AREAS.get(area_id, f"Área {area_id}")

        self.ajustes.lbl_nombre.setText(f"<b>Nombre:</b> {nombre}")
        self.ajustes.lbl_rol.setText(f"<b>Rol:</b> {rol}")
        self.ajustes.lbl_area.setText(f"<b>Área:</b> {area_nombre}")

        foto_b64 = self.config.get("perfil_b64")
        if foto_b64:
            self._mostrar_foto_b64(foto_b64)

    def _cambiar_foto(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self.ajustes, "Seleccionar Foto de Perfil", "", "Imágenes (*.png *.jpg *.jpeg)"
        )
        if file_path:
            # 1. Abrir el diálogo de edición
            editor = EditorFotoDialog(self.ajustes)
            editor.cargar_imagen(file_path)

            # 2. Si el usuario presiona "Aplicar"
            if editor.exec() == QDialog.DialogCode.Accepted:
                b64_resultante = editor.imagen_b64_resultante
                if b64_resultante:
                    self.config["perfil_b64"] = b64_resultante
                    self._mostrar_foto_b64(b64_resultante)
                    QMessageBox.information(
                        self.ajustes, "Aviso", "Foto recortada con éxito. No olvides presionar 'Guardar Cambios' al final de la pantalla.")

    def _mostrar_foto_b64(self, b64_string):
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(b64_string))
        if not pixmap.isNull():
            # Usar la nueva función de recorte circular
            circular_pixmap = self._crear_pixmap_circular(pixmap, 120)
            self.ajustes.lbl_foto.setPixmap(circular_pixmap)
            self.ajustes.lbl_foto.setText("")

    def _crear_pixmap_circular(self, pixmap, size):
        """Recorta una imagen en un círculo perfecto y la centra."""
        target = QPixmap(size, size)
        target.fill(Qt.GlobalColor.transparent)

        painter = QPainter(target)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addEllipse(0, 0, size, size)
        painter.setClipPath(path)

        # Escalar la imagen para que cubra el círculo (sin deformar)
        scaled = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                               Qt.TransformationMode.SmoothTransformation)

        # Calcular el centro para recortar
        x = (scaled.width() - size) // 2
        y = (scaled.height() - size) // 2

        painter.drawPixmap(0, 0, scaled, x, y, size, size)
        painter.end()
        return target

    def _guardar_ajustes(self):
        self.config["tema"] = self.ajustes.str_tema.currentText()
        self.config["api_url"] = self.ajustes.ln_api_url.text().strip()
        self.config["notificaciones"] = self.ajustes.chk_notificaciones.isChecked()

        if SettingsManager.guardar_config(self.config):
            QMessageBox.information(
                self.ajustes, "Éxito",
                "Ajustes guardados correctamente.\n\nReinicia la aplicación para ver el nuevo tema en los módulos (si aplica)."
            )
        else:
            QMessageBox.critical(self.ajustes, "Error",
                                 "No se pudieron guardar los ajustes.")

    def _probar_conexion(self):
        url = self.ajustes.ln_api_url.text().strip()
        if not url:
            return
        try:
            res = requests.get(url, timeout=3)
            if res.status_code in [200, 404]:
                QMessageBox.information(
                    self.ajustes, "Éxito", "Conexión establecida correctamente.")
            else:
                QMessageBox.warning(self.ajustes, "Aviso",
                                    f"Código de respuesta: {res.status_code}")
        except Exception:
            QMessageBox.critical(self.ajustes, "Error",
                                 "No se pudo conectar con la API.")

    def regresar(self):
        from desktop.modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.ajustes.close()

    def salir(self):
        self.ajustes.close()
