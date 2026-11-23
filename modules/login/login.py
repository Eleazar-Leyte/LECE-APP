from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

# from Desktop.modules.update_manager import UpdateManager
from data.usuarios import UsuarioData
from shared.model.user import Usuario
from modules.menu_admin import MenuAdmin  # MenuAdministrativo

from modules.update_progres import UpdateProgressWindow

import os
import sys
import subprocess
import ctypes
import json
import requests


class Login():
    def __init__(self):
        self.login = uic.loadUi("modules/login/Login.ui")
        self.initGUI()
        self.login.error_mesage.setText("")
        self.api_url = "http://localhost:8000/login"  # URL de la API para el login
        self.login.show()

    def ingresar(self):
        if len(self.login.ln_user.text()) < 2:
            self.login.error_mesage.setText("Ingrese un usuario válido")
            self.login.ln_user.setFocus()
        elif len(self.login.ln_password.text()) < 2:
            self.login.error_mesage.setText("Ingrese una contraseña válida")
            self.login.ln_password.setFocus()
        else:
            self.aurhenticate_api()

    def aurhenticate_api(self):
        """
        Autentica al usuario a través de la API
        """
        try:
            response = requests.post(
                self.api_url,
                data={
                    "username": self.login.ln_user.text(),
                    "password": self.login.ln_password.text()
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.handle_successful_login(data)
            else:
                self.handle_login_error(response)
        except requests.exceptions.ConnectionError:
            self.login.error_mesage.setText(
                "Error de conexión con el servidor")

    def handle_successful_login(self, data):
        """
        Manejar inicio de sesión exitoso con la nueva estructura
        """
        try:
            user_info = data['user_info']
            self.usuario_actual = {
                "name": user_info['name'],
                "rol": user_info['rol'],
                "area": user_info['area'],
                "area_name": user_info.get('area_name', f"Área {user_info['area']}"),
                "access_token": data['access_token']
            }

            # Abrir el menú principal
            from modules.menu_admin import MenuAdmin
            self.menu_controller = MenuAdmin(self.usuario_actual)
            self.login.close()

        except KeyError as e:
            print(f"Error en estructura de respuesta: {str(e)}")
            self.login.error_mesage.setText(
                "Error en formato de respuesta del servidor")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            self.login.error_mesage.setText(
                "Error inesperado al procesar la respuesta")

    def handle_login_error(self, response):
        """
        Manejar errores de autenticación
        """
        try:
            error_data = response.json()

            # Manejar diferentes formatos de error
            if 'detail' in error_data:
                if isinstance(error_data['detail'], list):
                    # Tomar el primer mensaje de error
                    error_msg = error_data['detail'][0].get(
                        'msg', "Error desconocido")
                else:
                    error_msg = error_data['detail']
            else:
                error_msg = str(error_data)
            self.login.error_mesage.setText(error_msg)

        except json.JSONDecodeError:
            error_text = f"Error {response.status_code}: {response.text}"
            print(f"Error al decodificar JSON: {error_text}")
            self.login.error_mesage.setText(error_text[:100])
            # Verificar actualizaciones si es Admin
            # updater = UpdateManager()
            # if updater.check_update():
            #     respuesta = QMessageBox.question(
            #         self.login,
            #         "Actualización Disponible",
            #         "¡Nueva versión detectada! ¿Actualizar ahora?",
            #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            #     )

            #     if respuesta == QMessageBox.StandardButton.Yes:
            #         self.login.hide()
            #         self.show_update_progress(updater)
            #         return

    # def show_update_progress(self, updater):
    #     self.update_window = UpdateProgressWindow()
    #     self.login.hide()
    #     updater.progress_updated.connect(self.update_window.update_progress)
    #     updater.update_finished.connect(self.handle_update_result)
    #     QTimer.singleShot(100, self.run_update)

    # def run_update(self):
    #     """Nuevo enfoque para lanzar actualización externa"""
    #     try:
    #         # 1. Cerrar ventana actual
    #         self.login.close()

    #         # 2. Lanzar actualizador externo
    #         updater_script = os.path.abspath("updater.py")
    #         subprocess.Popen([sys.executable, updater_script])

    #         # 3. Salir completamente
    #         sys.exit()

    #     except Exception as e:
    #         QMessageBox.critical(
    #             None, "Error", f"Error iniciando actualización: {str(e)}")

    # def handle_update_result(self, success):
    #     if success:
    #         QMessageBox.information(
    #             None,
    #             "Reinicio",
    #             "La aplicación se reiniciará para aplicar los cambios"
    #         )
    #         subprocess.Popen([sys.executable, os.path.abspath("index.py")])
    #         sys.exit()
    #     else:
    #         self.update_window.close()
    #         self.login.show()

    def open_user_menu(self, rol):
        if rol == "Admin":
            self.menuadmin = MenuAdmin(self.usuario_actual)
        elif rol == "Personal Técnico":
            print("Abriendo menú técnico")
        elif rol == "Personal Administrativo":
            print("Abriendo menú administrativo")
        else:
            QMessageBox.critical(self.login, "Error", "Rol no reconocido")

    def initGUI(self):
        self.login.btn_acceder.clicked.connect(self.ingresar)
