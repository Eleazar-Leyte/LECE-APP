from PyQt6.QtCore import QThread, pyqtSignal, QTimer
from PyQt6 import QtWidgets, uic
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import pandas as pd
import requests
import json
from TableManager import TableManager
from desktop.modules.A_P_Operativo.personal_ui import PersonalUI


class AreaLoaderThread(QThread):
    """Hilo para cargar áreas en segundo plano"""
    areas_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_url, headers, usuario_actual):
        super().__init__()
        self.api_url = api_url
        self.headers = headers
        self.usuario_actual = usuario_actual

    def run(self):
        try:
            response = requests.get(
                f"{self.api_url}/personal/areas",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                areas = response.json()
                self.areas_loaded.emit(areas)
            else:
                self.error_occurred.emit(
                    f"Error {response.status_code}: {response.text}")

        except Exception as e:
            self.error_occurred.emit(f"Error cargando áreas: {str(e)}")


class Personal:

    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.personal = PersonalUI()
        self.personal.showMaximized()

        # Verificar que contamos con la JWT
        if not self.usuario_actual.get("access_token"):
            QMessageBox.critical(self.personal, "Error",
                                 "No se encontró la información de autenticación.")
            self.personal.close()
            return

        # URL base de la API
        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        # Headers para las solicitudes API
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

        # Conectamos los botones
        self.setup_connections()

        # Iniciar carga de áreas en segundo plano
        self.cargar_areas_background()

        # Mostrar indicador de carga
        self.mostrar_indicador_carga()

    def setup_connections(self):
        self.personal.btn_agregar.clicked.connect(self.mostrar_formulario)
        self.personal.btn_eliminar.clicked.connect(self.eliminarpersonal)
        self.personal.btn_regresar.clicked.connect(self.regresar)
        self.personal.btn_cargarexcel.clicked.connect(self.cargarexcel)
        self.personal.btn_descargarexcel.clicked.connect(self.descargarexcel)
        self.personal.btn_guardar.clicked.connect(self.guardarpersonal)
        self.personal.btn_salir.clicked.connect(self.salir)
        self.personal.btn_buscar.clicked.connect(self.buscar)
        self.personal.btn_sincronizar.clicked.connect(self.sincronizar)
        self.personal.btn_leyaut.clicked.connect(self.descargarexcel_layout)
        self.personal.str_area.currentIndexChanged.connect(
            self.actualizar_cope)
        # Botones del formulario
        self.personal.btn_guardar_form.clicked.connect(
            self.guardar_personal_form)
        self.personal.btn_cancelar_form.clicked.connect(
            self.ocultar_formulario)

        # Sincronizar combos del formulario con los principales
        self.personal.str_area.currentIndexChanged.connect(
            self.sincronizar_combos_area)
        self.personal.str_cope.currentIndexChanged.connect(
            self.sincronizar_combos_cope)

    def hacer_solicitud_api(self, metodo, endpoint, datos=None):
        """
        Método helper para hacer solicitudes a la API
        """
        try:
            url = f"{self.api_url}{endpoint}"
            if metodo == "GET":
                response = requests.get(url, headers=self.headers)
            elif metodo == "POST":
                response = requests.post(url, headers=self.headers, json=datos)
            elif metodo == "DELETE":
                response = requests.delete(url, headers=self.headers)
            else:
                raise ValueError(f"Método {metodo} no soportado")

            # Manejar errores específicos
            if response.status_code == 401:
                # self.token_expired.emit()  # Comentado si no está definido
                QMessageBox.critical(self.personal, "Error",
                                     "Token expirado o no válido")
                return None
            elif response.status_code == 500:
                # Mostrar el mensaje de error del servidor
                try:
                    error_data = response.json()
                    error_msg = error_data.get(
                        'detail', 'Error interno del servidor')
                except:
                    # Si no se puede parsear JSON, usar el texto de la respuesta
                    error_msg = response.text or 'Error interno del servidor sin detalles'

                QMessageBox.critical(
                    self.personal, "Error del servidor",
                    f"Error al crear personal: {response.status_code}: {error_msg}"
                )
                return None
            elif response.status_code == 404:
                QMessageBox.information(
                    self.personal, "Información", "Recurso no encontrado")
                return None  # Recurso no encontrado

            response.raise_for_status()

            # Para respuestas DELETE exitosas que pueden no tener contenido
            if response.status_code == 204 or response.text.strip() == '':
                return {"message": "Operación exitosa"}

            return response.json()

        except requests.exceptions.Timeout:
            QMessageBox.critical(
                self.personal, "Error", "Tiempo de espera agotado al conectar con la API.")
            return None
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(
                self.personal, "Error", f"Error en la comunicación con la API: {str(e)}")
            return None

    def mostrar_indicador_carga(self):
        """Muestra un indicador de carga mientras se cargan las áreas"""
        self.personal.str_area.clear()
        self.personal.str_area.addItem("Cargando áreas...")
        self.personal.str_area.setEnabled(False)

    def cargar_areas_background(self):
        """Inicia la carga de áreas en un hilo separado"""
        self.area_loader = AreaLoaderThread(
            self.api_url,
            self.headers,
            self.usuario_actual
        )
        self.area_loader.areas_loaded.connect(self.on_areas_loaded)
        self.area_loader.error_occurred.connect(self.on_area_load_error)
        self.area_loader.start()

    def on_areas_loaded(self, areas):
        """Callback cuando las áreas se cargan exitosamente"""
        self.personal.str_area.clear()
        self.personal.str_area.setEnabled(True)

        if self.usuario_actual['rol'] == 'Admin':
            for area in areas:
                self.personal.str_area.addItem(area["nombre"], area["id"])
        else:
            # Para usuarios no Admin, usar la información del JWT
            area_id = self.usuario_actual['area']
            area_name = self.usuario_actual.get('area_name', f'Área {area_id}')
            self.personal.str_area.addItem(area_name, area_id)

        # Cargar copes automáticamente si hay un área seleccionada
        QTimer.singleShot(100, self.cargar_copes_automatico)

    def cargar_copes_automatico(self):
        """Carga los copes automáticamente después de cargar áreas"""
        if self.personal.str_area.count() > 0:
            self.actualizar_cope()

    def on_area_load_error(self, error_msg):
        """Callback cuando hay error cargando áreas"""
        self.personal.str_area.clear()
        self.personal.str_area.setEnabled(True)
        self.personal.str_area.addItem("Error al cargar áreas")

        # Mostrar error después de un breve delay para que la UI esté lista
        QTimer.singleShot(500, lambda: QMessageBox.critical(
            self.personal, "Error", f"Error cargando áreas: {error_msg}"
        ))

    def actualizar_cope(self):
        """
        Actualiza los copes usando la información del área seleccionada
        """
        # Obtener el ID del área seleccionada
        if self.usuario_actual['rol'] == 'Admin':
            area_id = self.personal.str_area.currentData()
        else:
            area_id = self.usuario_actual['area']

        self.personal.str_cope.clear()

        if not area_id:
            return

        try:
            copes = self.hacer_solicitud_api(
                "GET", f"/personal/areas/{area_id}/copes")

            if copes:
                for cope in copes:
                    self.personal.str_cope.addItem(cope["cope"])
            else:
                QMessageBox.information(self.personal, "Información",
                                        "No se encontraron Copé disponibles para esta área.")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al cargar copes: {str(e)}")

    def buscar(self):
        """Busca personal usando la API"""
        area_id = self.personal.str_area.currentData()
        cope = self.personal.str_cope.currentText()

        if not area_id or not cope:
            QMessageBox.warning(self.personal, "Advertencia",
                                "Por favor, seleccione un Área y un Copé.")
            return

        try:
            personal_data = self.hacer_solicitud_api(
                "GET", f"/personal/?area_id={area_id}&cope={cope}")

            if personal_data:
                # Mapear los datos de la API al formato CORRECTO para TableManager
                datos_para_tabla = []
                for item in personal_data:
                    nuevo_item = {
                        "id": item.get("id", ""),  # ✅ Número de Empleado
                        "Apellido Paterno": item.get("apellido_paterno", ""),
                        "Apellido Materno": item.get("apellido_materno", ""),
                        "Nombre (s)": item.get("nombre", ""),
                        "Expediente Técnico Cobre": item.get("expediente_tecnico_cobre", ""),
                        "Expediente Técnico F.O.": item.get("expediente_tecnico_fo", ""),
                        "id_area": item.get("id_area", ""),  # ✅ Área
                        "Cope": item.get("cope", ""),
                        "N.S.S.": item.get("nss", ""),
                        "R.F.C.": item.get("rfc", ""),
                        "Dirección": item.get("direccion", "")
                    }
                    datos_para_tabla.append(nuevo_item)

                TableManager.populate_table(
                    self.personal.tablapersonal, datos_para_tabla, "Personal_O")
            else:
                QMessageBox.information(
                    self.personal, "Información", "No se encontraron resultados")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al buscar personal: {str(e)}")

    def sincronizar(self):
        """Sincroniza los datos con la API"""
        try:
            self.buscar()
            QMessageBox.information(
                self.personal, "Éxito", "Datos sincronizados correctamente")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al sincronizar: {str(e)}")

    def cargarexcel(self):
        """Carga datos desde Excel y los envía a la API"""
        archivo, _ = QFileDialog.getOpenFileName(
            self.personal, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)"
        )

        if archivo:
            try:
                datos_excel = pd.read_excel(archivo)

                # Convertir a formato API
                datos_api = []
                for _, fila in datos_excel.iterrows():
                    personal_item = {
                        "apellido_paterno": fila.get("Apellido Paterno", ""),
                        "apellido_materno": fila.get("Apellido Materno", ""),
                        "nombre": fila.get("Nombre (s)", ""),
                        "expediente_tecnico_cobre": fila.get("Expediente Técnico Cobre", ""),
                        "expediente_tecnico_fo": fila.get("Expediente Técnico F.O.", ""),
                        "id_area": fila.get("id_area", ""),
                        "cope": fila.get("Cope", ""),
                        "nss": fila.get("N.S.S.", ""),
                        "rfc": fila.get("R.F.C.", ""),
                        "direccion": fila.get("Dirección", "")
                    }
                    datos_api.append(personal_item)

                # Enviar a API
                resultado = self.hacer_solicitud_api(
                    "POST", "/personal/importar-excel", datos_api)

                if resultado:
                    QMessageBox.information(self.personal, "Éxito", resultado.get(
                        "message", "Datos importados correctamente"))
                    self.buscar()  # Actualizar tabla
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al cargar Excel: {str(e)}")

    def descargarexcel(self):
        """Descarga los datos actuales a Excel"""
        try:
            # Obtener datos actuales de la tabla
            datos = []
            for row in range(self.personal.tablapersonal.rowCount()):
                item = {}
                for col in range(self.personal.tablapersonal.columnCount()):
                    header = self.personal.tablapersonal.horizontalHeaderItem(
                        col).text()
                    cell_value = self.personal.tablapersonal.item(row, col)
                    item[header] = cell_value.text() if cell_value else ""
                datos.append(item)

            if datos:
                df = pd.DataFrame(datos)
                archivo, _ = QFileDialog.getSaveFileName(
                    self.personal, "Guardar como", "", "Archivo Excel (*.xlsx)"
                )

                if archivo:
                    df.to_excel(archivo, index=False)
                    QMessageBox.information(
                        self.personal, "Éxito", "Datos exportados correctamente")
            else:
                QMessageBox.information(
                    self.personal, "Información", "No hay datos para exportar")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al exportar Excel: {str(e)}")

    def descargarexcel_layout(self):
        """Descarga un layout de Excel vacío"""
        try:
            # Crear DataFrame con columnas vacías
            columnas = [
                "Apellido Paterno", "Apellido Materno", "Nombre (s)",
                "Expediente Técnico Cobre", "Expediente Técnico F.O.",
                "id_area", "Cope", "N.S.S.", "R.F.C.", "Dirección"
            ]
            df = pd.DataFrame(columns=columnas)

            archivo, _ = QFileDialog.getSaveFileName(
                self.personal, "Guardar layout de Excel", "", "Archivo Excel (*.xlsx)"
            )

            if archivo:
                df.to_excel(archivo, index=False)
                QMessageBox.information(
                    self.personal, "Éxito", "Layout descargado correctamente")
        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al descargar layout: {str(e)}")

    def eliminarpersonal(self):
        """Elimina personal usando la API"""
        selected_row = self.personal.tablapersonal.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self.personal, "Advertencia",
                                "Por favor, seleccione un registro para eliminar.")
            return

        numero_empleado_item = self.personal.tablapersonal.item(
            selected_row, 0)
        if not numero_empleado_item:
            QMessageBox.warning(self.personal, "Advertencia",
                                "No se pudo obtener la información del empleado.")
            return

        numero_empleado = numero_empleado_item.text()
        confirmacion = QMessageBox.question(
            self.personal, "Eliminar personal",
            f"¿Está seguro de que desea eliminar el registro del empleado con Id: {numero_empleado}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirmacion == QMessageBox.StandardButton.Yes:
            try:
                resultado = self.hacer_solicitud_api(
                    "DELETE", f"/personal/{numero_empleado}")

                if resultado:
                    self.personal.tablapersonal.removeRow(selected_row)
                    QMessageBox.information(
                        self.personal, "Éxito", "Registro eliminado correctamente")
            except Exception as e:
                QMessageBox.critical(self.personal, "Error",
                                     f"Error al eliminar registro: {str(e)}")

    def guardarpersonal(self):
        """Guarda cambios en la base de datos (implementar según necesidad)"""
        QMessageBox.information(
            self.personal, "Información", "Funcionalidad en desarrollo")

    def regresar(self):
        """Regresa al menú principal"""
        from desktop.modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.personal.close()

    def salir(self):
        """Cierra la aplicación"""
        self.personal.close()


### ___________________Formulario para Agregar personal___________________###


    def mostrar_formulario(self):
        """
        Muestra el formulario de agregar personal
        """
        self.personal.show_form_panel()
        self.limpiar_formulario()
        self.llenar_combos_formulario()
        self.sincronizar_combos_area()
        self.sincronizar_combos_cope()

    def llenar_combos_formulario(self):
        """
        Llena los combos del formulario con los datos de los combos principales
        """
        # Limpiar combos del formulario
        self.personal.str_area_form.clear()
        self.personal.str_cope_form.clear()

        # Copiar áreas del combo principal al combo del formulario
        for i in range(self.personal.str_area.count()):
            texto = self.personal.str_area.itemText(i)
            datos = self.personal.str_area.itemData(i)
            self.personal.str_area_form.addItem(texto, datos)

        # Copiar copes del combo principal al combo del formulario
        for i in range(self.personal.str_cope.count()):
            texto = self.personal.str_cope.itemText(i)
            self.personal.str_cope_form.addItem(texto)

    def ocultar_formulario(self):
        """Oculta el formulario de agregar personal"""
        self.personal.hide_form_panel()

    def sincronizar_combos_area(self):
        """Sincroniza el combo de área del formulario con el principal"""
        # Obtener el texto seleccionado en el combo principal
        texto_seleccionado = self.personal.str_area.currentText()

        # Buscar y seleccionar el mismo texto en el combo del formulario
        index = self.personal.str_area_form.findText(texto_seleccionado)
        if index >= 0:
            self.personal.str_area_form.setCurrentIndex(index)

    def sincronizar_combos_cope(self):
        """
        Sincroniza el combo de cope del formulario con el principal
        """
        # Obtener el texto seleccionado en el combo principal
        texto_seleccionado = self.personal.str_cope.currentText()

        # Buscar y seleccionar el mismo texto en el combo del formulario
        index = self.personal.str_cope_form.findText(texto_seleccionado)
        if index >= 0:
            self.personal.str_cope_form.setCurrentIndex(index)

    def limpiar_formulario(self):
        """Limpia todos los campos del formulario"""
        self.personal.ln_apaterno.clear()
        self.personal.ln_materno.clear()
        self.personal.ln_nombre.clear()
        self.personal.ln_expediente_c.clear()
        self.personal.ln_expediente_fo.clear()
        self.personal.ln_nss.clear()
        self.personal.ln_rfc.clear()
        self.personal.ln_direccion.clear()

    def guardar_personal_form(self):
        """
        Guarda el nuevo personal desde el formulario
        """
        if not self.validar_formulario():
            return

        try:
            # Obtener los datos de los combos del FORMULARIO
            area_id = self.personal.str_area_form.currentData()
            cope_text = self.personal.str_cope_form.currentText()

            # Preparar datos para la API
            personal_data = {
                "apellido_paterno": self.personal.ln_apaterno.text().strip(),
                "apellido_materno": self.personal.ln_materno.text().strip(),
                "nombre": self.personal.ln_nombre.text().strip(),
                "expediente_tecnico_cobre": self.personal.ln_expediente_c.text().strip(),
                "expediente_tecnico_fo": self.personal.ln_expediente_fo.text().strip(),
                "nss": self.personal.ln_nss.text().strip(),
                "rfc": self.personal.ln_rfc.text().strip(),
                "direccion": self.personal.ln_direccion.toPlainText().strip(),
                "id_area": area_id,
                "cope": cope_text,
                "id_puesto": 1
            }

            # Enviar a la API
            resultado = self.hacer_solicitud_api(
                "POST", "/personal", personal_data)

            if resultado:
                QMessageBox.information(
                    self.personal, "Éxito", "Personal agregado correctamente")
                self.ocultar_formulario()
                self.buscar()  # Actualizar tabla
            else:
                pass

        except Exception as e:
            QMessageBox.critical(self.personal, "Error",
                                 f"Error al guardar personal: {str(e)}")

    def validar_formulario(self):
        """
        Valida los campos del formulario
        """
        campos_obligatorios = [
            (self.personal.ln_apaterno, "Apellido Paterno"),
            (self.personal.ln_materno, "Apellido Materno"),
            (self.personal.ln_nombre, "Nombre(s)"),
        ]

        for campo, nombre in campos_obligatorios:
            if not campo.text().strip():
                QMessageBox.warning(self.personal, "Validación",
                                    f"El campo {nombre} es obligatorio")
                campo.setFocus()
                return False

        # Validar área - verificar que tenga datos, no solo índice
        if self.personal.str_area_form.currentIndex() < 0 or not self.personal.str_area_form.currentData():
            QMessageBox.warning(self.personal, "Validación",
                                "Debe seleccionar un Área válida")
            self.personal.str_area_form.setFocus()
            return False

        # Validar cope - verificar que tenga texto
        if self.personal.str_cope_form.currentIndex() < 0 or not self.personal.str_cope_form.currentText().strip():
            QMessageBox.warning(self.personal, "Validación",
                                "Debe seleccionar un Cope válido")
            self.personal.str_cope_form.setFocus()
            return False

        return True
