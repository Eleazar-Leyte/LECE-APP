from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer

from modules.update_manager import UpdateManager
from data.usuarios import UsuarioData
from model.user import Usuario
from modules.menu_admin import MenuAdmin  # MenuAdminsitrativo

import os
import sys
import subprocess


class Login():
    def __init__(self):
        self.login = uic.loadUi("modules\login\Login.ui")
        self.initGUI()
        self.login.error_mesage.setText("")
        self.login.show()

    def ingresar(self):
        if len(self.login.ln_user.text()) < 2:
            self.login.error_mesage.setText("Ingrese un usuario válido")
            self.login.ln_user.setFocus()
        elif len(self.login.ln_password.text()) < 2:
            self.login.error_mesage.setText("Ingrese una contraseña válida")
            self.login.ln_password.setFocus()
        else:
            self.login.error_mesage.setText("")
            usu = Usuario(usuario=self.login.ln_user.text(),
                          contraseña=self.login.ln_password.text())
            usuData = UsuarioData()
            res = usuData.login(usu)

            if res:
                # Determinar el rol del usuario y pasar la información
                self.usuario_actual = {
                    "nombre": res._nombre,
                    "rol": res._rol,
                    "area": res._area  # Ahora incluye el área
                }
                # Verificar actualizaciones si es Admin
                updater = UpdateManager()
                if updater.check_update():
                    respuesta = QMessageBox.question(
                        self.login,
                        "Actualización Disponible",
                        "¡Nueva versión detectada! ¿Actualizar ahora?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )

                    if respuesta == QMessageBox.StandardButton.Yes:
                        self.login.hide()
                        self.show_update_progress(updater)
                        return

                # Continuar al menú correspondiente
                self.open_user_menu(res._rol)
                self.login.close()
            else:
                self.login.error_mesage.setText("Datos de acceso incorrectos")

    def show_update_progress(self, updater):
        self.update_window = UpdateProgressWindow()
        self.update_window.show()

        updater.progress_updated.connect(self.update_window.update_progress)
        updater.update_finished.connect(self.handle_update_result)

        QTimer.singleShot(100, lambda: self.run_update(updater))

    def run_update(self, updater):
        success = updater.perform_update()
        self.handle_update_result(success)

    def handle_update_result(self, success):
        if success:
            QMessageBox.information(
                self.update_window,
                "Reinicio",
                "La aplicación se reiniciará para aplicar los cambios"
            )
            subprocess.Popen([sys.executable, os.path.abspath("index.py")])
            sys.exit()
        else:
            self.update_window.close()
            self.login.show()

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
