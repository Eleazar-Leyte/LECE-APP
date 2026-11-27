import uuid
from PyQt6.QtWidgets import QMessageBox, QInputDialog, QLineEdit, QTableWidgetItem
from PyQt6.QtCore import Qt

from modules.usuarios.usuarios_ui import UsuariosUI
from modules.Almacenes.api_worker import ApiWorker


class UsuariosController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.ui = UsuariosUI()
        self.ui.closing.connect(self.cleanup_workers)
        self.ui.showMaximized()

        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.active_workers = {}

        self.setup_connections()
        self.cargar_datos_iniciales()

    def cleanup_workers(self):
        """Detiene y espera a que terminen todos los hilos antes de cerrar."""
        for worker in list(self.active_workers.values()):
            if worker.isRunning():
                worker.quit()
                worker.wait()
            worker.deleteLater()
        self.active_workers.clear()

    def setup_connections(self):
        self.ui.btn_regresar.clicked.connect(self.regresar)
        self.ui.btn_salir.clicked.connect(self.salir)
        self.ui.btn_crear.clicked.connect(self._crear_usuario)
        self.ui.btn_reset_pass.clicked.connect(self._reset_password)
        self.ui.btn_toggle_status.clicked.connect(self._toggle_status)

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

        def on_error(error_msg):
            if callback_error:
                callback_error(error_msg)
            else:
                QMessageBox.critical(self.ui, "Error API", error_msg)
            self.active_workers.pop(worker_id, None)
            worker.deleteLater()

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def cargar_datos_iniciales(self):
        self._cargar_usuarios()
        self._cargar_personal_disponible()

    def _cargar_usuarios(self):
        self._run_api_task(
            method="GET", endpoint="/users/",
            callback_success=self._poblar_tabla
        )

    def _poblar_tabla(self, usuarios):
        self.ui.tabla_usuarios.clear()
        self.ui.tabla_usuarios.setColumnCount(5)
        self.ui.tabla_usuarios.setHorizontalHeaderLabels(
            ["ID", "Nombre", "Usuario", "Rol", "Estado"])
        self.ui.tabla_usuarios.setRowCount(0)

        for row, u in enumerate(usuarios):
            self.ui.tabla_usuarios.insertRow(row)
            self.ui.tabla_usuarios.setItem(
                row, 0, QTableWidgetItem(str(u.get("id"))))
            self.ui.tabla_usuarios.setItem(
                row, 1, QTableWidgetItem(u.get("nombre", "")))
            self.ui.tabla_usuarios.setItem(
                row, 2, QTableWidgetItem(u.get("usuario", "")))
            self.ui.tabla_usuarios.setItem(
                row, 3, QTableWidgetItem(u.get("rol", "")))

            status = "Activo" if u.get("estado") else "Inactivo"
            item_status = QTableWidgetItem(status)
            if not u.get("estado"):
                item_status.setForeground(Qt.GlobalColor.red)
            self.ui.tabla_usuarios.setItem(row, 4, item_status)

        self.ui.tabla_usuarios.setColumnHidden(0, True)
        self.ui.tabla_usuarios.horizontalHeader().setSectionResizeMode(
            1, self.ui.tabla_usuarios.horizontalHeader().ResizeMode.Stretch)

    def _cargar_personal_disponible(self):
        self._run_api_task(
            method="GET", endpoint="/users/personal_disponible",
            callback_success=self._poblar_combo_personal
        )

    def _poblar_combo_personal(self, data):
        self.ui.cb_personal.clear()
        self.ui.cb_personal.addItem("Seleccionar empleado", None)

        for p in data.get("admins", []):
            nombre = f"{p['nombre']} {p['apellido']} ({p['tipo']})"
            self.ui.cb_personal.addItem(
                nombre, {"id": p['id'], "tipo": "admin", "id_area": p['id_area']})

        for p in data.get("operativos", []):
            nombre = f"{p['nombre']} {p['apellido']} ({p['tipo']})"
            self.ui.cb_personal.addItem(
                nombre, {"id": p['id'], "tipo": "operativo", "id_area": p['id_area']})

    def _crear_usuario(self):
        idx = self.ui.cb_personal.currentIndex()
        if idx <= 0:
            QMessageBox.warning(
                self.ui, "Aviso", "Seleccione un empleado de la lista.")
            return

        usuario = self.ui.ln_usuario.text().strip()
        password = self.ui.ln_password.text().strip()
        rol = self.ui.cb_rol.currentText()

        if not usuario or not password:
            QMessageBox.warning(
                self.ui, "Aviso", "Complete el usuario y la contraseña.")
            return

        info_personal = self.ui.cb_personal.itemData(idx)
        nombre_mostrar = self.ui.cb_personal.currentText().split(" (")[0]

        payload = {
            "nombre": nombre_mostrar,
            "usuario": usuario,
            "password": password,
            "rol": rol,
            "id_area": info_personal.get("id_area")
        }

        if info_personal["tipo"] == "admin":
            payload["id_personal_admin"] = info_personal["id"]
        else:
            payload["id_personal_operativo"] = info_personal["id"]

        self._run_api_task(
            method="POST", endpoint="/users/", data=payload,
            callback_success=lambda r: [
                QMessageBox.information(
                    self.ui, "Éxito", "Usuario creado correctamente"),
                self.ui.ln_usuario.clear(), self.ui.ln_password.clear(),
                self.cargar_datos_iniciales()
            ]
        )

    def _reset_password(self):
        row = self.ui.tabla_usuarios.currentRow()
        if row == -1:
            QMessageBox.warning(
                self.ui, "Aviso", "Seleccione un usuario de la tabla.")
            return

        id_usuario = self.ui.tabla_usuarios.item(row, 0).text()

        nueva_pass, ok = QInputDialog.getText(
            self.ui, "Resetear Contraseña", "Ingrese la nueva contraseña:", QLineEdit.EchoMode.Password)
        if ok and nueva_pass:
            self._run_api_task(
                method="PUT", endpoint=f"/users/{id_usuario}/reset-password", data={"nueva_password": nueva_pass},
                callback_success=lambda r: QMessageBox.information(
                    self.ui, "Éxito", "Contraseña actualizada correctamente.")
            )

    def _toggle_status(self):
        row = self.ui.tabla_usuarios.currentRow()
        if row == -1:
            QMessageBox.warning(
                self.ui, "Aviso", "Seleccione un usuario de la tabla.")
            return

        id_usuario = self.ui.tabla_usuarios.item(row, 0).text()
        nombre = self.ui.tabla_usuarios.item(row, 1).text()

        if QMessageBox.question(self.ui, "Confirmar", f"¿Cambiar el estado de acceso para {nombre}?",
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self._run_api_task(
                method="PUT", endpoint=f"/users/{id_usuario}/toggle-status",
                callback_success=lambda r: self._cargar_usuarios()
            )

    def regresar(self):
        self.cleanup_workers()
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.ui.close()

    def salir(self):
        self.cleanup_workers()
        self.ui.close()
