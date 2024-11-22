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


class BarcodeScanner(QThread):
    # Emitimos el código y la imagen capturada
    code_detected = pyqtSignal(str, np.ndarray)
    # Nueva señal para el frame capturado
    frame_captured = pyqtSignal(np.ndarray)

    def __init__(self, camera_index=0):
        super().__init__()
        self.camera_index = camera_index
        self._run_flag = True

    def run(self):
        cap = cv2.VideoCapture(self.camera_index)
        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                break

            # Emitimos el frame para mostrarlo en la interfaz
            self.frame_captured.emit(frame)

            # Detectamos códigos de barras
            decoded_objects = decode(
                frame, symbols=[ZBarSymbol.EAN13,
                                ZBarSymbol.EAN8, ZBarSymbol.CODE128]
            )
            for obj in decoded_objects:
                codigo = obj.data.decode("utf-8")
                self.code_detected.emit(codigo, frame)
                self._run_flag = False  # Detenemos el hilo después de detectar un código
                break

        cap.release()

    def stop(self):
        self._run_flag = False


class R_MODEM():
    def __init__(self):
        # Carga de la interfaz grafica R_MODEM
        self.r_modem = uic.loadUi("modules/R_MODEM.ui")
        self.r_modem.show()

        # Desactiva el label_imagen al inicio
        self.r_modem.label_imagen.setEnabled(False)

        # Conectar a las bases de datos usando DatabaseManager
        self.db_personal = DatabaseManager("personal.db")
        self.db_areas = DatabaseManager("Areas.db")
        self.db_almacen = DatabaseManager("Almacen_construcción.db")

        self.cargar_botones()
        self.cargar_areas()

    def cargar_botones(self):
        # Conectamos los botones
        self.r_modem.str_area.currentIndexChanged.connect(self.actualizar_cope)
        self.r_modem.str_ubicacion.currentIndexChanged.connect(
            self.actualizar_exptec)
        self.r_modem.str_cope.currentIndexChanged.connect(
            self.actualizar_exptec)
        self.r_modem.btn_codebar.clicked.connect(self.star_barcode_scanner)
        self.r_modem.btn_imagen.clicked.connect(self.importarimagen)
        self.r_modem.btn_guardar.clicked.connect(self.guardar)
        self.r_modem.btn_regresar.clicked.connect(self.regresar)

    def is_connected(self):
        try:
            self.connection.cursor()
            return True
        except sqlite3.ProgrammingError:
            return False

    def cargar_areas(self):
        if not self.db_areas.is_connected():
            # Reabrir la conexión si está cerrada
            self.db_areas = DatabaseManager("Areas.db")
        query = "SELECT name FROM sqlite_master WHERE type='table'"
        cursor = self.db_areas.execute_query(query)  # Obtener el cursor
        tablas = cursor.fetchall()  # Recuperar los resultados
        cursor.close()  # Cerrar el cursor después de usarlo

        self.r_modem.str_area.clear()
        for tabla in tablas:
            self.r_modem.str_area.addItem(tabla[0])

    def actualizar_cope(self):
        area_seleccionada = self.r_modem.str_area.currentText()
        if area_seleccionada:
            # Validamos el nombre de la tabla
            if not area_seleccionada.isidentifier():
                QMessageBox.critical(self.r_modem, "Error",
                                     "Nombre de área invalido")
                return

            # Construimos la consulta de forma segura
            query = f"SELECT DISTINCT Copé FROM {area_seleccionada}"
            try:
                cursor = self.db_areas.execute_query(query)
                valores_cope = cursor.fetchall()
                cursor.close()

                self.r_modem.str_cope.clear()
                for valor in valores_cope:
                    self.r_modem.str_cope.addItem(valor[0])
            except sqlite3.Error as e:
                QMessageBox.critical(self.r_modem, "Error",
                                     f"Error al cargar los datos de Coper: {e}")

    def actualizar_exptec(self):
        ubicacion_seleccionada = self. r_modem.str_ubicacion.currentText()

        # Función para activar el filtro 'Expediente Técnico' en base al modo seleccionado
        if ubicacion_seleccionada == "Almacén":
            self.r_modem.str_exptec.setVisible(False)
            self.r_modem.label_7.setVisible(False)

        elif ubicacion_seleccionada == "En campo":
            self.r_modem.str_exptec.setVisible(True)
            self.r_modem.label_7.setVisible(True)
            self.cargar_tecnicos()

    def cargar_tecnicos(self):
        # Cargamos el nombre del personal operativo filtrado por Área y Copé
        area_seleccionada = self.r_modem.str_area.currentText()
        cope_seleccionado = self.r_modem.str_cope.currentText()

        if area_seleccionada and cope_seleccionado:
            try:
                consulta = """
                    SELECT [Nombre (s)], [Apellido Paterno] 
                    FROM Personal_O
                    WHERE  [Área] = ? AND [Cope] = ?
                    """
                cursor = self.db_personal.execute_query(
                    consulta, (area_seleccionada, cope_seleccionado))
                tecnicos = cursor.fetchall()
                cursor.close()

                self.r_modem.str_exptec.clear()
                for nombre, apellido in tecnicos:
                    self.r_modem.str_exptec.addItem(f"{nombre} {apellido}")
            except sqlite3.Error as e:
                QMessageBox.critical(
                    self.r_modem, "Error", f"Error al cargar los datos técnicos: {e}")

    def star_barcode_scanner(self):
        self.barcode_scaner = BarcodeScanner()
        self.barcode_scaner.code_detected.connect(self.leercodebar)
        self.barcode_scaner.frame_captured.connect(
            self.show_frame_in_ui)  # Conectamos el frame capturado
        self.barcode_scaner.start()

    def show_frame_in_ui(self, frame):
        # Mostramos el frame en el Qlabel
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_rgb.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)
        # Activa el label_imagen y muestra el frame capturado
        self.r_modem.label_imagen.setEnabled(True)
        self.r_modem.label_imagen.setPixmap(QPixmap.fromImage(q_image))

    def leercodebar(self, code, frame):
        self.r_modem.ln_ns.setText(code)
        print(f"Código de barras detectado: {code}")
        self.save_image(frame)
        self.barcode_scaner.stop()

    def save_image(self, frame):
        # Convertir el frame a RGB y crear un QImage
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_rgb.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)

        # Mostramos la imagen en el QLabel
        self.r_modem.label_imagen.setEnabled(True)
        self.r_modem.label_imagen.setPixmap(QPixmap.fromImage(q_image))

        # Guardar la imagen como QByteArray en formato .jpg
        buffer = QBuffer()
        # Cambiado de QIODevice.WriteOnly a QBuffer.WriteOnly
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        q_image.save(buffer, "JPG")  # Cambiado el formato a JPG
        self.imagen_bytes = buffer.data()
        buffer.close()

        # Limpia y desactiva el label_imagen después de guardar
        self.r_modem.label_imagen.clear()
        self.r_modem.label_imagen.setEnabled(False)

    def importarimagen(self):
        # Abrir un cuadro de diálogo para seleccionar la imagen
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self.r_modem, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")

        if not image_path:
            QMessageBox.warning(self.r_modem, "Advertencia",
                                "No se seleccionó ninguna imagen.")
            return

        # Cargar la imagen seleccionada
        image = cv2.imread(image_path)
        if image is None:
            QMessageBox.critical(self.r_modem, "Error",
                                 "No se pudo cargar la imagen seleccionada.")
            return

        # Mostrar la imagen en el QLabel
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_rgb.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)
        self.r_modem.label_imagen.setEnabled(True)
        self.r_modem.label_imagen.setPixmap(QPixmap.fromImage(q_image))

        # Detectar el código de barras en la imagen
        decoded_objects = decode(
            image, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.CODE128])

        if not decoded_objects:
            QMessageBox.warning(
                self.r_modem, "Advertencia", "No se detectó ningún código de barras en la imagen.")
            return

        # Usar el primer código detectado
        codigo = decoded_objects[0].data.decode("utf-8")
        self.r_modem.ln_ns.setText(codigo)
        QMessageBox.information(
            self.r_modem, "Código Detectado", f"Código de barras detectado: {codigo}")

        # Guardar la imagen como bytes para la base de datos
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        q_image.save(buffer, "JPG")
        self.imagen_bytes = buffer.data()
        buffer.close()

    def guardar(self):
        numero_serie = self.r_modem.ln_ns.text().strip()
        modelo = self.r_modem.ln_modelo.text().strip()
        area = self.r_modem.str_area.currentText().strip()
        centro_trabajo = self.r_modem.str_cope.currentText().strip()
        expediente_tecnico = self.r_modem.str_exptec.currentText().strip()
        ubicacion = self.r_modem.str_ubicacion.currentText().strip()

        if not numero_serie or not modelo or not area or not centro_trabajo:
            QMessageBox.warning(
                self.r_modem, "Advertencia", "Por favor, complete todos los campos obligatorios.")
            return

        cantidad = 1
        unidad = "pieza"

        pixmap = self.r_modem.label_imagen.pixmap()
        if pixmap is None:
            QMessageBox.warning(self.r_modem, "Advertencia",
                                "Por favor, capture o seleccione una imagen.")
            return

        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "JPG")
        imagen_bytes = buffer.data()
        buffer.close()

        if ubicacion == "Almacén":
            consulta = """
                INSERT INTO MODEM (
                    "Numero de serie", "Cantidad", "Unidad", "Modelo", "Area", "Centro de Trabajo", "Imagen", "Ubicación"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
            datos = (numero_serie, cantidad, unidad, modelo,
                     area, centro_trabajo, imagen_bytes, ubicacion)
            db = self.db_almacen

        elif ubicacion == "En campo":
            if not expediente_tecnico:
                QMessageBox.warning(
                    self.r_modem, "Advertencia", "Por favor, ingrese el expediente técnico.")
                return
            # Verificar y crear la tabla si no existe
            if not self.verificar_tabla("MODEM en campo"):
                self.crear_tabla_modem_en_campo()

            consulta = """
                INSERT INTO "MODEM en campo" (
                    "Numero de serie", "Cantidad", "Unidad", "Modelo", "Area", "Centro de Trabajo", "Expediente Técnico", "Imagen"
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
            datos = (numero_serie, cantidad, unidad, modelo, area,
                     centro_trabajo, expediente_tecnico, imagen_bytes)
            db = self.db_almacen

        else:
            QMessageBox.warning(
                self.r_modem, "Advertencia", "Ubicación no válida.")
            return

        try:
            db.execute_query(consulta, datos)
            QMessageBox.information(
                self.r_modem, "Éxito", "Datos guardados correctamente.")
            self.limpiar_campos()
        except sqlite3.IntegrityError:
            QMessageBox.critical(
                self.r_modem, "Error", "El número de serie ya existe en la base de datos.")
        except Exception as e:
            QMessageBox.critical(self.r_modem, "Error",
                                 f"Error al guardar los datos: {e}")

    def verificar_tabla(self, table_name):
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        cursor = self.db_almacen.execute_query(query, (table_name,))
        resultado = cursor.fetchone()
        cursor.close()
        return resultado is not None

    def crear_tabla_modem_en_campo(self):
        query = """
        CREATE TABLE IF NOT EXISTS "MODEM en campo" (
            "Numero de serie" TEXT PRIMARY KEY,
            "Cantidad" INTEGER NOT NULL,
            "Unidad" TEXT NOT NULL,
            "Modelo" TEXT NOT NULL,
            "Area" TEXT NOT NULL,
            "Centro de Trabajo" TEXT NOT NULL,
            "Expediente Técnico" TEXT NOT NULL,
            "Imagen" BLOB
        )
        """
        self.db_almacen.execute_query(query)

    def limpiar_campos(self):
        self.r_modem.ln_ns.clear()
        self.r_modem.ln_modelo.clear()
        self.r_modem.label_imagen.clear()
        self.r_modem.str_area.setCurrentIndex(0)
        self.r_modem.str_cope.setCurrentIndex(0)
        self.r_modem.str_exptec.setCurrentIndex(0)
        self.r_modem.str_ubicacion.setCurrentIndex(0)

    def regresar(self):
        self.r_modem.close()
