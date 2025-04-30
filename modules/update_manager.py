import os
import sys
import zipfile
import requests
import tempfile
import shutil
import time
import stat
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox


class UpdateManager(QObject):
    progress_updated = pyqtSignal(int)
    update_finished = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.config = {
            "repo": "Eleazar-Leyte/LECE-APP",
            "branch": "master",
            "version_file": "version.txt",
            "excluded_files": ["config.json", ".env", ".gitignore", ".github", ".github/workflows/main.yml"],
            "token": os.getenv("GH_PAT")
        }
        self.progress = 0

    def _update_progress(self, increment):
        self.progress += increment
        self.progress_updated.emit(self.progress)

    def check_update(self):
        try:
            with open(self.config["version_file"], "r") as f:
                local_version = f.read().strip()

            url = f"https://raw.githubusercontent.com/{self.config['repo']}/{self.config['branch']}/{self.config['version_file']}"
            remote_version = requests.get(url).text.strip()

            return remote_version != local_version

        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    def perform_update(self):
        try:
            url = f"https://github.com/{self.config['repo']}/archive/refs/heads/{self.config['branch']}.zip"
            response = requests.get(url, stream=True)

            if response.status_code != 200:
                raise Exception(f"Error HTTP {response.status_code}")

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            # Manejo de descarga
            if total_size == 0:
                self.progress_updated.emit(15)
                with open("update.zip", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            else:
                self._update_progress(15)
                with open("update.zip", "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        downloaded += len(chunk)
                        progress = int(15 + (downloaded / total_size) * 50)
                        self.progress_updated.emit(progress)

            self._update_progress(65)

            # Proceso de extracción
            temp_dir = tempfile.mkdtemp()
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                root_dir = zip_ref.namelist()[0].split('/')[0]
                zip_ref.extractall(temp_dir)
                # Fijar permisos antes de copiar
                self.fix_permissions(temp_dir)

                source_dir = os.path.join(temp_dir, root_dir)
                files = [f for f in zip_ref.namelist() if not any(
                    excl in f for excl in self.config["excluded_files"])]
                total_files = len(files)

                for i, file in enumerate(files):
                    src_path = os.path.join(temp_dir, file)
                    rel_path = os.path.relpath(src_path, source_dir)
                    dest_path = os.path.join(".", rel_path)

                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    shutil.copy2(src_path, dest_path)

                    self.progress_updated.emit(
                        65 + int((i / total_files) * 25))

            os.remove("update.zip")
            self.safe_delete(temp_dir)
            self._update_progress(100)
            return True

        except Exception as e:
            self.update_finished.emit(False)
            QMessageBox.critical(
                None, "Error", f"Actualización fallida: {str(e)}")
            return False

    # Funciones de manejo de permisos
    @staticmethod
    def fix_permissions(path):
        """Establece permisos completos recursivamente"""
        for root, dirs, files in os.walk(path):
            for item in dirs + files:
                full_path = os.path.join(root, item)
                try:
                    os.chmod(full_path, stat.S_IRWXU |
                             stat.S_IRWXG | stat.S_IRWXO)
                except:
                    pass

    def safe_delete(self, path, max_retries=5, delay=1.5):
        """Eliminación con manejo mejorado para Windows"""
        for attempt in range(max_retries):
            try:
                if not os.path.exists(path):
                    return
                self.fix_permissions(path)
                shutil.rmtree(path, onerror=self.handle_remove_readonly)
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Error eliminando {path}: {str(e)}")
                time.sleep(delay * (attempt + 1))

    @staticmethod
    def handle_remove_readonly(func, path, _):
        """Manejador de errores para archivos bloqueados"""
        try:
            os.chmod(path, stat.S_IRWXU)
        except:
            pass
        try:
            func(path)
        except:
            pass
