from modules.administracion.administracion_ui import AdministracionUI


class AdministracionController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.ui = AdministracionUI()
        self.ui.showMaximized()
        self.ui.btn_regresar.clicked.connect(self.regresar)

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.ui.close()
