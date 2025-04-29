import os
import sys
import zipfile
import requests
import tempfile
import shutil
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox


class UpdateManager:
    progress_updated = pyqtSignal(int)
    update_finished = pyqtSignal(bool)

    def __init__(self):
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
            # Obtener versión local
            with open(self.config["version_file"], "r") as f:
                local_version = f.read().strip()

            # Obtener versión remota
            url = f"https://raw.githubusercontent.com/{self.config['repo']}/{self.config['branch']}/{self.config['version_file']}"
            remote_version = requests.get(url).text.strip()

            return remote_version != local_version

        except Exception as e:
            print(f"Error: {str(e)}")
            return False

    def perform_update(self):
        try:
            # Descargar usando el token
            # En UpdateManager.perform_update():
            url = f"https://github.com/{self.config['repo']}/archive/refs/heads/{self.config['branch']}.zip"
            headers = {}
            response = requests.get(url)

            # Validar respuesta
            if response.status_code != 200:
                raise Exception(f"Error HTTP {response.status_code}")
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            self._update_progress(15)

            # Guardar ZIP
            with open("update.zip", "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    progress = int(15 + (downloaded / total_size) * 50)
                    self.progress_updated.emit(progress)

            self._update_progress(65)
            temp_dir = tempfile.mkdtemp()
            # Extraer ZIP
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                root_dir = zip_ref.namelist()[0].split('/')[0]
                zip_ref.extractall(temp_dir)
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
            shutil.rmtree(temp_dir)
            self._update_progress(100)
            return True

        except Exception as e:
            self.update_finished.emit(False)
            QMessageBox.critical(
                None, "Error", f"Actualización fallida: {str(e)}")
            return False
