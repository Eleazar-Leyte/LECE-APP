import os
import tufup
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtWidgets import QMessageBox
from cryptography.hazmat.primitives import serialization


class UpdateWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool)

    def __init__(self, updater):
        super().__init__()
        self.updater = updater

    def run(self):
        try:
            # Descargar y verificar actualización
            self.progress.emit(10)
            update_available = self.updater.check_for_updates()

            if update_available:
                self.progress.emit(20)
                self.updater.download_update(
                    progress_callback=lambda p: self.progress.emit(
                        20 + int(p*60))
                )
                self.progress.emit(85)

                # Validar firma antes de aplicar
                if self.updater.validate_signature():
                    self.progress.emit(90)
                    self.updater.apply_update()
                    self.finished.emit(True)
                else:
                    raise Exception("Firma inválida")
            else:
                self.finished.emit(False)

        except Exception as e:
            self.finished.emit(False)
            raise e


class UpdateManager(QObject):
    progress_updated = pyqtSignal(int)
    update_finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.worker = None
        self.config = {
            'repo_url': 'https://github.com/Eleazar-Leyte/LECE-APP/releases/latest',
            'public_key': self.load_public_key(),
            'current_version': self.get_current_version(),
            'target_dir': 'updates'
        }

        self.updater = tufup.Client(
            app_name='LECECOM',
            current_version=self.config['current_version'],
            metadata_dir=os.path.join(self.config['target_dir'], 'meta'),
            repository_url=self.config['repo_url'],
            public_key=self.config['public_key']
        )

    def load_public_key(self):
        """Carga la clave pública embebida"""
        public_key_pem = b"""-----BEGIN PUBLIC KEY-----
        ... (tu clave pública aquí) ...
        -----END PUBLIC KEY-----"""
        return serialization.load_pem_public_key(public_key_pem)

    def get_current_version(self):
        with open('version.txt') as f:
            return f.read().strip()

    def check_update(self):
        """Inicia el proceso de actualización"""
        self.worker = UpdateWorker(self.updater)
        self.worker.progress.connect(self.progress_updated)
        self.worker.finished.connect(self.update_finished)
        self.worker.start()

    def cleanup(self):
        """Limpieza post-actualización"""
        if os.path.exists(self.config['target_dir']):
            shutil.rmtree(self.config['target_dir'])
