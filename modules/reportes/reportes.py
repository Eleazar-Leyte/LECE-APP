import uuid
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCharts import QChart, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries, QLineSeries, QDateTimeAxis
from PyQt6.QtGui import QPainter, QColor, QFont
from PyQt6.QtCore import Qt, QDateTime

from modules.reportes.reportes_ui import ReportesUI
from modules.Almacenes.api_worker import ApiWorker


class ReportesController:
    def __init__(self, usuario_actual):
        self.usuario_actual = usuario_actual
        self.reportes = ReportesUI()
        self.reportes.showMaximized()

        if not self.usuario_actual.get("access_token"):
            QMessageBox.critical(
                self.reportes, "Error", "No se encontró la información de autenticación.")
            self.reportes.close()
            return

        self.api_url = "http://localhost:8000"
        self.access_token = usuario_actual["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        self.active_workers = {}

        self.setup_connections()
        self.cargar_areas()

    def setup_connections(self):
        self.reportes.btn_regresar.clicked.connect(self.regresar)
        self.reportes.btn_salir.clicked.connect(self.salir)
        self.reportes.btn_actualizar.clicked.connect(self.generar_reporte)

    def _run_api_task(self, method, endpoint, data=None, callback_success=None, callback_error=None):
        worker_id = str(uuid.uuid4())
        url = endpoint if endpoint.startswith(
            "http") else f"{self.api_url}{endpoint}"
        worker = ApiWorker(method, url, self.headers, data)
        self.active_workers[worker_id] = worker

        def on_finished(result):
            if callback_success:
                callback_success(result)
            self.active_workers.pop(worker_id, None)
            worker.deleteLater()

        def on_error(error_msg):
            if callback_error:
                callback_error(error_msg)
            else:
                QMessageBox.critical(self.reportes, "Error API", error_msg)
            self.active_workers.pop(worker_id, None)
            worker.deleteLater()

        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        worker.start()

    def cargar_areas(self):
        self.reportes.str_area.addItem("Cargando...")
        self._run_api_task(
            method="GET", endpoint="/almacen/areas",
            callback_success=self._on_areas_cargadas
        )

    def _on_areas_cargadas(self, areas):
        self.reportes.str_area.clear()
        self.reportes.str_area.addItem("Todas", "Todas")
        for area in areas:
            self.reportes.str_area.addItem(area["nombre"], area["nombre"])

    def generar_reporte(self):
        area = self.reportes.str_area.currentData()
        fecha_ini = self.reportes.date_ini.date().toString("yyyy-MM-dd")
        fecha_fin = self.reportes.date_fin.date().toString("yyyy-MM-dd")

        # Si el usuario elige "Todas", la API debería adaptarse,
        # pero para este ejemplo forzaremos que elija una para ver los datos.
        if not area or area == "Todas":
            QMessageBox.warning(self.reportes, "Aviso",
                                "Por favor, seleccione un Área específica.")
            return

        self.reportes.btn_actualizar.setEnabled(False)
        self.reportes.btn_actualizar.setText(" Generando...")

        endpoint = f"/reportes/dashboard?area={area}&fecha_ini={fecha_ini}&fecha_fin={fecha_fin}"
        self._run_api_task(
            method="GET", endpoint=endpoint,
            callback_success=self._procesar_datos,
            callback_error=lambda e: self._on_error(e)
        )

    def _on_error(self, error):
        self.reportes.btn_actualizar.setEnabled(True)
        self.reportes.btn_actualizar.setText(" Generar Reporte")
        QMessageBox.critical(self.reportes, "Error", error)

    def _procesar_datos(self, data):
        self.reportes.btn_actualizar.setEnabled(True)
        self.reportes.btn_actualizar.setText(" Generar Reporte")

        self._graficar_tecnicos(data.get("tecnicos", []))
        self._graficar_tecnologias(data.get("tecnologias", []))
        self._graficar_tendencia(data.get("tendencia", []))

    def _graficar_tecnicos(self, datos):
        """Gráfico de Barras: Trabajos por Técnico"""
        series = QBarSeries()
        bar_set = QBarSet("Trabajos")
        bar_set.setColor(QColor("#EFBFBC"))  # Color Durazno

        categorias = []
        for item in datos:
            tecnico = item.get("exp_tecnico", "Desconocido")
            total = item.get("total_trabajos", 0)
            categorias.append(tecnico)
            bar_set.append(total)

        series.append(bar_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Top Técnicos (Trabajos Realizados)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("white"))

        axis_x = QBarCategoryAxis()
        axis_x.append(categorias)
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.reportes.chart_view_tecnicos.setChart(chart)

    def _graficar_tecnologias(self, datos):
        """Gráfico de Pastel: Distribución de Tecnologías"""
        series = QPieSeries()

        colores = ["#013B3D", "#1E7572", "#EFBFBC", "#E5AFA9"]

        for i, item in enumerate(datos):
            total = item.get("total", 0)
            if total > 0:
                nombre = item.get("tecnologia", "").replace("_", " ").title()
                slice_pie = series.append(f"{nombre} ({total})", total)
                slice_pie.setBrush(QColor(colores[i % len(colores)]))

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Distribución por Tecnología")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("white"))
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        self.reportes.chart_view_tecnologias.setChart(chart)

    def _graficar_tendencia(self, datos):
        """Gráfico de Líneas: Tendencia de Producción Diaria"""
        series = QLineSeries()
        series.setName("Trabajos Totales")
        series.setColor(QColor("#1E7572"))

        max_y = 0
        for item in datos:
            fecha_str = item.get("fecha")
            total = item.get("total", 0)
            if max_y < total:
                max_y = total

            # Convertir fecha (yyyy-mm-dd) a timestamp para el eje X
            qdt = QDateTime.fromString(fecha_str, "yyyy-MM-dd")
            series.append(qdt.toMSecsSinceEpoch(), total)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Tendencia de Producción (Por Día)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        chart.setBackgroundBrush(QColor("white"))

        axis_x = QDateTimeAxis()
        axis_x.setFormat("dd/MM")
        axis_x.setTickCount(min(len(datos), 10))
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setRange(0, max_y + 5)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        self.reportes.chart_view_tendencia.setChart(chart)

    def regresar(self):
        from modules.menu_admin import MenuAdmin
        self.menuadmin = MenuAdmin(self.usuario_actual)
        self.reportes.close()

    def salir(self):
        self.reportes.close()
