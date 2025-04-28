from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox, QFileDialog, QProgressDialog
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6 import uic, QtWidgets, QtCore
from psycopg2 import Binary, sql
from datetime import datetime
from DatabaseManager import DatabaseManager
import json
import os
import pandas as pd
import zipfile
import io


class ExportWorker(QObject):
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int)

    def __init__(self, db_produccion, params, excel_path):
        super().__init__()
        self.db_produccion = db_produccion
        self.params = params
        self.excel_path = excel_path
        self._is_running = True

    def run(self):
        try:
            # Paso 1: Obtener datos organizados por tablas
            datos_por_tabla = self.obtener_datos_produccion()
            if not any(datos_por_tabla.values()):
                raise Exception(
                    "No se encontraron registros en las fechas seleccionadas")

            # Paso 2: Exportar imágenes con datos originales
            self.exportar_imagenes(datos_por_tabla)

            # Paso 3: Procesar datos y consumo
            dataframes, df_consumo = self.procesar_datos(datos_por_tabla)

            # Paso 4: Guardar Excel
            with pd.ExcelWriter(self.excel_path) as writer:
                total_data = False

                for tabla, df in dataframes.items():
                    if not df.empty:
                        df.to_excel(writer, index=False, sheet_name=tabla[:31])
                        total_data = True
                        print(
                            f"Datos exportados en hoja {tabla}: {len(df)} registros")

                if not df_consumo.empty:
                    df_consumo.to_excel(writer, index=False,
                                        sheet_name="Consumo")
                    total_data = True
                    print(
                        f"Datos de consumo exportados: {len(df_consumo)} registros")

                if not total_data:
                    raise Exception("Todas las tablas están vacías")

            self.finished.emit(True, self.excel_path)

        except Exception as e:
            self.finished.emit(False, str(e))

    def obtener_datos_produccion(self):
        tablas = ["fibra_optica", "cobre", "a4_incentivos", "quejas"]
        datos_por_tabla = {tabla: [] for tabla in tablas}

        try:
            for tabla in tablas:
                # Construir consulta con parámetros posicionales
                query = """
                    SELECT 
                        *,
                        COALESCE(consumo, '{{}}'::jsonb) AS consumo,
                        imagen
                    FROM "{table}"
                    WHERE LOWER(area) = LOWER(%s)
                    AND ({cope_cond})
                    AND fecha_posteo BETWEEN %s AND %s
                """.format(
                    table=tabla,
                    cope_cond="TRUE" if self.params[2] is None else "cope = %s"
                )

                # Construir parámetros
                params = [
                    self.params[1].lower(),  # Área en minúscula
                ]

                if self.params[2] is not None:
                    params.append(self.params[3])  # Valor COPE

                params.extend([
                    self.params[4],  # fecha_ini
                    self.params[5]   # fecha_fin
                ])

                print(f"Consulta para {tabla}:\n{query}")
                print(f"Parámetros: {params}")

                # Ejecutar consulta directamente con parámetros posicionales
                resultados = self.db_produccion.execute_query(
                    query, tuple(params))
                print(f"Registros encontrados en {tabla}: {len(resultados)}")
                datos_por_tabla[tabla] = resultados

            return datos_por_tabla

        except Exception as e:
            raise Exception(f"Error en consulta SQL: {str(e)}")

    def procesar_datos(self, datos_por_tabla):
        dataframes = {}
        consumo_data = []

        for tabla, datos in datos_por_tabla.items():
            expanded_data = []
            for item in datos:
                # Hacer copia para no modificar el original
                item_copy = item.copy()

                # Procesar consumo
                consumo = item_copy.get('consumo', {})
                for consumo_item in consumo.get('items', []):
                    consumo_data.append({
                        'folio_pisa': item_copy.get('folio_pisa'),
                        'telefono_asignado': item_copy.get('telefono_asignado'),
                        'material': consumo_item.get('descripcion'),
                        'tipo_material': consumo_item.get('tipo'),
                        'cantidad': consumo_item.get('cantidad'),
                        'fecha_cuadre': item_copy.get('fecha_posteo')
                    })

                # Eliminar campos no necesarios
                item_copy.pop('consumo', None)
                item_copy.pop('imagen', None)
                expanded_data.append(item_copy)

            dataframes[tabla] = pd.DataFrame(expanded_data)
            print(f"Procesados {len(expanded_data)} registros para {tabla}")

        return dataframes, pd.DataFrame(consumo_data)

    def exportar_imagenes(self, datos_por_tabla):
        try:
            for tabla, datos in datos_por_tabla.items():
                if not datos:
                    print(f"No hay imágenes para {tabla}")
                    continue

                zip_path = f"{os.path.splitext(self.excel_path)[0]}_{tabla.upper()}_IMAGENES.zip"
                print(f"Creando archivo ZIP en: {zip_path}")

                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    contador = 0
                    for idx, item in enumerate(datos):
                        if all(key in item for key in ['imagen', 'numero_serie']):
                            if item['imagen'] and item['numero_serie']:
                                try:
                                    # Usar formato PNG
                                    img_name = f"{item['numero_serie']}_{idx}.png"
                                    img_data = bytes(item['imagen'])
                                    zipf.writestr(img_name, img_data)
                                    contador += 1
                                except Exception as e:
                                    print(f"Error con imagen {idx}: {str(e)}")

                    print(f"Exportadas {contador} imágenes para {tabla}")

        except Exception as e:
            raise Exception(f"Error al exportar imágenes: {str(e)}")

    def stop(self):
        self._is_running = False


class Exportar():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.exportar = uic.loadUi("modules/Montaje/Exportar.ui")
        self.exportar.show()

        # Conexiones a bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_areas = DatabaseManager("Áreas")
        self.db_produccion = DatabaseManager("Producción")

        # Configuración inicial
        self.cargar_botones()
        self.cargar_areas()
        self.thread = None
        self.worker = None
        self.progress_dialog = None

    def cargar_botones(self):
        self.exportar.btn_exportar.clicked.connect(self.iniciar_exportacion)
        self.exportar.btn_cancelar.clicked.connect(self.exportar.close)

    def cargar_areas(self):
        self.exportar.str_area.clear()
        self.exportar.str_area.currentIndexChanged.connect(self.cargar_cope)
        try:
            if self.usuario_actual["rol"] == "Directivo":
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(query)
            else:
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(
                    query, (self.usuario_actual['area'],))

            if resultados:
                for resultado in resultados:
                    self.exportar.str_area.addItem(
                        resultado['Nombre del Área'])
            else:
                QMessageBox.information(
                    self.exportar, "Información", "No se encontraron áreas disponibles.")
        except Exception as e:
            QMessageBox.critical(self.exportar, "Error",
                                 f"Error al cargar las áreas: {e}")

    def cargar_cope(self):
        area_seleccionada = self.exportar.str_area.currentText().strip()
        self.exportar.str_cope.clear()
        self.exportar.str_cope.addItem("Todos los COPE")

        if not area_seleccionada:
            QMessageBox.warning(self.exportar, "Advertencia",
                                "Por favor, seleccione un área.")
            return

        try:
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.exportar, "Error", f"La tabla del área '{area_seleccionada}' no existe.")
                return

            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.exportar.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.exportar, "Información", "No se encontraron Copé disponibles.")
        except Exception as e:
            QMessageBox.critical(self.exportar, "Error",
                                 f"Error al cargar los datos de Copé:{e}")

    def iniciar_exportacion(self):
        try:
            area = self.exportar.str_area.currentText().strip()
            cope = self.exportar.str_cope.currentText().strip()
            qdate_ini = self.exportar.fecha_ini.date()
            qdate_fin = self.exportar.fecha_fin.date()

            # Convertir fechas incluyendo hora final
            fecha_ini = datetime(
                qdate_ini.year(), qdate_ini.month(), qdate_ini.day())
            fecha_fin = datetime(
                qdate_fin.year(), qdate_fin.month(), qdate_fin.day(), 23, 59, 59)

            # Generar nombre sugerido
            default_name = (
                f"Produccion_{fecha_ini.strftime('%Y-%m-%d')}_"
                f"a_{fecha_fin.strftime('%Y-%m-%d')}.xlsx"
            )

            # Obtener ruta de guardado
            excel_path, _ = QFileDialog.getSaveFileName(
                self.exportar,
                "Guardar Reporte",
                default_name,
                "Excel Files (*.xlsx)"
            )

            if not excel_path:
                return

            # Configurar diálogo de progreso
            self.progress_dialog = QProgressDialog(
                "Exportando datos...",
                "Cancelar",
                0,
                0,
                self.exportar
            )
            self.progress_dialog.canceled.connect(self.detener_exportacion)
            self.progress_dialog.show()

            # Preparar parámetros
            params = (
                "dummy_value",
                area,
                cope if cope != "Todos los COPE" else None,
                cope if cope != "Todos los COPE" else None,
                fecha_ini.strftime("%Y-%m-%d"),
                fecha_fin.strftime("%Y-%m-%d %H:%M:%S")
            )

            print(f"Parámetros finales: {params}")

            # Configurar hilo
            self.thread = QThread()
            self.worker = ExportWorker(self.db_produccion, params, excel_path)
            self.worker.moveToThread(self.thread)

            # Conexiones
            self.thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.finalizar_exportacion)
            self.worker.finished.connect(self.thread.quit)
            self.worker.finished.connect(self.worker.deleteLater)
            self.thread.finished.connect(self.thread.deleteLater)

            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self.exportar, "Error",
                                 f"Error inicial: {str(e)}")

    def finalizar_exportacion(self, success, message):
        self.progress_dialog.close()

        if success:
            QMessageBox.information(
                self.exportar, "Éxito", f"Reporte exportado:\n{message}")
            self.exportar.close()
        else:
            QMessageBox.critical(self.exportar, "Error", f"Error:\n{message}")
            print(f"ERROR DETALLADO: {message}")

    def detener_exportacion(self):
        if self.worker:
            self.worker.stop()
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
