from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QComboBox, QDateEdit, QFrame,
                             QGridLayout, QSizePolicy)
from PyQt6.QtGui import QPixmap, QIcon, QFont, QColor
from PyQt6.QtCore import Qt, QSize, QDate
from PyQt6.QtCharts import QChart, QChartView, QBarSeries, QBarSet, QBarCategoryAxis, QValueAxis, QPieSeries, QLineSeries
from PyQt6.QtGui import QPainter


class ReportesUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("Reportes")
        self.setWindowTitle("Dashboard de Reportes")
        self.setWindowIcon(QIcon("assets/icons/report.png"))
        self.resize(1400, 800)

        self.centralwidget = QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setSpacing(15)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        self.setup_header()
        self.setup_filters()
        self.setup_charts()
        self.apply_styles()

    def setup_header(self):
        header_layout = QHBoxLayout()

        self.Logo = QLabel()
        self.Logo.setMaximumSize(80, 70)
        self.Logo.setPixmap(QPixmap("assets/images/Nuevo aspecto.png"))
        self.Logo.setScaledContents(True)
        header_layout.addWidget(self.Logo)

        self.btn_regresar = QPushButton()
        self.btn_regresar.setObjectName("btn_regresar")
        self.btn_regresar.setFixedSize(45, 35)
        self.btn_regresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))
        self.btn_regresar.setIconSize(QSize(20, 20))
        header_layout.addWidget(self.btn_regresar)

        header_layout.addStretch()

        self.Titulo = QLabel("Dashboard de Producción")
        self.Titulo.setFont(QFont("Times New Roman", 26, QFont.Weight.Bold))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.Titulo)

        header_layout.addStretch()

        self.btn_salir = QPushButton()
        self.btn_salir.setObjectName("btn_salir")
        self.btn_salir.setFixedSize(45, 35)
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        self.btn_salir.setIconSize(QSize(20, 20))
        header_layout.addWidget(self.btn_salir)

        self.main_layout.addLayout(header_layout)

    def setup_filters(self):
        filter_frame = QFrame()
        filter_frame.setObjectName("filter_frame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setSpacing(15)

        filter_layout.addWidget(QLabel("Área:"))
        self.str_area = QComboBox()
        self.str_area.setFixedSize(200, 35)
        filter_layout.addWidget(self.str_area)

        filter_layout.addWidget(QLabel("Desde:"))
        self.date_ini = QDateEdit()
        self.date_ini.setCalendarPopup(True)
        self.date_ini.setDate(QDate.currentDate().addMonths(-1))
        self.date_ini.setFixedSize(120, 35)
        filter_layout.addWidget(self.date_ini)

        filter_layout.addWidget(QLabel("Hasta:"))
        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())
        self.date_fin.setFixedSize(120, 35)
        filter_layout.addWidget(self.date_fin)

        self.btn_actualizar = QPushButton(" Generar Reporte")
        self.btn_actualizar.setObjectName("btn_actualizar")
        self.btn_actualizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_actualizar.setIcon(QIcon("assets/icons/sincronizar.svg"))
        self.btn_actualizar.setFixedHeight(35)
        filter_layout.addWidget(self.btn_actualizar)

        filter_layout.addStretch()
        self.main_layout.addWidget(filter_frame)

    def setup_charts(self):
        # Contenedor de Gráficos (Grid)
        grid = QGridLayout()
        grid.setSpacing(15)

        # 1. Gráfico de Barras (Técnicos)
        self.chart_view_tecnicos = QChartView()
        self.chart_view_tecnicos.setRenderHint(
            QPainter.RenderHint.Antialiasing)
        self.chart_view_tecnicos.setMinimumHeight(350)
        grid.addWidget(self.chart_view_tecnicos, 0, 0)

        # 2. Gráfico de Pastel (Tecnologías)
        self.chart_view_tecnologias = QChartView()
        self.chart_view_tecnologias.setRenderHint(
            QPainter.RenderHint.Antialiasing)
        self.chart_view_tecnologias.setMinimumHeight(350)
        grid.addWidget(self.chart_view_tecnologias, 0, 1)

        # 3. Gráfico de Líneas (Tendencia)
        self.chart_view_tendencia = QChartView()
        self.chart_view_tendencia.setRenderHint(
            QPainter.RenderHint.Antialiasing)
        self.chart_view_tendencia.setMinimumHeight(300)
        grid.addWidget(self.chart_view_tendencia, 1,
                       0, 1, 2)  # Ocupa 2 columnas

        self.main_layout.addLayout(grid)

    def apply_styles(self):
        self.centralwidget.setStyleSheet("""
            QWidget#centralwidget {
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 rgba(1, 59, 61, 255), stop:1 rgba(1, 85, 82, 255));
            }
            QLabel#Titulo { color: #EFBFBC; }
            QFrame#filter_frame {
                background-color: rgba(255, 255, 255, 15);
                border-radius: 10px;
                border: 1px solid rgba(255, 255, 255, 40);
                padding: 10px;
            }
            QLabel { color: white; font: 11pt "MS Shell Dlg 2"; }
            QComboBox, QDateEdit {
                background-color: white; color: black; border-radius: 6px; padding: 4px 8px; font: 11pt "MS Shell Dlg 2";
            }
            QPushButton#btn_actualizar {
                background-color: #EFBFBC; color: #013B3D; border-radius: 6px; padding: 6px 15px; font: bold 11pt "MS Shell Dlg 2";
            }
            QPushButton#btn_actualizar:hover { background-color: #E5AFA9; }
            QPushButton#btn_regresar, QPushButton#btn_salir { background-color: rgb(220, 53, 69); border-radius: 8px; border: none; }
            QPushButton#btn_regresar:hover, QPushButton#btn_salir:hover { background-color: rgb(200, 35, 51); }
            
            QChartView {
                background-color: white;
                border-radius: 10px;
            }
        """)
