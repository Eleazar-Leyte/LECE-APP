import os
import sys
import zipfile
import requests
from PyQt6.QtWidgets import QMessageBox


class UpdateManager:
    def __init__(self):
        self.config = {
            "repo": "EleazarLeyteZ/LECE-APP",
            "branch": "master",
            "version_file": "version.txt",
            "excluded_files": ["config.json"],
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
            # Descargar actualización
            url = f"https://github.com/{self.config['repo']}/archive/refs/heads/{self.config['branch']}.zip"
            response = requests.get(url)

            # Guardar temporalmente
            with open("update.zip", "wb") as f:
                f.write(response.content)

            # Extraer archivos
            with zipfile.ZipFile("update.zip", 'r') as zip_ref:
                for file in zip_ref.namelist():
                    if not any(excluido in file for excluido in self.config["excluded_files"]):
                        zip_ref.extract(file, ".")

            os.remove("update.zip")
            return True

        except Exception as e:
            print(f"Error: {str(e)}")
            return False
