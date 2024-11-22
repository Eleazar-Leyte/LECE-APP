from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox

from data.usuarios import UsuarioData
from model.user import Usuario
from modules.almacen import Almacen
from modules.personal import Personal


class Pestaña1():
    def __init__(self):
        self.pestaña1 = uic.loadUi("modules/Pestaña 1.ui")
        self.pestaña1.show()
        self.botones()

    def botones(self):
        self.pestaña1.btn_personal.clicked.connect(self.win_personal)
        self.pestaña1.btn_almacen.clicked.connect(self.win_almacen)
        self.pestaña1.btn_produccion.clicked.connect(self.win_produccion)
        self.pestaña1.btn_salir.clicked.connect(self.salir)

    def win_personal(self):
        self.personal = Personal()
        self.pestaña1.close()

    def win_almacen(self):
        self.almacen = Almacen()
        self.pestaña1.close()

    def win_produccion(self):
        print('Abriendo ventana de producción')

    def salir(self):
        self.pestaña1.close()
