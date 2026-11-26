import json
import os
import base64

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "tema": "Oscuro",  # Oscuro, Claro, Sistema
    "api_url": "http://localhost:8000",
    "perfil_b64": None,  # Foto de perfil en base64
    "notificaciones": True
}


class SettingsManager:
    @staticmethod
    def cargar_config():
        if not os.path.exists(CONFIG_FILE):
            return DEFAULT_CONFIG
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Asegurar que existan todas las llaves
                for key, value in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = value
                return data
        except:
            return DEFAULT_CONFIG

    @staticmethod
    def guardar_config(data):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            return True
        except:
            return False

    @staticmethod
    def get_theme_stylesheet(tema):
        if tema == "Claro":
            return """
                QWidget { background-color: #F0F0F0; color: #333333; }
                QLabel { color: #333333; }
                QPushButton { background-color: #E0E0E0; color: #333333; border: 1px solid #CCC; border-radius: 4px; padding: 5px; }
                QPushButton:hover { background-color: #D0D0D0; }
                QLineEdit, QComboBox, QTextEdit { background-color: #FFFFFF; color: #000000; border: 1px solid #CCC; border-radius: 4px; }
                QTableWidget { background-color: #FFFFFF; color: #000000; }
                QHeaderView::section { background-color: #E0E0E0; color: #000000; }
            """
        elif tema == "Oscuro":
            return """
                QWidget { background-color: #2D2D2D; color: #FFFFFF; }
                QLabel { color: #FFFFFF; }
                QPushButton { background-color: #3D3D3D; color: #FFFFFF; border: 1px solid #555; border-radius: 4px; padding: 5px; }
                QPushButton:hover { background-color: #4D4D4D; }
                QLineEdit, QComboBox, QTextEdit { background-color: #1E1E1E; color: #FFFFFF; border: 1px solid #555; border-radius: 4px; }
                QTableWidget { background-color: #1E1E1E; color: #FFFFFF; }
                QHeaderView::section { background-color: #3D3D3D; color: #FFFFFF; }
            """
        return ""  # Del Sistema (deja el original)
