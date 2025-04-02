import cv2
import numpy as np
import os

from pyzbar.pyzbar import decode, ZBarSymbol
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QThread, pyqtSignal, QByteArray, QBuffer, QIODevice, Qt

from DatabaseManager import DatabaseManager


class BarcodeScanner(QThread):
    # Emitimos el código y la imagen capturada
    code_detected = pyqtSignal(str, np.ndarray)
    # Nueva señal para el frame capturado
    frame_captured = pyqtSignal(np.ndarray)
    # Nueva señal para indicar que el hilo ha terminado
    finished = pyqtSignal()

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
                self._run_flag = False  # Señal para detener el bucle
                break

        cap.release()
        self.finished.emit()  # Señal para indicar que el hilo ha terminado

    def stop(self):
        self._run_flag = False


class R_ont():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        # Carga de la interfaz grafica R_ONT
        self.r_ont = uic.loadUi("modules/Almacenes/R_ONT.ui")
        self.r_ont.show()

        # Desactiva el label_imagen al inicio
        self.r_ont.label_imagen.setEnabled(False)

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")

        self.cargar_botones()
        self.cargar_areas()

    def cargar_botones(self):
        self.r_ont.str_area.currentIndexChanged.connect(self.actualizar_cope)
        self.r_ont.str_ubicacion.currentIndexChanged.connect(
            self.actualizar_exptec)
        self.r_ont.str_cope.currentIndexChanged.connect(self.actualizar_exptec)
        self.r_ont.btn_codebar.clicked.connect(self.star_barcode_scanner)
        self.r_ont.btn_imagen.clicked.connect(self.importarimagen)
        self.r_ont.btn_guardar.clicked.connect(self.guardar)
        self.r_ont.btn_regresar.clicked.connect(self.regresar)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.r_ont.str_area.clear()
        self.r_ont.str_area.currentIndexChanged.connect(self.actualizar_cope)
        try:
            if self.usuario_actual["rol"] == "Directivo":
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(query)
            else:
                query = query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(
                    query, (self.usuario_actual['area'],)
                )

            if resultados:
                for resultado in resultados:
                    self.r_ont.str_area.addItem(resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.r_ont, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.r_ont, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.r_ont.str_area.currentText().strip()
        self.r_ont.str_cope.clear()

        if not area_seleccionada:
            QMessageBox.warning(
                self.r_ont, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.r_ont,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.r_ont.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.r_ont,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.r_ont, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def actualizar_exptec(self):
        ubicacion_selecionada = self.r_ont.str_ubicacion.currentText()

        # Función para actualizar el filtro de 'Expediente Técnico' en base al modo seleccionado
        if ubicacion_selecionada == "Almacén":
            self.r_ont.str_exptec.setVisible(False)
            self.r_ont.label_7.setVisible(False)

        elif ubicacion_selecionada == "En campo":
            self.r_ont.str_exptec.setVisible(True)
            self.r_ont.label_7.setVisible(True)
            self.cargar_tecnicos()

    def cargar_tecnicos(self):
        """
        Carga los técnicos filtrando por Área (id_area) y Copé.
        """
        area_seleccionada = self.r_ont.str_area.currentText()
        cope_seleccionado = self.r_ont.str_cope.currentText()

        if not area_seleccionada or not cope_seleccionado:
            QMessageBox.warning(
                self.r_ont, "Advertencia", "Por favor, seleccione un Área y un Copé válidos."
            )
            return
        try:
            # Obtener el id_area correspondiente al nombre del área seleccionada
            query_id_area = """
                SELECT id
                FROM Areas
                WHERE "Nombre del Área" = %s
            """
            resultado_id_area = self.db_personal.execute_query(
                query_id_area, (area_seleccionada,)
            )

            if not resultado_id_area:
                QMessageBox.critical(
                    self.r_ont, "Error", f"No se encontró el área '{area_seleccionada}' en la base de datos."
                )
                return

            id_area = resultado_id_area[0]["id"]

            # Consultar los técnicos usando el id_area y el cope seleccionado
            consulta_tecnicos = """
                SELECT "Nombre (s)", "Apellido Paterno"
                FROM Personal_O
                WHERE "id_area" = %s AND "Cope" = %s
            """
            resultados_tecnicos = self.db_personal.execute_query(
                consulta_tecnicos, (id_area, cope_seleccionado)
            )

            # Poblar el ComboBox con los nombres de los técnicos
            self.r_ont.str_exptec.clear()
            if resultados_tecnicos:
                for tecnico in resultados_tecnicos:
                    self.r_ont.str_exptec.addItem(
                        f"{tecnico['Nombre (s)']} {tecnico['Apellido Paterno']}"
                    )
            else:
                QMessageBox.information(
                    self.r_ont, "Información", "No se encontraron técnicos para los filtros seleccionados."
                )

        except Exception as e:
            QMessageBox.critical(
                self.r_ont, "Error", f"Error al cargar los técnicos: {e}"
            )

    def star_barcode_scanner(self):
        self.barcode_scanner = BarcodeScanner()
        self.barcode_scanner.code_detected.connect(self.leercodebar)
        self.barcode_scanner.frame_captured.connect(self.show_frame_in_ui)
        self.barcode_scanner.finished.connect(
            self.on_scanner_finished)  # Conexión a la señal
        self.barcode_scanner.start()

    def on_scanner_finished(self):
        QMessageBox.information(self.r_ont, "Escáner",
                                "El escaneo ha finalizado.")

    def show_frame_in_ui(self, frame):
        # Mostrar el frame en el QLabel
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(frame_rgb.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)
        # Activa el label_imagen y muestra el frame
        self.r_ont.label_imagen.setEnabled(True)
        self.r_ont.label_imagen.setPixmap(QPixmap.fromImage(q_image))

    def leercodebar(self, code, frame):
        self.r_ont.ln_ns.setText(code)
        self.save_image(frame)
        self.barcode_scanner.stop()

    def save_image(self, frame):
        """
        Convierte un frame capturado en una imagen JPEG en formato binario
        y lo almacena en el atributo `imagen_bytes` para ser guardado en la base de datos.
        """
        try:
            # Convertir el frame a RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convertir el frame a imagen
            height, width, channel = frame_rgb.shape
            bytes_per_line = 3 * width
            q_image = QImage(frame_rgb.data, width, height,
                             bytes_per_line, QImage.Format.Format_RGB888)

            pixmap = QPixmap.fromImage(q_image)
            if pixmap.isNull():
                raise ValueError("Error al convertir la imagen.")

            # Mostrar la imagen en el QLabel
            self.r_ont.label_imagen.setPixmap(pixmap.scaled(
                100, 100, Qt.AspectRatioMode.KeepAspectRatio
            ))
            self.r_ont.label_imagen.setEnabled(True)

            # Guardar la imagen como bytes
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            pixmap.save(buffer, "JPG")
            self.imagen_bytes = buffer.data()
            buffer.close()

        except Exception as e:
            QMessageBox.critical(self.r_ont, "Error",
                                 f"Error al guardar la imagen: {e}")

    def importarimagen(self):
        # Abrir un cuadro de diálogo para seleccionar la imagen
        file_dialog = QFileDialog()
        image_path, _ = file_dialog.getOpenFileName(
            self.r_ont, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp)")

        if not image_path:
            QMessageBox.warning(self.r_ont, "Advertencia",
                                "No se seleccionó ninguna imagen.")
            return

        # Cargar la imagen seleccionada
        image = cv2.imread(image_path)
        if image is None:
            QMessageBox.critical(self.r_ont, "Error",
                                 "No se pudo cargar la imagen seleccionada.")
            return

        # Mostrar la imagen en el QLabel
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        height, width, channel = image_rgb.shape
        bytes_per_line = 3 * width
        q_image = QImage(image_rgb.data, width, height,
                         bytes_per_line, QImage.Format.Format_RGB888)
        self.r_ont.label_imagen.setEnabled(True)
        self.r_ont.label_imagen.setPixmap(QPixmap.fromImage(q_image))

        # Detectar el código de barras en la imagen
        decoded_objects = decode(
            image, symbols=[ZBarSymbol.EAN13, ZBarSymbol.EAN8, ZBarSymbol.CODE128])

        if not decoded_objects:
            QMessageBox.warning(
                self.r_ont, "Advertencia", "No se detectó ningún código de barras en la imagen.")
            return

        # Usar el primer código detectado
        codigo = decoded_objects[0].data.decode("utf-8")
        self.r_ont.ln_ns.setText(codigo)
        QMessageBox.information(
            self.r_ont, "Código Detectado", f"Código de barras detectado: {codigo}")

        # Guardar la imagen como bytes para la base de datos
        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        q_image.save(buffer, "JPG")
        self.imagen_bytes = buffer.data()
        buffer.close()

    def guardar(self):
        numero_serie = self.r_ont.ln_ns.text().strip()
        modelo = self.r_ont.ln_modelo.text().strip().upper()
        area = self.r_ont.str_area.currentText().strip()
        centro_trabajo = self.r_ont.str_cope.currentText().strip()
        expediente_tecnico = self.r_ont.str_exptec.currentText().strip()
        ubicacion = self.r_ont.str_ubicacion.currentText().strip()

        if not numero_serie or not modelo or not area or not centro_trabajo:
            QMessageBox.warning(
                self.r_ont, "Advertencia", "Por favor, complete todos los campos obligatorios.")
            return

        cantidad = 1
        unidad = "Pieza"

        pixmap = self.r_ont.label_imagen.pixmap()
        if pixmap is None:
            QMessageBox.warning(self.r_ont, "Advertencia",
                                "Por favor, capture o seleccione una imagen.")
            return

        buffer = QBuffer()
        buffer.open(QBuffer.OpenModeFlag.WriteOnly)
        pixmap.save(buffer, "JPG")
        imagen_bytes = bytes(buffer.data())
        buffer.close()

        try:
            if ubicacion == "Almacén":
                consulta = """
                    INSERT INTO ont (
                        "Numero de Serie", "cantidad", "unidad", "modelo", "area", "Centro de Trabajo", "ubicacion", "imagen"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                datos = (numero_serie, cantidad, unidad, modelo, area,
                         centro_trabajo, ubicacion, imagen_bytes)
                db = self.db_almacen

            elif ubicacion == "En campo":
                if not expediente_tecnico:
                    QMessageBox.warning(
                        self.r_ont, "Advertencia", "Por favor, ingrese el expediente técnico.")
                    return
                # Verificar y crear la tabla si no existe
                if not self.verificar_tabla("ONT en Campo"):
                    self.crear_tabla_ont_en_campo()

                consulta = """
                    INSERT INTO "ONT en Campo" (
                        "Numero de Serie", "cantidad", "unidad", "modelo", "area", "Centro de Trabajo", "Expediente Técnico", "imagen"
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                datos = (numero_serie, cantidad, unidad, modelo, area,
                         centro_trabajo, expediente_tecnico, imagen_bytes)
                db = self.db_almacen

            else:
                QMessageBox.warning(
                    self.r_ont, "Advertencia", "Ubicación no válida.")
                return

            db.execute_query(consulta, datos, fetch=False)
            # Llamar a la función para actualizar el catálogo
            self.actualizar_catalogo('ONT', modelo, numero_serie)
            QMessageBox.information(
                self.r_ont, "Éxito", "Datos guardados correctamente."
            )
            self.limpiar_campos()

        except Exception as e:
            QMessageBox.critical(self.r_ont, "Error",
                                 f"Error al guardar los datos: {e}")

    def verificar_tabla(self, table_name):
        query = """
        SELECT tablename FROM pg_catalog.pg_tables
        WHERE schemaname = 'public' AND tablename = %s
        """
        resultado = self.db_almacen.execute_query(query, (table_name,))
        return len(resultado) > 0

    def crear_tabla_ont_en_campo(self):
        query = """
        CREATE TABLE IF NOT EXISTS "ONT en Campo" (
            "Numero de serie" TEXT PRIMARY KEY,
            "Cantidad" INTEGER NOT NULL,
            "Unidad" TEXT NOT NULL,
            "Modelo" TEXT NOT NULL,
            "Area" TEXT NOT NULL,
            "Centro de Trabajo" TEXT NOT NULL,
            "Expediente Técnico" TEXT NOT NULL,
            "Imagen" BYTEA
        )
        """
        self.db_almacen.execute_query(query)

    def actualizar_catalogo(self, tipo, marca, codigo_barras=None):
        """
        Actualiza el catálogo de artículos estándar y el catálogo interno con un nuevo MODEM u ONT si no existe.
        :param tipo: 'ONT' o 'MODEM'
        :param marca: Modelo del equipo
        :param codigo_barras: Código de barras del artículo (opcional)
        """
        try:
            # Estandarizar el nombre del artículo
            nombre_articulo = f"{tipo} {marca}"

            # Verificar si el artículo ya existe en `articulos_estandar`
            query_verificar_estandar = """
                SELECT * FROM articulos_estandar WHERE nombre_articulo = %s
            """
            resultado_estandar = self.db_almacen.execute_query(
                query_verificar_estandar, (nombre_articulo,))

            # Si no existe en `articulos_estandar`, agregarlo
            if not resultado_estandar:
                # Obtener el siguiente código AX consecutivo
                query_codigo_ax = """
                    SELECT MAX(CAST(codigo_ax AS INTEGER)) FROM articulos_estandar
                    WHERE codigo_ax ~ '^\d+$'
                """
                resultado_codigo = self.db_almacen.execute_query(
                    query_codigo_ax)
                max_codigo_ax = resultado_codigo[0]['max'] if resultado_codigo[0]['max'] else 0
                nuevo_codigo_ax = int(max_codigo_ax) + 1

                # Insertar el nuevo artículo en `articulos_estandar`
                query_insertar_estandar = """
                    INSERT INTO articulos_estandar (codigo_ax, nombre_articulo, unidad)
                    VALUES (%s, %s, %s)
                """
                datos_estandar = (nuevo_codigo_ax, nombre_articulo, 'pieza')
                self.db_almacen.execute_query(
                    query_insertar_estandar, datos_estandar, fetch=False)
            else:
                # Si ya existe en `articulos_estandar`, obtener su `codigo_ax`
                nuevo_codigo_ax = resultado_estandar[0]['codigo_ax']

            # Verificar si el artículo ya existe en `catalogo`
            query_verificar_catalogo = """
                SELECT * FROM catalogo WHERE codigo_ax = %s
            """
            resultado_catalogo = self.db_almacen.execute_query(
                query_verificar_catalogo, (nuevo_codigo_ax,))

            # Si no existe en `catalogo`, agregarlo
            if not resultado_catalogo:
                # Usar el código de barras proporcionado o asignar un valor predeterminado
                if not codigo_barras:
                    codigo_barras = "SIN-CODIGO"

                query_insertar_catalogo = """
                    INSERT INTO catalogo (codigo_barras, codigo_ax, descripcion, unidad_pieza, unidad_caja)
                    VALUES (%s, %s, %s, %s, %s)
                """
                datos_catalogo = (codigo_barras, nuevo_codigo_ax,
                                  nombre_articulo, 0, 0)  # Inicializamos las cantidades en 0
                self.db_almacen.execute_query(
                    query_insertar_catalogo, datos_catalogo, fetch=False)

        except Exception as e:
            QMessageBox.critical(
                self.r_ont, "Error", f"Error al actualizar el catálogo: {e}"
            )

    def sincronizar_catalogo(self, tipo):
        """
        Sincroniza el catálogo de artículos estándar y el catálogo interno con las tablas de ONT o MODEM.
        :param tipo: 'ONT' o 'MODEM'
        """
        try:
            # Definir tabla a consultar según el tipo
            tabla = "ONT" if tipo == "ONT" else "MODEM"

            # Consultar las marcas y modelos actuales en la tabla
            query_datos = f"""
                SELECT DISTINCT modelo
                FROM {tabla}
            """
            resultados = self.db_almacen.execute_query(query_datos)

            for registro in resultados:
                modelo = registro["modelo"]

                # Actualizar el catálogo para este modelo y tipo
                self.actualizar_catalogo(tipo, modelo)

        except Exception as e:
            QMessageBox.critical(
                self.r_ont, "Error", f"Error al sincronizar el catálogo: {e}"
            )

    def limpiar_campos(self):
        self.r_ont.ln_ns.clear()
        self.r_ont.ln_modelo.clear()
        self.r_ont.label_imagen.clear()
        self.r_ont.str_area.setCurrentIndex(0)
        self.r_ont.str_cope.setCurrentIndex(0)
        self.r_ont.str_exptec.setCurrentIndex(0)
        self.r_ont.str_ubicacion.setCurrentIndex(0)

    def regresar(self):
        self.r_ont.close()
