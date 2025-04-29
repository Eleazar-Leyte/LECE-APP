import os
import sys
import zipfile
import requests
import tempfile
import shutil
from PyQt6.QtWidgets import QMessageBox


class UpdateManager:
    def __init__(self):
        self.config = {
            "repo": "Eleazar-Leyte/LECE-APP",
            "branch": "master",
            "version_file": "version.txt",
            "excluded_files": ["config.json", ".env", ".gitignore", ".github", ".github/workflows/main.yml"],
            "token": os.getenv("GH_PAT")
        }

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

            # Guardar ZIP
            with open("update.zip", "wb") as f:
                f.write(response.content)

            # Extraer a directorio temporal
            temp_dir = None
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                # Crear directorio temporal
                temp_dir = tempfile.mkdtemp()
                zip_ref.extractall(temp_dir)

                # Obtener directorio raíz del repositorio dentro del ZIP
                root_dir = zip_ref.namelist()[0].split('/')[0]
                source_dir = os.path.join(temp_dir, root_dir)

                # Copiar archivos excluyendo los especificados
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, source_dir)

                        if any(excl in rel_path for excl in self.config["excluded_files"]):
                            continue

                        dest_path = os.path.join(".", rel_path)
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        shutil.copy2(src_path, dest_path)

            # Limpiar
            os.remove("update.zip")
            if temp_dir:
                shutil.rmtree(temp_dir)

            return True

        except Exception as e:
            QMessageBox.critical(
                None, "Error de Actualización", f"Falló: {str(e)}")
            return False
