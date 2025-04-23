from PyQt6 import uic

from modules.Almacenes.almacen import Almacen
from modules.A_P_Operativo.personal import Personal
from modules.Produccion.producción import Producción
from modules.Montaje.montaje import Montaje


class MenuAdmin():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.pestaña1 = uic.loadUi("modules/Pestaña 1.ui")
        self.pestaña1.show()
        self.botones()

    def botones(self):
        self.pestaña1.btn_personal.clicked.connect(self.win_personal)
        self.pestaña1.btn_almacen.clicked.connect(self.win_almacen)
        self.pestaña1.btn_produccion.clicked.connect(self.win_produccion)
        self.pestaña1.btn_montaje.clicked.connect(self.win_montaje)
        self.pestaña1.btn_salir.clicked.connect(self.salir)

    def win_personal(self):
        self.personal = Personal(self.usuario_actual)
        self.pestaña1.close()

    def win_almacen(self):
        self.almacen = Almacen(self.usuario_actual)
        self.pestaña1.close()

    def win_produccion(self):
        self.produccion = Producción(self.usuario_actual)
        self.pestaña1.close()

    def win_montaje(self):
        self.montaje = Montaje(self.usuario_actual)
        self.pestaña1.close()

    def salir(self):
        self.pestaña1.close()
