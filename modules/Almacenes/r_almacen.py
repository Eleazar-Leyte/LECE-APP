import cv2
import numpy as np
import os

from pyzbar.pyzbar import decode, ZBarSymbol
from PyQt6 import uic
from PyQt6.QtWidgets import QMessageBox, QFileDialog
from PyQt6.QtGui import QImage, QPixmap, QStandardItem, QStandardItemModel
from PyQt6.QtCore import Qt

from DatabaseManager import DatabaseManager


class R_Almacen():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.r_almacen = uic.loadUi("modules/Almacenes/R_almacen.ui")
        self.r_almacen.show()

        # Conexión a la base de datos
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")
        self.db_personal = DatabaseManager("Personal")

        # Configurar botones y funcionalidades
        self.cargar_botones()
        self.cargar_areas()
        self.cargar_codigos_ax()

    def cargar_botones(self):
        """Conecta los botones a sus respectivas funciones."""
        self.r_almacen.btn_guardar.clicked.connect(self.guardar_registro)
        self.r_almacen.btn_regresar.clicked.connect(self.regresar)
        self.r_almacen.ln_ns.editingFinished.connect(
            self.buscar_por_numero_serie)

    def cargar_areas(self):
        """
        Carga las áreas disponibles en el ComboBox según el rol y área del usuario actual.
        """
        self.r_almacen.str_area.clear()
        self.r_almacen.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
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
                    self.r_almacen.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.r_almacen, "Información", "No se encontraron áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.r_almacen, "Error", f"Error al cargar las áreas: {e}"
            )

    def actualizar_cope(self):
        """
        Actualiza los valores del ComboBox de Copé basándose en el área seleccionada.
        """
        area_seleccionada = self.r_almacen.str_area.currentText().strip()
        self.r_almacen.str_cope.clear()

        if not area_seleccionada:
            QMessageBox.warning(
                self.r_almacen, "Advertencia", "Por favor, seleccione un área."
            )
            return

        try:
            # Validar que el área seleccionada exista como tabla en la base de datos
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.r_almacen,
                    "Error",
                    f"La tabla correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar los Copé para el área seleccionada
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.r_almacen.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.r_almacen,
                    "Información",
                    "No se encontraron Copé disponibles para esta área.",
                )
        except Exception as e:
            QMessageBox.critical(
                self.r_almacen, "Error", f"Error al cargar los datos de Copé: {e}"
            )

    def cargar_codigos_ax(self):
        """Carga los códigos AX disponibles en el ComboBox, mostrando también el nombre del artículo."""
        try:
            query = "SELECT codigo_ax, nombre_articulo FROM articulos_estandar"
            resultados = self.db_almacen.execute_query(query)

            if resultados:
                # Crear un modelo para el ComboBox
                model = QStandardItemModel()
                for resultado in resultados:
                    codigo_ax = resultado["codigo_ax"]
                    nombre_articulo = resultado["nombre_articulo"]

                    # Concatenar descripción y código
                    display_text = f"{nombre_articulo} ({codigo_ax})"

                    # Crear un QStandardItem con el texto y datos asociados
                    item = QStandardItem(display_text)
                    item.setData(codigo_ax, Qt.ItemDataRole.UserRole)
                    model.appendRow(item)

                # Asignar el modelo al ComboBox
                self.r_almacen.str_codigoax.setModel(model)

        except Exception as e:
            QMessageBox.critical(
                self.r_almacen, "Error", f"Error al cargar los códigos AX: {e}"
            )

    def buscar_por_numero_serie(self):
        """
        Busca un registro por número de serie y precarga la información si existe.
        Si no existe, permite al usuario continuar con el registro sin interrupciones.
        """
        numero_serie = self.r_almacen.ln_ns.text().strip()

        if not numero_serie:
            return  # Si el campo está vacío, no hacer nada

        try:
            # Debug temporal
            print(f"Buscando número de serie: {numero_serie}")
            # Deshabilitar el evento temporalmente
            self.r_almacen.ln_ns.blockSignals(True)

            # Consulta para buscar el número de serie en la base de datos
            query = """
                SELECT descripcion, codigo_ax, area, cope
                FROM almacen
                WHERE "Numero de Serie" = %s
                LIMIT 1
            """
            resultado = self.db_almacen.execute_query(query, (numero_serie,))

            if resultado:
                registro = resultado[0]
                self.r_almacen.texedit_descripcon.setPlainText(
                    registro["descripcion"]
                )
                self.r_almacen.str_codigoax.setCurrentText(
                    f"{registro['codigo_ax']} ({registro['descripcion']})"
                )
                self.r_almacen.str_area.setCurrentText(registro["area"])
                self.r_almacen.str_cope.setCurrentText(registro["cope"])
            else:
                # Continuar sin interrupciones si no se encuentra
                self.limpiar_campos_menos_numero_serie()
                QMessageBox.information(
                    self.r_almacen,
                    "Información",
                    "No se encontró información para el número de serie ingresado. Puede continuar registrando un nuevo material."
                )
        except Exception as e:
            print(f"Error en buscar_por_numero_serie: {e}")  # Debug temporal
            QMessageBox.critical(
                self.r_almacen, "Error", f"Error al buscar el número de serie: {e}"
            )
        finally:
            # Asegurar que el evento se reactiva
            self.r_almacen.ln_ns.blockSignals(False)

    def guardar_registro(self):
        """Guarda el registro en la base de datos."""
        numero_serie = self.r_almacen.ln_ns.text().strip()
        cantidad = self.r_almacen.ln_modelo.text().strip()
        unidad = self.r_almacen.str_unidad.currentText()
        descripcion = self.r_almacen.texedit_descripcon.toPlainText().strip()
        codigo_ax = self.r_almacen.str_codigoax.currentText()
        area = self.r_almacen.str_area.currentText()
        cope = self.r_almacen.str_cope.currentText()

        if not numero_serie or not cantidad or not unidad or not descripcion:
            QMessageBox.warning(
                self.r_almacen,
                "Advertencia",
                "Por favor complete todos los campos obligatorios.",
            )
            return

        if not cantidad.isdigit() or int(cantidad) <= 0:
            QMessageBox.warning(
                self.r_almacen,
                "Advertencia",
                "La cantidad debe ser un número positivo.",
            )
            return

        try:
            # Insertar registro en la tabla `almacen`
            query_almacen = """
                INSERT INTO almacen (
                    "Numero de Serie", cantidad, unidad, descripcion, codigo_ax, area, cope
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            self.db_almacen.execute_query(query_almacen, (
                numero_serie, cantidad, unidad, descripcion, codigo_ax, area, cope
            ), fetch=False)
            # self.actualizar_catalogo()

            QMessageBox.information(
                self.r_almacen, "Éxito", "Registro guardado correctamente."
            )

            self.limpiar_campos()

        except Exception as e:
            QMessageBox.critical(
                self.r_almacen, "Error", f"Error al guardar el registro: {e}"
            )

    def limpiar_campos(self):
        """Limpia los campos del formulario."""
        self.r_almacen.ln_ns.clear()
        self.r_almacen.ln_modelo.clear()
        self.r_almacen.texedit_descripcon.clear()
        self.r_almacen.str_area.setCurrentIndex(0)
        self.r_almacen.str_cope.setCurrentIndex(0)
        self.r_almacen.str_codigoax.setCurrentIndex(0)

    def limpiar_campos_menos_numero_serie(self):
        """Limpia los campos del formulario excepto el número de serie."""
        self.r_almacen.ln_modelo.clear()
        self.r_almacen.texedit_descripcon.clear()
        self.r_almacen.str_area.setCurrentIndex(0)
        self.r_almacen.str_cope.setCurrentIndex(0)
        self.r_almacen.str_codigoax.setCurrentIndex(0)

    def regresar(self):
        """Cierra la ventana."""
        self.r_almacen.close()

    # def actualizar_catalogo(self):
    #     """
    #     Inserta un registro en el catálogo de almacén por cada producto ingresado.
    #     """
    #     try:
    #         # Recuperar información relevante de la interfaz
    #         descripcion = self.r_almacen.texedit_descripcon.toPlainText().strip()
    #         codigo_ax = self.r_almacen.str_codigoax.currentText()
    #         cantidad = self.r_almacen.ln_modelo.text().strip()
    #         unidad = self.r_almacen.str_unidad.currentText()

    #         if not descripcion or not codigo_ax or cantidad <= 0:
    #             QMessageBox.warning(
    #                 self.r_almacen,
    #                 "Advertencia",
    #                 "Por favor complete todos los campos obligatorios (Descripción, Código AX, Cantidad).",
    #             )
    #             return

    #         # Insertar en el catálogo
    #         query_catalogo = (
    #             "INSERT OR IGNORE INTO catalogo (descripcion, codigo_ax, unidad) "
    #             "VALUES (?, ?, ?)"
    #         )
    #         self.db_almacen.execute_query(
    #             query_catalogo, (descripcion, codigo_ax, unidad)
    #         )

    #         QMessageBox.information(
    #             self.r_almacen, "Éxito", "El producto fue registrado en el almacén y el catálogo exitosamente."
    #         )

    #     except Exception as e:
    #         QMessageBox.critical(
    #             self.r_almacen,
    #             "Error",
    #             f"Error al ingresar el producto: {e}"
    #         )
