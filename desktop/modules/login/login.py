from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

# Importamos nuestra nueva UI
from desktop.modules.login.login_ui import LoginUI
from desktop.modules.menu_admin import MenuAdmin

import os
import sys
import json
import requests


class Login():
    def __init__(self):
        # 1. Cambiamos el uic.loadUi por nuestra clase
        self.login = LoginUI()

        self.initGUI()
        self.login.error_mesage.setText("")
        self.api_url = "http://localhost:8000/login"

        # 2. Mostramos la ventana
        self.login.show()

    def initGUI(self):
        self.login.btn_acceder.clicked.connect(self.ingresar)

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
        # Deshabilitamos el botón mientras carga
        self.login.btn_acceder.setEnabled(False)
        self.login.btn_acceder.setText("Autenticando...")
        self.login.error_mesage.setText("")

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
            self.login.btn_acceder.setEnabled(True)
            self.login.btn_acceder.setText("Acceder")

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
            self.menu_controller = MenuAdmin(self.usuario_actual)
            self.login.close()

        except KeyError as e:
            print(f"Error en estructura de respuesta: {str(e)}")
            self.login.error_mesage.setText(
                "Error en formato de respuesta del servidor")
            self.login.btn_acceder.setEnabled(True)
            self.login.btn_acceder.setText("Acceder")
        except Exception as e:
            print(f"Error inesperado: {str(e)}")
            self.login.error_mesage.setText(
                "Error inesperado al procesar la respuesta")
            self.login.btn_acceder.setEnabled(True)
            self.login.btn_acceder.setText("Acceder")

    def handle_login_error(self, response):
        """
        Manejar errores de autenticación
        """
        self.login.btn_acceder.setEnabled(True)
        self.login.btn_acceder.setText("Acceder")

        try:
            error_data = response.json()
            if 'detail' in error_data:
                if isinstance(error_data['detail'], list):
                    error_msg = error_data['detail'][0].get(
                        'msg', "Error desconocido")
                else:
                    error_msg = error_data['detail']
            else:
                error_msg = str(error_data)
            self.login.error_mesage.setText(error_msg)

        except json.JSONDecodeError:
            self.login.error_mesage.setText(
                f"Error {response.status_code}: Credenciales incorrectas")
