import uuid
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from modules.A_P_Administrativo.personal_admin_ui import PersonalAdminUI
from modules.Almacenes.api_worker import ApiWorker


class PersonalAdminController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.ui = PersonalAdminUI()
        self.ui.closing.connect(self.cleanup_workers)
        self.ui.showMaximized()

        self.api_url = "http://localhost:8000"
        self.headers = {
            "Authorization": f"Bearer {usuario_actual['access_token']}", "Content-Type": "application/json"}
        self.active_workers = {}

        self.setup_connections()
        self.cargar_areas()
        self.cargar_tabla()

    def setup_connections(self):
        self.ui.btn_regresar.clicked.connect(self.regresar)
        self.ui.btn_salir.clicked.connect(self.salir)
        self.ui.btn_guardar.clicked.connect(self._guardar)

    def cleanup_workers(self):
        for w in list(self.active_workers.values()):
            if w.isRunning():
                w.quit()
                w.wait()
            w.deleteLater()
        self.active_workers.clear()

    def _run_api_task(self, method, endpoint, data=None, callback_success=None, callback_error=None):
        worker_id = str(uuid.uuid4())
        url = endpoint if endpoint.startswith(
            "http") else f"{self.api_url}{endpoint}"
        worker = ApiWorker(method, url, self.headers, data)
        self.active_workers[worker_id] = worker

        def on_finished(result):
            if callback_success:
                callback_success(result)
            self.active_workers.pop(worker_id, None)
            worker.deleteLater()

        def on_error(error):
            if callback_error:
                callback_error(error)
            else:
                QMessageBox.critical(self.ui, "Error", error)
            self.active_workers.pop(worker_id, None)
            worker.deleteLater()

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def cargar_areas(self):
        self._run_api_task("GET", "/personal/areas",
                           callback_success=self._poblar_areas)

    def _poblar_areas(self, areas):
        self.ui.cb_area.clear()
        for a in areas:
            self.ui.cb_area.addItem(a["nombre"], a["id"])

    def cargar_tabla(self):
        self._run_api_task("GET", "/personal/admin",
                           callback_success=self._poblar_tabla)

    def _poblar_tabla(self, data):
        self.ui.tabla_admin.clear()
        self.ui.tabla_admin.setColumnCount(5)
        self.ui.tabla_admin.setHorizontalHeaderLabels(
            ["Nombre", "Apellidos", "Correo", "Área", "Teléfono"])
        self.ui.tabla_admin.setRowCount(0)

        for row, item in enumerate(data):
            self.ui.tabla_admin.insertRow(row)
            self.ui.tabla_admin.setItem(
                row, 0, QTableWidgetItem(item.get("nombre", "")))
            self.ui.tabla_admin.setItem(row, 1, QTableWidgetItem(
                f"{item.get('apellido_paterno','')} {item.get('apellido_materno','')}"))
            self.ui.tabla_admin.setItem(
                row, 2, QTableWidgetItem(item.get("correo", "")))
            self.ui.tabla_admin.setItem(
                row, 3, QTableWidgetItem(str(item.get("id_area", ""))))
            self.ui.tabla_admin.setItem(
                row, 4, QTableWidgetItem(item.get("telefono", "")))

        self.ui.tabla_admin.horizontalHeader().setSectionResizeMode(
            1, self.ui.tabla_admin.horizontalHeader().ResizeMode.Stretch)

    def _guardar(self):
        nombre = self.ui.ln_nombre.text().strip()
        apaterno = self.ui.ln_apaterno.text().strip()
        amaterno = self.ui.ln_amaterno.text().strip()
        correo = self.ui.ln_correo.text().strip()
        area_id = self.ui.cb_area.currentData()

        if not nombre or not apaterno or not correo or not area_id:
            QMessageBox.warning(
                self.ui, "Aviso", "Complete los campos obligatorios (Nombre, Apellidos, Correo, Área).")
            return

        payload = {
            "nombre": nombre,
            "apellido_paterno": apaterno,
            "apellido_materno": amaterno,
            "correo": correo,
            "telefono": self.ui.ln_telefono.text().strip(),
            "id_area": area_id,
            "id_puesto": int(self.ui.ln_puesto.text().strip() or 1)
        }

        self._run_api_task("POST", "/personal/admin",
                           data=payload, callback_success=self._on_guardado)

    def _on_guardado(self, res):
        QMessageBox.information(
            self.ui, "Éxito", "Registro guardado correctamente.")
        self.ui.ln_nombre.clear()
        self.ui.ln_apaterno.clear()
        self.ui.ln_amaterno.clear()
        self.ui.ln_correo.clear()
        self.ui.ln_telefono.clear()
        self.cargar_tabla()

    def regresar(self):
        self.cleanup_workers()
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.ui.close()

    def salir(self):
        self.cleanup_workers()
        self.ui.close()
