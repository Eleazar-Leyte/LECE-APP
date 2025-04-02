from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox

from data.usuarios import UsuarioData
from model.user import Usuario
from modules.menu_admin import MenuAdmin  # MenuAdminsitrativo
# from modules.tecnico_menu import TecnicoMenu


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

                if res._rol == "Admin":
                    self.menuadmin = MenuAdmin(self.usuario_actual)
                    print(self.usuario_actual)
                elif res._rol == "Personal Técnico":
                    # self.menutecnico = Menutecnico(self.usuario_actual)
                    print("Abriendo menú técnico")
                elif res._rol == "Personal Administrativo":
                    # self.menuadministrativo = MenuAdministrativo(self.usuario_actual)
                    print("Abriendo menú administrativo")
                else:
                    QMessageBox.critical(self.login, "Error",
                                         "El rol del usuario no está reconocido. Contacte al administrador.")
                    return
                self.login.close()
            else:
                self.login.error_mesage.setText("Datos de acceso incorrectos")

    def initGUI(self):
        self.login.btn_acceder.clicked.connect(self.ingresar)
