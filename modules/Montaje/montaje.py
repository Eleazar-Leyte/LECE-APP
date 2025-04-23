from functools import partial
from PyQt6.QtWidgets import QTableWidgetItem, QMessageBox
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6 import uic, QtWidgets, QtCore, QtGui
from psycopg2 import Binary, sql
from datetime import datetime
import os
import uuid
import subprocess
import json

from DatabaseManager import DatabaseManager
from TableManager import TableManager


class Montaje():
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.montaje = uic.loadUi("modules/Montaje/Cuadre.ui")
        self.montaje.showMaximized()

        # Inicializamos las conexiones a las bases de datos
        self.db_personal = DatabaseManager("Personal")
        self.db_almacen = DatabaseManager("Almacen_construcción")
        self.db_areas = DatabaseManager("Áreas")
        self.db_produccion = DatabaseManager("Producción")

        self.cargar_botonoes()
        self.cargar_areas()
        self._configurar_tabla_consumo()

    def cargar_botonoes(self):
        """
        Carga los botones y señales de la Ui Cuadre.
        """
        self.montaje.btn_salir.clicked.connect(self.salir)
        self.montaje.btn_regresar.clicked.connect(self.regresar)
        self.montaje.btn_buscar.clicked.connect(self.buscar_folios)
        self.montaje.lista_instalaciones.itemClicked.connect(
            self._actualizar_tabla_materiales)
        self.montaje.btn_guardar.clicked.connect(self._guardar_cambios)

    def regresar(self):
        """
        Regresa al menú de administración.
        """
        from modules.menu_admin import MenuAdmin
        self.montaje.close()
        self.menu_admin = MenuAdmin(self.usuario_actual)

    def salir(self):
        """
        Cierra la ventana sesión actual y redirige al usuarios al Login.
        """
        try:
            # Limpia la sesión actual
            self.usuario_actual.clear()
            # Cierra la ventana de montaje
            self.montaje.close()

            from modules.login.login import Login
            self.login = Login()

            QMessageBox.information(
                None, "Sesión cerrada", "Se ha cerrado la sesión exitosamente."
            )
        except Exception as e:
            QMessageBox.critical(
                None, "Error", f"Error al cerrar la sesión: {e}"
            )

    def cargar_areas(self):
        """
        Carga las áreas desde la base de datos.
        """
        self.montaje.str_area.clear()
        self.montaje.str_area.currentIndexChanged.connect(self.cargar_cope)

        try:
            if self.usuario_actual["rol"] == "Directivo":
                query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(query)
            else:
                query = query = "SELECT \"Nombre del Área\" FROM Areas WHERE \"Nombre del Área\" = %s AND \"Estado\" = TRUE"
                resultados = self.db_personal.execute_query(query, (self.usuario_actual["area"],)
                                                            )
            if resultados:
                for resultado in resultados:
                    self.montaje.str_area.addItem(resultado['Nombre del Área'])
            else:
                QMessageBox.warning(
                    self.montaje, "Información", "No hay áreas disponibles."
                )
        except Exception as e:
            QMessageBox.critical(
                self.montaje, "Error", f"Error al cargar las áreas: {e}"
            )

    def cargar_cope(self):
        """
        Carga los COPE desde la base de datos.
        """
        area_seleccionada = self.montaje.str_area.currentText().strip()
        self.montaje.str_cope.clear()
        self.montaje.str_cope.addItem("Seleccione un COPE")
        self.montaje.str_cope.currentIndexChanged.connect(
            self.actualizar_exptec)

        if not area_seleccionada:
            QMessageBox.warning(
                self.montaje, "Advertencia", "Seleccione un área primero."
            )
            return

        try:
            # Verificar que el área seleccionada exista como tabla en la base de datos.
            query_tablas = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            tablas_disponibles = [tabla["table_name"]
                                  for tabla in self.db_areas.execute_query(query_tablas)]

            if area_seleccionada not in tablas_disponibles:
                QMessageBox.critical(
                    self.montaje, "Error", f"La tablas correspondiente al área '{area_seleccionada}' no existe en la base de datos."
                )
                return

            # Consultar el área para el Copé seleccionado
            query = f"SELECT DISTINCT \"Copé\" FROM \"{area_seleccionada}\""
            resultados = self.db_areas.execute_query(query)

            if resultados:
                for resultado in resultados:
                    self.montaje.str_cope.addItem(resultado["Copé"])
            else:
                QMessageBox.information(
                    self.montaje,
                    "Información",
                    "No se encontraron Copé disponibles para esta Área"
                )
        except Exception as e:
            QMessageBox.critical(
                self.montaje, "Error", f"Error al cargar los datos de Copé:{e}"
            )

    def actualizar_exptec(self):
        """
        Cargar el nombre de los técnicos en el ComboBox según el Área y Copé seleccionado.
        """
        try:
            self.montaje.str_exptec.clear()

            area_seleccionada = self.montaje.str_area.currentText().strip()
            cope_seleccionado = self.montaje.str_cope.currentText().strip()

            if not area_seleccionada or not cope_seleccionado:
                QMessageBox.warning(
                    self.montaje,
                    "Datos incompletos",
                    "Por favor, Seleccione una Área y un Copé"
                )
                return
            # Obtener el id_area correspondiente al nombre del área
            query_id_area = """
            SELECT id FROM areas
            WHERE "Nombre del Área" = %s
            """

            resultados_id_area = self.db_personal.execute_query(
                query_id_area, (area_seleccionada,))

            if not resultados_id_area:
                QMessageBox.critical(
                    self.montaje,
                    "Error",
                    f"No se encontró el Id pa el área: {area_seleccionada}"
                )
                return
            id_area = resultados_id_area[0]["id"]

            query_tecnicos = """
            SELECT id,
            "Apellido Paterno",
            "Apellido Materno",
            "Nombre (s)"
            FROM personal_o
            WHERE "id_area" = %s AND "Cope" = %s
            """
            resultados = self.db_personal.execute_query(
                query_tecnicos, (id_area, cope_seleccionado))

            if resultados:
                for tecnicos in resultados:
                    nombre_completo = (
                        f"{tecnicos['Nombre (s)']} "
                        f"{tecnicos['Apellido Paterno']} "
                        f"{tecnicos['Apellido Materno']}"
                    )
                    self.montaje.str_exptec.addItem(
                        nombre_completo)
            else:
                QMessageBox.information(
                    self.montaje,
                    "Sin técnicos",
                    "No se encontraron técnicos disponibles para esta Área y Copé."
                )
        except Exception as e:
            QMessageBox.critical(
                self.montaje,
                "Error",
                f"Error al cargar los técnicos: {e}."
            )
# ----------------------------Lógica principal --------------------------------

    def buscar_folios(self):
        """
        Función padre para la busque de folios en la base de datos
        """
        try:

            if not self._validar_parametros():
                return

            self.montaje.lista_instalaciones.clear()
            self._configurar_tabla_consumo()

            tablas = {"fibra_optica": "Fibra Óptica",
                      "cobre": "Cobre", "a4_incentivos": "A4 Incentivos",
                      "quejas": "Quejas", }
            EMOJIS = self._configurar_emojis()

            for tabla, titulo in tablas.items():
                self._procesar_tabla(tabla, titulo, EMOJIS)

        except Exception as e:
            self._manejar_error(e)

    def _actualizar_tabla_materiales(self, item):
        try:
            tabla_origen, folio = item.data(Qt.ItemDataRole.UserRole)

            # Obtener datos del folio
            query_folio = sql.SQL("""
                SELECT
                    numero_serie,
                    exp_tecnico AS tecnico_prod,
                    area AS area_prod,
                    cope AS cope_prod
                FROM public.{table}
                WHERE folio_pisa = %s
            """).format(table=sql.Identifier(tabla_origen))

            datos_folio = self.db_produccion.execute_query(
                query_folio, (folio,))[0]
            tecnico = datos_folio["tecnico_prod"].strip()
            area = datos_folio["area_prod"].strip()
            cope = datos_folio["cope_prod"].strip()
            serie = datos_folio.get("numero_serie")

            # Consultar ambos tipos de datos
            datos = []

            # 1. Consultar equipo si existe
            if tabla_origen in ["fibra_optica", "cobre", "a4_incentivos", "quejas"] and serie:
                datos_equipo = self._consultar_equipo(tabla_origen, serie)
                datos.extend(datos_equipo)

            # 2. Siempre consultar misceláneos
            datos_misc = self._consultar_miscelaneos(tecnico, area, cope)
            datos.extend(datos_misc)

            # Formatear y cargar
            datos_formateados = self._formatear_datos(datos, tabla_origen)
            TableManager.populate_table(
                self.montaje.tabla_materiales, datos_formateados, "Consumo")

        except IndexError:
            QMessageBox.warning(self.montaje, "Error",
                                "Folio sin datos asociados")
        except Exception as e:
            QMessageBox.critical(self.montaje, "Error", f"Error: {str(e)}")
# ---------------------------Consultas SQL ------------------------------------

    def _consultar_equipo(self, tipo_tabla: str, serie: str) -> list:
        TABLAS_EQUIPO = {
            "fibra_optica": {"tabla": "ONT en Campo", "tipo": "ONT"},
            "cobre": {"tabla": "modem_en_campo", "tipo": "MODEM"},
            "a4_incentivos": {"tabla": "modem_en_campo", "tipo": "MODEM"},
            "quejas": {"tabla": None, "tipo": None}  # Caso especial
        }

        # Obtener metadata de la tabla
        metadata = TABLAS_EQUIPO.get(tipo_tabla, {"tabla": None, "tipo": None})
        tabla_almacen = metadata["tabla"]
        tipo = metadata["tipo"]

        if tabla_almacen and serie:
            query = sql.SQL("""
                SELECT 
                    "Numero de Serie" AS n_serie,
                    modelo AS material,
                    cantidad AS asignado,
                    %s AS tipo  -- Añadir columna tipo
                FROM public.{tabla}
                WHERE "Numero de Serie" = %s
            """).format(tabla=sql.Identifier(tabla_almacen))

            resultados = self.db_almacen.execute_query(query, (tipo, serie))
            return resultados
        return []

    def _consultar_miscelaneos(self, tecnico: str, area: str, cope: str) -> list:
        """Consulta misceláneos con validación de parámetros"""
        # Validar parámetros no vacíos
        if not all([tecnico, area, cope]):
            raise ValueError(
                "Parámetros incompletos para consulta de misceláneos")

        # Consulta con nombres exactos
        query = sql.SQL("""
            SELECT
                "Numero de Serie" AS n_serie,
                descripcion AS material,
                SUM(cantidad) AS asignado
            FROM miselaneo_en_campo
            WHERE "Expediente Técnico" ILIKE %s
            AND area ILIKE %s
            AND "Centro de Trabajo" ILIKE %s
            GROUP BY "Numero de Serie", descripcion
        """)

        return self.db_almacen.execute_query(query, (
            f"%{tecnico}%",
            f"%{area}%",
            f"%{cope}%"
        ))
# -------------------------------Helpers -------------------------------------

    def _validar_parametros(self):
        """Validación unificada de parámetros"""
        params = [
            self.montaje.str_area.currentText().strip(),
            self.montaje.str_cope.currentText().strip(),
            self.montaje.str_exptec.currentText().strip()
        ]
        if not all(params):
            QMessageBox.warning(
                self.montaje,
                "Datos incompletos",
                "Seleccione Área, COPÉ y técnico."
            )
            return False
        return True

    def _formatear_datos(self, datos: list, tipo_tabla: str) -> list:
        """Formateo unificado de datos"""
        formatted = []
        for item in datos:
            entry = {
                "Número de Serie": item.get("n_serie"),
                "Materiales": item["material"],
                "Tipo": item.get("tipo", "Misceláneo"),
                "Asignado": str(item["asignado"]),
                "Consumido": "0",  # Placeholder para lógica futura
                "Diferencia": str(item["asignado"])
            }

            formatted.append(entry)
        return formatted

    def _configurar_tabla_consumo(self):
        """
        Configurar los encabezados de la tabla consumo.
        """
        TableManager.populate_table(
            self.montaje.tabla_materiales,
            [],
            "Consumo"
        )
        # Bloquear todas las columnas excepto "Consumido" (Indice 3)
        for col in range(self.montaje.tabla_materiales.columnCount()):
            if col != 3:
                for row in range(self.montaje.tabla_materiales.rowCount()):
                    item = self.montaje.tabla_materiales.item(row, col)
                    if item:
                        item.setFlags(item.flags() & ~
                                      Qt.ItemFlag.ItemIsEditable)

        # Conectar señal de cambio
        self.montaje.tabla_materiales.cellChanged.connect(
            self._actualizar_diferencia)

    def _configurar_emojis(self):
        """
        Retorno un directorio de recursos gráficos (función hija)
        """

        return {
            "pendiente": QtGui.QIcon("assets/icons/advertencia.png"),
            "completado": QtGui.QIcon("assets/icons/paloma.png"),
            "error": QtGui.QIcon("assets/icons/error.png")
        }

    def _procesar_tabla(self, tabla: str, titulo: str, emojis: dict):
        """
        Procesar una tabla completa.
        """
        resultados = self._consultar_folios(tabla)
        self._agregar_encabezado(titulo)
        self._procesar_resultados(tabla, resultados, emojis)

    def _consultar_folios(self, tabla: str) -> list:
        """
        Ejecuta la consulta con filtro de 24 horas para completados
        """
        query = sql.SQL("""
            SELECT folio_pisa, estatus, fecha_cuadre, exp_tecnico
            FROM public.{table}
            WHERE area = %s
            AND cope = %s
            AND exp_tecnico = %s
            AND (
                estatus IS NULL  -- Pendientes
                OR (
                    estatus ILIKE 'completado%%'  -- Completados recientes
                    AND fecha_cuadre >= NOW() - INTERVAL '24 HOURS'
                )
            )
        """).format(table=sql.Identifier(tabla))

        # Parámetros para la consulta (asegúrate de que no estén vacíos)
        params = (
            self.montaje.str_area.currentText().strip(),
            self.montaje.str_cope.currentText().strip(),
            self.montaje.str_exptec.currentText().strip()
        )

        # Verificar que ningún parámetro esté vacío
        if not all(params):
            raise ValueError("Faltan parámetros en la búsqueda")

        return self.db_produccion.execute_query(query, params)

    def _agregar_encabezado(self, titulo: str):
        """Crea un ítem de encabezado para la lista"""
        header = QtWidgets.QListWidgetItem(titulo)
        header.setFont(QtGui.QFont("Arial", 12, QtGui.QFont.Weight.Bold))
        header.setBackground(QtGui.QColor(230, 240, 250))
        self.montaje.lista_instalaciones.addItem(header)

    def _procesar_resultados(self, tabla: str, resultados: list, emojis: dict):
        """Procesa los registros de una tabla"""
        if not resultados:
            self._agregar_item_vacio(emojis["error"])
            return

        for registro in resultados:
            self._agregar_item(registro, tabla, emojis)

    def _agregar_item(self, registro: dict, tabla: str, emojis: dict):
        """Crea y configura un ítem de la lista"""
        folio = registro["folio_pisa"]
        estatus = registro["estatus"]

        emoji, tooltip = self._determinar_emoji_y_tooltip(estatus, emojis)

        item = QtWidgets.QListWidgetItem(emoji, f"  {folio}")
        item.setData(Qt.ItemDataRole.UserRole, (tabla, folio))
        item.setToolTip(tooltip)
        item.setFont(QtGui.QFont("Arial", 10))
        item.setForeground(QtGui.QColor(50, 50, 50))

        self.montaje.lista_instalaciones.addItem(item)

    def _determinar_emoji_y_tooltip(self, estatus: str, emojis: dict) -> tuple:
        """Determina recursos visuales según el estatus"""
        if estatus is None:
            return emojis["pendiente"], "Pendiente de cuadre"

        estatus = estatus.lower()

        if "completado" in estatus:
            return emojis["completado"], "Cuadre aplicado"
        elif "error" in estatus:
            return emojis["error"], "Error en el cuadre"

        return emojis["pendiente"], "Estado desconocido"

    def _agregar_item_vacio(self, emoji):
        """Agrega ítem para tablas vacías"""
        item = QtWidgets.QListWidgetItem(emoji, "  Sin registros")
        item.setForeground(QtGui.QColor(150, 150, 150))
        self.montaje.lista_instalaciones.addItem(item)

    def _manejar_error(self, error: Exception):
        """Centraliza el manejo de errores"""
        QMessageBox.critical(
            self.montaje,
            "Error",
            f"Error al buscar folios:\n{str(error)}"
        )
        print(f"Error en la búsqueda de folios: {str(error)}")

    def _poblar_tabla_consumos(self):
        """Llama a las consultas y llena la tabla de consumos"""
        try:
            # Consultar equipos principales
            ont_data = self._consultar_consumos("ONT en campo")
            modem_data = self._consultar_consumos("modem_en_campo")

            # Consultar misceláneos
            misc_data = self._consultar_consumos(
                "miselaneo_en_campo", es_misc=True)

            # Combinar y formatear datos
            combined_data = self._formatear_datos(
                ont_data + modem_data + misc_data)

            # Actualizar tabla usando TableManager
            TableManager.populate_table(
                self.montaje.tabla_materiales,
                combined_data,
                "Consumo"
            )
            # Bloquear todas las columnas excepto "Consumido" (Indice 3)
            for col in range(self.montaje.tabla_materiales.columnCount()):
                if col != 3:
                    for row in range(self.montaje.tabla_materiales.rowCount()):
                        item = self.montaje.tabla_materiales.item(row, col)
                        if item:
                            item.setFlags(item.flags() & ~
                                          Qt.ItemFlag.ItemIsEditable)

        except Exception as e:
            QMessageBox.critical(self.montaje, "Error",
                                 f"Error al cargar consumos: {str(e)}")

    def _consultar_consumos(self, tabla: str, es_misc: bool = False) -> list:
        """Consulta los datos de consumo (modificado para compatibilidad)"""
        query = sql.SQL("""
            SELECT
                numero_serie AS "Número de Serie",
                materiales AS "Materiales",
                asignado AS "Asignado",
                consumido AS "Consumido"
            FROM public.{table}
            WHERE area = %s
            AND cope = %s
            AND exp_tecnico = %s
            {filtro_adicional}
        """).format(
            table=sql.Identifier(tabla),
            filtro_adicional=sql.SQL("") if es_misc else sql.SQL(
                "AND numero_serie IS NOT NULL")
        )

        params = (
            self.montaje.str_area.currentText().strip(),
            self.montaje.str_cope.currentText().strip(),
            self.montaje.str_exptec.currentText().strip()
        )

        return self.db_produccion.execute_query(query, params)

    def _actualizar_diferencia(self, row, column):
        """
        Actualizar diferencia y validar valores.
        """
        if column != 4:
            return

        try:
            asignado = int(self.montaje.tabla_materiales.item(row, 3).text())
            consumido = int(self.montaje.tabla_materiales.item(row, 4).text())
            if consumido < 0 or consumido > asignado:
                raise ValueError("Consumo inválido")

            diferencia = asignado - consumido

            # Actualizar la celda de diferencia
            item = QTableWidgetItem(str(diferencia))
            # item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.montaje.tabla_materiales.setItem(row, 5, item)

            # En caso de diferencia negativo
            if diferencia < 0:
                item.setForeground(QtGui.QColor(255, 0, 0))
            else:
                item.setForeground(QtGui.QColor(0, 0, 0))

        except ValueError as e:
            self.montaje.tabla_materiales.item(row, 3).setText("0")
            QMessageBox.warning(self.montaje, "Error",
                                f"Datos inválidos: {str(e)}")

    def _guardar_cambios(self):
        try:
            # Obtener datos base
            item_seleccionado = self.montaje.lista_instalaciones.currentItem()
            if not item_seleccionado or not item_seleccionado.data(Qt.ItemDataRole.UserRole):
                QMessageBox.warning(self.montaje, "Error",
                                    "Seleccione un folio válido")
                return

            tabla_origen, folio = item_seleccionado.data(
                Qt.ItemDataRole.UserRole)
            area = self.montaje.str_area.currentText().strip()
            cope = self.montaje.str_cope.currentText().strip()
            exp_tecnico = self.montaje.str_exptec.currentText().strip()

            if not all([area, cope, exp_tecnico]):
                QMessageBox.warning(
                    self.montaje, "Error", "Faltan datos esenciales (Área/COPÉ/Técnico)")
                return

            consumo_data = []

            # Procesar cada fila de la tabla
            for row in range(self.montaje.tabla_materiales.rowCount()):
                n_serie = self.montaje.tabla_materiales.item(
                    row, 0).text().strip()
                material = self.montaje.tabla_materiales.item(
                    row, 1).text().strip()
                consumido = int(
                    self.montaje.tabla_materiales.item(row, 4).text() or 0)
                tipo = self.montaje.tabla_materiales.item(
                    row, 2).text().strip()

                if consumido <= 0:
                    continue

                # Determinar tipo de item y columna técnica
                if tipo == "ONT":
                    tabla_almacen = "ONT en Campo"
                    columna_cope = "Centro de Trabajo"
                    columna_tecnico = "Expediente Técnico"
                elif tipo == "MODEM":
                    tabla_almacen = "modem_en_campo"
                    columna_cope = "Centro de Trabajo"
                    columna_tecnico = "Expediente Técnico"
                else:
                    self._descontar_miscelaneos(
                        n_serie, material, consumido, area, cope, exp_tecnico, consumo_data
                    )
                    continue

                # Operaciones de descuento (usar tabla_almacen y columnas)
                try:
                    with self.db_almacen.connection.cursor() as cursor:
                        # Paso 1: Descontar
                        cursor.execute(
                            sql.SQL("""
                                UPDATE {}
                                SET cantidad = cantidad - %s
                                WHERE "Numero de Serie" = %s
                                AND area = %s
                                AND {} = %s
                                AND {} = %s
                            """).format(
                                sql.Identifier(tabla_almacen),
                                sql.Identifier(columna_cope),
                                sql.Identifier(columna_tecnico)
                            ),
                            (consumido, n_serie, area, cope, exp_tecnico)
                        )

                        # Paso 2: Eliminar si es necesario
                        cursor.execute(
                            sql.SQL("""
                                DELETE FROM {}
                                WHERE "Numero de Serie" = %s
                                AND area = %s
                                AND {} = %s
                                AND {} = %s
                                AND cantidad <= 0
                            """).format(
                                sql.Identifier(tabla_almacen),
                                sql.Identifier(columna_cope),
                                sql.Identifier(columna_tecnico)
                            ),
                            (n_serie, area, cope, exp_tecnico)
                        )
                        self.db_almacen.connection.commit()

                        consumo_data.append({
                            "numero_serie": n_serie,
                            "tipo": tipo.lower(),
                            "descripcion": material,
                            "cantidad": consumido
                        })

                except Exception as e:
                    self.db_almacen.connection.rollback()
                    QMessageBox.critical(self.montaje, "Error",
                                         f"Error en fila {row+1}: {str(e)}")
                    return
            # Guardar en producción
            if consumo_data:
                self.db_produccion.execute_query(
                    sql.SQL("""
                        UPDATE {}
                        SET consumo = %s::JSONB,
                            estatus = 'Completado',
                            fecha_cuadre = NOW()
                        WHERE folio_pisa = %s
                    """).format(sql.Identifier(tabla_origen)),
                    (json.dumps({"items": consumo_data}), folio),
                    fetch=False
                )
                QMessageBox.information(
                    self.montaje, "Éxito", "Datos guardados correctamente")
            else:
                QMessageBox.warning(
                    self.montaje, "Advertencia", "No hay consumos válidos")

        except Exception as e:
            QMessageBox.critical(self.montaje, "Error",
                                 f"Error crítico: {str(e)}")

    def _descontar_miscelaneos(self, n_serie: str, material: str, consumido: int, area: str, cope: str, exp_tecnico: str, consumo_data: list):
        """Descuenta misceláneos usando lógica FIFO."""
        try:
            with self.db_almacen.connection.cursor() as cursor:
                # Obtener registros ordenados por fecha ascendente (más antiguos primero)
                cursor.execute(
                    sql.SQL("""
                        SELECT "Numero de Serie", cantidad, "Fecha de surtido"
                        FROM miselaneo_en_campo
                        WHERE descripcion = %s
                        AND area = %s
                        AND "Centro de Trabajo" = %s
                        AND "Expediente Técnico" = %s
                        ORDER BY "Fecha de surtido"
                    """),
                    (material, area, cope, exp_tecnico)
                )
                registros = cursor.fetchall()

                consumido_restante = consumido

                for registro in registros:
                    if consumido_restante <= 0:
                        break

                    serie, cantidad_disponible, fecha = registro
                    descuento = min(cantidad_disponible, consumido_restante)

                    # Actualizar registro
                    cursor.execute(
                        sql.SQL("""
                            UPDATE miselaneo_en_campo
                            SET cantidad = cantidad - %s
                            WHERE "Numero de Serie" = %s
                            AND "Fecha de surtido" = %s
                        """),
                        (descuento, serie, fecha)
                    )

                    # Eliminar si la cantidad llega a 0
                    if (cantidad_disponible - descuento) <= 0:
                        cursor.execute(
                            sql.SQL("""
                                DELETE FROM miselaneo_en_campo
                                WHERE "Numero de Serie" = %s
                                AND "Fecha de surtido" = %s
                            """),
                            (serie, fecha)
                        )

                    consumido_restante -= descuento

                # Registrar solo el consumo real aplicado
                if (consumido - consumido_restante) > 0:
                    consumo_data.append({
                        "numero_serie": n_serie,
                        "tipo": "miselaneo",
                        "descripcion": material,
                        "cantidad": (consumido - consumido_restante)
                    })

                self.db_almacen.connection.commit()

        except Exception as e:
            self.db_almacen.connection.rollback()
            QMessageBox.critical(
                self.montaje,
                "Error en misceláneo",
                f"No se pudo actualizar el inventario: {str(e)}"
            )
            raise
