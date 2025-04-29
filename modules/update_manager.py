import os
import sys
import zipfile
import requests
from PyQt6.QtWidgets import QMessageBox


class UpdateManager:
    def __init__(self):
        self.config = {
            "repo": "Eleazar-Leyte/LECE-APP",
            "branch": "master",
            "version_file": "version.txt",
            "excluded_files": ["config.json", ".env", ".gitignore", ".github/workflows/main.yml"],
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
            response = requests.get(url, headers=headers)

            # Validar respuesta
            if response.status_code != 200:
                raise Exception(f"Error HTTP {response.status_code}")

            # Guardar ZIP
            with open("update.zip", "wb") as f:
                f.write(response.content)

            # Extraer ajustando rutas
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                root_dir = zip_ref.namelist()[0]  # Ej: "LECE-APP-master/"
                for file in zip_ref.namelist():
                    if not any(excluido in file for excluido in self.config["excluded_files"]):
                        target_path = file.replace(root_dir, "", 1)
                        if target_path:
                            zip_ref.extract(file, ".")
                            os.rename(file, target_path)

            os.remove("update.zip")
            return True

        except Exception as e:
            QMessageBox.critical(None, "Error de Actualización",
                                 f"Falló la actualización: {str(e)}")
            return False
