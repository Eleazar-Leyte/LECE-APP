from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox

from data.usuarios import UsuarioData
from model.user import Usuario
from modules.menu import Pestaña1


class Login():
    def __init__(self):
        self.login = uic.loadUi("modules/Login.ui")
        self.initGUI()
        self.login.error_mesage.setText("")
        self.login.show()

    def ingresar(self):
        if len(self.login.ln_user.text()) < 2:
            self.login.error_mesage.setText("Ingrese un usuario válido")
            self.login.ln_user.setFocus()
        elif len(self.login.ln_password.text()) < 2:
            self.login.error_mesage.setText("Ingrese una contrasena válida")
            self.login.ln_password.setFocus()
        else:
            self.login.error_mesage.setText("")
            usu = Usuario(usuario=self.login.ln_user.text(),
                          contraseña=self.login.ln_password.text())
            usuData = UsuarioData()
            res = usuData.login(usu)
            if res:
                self.pestaña1 = Pestaña1()
                self.login.close()
            else:
                self.login.error_mesage.setText("Datos de acceso incorrectos")

    def initGUI(self):
        self.login.btn_acceder.clicked.connect(self.ingresar)
