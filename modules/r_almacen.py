import sqlite3
import cv2
import numpy as np
import os

from pyzbar.pyzbar import decode, ZBarSymbol
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, QByteArray, QBuffer, QIODevice

from DatabaseManager import DatabaseManager


class R_Almacen():
    def __init__(self):
        # Carga de la interfaz grafica R_almacen
        self.r_ont = uic.loadUi("modules/R_almacen.ui")
        self.r_ont.show()
