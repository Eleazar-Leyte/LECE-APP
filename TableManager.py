from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QTableWidgetItem, QLabel
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt


class TableManager:
    # Diccionario para mapear tablas con sus respectivos encabezados
    TABLE_HEADERS = {
        "Almacén": [
            "Cantidad", "Unidad", "Descripción", "Número de Serie", "Área", "COPE"
        ],
        "Catalogo": [
            "Id", "Código AX", "Descripción"
        ],
        "MODEM": [
            "Número de Serie", "Cantidad", "Unidad", "Modelo", "Área",
            "Centro de Trabajo", "Ubicación", "Imagen"
        ],
        "ONT": [
            "Número de Serie", "Cantidad", "Unidad", "Modelo", "Área",
            "Centro de Trabajo", "Ubicación", "Imagen"
        ],
        "ONT en campo": [
            "Número de Serie", "Cantidad", "Unidad", "Modelo", "Área",
            "Centro de Trabajo", "Expediente Técnico", "Imagen"
        ],
        "Personal_O": [
            "Número de Empleado", "Apellido Paterno", "Apellido Materno",
            "Nombre (s)", "Expediente Técnico Cobre", "Expediente Técnico F.O.",
            "Área", "COPE", "N.S.S.", "R.F.C.", "Dirección"
        ],
        "M_Almacen": [
            "Número de serie", "Cantidad disponible", "Unidad", "Descripción", "Tipo",
            "Cantidad a enviar"
        ],
        "Reportes": [
            "Id Movimiento", "Origen", "Destino", "Fecha de Movimiento", "Estatus",
            "Reporte"
        ],
        "Asignacion_PO": [
            "Número de Serie", "Cantidad", "Unidad", "Modelo", "Imagen", "Tipo", "Fecha",
            "Cantidad a Entregar"
        ],
        "Entregas": [
            "Id entrega", "Area", "COPE", "Expediente técnico", "Fecha de entrega",
            "Reporte"
        ],
        "Producción F.O.": [
            "Folio Pisa", "Número de Teléfono", "Tipo de Tarea", "Metros", "Número de Serie",
            "Modelo", "Fecha de Posteo", "Imagen"
        ],
        "Producción Cobre": [
            "Folio Pisa", "Número de Teléfono", "Tipo de Tarea", "Metros", "Número de Serie",
            "Modelo", "Fecha de Posteó", "Imagen"
        ],
        "Producción Quejas": [
            "Folio Pisa", "Número de Teléfono", "Tipo de Tarea", "Metros", "Número de Serie",
            "Modelo", "Fecha de Posteó", "Imagen"
        ],
        "Producción A4": [
            "Folio Pisa", "Número de Teléfono", "Tipo de Tarea", "Metros", "Número de Serie",
            "Modelo", "Fecha de Posteó", "Imagen"
        ],
        "Consumo": [
            "Número de Serie", "Materiales", "Tipo", "Asignado", "Consumido", "Diferencia"
        ]
        # Agrega más tablas según sea necesario
    }

    COLUMN_MAPPINGS = {
        "Almacén": {
            "Cantidad": "total_cantidad",
            "Unidad": "unidad",
            "Descripción": "descripcion",
            "Número de Serie": "numeros_de_serie",
            "Área": "area",
            "COPE": "cope"
        },
        "MODEM": {
            "Número de Serie": "Numero de Serie",
            "Cantidad": "cantidad",
            "Unidad": "unidad",
            "Modelo": "modelo",
            "Área": "area",
            "Centro de Trabajo": "Centro de Trabajo",
            "Ubicación": "ubicacion",
            "Imagen": "imagen"
        },
        "ONT": {
            "Número de Serie": "Numero de Serie",
            "Cantidad": "cantidad",
            "Unidad": "unidad",
            "Modelo": "modelo",
            "Área": "area",
            "Centro de Trabajo": "Centro de Trabajo",
            "Ubicación": "ubicacion",
            "Imagen": "imagen"
        },
        "ONT en campo": {
            "Número de Serie": "Numero de Serie",
            "Cantidad": "cantidad",
            "Unidad": "unidad",
            "Modelo": "modelo",
            "Área": "area",
            "Centro de Trabajo": "Centro de Trabajo",
            "Expediente Técnico": "Expediente Técnico",
            "Imagen": "imagen"
        },
        "modem_en_campo": {
            "Número de Serie": "Numero de Serie",
            "Cantidad en almacen": "cantidad",
            "Unidad": "unidad",
            "Modelo": "modelo",
            "Área": "area",
            "Centro de Trabajo": "Centro de Trabajo",
            "Expediente Técnico": "Expediente Técnico",
            "Imagen": "imagen"
        },
        "Personal_O": {
            "Número de Empleado": "id",
            "Apellido Paterno": "Apellido Paterno",
            "Apellido Materno": "Apellido Materno",
            "Nombre (s)": "Nombre (s)",
            "Expediente Técnico Cobre": "Expediente Técnico Cobre",
            "Expediente Técnico F.O.": "Expediente Técnico F.O.",
            "Área": "id_area",
            "COPE": "Cope",
            "N.S.S.": "N.S.S.",
            "R.F.C.": "R.F.C.",
            "Dirección": "Dirección"
        },
        "Catalogo": {
            "Id": "id_producto",
            "Código AX": "codigo_ax",
            "Descripción": "descripcion",
        },
        "M_Almacen": {
            "Número de serie": "Numero de Serie",
            "Cantidad disponible": "cantidad",
            "Unidad": "unidad",
            "Descripción": "descripcion",
            "Tipo": "tipo",
            "Cantidad a enviar": "cantidad_a_enviar"
        },
        "Reportes": {
            "Id Movimiento": "id_movimiento",
            "Origen": "origen",
            "Destino": "destino",
            "Fecha de Movimiento": "Fecha de Movimiento",
            "Estatus": "Tipo de Movimiento",
            "Reporte": "reporte_path"
        },
        "Asignacion_PO": {
            "Número de Serie": "Numero de Serie",
            "Cantidad en almacén": "total_cantidad",
            "Unidad": "unidad",
            "Modelo": "modelo",
            "Imagen": "imagen",
            "Tipo": "tipo",
            "Fecha": "Fecha de Registro",
            "Cantidad a Entregar": "cantidad_a_entregar"
        },
        "Entregas": {
            "Id entrega": "id_entrega",
            "Area": "area",
            "COPE": "cope",
            "Expediente técnico": "expediente_tecnico",
            "Fecha de entrega": "Fecha de Entrega",
            "Reporte": "reporte_path"
        },
        "Producción F.O.": {
            "Folio Pisa": "folio_pisa",
            "Número de Teléfono": "telefono_asignado",
            "Tipo de Tarea": "tipo_tarea",
            "Metros": "cantidad_mts",
            "Número de Serie": "numero_de_serie",
            "Modelo": "modelo_ont",
            "Fecha de Posteo": "fecha_posteo",
            "Imagen": "imagen"
        },
        "Producción Cobre": {
            "Folio Pisa": "folio_pisa",
            "Número de Teléfono": "telefono_asignado",
            "Tipo de Tarea": "tipo_tarea",
            "Metros": "cantidad_mts",
            "Número de Serie": "numero_serie",
            "Modelo": "modelo_modem",
            "Fecha de Posteo": "fecha_posteo",
            "Imagen": "imagen"
        },
        "Producción Quejas": {
            "Folio Pisa": "folio_pisa",
            "Número de Teléfono": "telefono_asignado",
            "Tipo de Tarea": "tipo_tarea",
            "Metros": "cantidad_mts",
            "Número de Serie": "numero_serie",
            "Modelo": "modelo_ont",
            "Fecha de Posteo": "fecha_posteo",
            "Imagen": "imagen"
        },
        "Producción A4": {
            "Folio Pisa": "folio_pisa",
            "Número de Teléfono": "telefono_asignado",
            "Tipo de Tarea": "tipo_tarea",
            "Metros": "cantidad_mts",
            "Número de Serie": "numero_serie",
            "Modelo": "modelo_ont",
            "Fecha de Posteo": "fecha_posteo",
            "Imagen": "imagen"
        },
        "Consumo": {
            "Número de Serie": "Número de Serie",
            "Materiales": "Materiales",
            "Tipo": "Tipo",
            "Asignado": "Asignado",
            "Consumido": "Consumido",
            "Diferencia": "Diferencia"
        }
        # Agrega más tablas según sea necesario
    }

    @staticmethod
    def populate_table(table_widget, data, table_name):
        """
        Llena un widget de tabla (QTableWidget) con datos de la base de datos y encabezados predefinidos.
        """
        # Obtener los encabezados y el mapeo de columnas
        headers = TableManager.TABLE_HEADERS.get(table_name)
        column_mapping = TableManager.COLUMN_MAPPINGS.get(table_name)

        if not headers or not column_mapping:
            raise ValueError(
                f"Los encabezados o columnas para la tabla '{table_name}' no están definidos."
            )

        # Configurar encabezados
        table_widget.setColumnCount(len(headers))
        table_widget.setHorizontalHeaderLabels(headers)

        # Limpiar la tabla antes de llenarla
        table_widget.setRowCount(0)

        # Determinar si la tabla tiene una columna de imagen
        has_image = "Imagen" in headers
        image_column_index = headers.index("Imagen") if has_image else -1

        # Rellenar la tabla con datos
        for row_idx, row_data in enumerate(data):
            table_widget.insertRow(row_idx)
            for col_idx, header in enumerate(headers):
                # Obtener el nombre de la columna correspondiente
                column_name = column_mapping.get(header)
                # Recuperar el valor por columna real
                value = row_data.get(column_name, "")
                if has_image and col_idx == image_column_index and value:
                    # Procesar y mostrar la imagen
                    label = QLabel()
                    pixmap = TableManager._convert_blob_to_pixmap(value)
                    if pixmap:
                        label.setPixmap(pixmap.scaled(
                            100, 100, Qt.AspectRatioMode.KeepAspectRatio
                        ))
                        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                        table_widget.setCellWidget(row_idx, col_idx, label)
                    else:
                        table_widget.setItem(
                            row_idx, col_idx, QTableWidgetItem("Imagen inválida"))
                else:
                    # Insertar texto normal
                    table_widget.setItem(
                        row_idx, col_idx, QTableWidgetItem(str(value) if value else ""))

        # Ajustar el tamaño de las columnas
        table_widget.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.ResizeMode.Stretch
        )

    @staticmethod
    def _convert_blob_to_pixmap(blob_data):
        """
        Convierte datos binarios (blob) a un objeto QPixmap para ser mostrado en la tabla.

        :param blob_data: Datos binarios de la imagen
        :return: QPixmap o None si la conversión falla
        """
        try:
            # Convertir memoryview a bytes si es necesario
            if isinstance(blob_data, memoryview):
                blob_data = blob_data.tobytes()

            # Crear el QImage a partir de los datos
            image = QImage.fromData(blob_data)
            if image.isNull():
                raise ValueError("La imagen no es válida o está corrupta.")

            return QPixmap.fromImage(image)
        except Exception as e:
            print(f"Error al convertir blob a imagen: {e}")
            return None
