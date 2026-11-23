from PyQt6.QtCore import QThread, pyqtSignal
import requests
import json


class ApiWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, method, url, headers, data=None, timeout=30, binary=False):
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers
        self.data = data
        self.timeout = timeout
        self.binary = binary

    def run(self):
        try:
            if self.method == "GET":
                response = requests.get(
                    self.url, headers=self.headers, timeout=self.timeout)
            elif self.method == "POST":
                response = requests.post(
                    self.url, headers=self.headers, json=self.data, timeout=self.timeout)
            elif self.method == "PUT":
                response = requests.put(
                    self.url, headers=self.headers, json=self.data, timeout=self.timeout)
            elif self.method == "DELETE":
                response = requests.delete(
                    self.url, headers=self.headers, timeout=self.timeout)
            else:
                self.error.emit(f"Método {self.method} no soportado")
                return

            if response.status_code in [200, 201, 204]:
                if self.binary:
                    # Devolver el contenido binario directamente
                    self.finished.emit(response.content)
                else:
                    if response.status_code == 204 or not response.text.strip():
                        self.finished.emit({"message": "Operación exitosa"})
                    else:
                        self.finished.emit(response.json())
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', response.text)
                except:
                    error_msg = response.text
                self.error.emit(f"Error {response.status_code}: {error_msg}")

        except requests.exceptions.Timeout:
            self.error.emit("Tiempo de espera agotado al conectar con la API.")
        except Exception as e:
            self.error.emit(f"Error en la solicitud: {str(e)}")
