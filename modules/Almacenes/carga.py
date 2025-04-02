import pandas as pd
from PyQt6.QtWidgets import QFileDialog, QMessageBox


def cargar_catalogo_ax(self):
    """
    Carga los datos del catálogo AX desde un archivo Excel a la tabla 'articulos_estandar'.
    """
    # Abrir cuadro de diálogo para seleccionar el archivo Excel
    file_dialog = QFileDialog()
    file_path, _ = file_dialog.getOpenFileName(
        self, "Seleccionar archivo Excel", "", "Archivos Excel (*.xlsx *.xls)"
    )

    if not file_path:
        QMessageBox.warning(self, "Advertencia",
                            "No se seleccionó ningún archivo.")
        return

    try:
        # Leer el archivo Excel
        df = pd.read_excel(file_path)

        # Verificar que las columnas necesarias estén presentes
        columnas_requeridas = ["Código AX",
                               "Código Siatel", "Nombre del Artículo", "Unidad"]
        if not all(col in df.columns for col in columnas_requeridas):
            QMessageBox.critical(
                self,
                "Error",
                f"El archivo debe contener las columnas: {', '.join(columnas_requeridas)}.",
            )
            return

        # Renombrar columnas para que coincidan con la tabla
        df.rename(
            columns={
                "Código AX": "codigo_ax",
                "Código Siatel": "codigo_siatel",
                "Nombre del Artículo": "nombre_articulo",
                "Unidad": "unidad",
            },
            inplace=True,
        )

        # Insertar datos en la base de datos
        query = """
            INSERT INTO articulos_estandar (codigo_ax, codigo_siatel, nombre_articulo, unidad)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (codigo_ax) DO NOTHING;
        """
        datos = df.to_records(index=False)
        self.db.execute_many(query, datos)

        QMessageBox.information(
            self, "Éxito", "El catálogo AX se ha cargado correctamente a la base de datos."
        )
    except Exception as e:
        QMessageBox.critical(
            self, "Error", f"Error al cargar el catálogo AX: {e}")
