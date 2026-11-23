from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QComboBox,
                             QLineEdit, QTextEdit, QFrame, QSpacerItem, QSizePolicy,
                             QScrollArea, QGridLayout, QStackedWidget, QGroupBox,
                             QHeaderView, QTableWidgetItem)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QIcon, QFont


class AlmacenUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Paneles laterales
        self.right_panel = None
        self.right_panel_animation = None
        self.current_panel = None

        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("Almacen")
        self.setWindowTitle("Almacén")
        self.setWindowIcon(QIcon("assets/icons/almacen ngr.svg"))
        self.resize(1200, 700)

        # Widget central
        self.centralwidget = QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        # Layout principal
        self.main_layout = QVBoxLayout(self.centralwidget)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # BARRA SUPERIOR
        self.setup_header()

        # CONTENIDO PRINCIPAL
        self.setup_main_content()

        # PANEL LATERAL DERECHO (inicialmente oculto)
        self.setup_right_panel()

        # Aplicar estilos
        self.apply_styles()

        # Conectar señales
        self.connect_signals()

    def setup_header(self):
        """Configura la barra superior con logo, título y botón salir"""
        horizontalLayout = QHBoxLayout()
        horizontalLayout.setSpacing(10)

        # Logo
        self.Logo = QLabel()
        self.Logo.setMinimumSize(0, 0)
        self.Logo.setMaximumSize(100, 90)
        self.Logo.setPixmap(QPixmap("assets/images/Nuevo aspecto.png"))
        self.Logo.setScaledContents(True)
        horizontalLayout.addWidget(self.Logo)

        # Espaciador central
        horizontalLayout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Título
        self.Titulo = QLabel("Comercializadora LECE Comunicaciones")
        self.Titulo.setFont(QFont("Times New Roman", 28))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        horizontalLayout.addWidget(self.Titulo)

        # Espaciador derecho
        horizontalLayout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Botón salir
        self.btn_salir = QPushButton()
        self.btn_salir.setFixedSize(50, 35)
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.setToolTip("Salir")
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        self.btn_salir.setIconSize(QSize(20, 20))
        horizontalLayout.addWidget(self.btn_salir)

        self.main_layout.addLayout(horizontalLayout)

    def setup_main_content(self):
        """Configura el contenido principal con controles laterales y tabla"""
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(15)

        # PANEL LATERAL IZQUIERDO (Controles)
        self.setup_left_panel()

        # CONTENEDOR CENTRAL (Tabla + Panel derecho)
        self.center_container = QWidget()
        self.center_layout = QHBoxLayout(self.center_container)
        self.center_layout.setSpacing(5)
        self.center_layout.setContentsMargins(0, 0, 0, 0)

        # TABLA CENTRAL
        self.tablaalmacen = QTableWidget()
        self.tablaalmacen.setCursor(Qt.CursorShape.IBeamCursor)
        self.center_layout.addWidget(self.tablaalmacen)

        # PANEL LATERAL DERECHO (Botones de acción)
        self.setup_action_buttons()

        self.content_layout.addWidget(self.center_container)
        self.main_layout.addLayout(self.content_layout)

    def setup_left_panel(self):
        """Configura el panel lateral izquierdo con controles"""
        left_container = QFrame()
        left_container.setFixedWidth(200)
        left_container.setFrameShape(QFrame.Shape.StyledPanel)

        verticalLayout = QVBoxLayout(left_container)
        verticalLayout.setSpacing(30)
        verticalLayout.setContentsMargins(15, 20, 15, 50)

        # Botón regresar
        self.btn_regresar = QPushButton()
        self.btn_regresar.setFixedSize(45, 35)
        self.btn_regresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_regresar.setToolTip("Regresar")
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))
        self.btn_regresar.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_regresar)

        # Espaciador
        verticalLayout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Grupo de Filtros
        filter_group = QGroupBox("Filtros")
        filter_group.setFixedHeight(300)
        filter_layout = QVBoxLayout(filter_group)
        filter_layout.setSpacing(10)

        # Filtro Área
        label_area = QLabel("Área:")
        self.str_area = QComboBox()
        self.str_area.setFixedHeight(28)
        self.str_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.str_area.addItem("Seleccionar")
        self.str_area.addItems(
            ["Área"])
        filter_layout.addWidget(label_area)
        filter_layout.addWidget(self.str_area)

        # Filtro Copé
        label_cope = QLabel("Copé:")
        self.str_cope = QComboBox()
        self.str_cope.setFixedHeight(28)
        self.str_cope.setCursor(Qt.CursorShape.PointingHandCursor)
        self.str_cope.addItem("Seleccionar")
        self.str_cope.addItems(
            ["Centro de Trabajo"])
        filter_layout.addWidget(label_cope)
        filter_layout.addWidget(self.str_cope)

        # Espaciador
        filter_layout.addItem(QSpacerItem(
            30, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Filtro Inventario
        label_inventario = QLabel("Inventario:")
        self.str_tabla = QComboBox()
        self.str_tabla.setFixedHeight(28)
        self.str_tabla.setCursor(Qt.CursorShape.PointingHandCursor)
        self.str_tabla.addItems(["Seleccionar", "Almacén", "ONT", "MODEM"])
        filter_layout.addWidget(label_inventario)
        filter_layout.addWidget(self.str_tabla)

        verticalLayout.addWidget(filter_group)

        # Botón buscar
        self.btn_buscar = QPushButton(" Buscar")
        self.btn_buscar.setFixedHeight(40)
        self.btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buscar.setToolTip("Buscar en inventario")
        self.btn_buscar.setIcon(QIcon("assets/icons/buscar.svg"))
        self.btn_buscar.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_buscar)

        # Espaciador final
        verticalLayout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.content_layout.addWidget(left_container)

    def setup_action_buttons(self):
        """Configura el panel lateral derecho con botones de acción"""
        button_container = QFrame()
        button_container.setFixedWidth(120)
        button_container.setFrameShape(QFrame.Shape.StyledPanel)

        verticalLayout = QVBoxLayout(button_container)
        verticalLayout.setSpacing(8)
        verticalLayout.setContentsMargins(5, 10, 5, 10)

        # Espaciador superior
        verticalLayout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Botón ONT
        self.btn_ont = QPushButton("ONT")
        self.btn_ont.setFixedHeight(35)
        self.btn_ont.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ont.setToolTip("Registrar ONT")
        self.btn_ont.setIcon(QIcon("assets/icons/ONT_1.png"))
        self.btn_ont.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_ont)

        # Botón MODEM
        self.btn_modem = QPushButton("MODEM")
        self.btn_modem.setFixedHeight(35)
        self.btn_modem.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_modem.setToolTip("Registrar MODEM")
        self.btn_modem.setIcon(QIcon("assets/icons/MODEM_1.png"))
        self.btn_modem.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_modem)

        # Botón Almacén
        self.btn_almacen = QPushButton("Almacén")
        self.btn_almacen.setFixedHeight(35)
        self.btn_almacen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_almacen.setToolTip("Ingresar a Almacén")
        self.btn_almacen.setIcon(QIcon("assets/icons/almacen_1.svg"))
        self.btn_almacen.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_almacen)

        # Espaciador
        verticalLayout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed))

        # Botón Catálogo
        self.btn_catalogo = QPushButton("Catálogo")
        self.btn_catalogo.setFixedHeight(35)
        self.btn_catalogo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_catalogo.setToolTip("Abrir catálogo")
        self.btn_catalogo.setIcon(QIcon("assets/icons/catalogo.svg"))
        self.btn_catalogo.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_catalogo)

        # Botón Mover Almacén
        self.btn_movalmacen = QPushButton("Mover")
        self.btn_movalmacen.setFixedHeight(35)
        self.btn_movalmacen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_movalmacen.setToolTip("Mover entre almacenes")
        self.btn_movalmacen.setIcon(QIcon("assets/icons/truck.svg"))
        self.btn_movalmacen.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_movalmacen)

        # Botón Entrega Técnico
        self.btn_almacentecnico = QPushButton("Entrega")
        self.btn_almacentecnico.setFixedHeight(35)
        self.btn_almacentecnico.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_almacentecnico.setToolTip("Entregar a técnico")
        self.btn_almacentecnico.setIcon(QIcon("assets/icons/user-check.svg"))
        self.btn_almacentecnico.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_almacentecnico)

        # Botón Recibir
        self.btn_recibir = QPushButton("Recibir")
        self.btn_recibir.setFixedHeight(35)
        self.btn_recibir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_recibir.setToolTip("Recibir material")
        self.btn_recibir.setIcon(QIcon("assets/icons/truck-loading.png"))
        self.btn_recibir.setIconSize(QSize(20, 20))
        verticalLayout.addWidget(self.btn_recibir)

        # Espaciador final
        verticalLayout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.center_layout.addWidget(button_container)

    def setup_right_panel(self):
        """Configura el panel lateral derecho para formularios auxiliares"""
        self.right_panel = QFrame()
        self.right_panel.setFixedWidth(0)  # Inicialmente oculto
        self.right_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.right_panel.setFrameShadow(QFrame.Shadow.Raised)

        # Layout principal del panel
        panel_layout = QVBoxLayout(self.right_panel)
        panel_layout.setSpacing(10)
        panel_layout.setContentsMargins(15, 15, 15, 15)

        # Header del panel
        panel_header = QHBoxLayout()

        self.panel_title = QLabel("Panel de Control")
        self.panel_title.setFont(
            QFont("Times New Roman", 16, QFont.Weight.Bold))
        self.panel_title.setStyleSheet("color: white;")

        self.btn_close_panel = QPushButton()
        self.btn_close_panel.setFixedSize(30, 30)
        self.btn_close_panel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_close_panel.setToolTip("Cerrar panel")
        self.btn_close_panel.setIcon(QIcon("assets/icons/atras_bc.svg"))
        self.btn_close_panel.setIconSize(QSize(16, 16))

        panel_header.addWidget(self.panel_title)
        panel_header.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        panel_header.addWidget(self.btn_close_panel)

        panel_layout.addLayout(panel_header)

        # Stacked widget para diferentes formularios
        self.stacked_panels = QStackedWidget()
        panel_layout.addWidget(self.stacked_panels)

        # Configurar los diferentes paneles
        self.setup_ont_panel()
        self.setup_modem_panel()
        self.setup_almacen_panel()
        self.setup_catalogo_panel()
        self.setup_movimiento_panel()
        self.setup_entrega_panel()
        self.setup_recibir_panel()

        # Agregar el panel al layout principal
        self.content_layout.addWidget(self.right_panel)

        # Configurar animación
        self.right_panel_animation = QPropertyAnimation(
            self.right_panel, b"minimumWidth")
        self.right_panel_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)
        self.right_panel_animation.setDuration(300)

    def setup_ont_panel(self):
        """
        Configura el panel para registro de ONT con estilos modernos
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Título del panel ONT
        title_layout = QVBoxLayout()

        ont_main_title = QLabel("Comercializadora LECE Comunicaciones")
        ont_main_title.setFont(QFont("Times New Roman", 16, QFont.Weight.Bold))
        ont_main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ont_main_title.setStyleSheet("""
            color: rgba(239, 191, 188, 255);
            padding: 8px;
            background-color: rgba(1, 59, 61, 200);
            border-radius: 8px;
            margin-bottom: 5px;
        """)
        title_layout.addWidget(ont_main_title)

        # Campos del formulario
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(0, 0)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 0)

        # Fila 0: Número de Serie
        ont_label_serie = QLabel("Número de Serie:")
        ont_label_serie.setFixedSize(140, 30)
        ont_label_serie.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.ont_ln_ns = QLineEdit()
        self.ont_ln_ns.setObjectName("ont_ln_ns")
        self.ont_ln_ns.setFixedHeight(35)
        self.ont_ln_ns.setPlaceholderText("Ingresar número de serie")
        self.ont_ln_ns.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.ont_btn_codebar = QPushButton()
        self.ont_btn_codebar.setObjectName("ont_btn_codebar")
        self.ont_btn_codebar.setFixedSize(45, 35)
        self.ont_btn_codebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ont_btn_codebar.setToolTip("Leer código de barras")
        self.ont_btn_codebar.setIcon(QIcon("assets/icons/camara.svg"))
        self.ont_btn_codebar.setIconSize(QSize(18, 18))

        form_layout.addWidget(ont_label_serie, 0, 0)
        form_layout.addWidget(self.ont_ln_ns, 0, 1)
        form_layout.addWidget(self.ont_btn_codebar, 0, 2)

        # Fila 1: Modelo
        ont_label_modelo = QLabel("Modelo:")
        ont_label_modelo.setFixedSize(140, 30)
        ont_label_modelo.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.ont_ln_modelo = QLineEdit()
        self.ont_ln_modelo.setObjectName("ont_ln_modelo")
        self.ont_ln_modelo.setFixedHeight(35)
        self.ont_ln_modelo.setPlaceholderText("Ingresar modelo")
        self.ont_ln_modelo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout.addWidget(ont_label_modelo, 1, 0)
        form_layout.addWidget(self.ont_ln_modelo, 1, 1)

        # Fila 2: Proyecto
        ont_label_proyecto = QLabel("Proyecto:")
        ont_label_proyecto.setObjectName("ont_label_proyecto")
        ont_label_proyecto.setFixedSize(140, 30)
        ont_label_proyecto.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.ont_str_proyecto = QLineEdit()
        self.ont_str_proyecto.setObjectName("ont_str_proyecto")
        self.ont_str_proyecto.setPlaceholderText("Ingresar proyecto")
        self.ont_str_proyecto.setFixedHeight(35)
        self.ont_str_proyecto.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout.addWidget(ont_label_proyecto, 2, 0)
        form_layout.addWidget(self.ont_str_proyecto, 2, 1)

        # Fila 3: Ubicación
        ont_label_ubicacion = QLabel("Ubicación:")
        ont_label_ubicacion.setFixedSize(140, 30)
        ont_label_ubicacion.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.ont_str_ubicacion = QComboBox()
        self.ont_str_ubicacion.setObjectName("ont_str_ubicacion")
        self.ont_str_ubicacion.setFixedHeight(35)
        self.ont_str_ubicacion.addItems(["Almacén", "En campo"])
        self.ont_str_ubicacion.setCursor(Qt.CursorShape.PointingHandCursor)

        self.ont_btn_imagen = QPushButton()
        self.ont_btn_imagen.setObjectName("ont_btn_imagen")
        self.ont_btn_imagen.setFixedSize(45, 35)
        self.ont_btn_imagen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ont_btn_imagen.setToolTip("Cargar imagen")
        self.ont_btn_imagen.setIcon(QIcon("assets/icons/foto.svg"))
        self.ont_btn_imagen.setIconSize(QSize(18, 18))

        form_layout.addWidget(ont_label_ubicacion, 3, 0)
        form_layout.addWidget(self.ont_str_ubicacion, 3, 1)
        form_layout.addWidget(self.ont_btn_imagen, 3, 2)

        # Fila 4: Expediente Técnico
        ont_label_expediente = QLabel("Expediente Técnico:")
        ont_label_expediente.setFixedSize(145, 30)
        ont_label_expediente.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.ont_str_exptec = QComboBox()
        self.ont_str_exptec.setObjectName("ont_str_exptec")
        self.ont_str_exptec.setFixedHeight(35)
        self.ont_str_exptec.setToolTip("Seleccionar expediente técnico")
        self.ont_str_exptec.addItems(
            ["Seleccionar", "Seleccione un Área y COPE"])
        self.ont_str_exptec.setCursor(Qt.CursorShape.PointingHandCursor)

        form_layout.addWidget(ont_label_expediente, 4, 0)
        form_layout.addWidget(self.ont_str_exptec, 4, 1)

        main_layout.addLayout(form_layout)

        # QLabel para imagen - MÁS GRANDE para mejor visualización
        self.ont_label_imagen = QLabel()
        self.ont_label_imagen.setObjectName("ont_label_imagen")
        self.ont_label_imagen.setMinimumHeight(300)  # Más grande
        self.ont_label_imagen.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 20);
                border:2px dashed rgba(255, 255, 255, 60);
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self.ont_label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ont_label_imagen.setText(
            "Vista previa de imagen/etiqueta\n\nHaga clic en el botón de cámara para cargar una imagen")
        self.ont_label_imagen.setWordWrap(True)
        main_layout.addWidget(self.ont_label_imagen)

        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.ont_btn_guardar = QPushButton(" Guardar ONT")
        self.ont_btn_guardar.setObjectName("ont_btn_guardar")
        self.ont_btn_guardar.setFixedSize(140, 40)
        self.ont_btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.ont_btn_guardar.setToolTip("Guardar registro de ONT")
        self.ont_btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.ont_btn_guardar.setIconSize(QSize(18, 18))

        button_layout.addWidget(self.ont_btn_guardar)
        button_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addLayout(button_layout)

        # Espaciador final
        main_layout.addItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_panels.addWidget(widget)

    def setup_modem_panel(self):
        """
        Configura el panel para registro de MODEM reutilizando el código de ONT
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(12, 12, 12, 12)

        # Título del panel MODEM
        title_layout = QVBoxLayout()

        main_layout.addLayout(title_layout)

        # Campos del formulario
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setColumnStretch(0, 0)
        form_layout.setColumnStretch(1, 1)
        form_layout.setColumnStretch(2, 0)

        # Fila 0: Número de Serie
        modem_label_serie = QLabel("Número de Serie:")
        modem_label_serie.setFixedSize(140, 30)
        modem_label_serie.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.modem_ln_ns = QLineEdit()
        self.modem_ln_ns.setObjectName("modem_ln_ns")
        self.modem_ln_ns.setFixedHeight(35)
        self.modem_ln_ns.setPlaceholderText("Ingresar número de serie")
        self.modem_ln_ns.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.modem_btn_codebar = QPushButton()
        self.modem_btn_codebar.setObjectName("modem_btn_codebar")
        self.modem_btn_codebar.setFixedSize(45, 35)
        self.modem_btn_codebar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.modem_btn_codebar.setToolTip("Leer código de barras")
        self.modem_btn_codebar.setIcon(QIcon("assets/icons/camara.svg"))
        self.modem_btn_codebar.setIconSize(QSize(16, 16))

        form_layout.addWidget(modem_label_serie, 0, 0)
        form_layout.addWidget(self.modem_ln_ns, 0, 1)
        form_layout.addWidget(self.modem_btn_codebar, 0, 2)

        # Fila 1: Modelo
        modem_label_modelo = QLabel("Modelo:")
        modem_label_modelo.setFixedSize(140, 30)
        modem_label_modelo.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.modem_ln_modelo = QLineEdit()
        self.modem_ln_modelo.setObjectName("modem_ln_modelo")
        self.modem_ln_modelo.setFixedHeight(35)
        self.modem_ln_modelo.setPlaceholderText("Ingresar modelo")
        self.modem_ln_modelo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout.addWidget(modem_label_modelo, 1, 0)
        form_layout.addWidget(self.modem_ln_modelo, 1, 1)

        # Fila 2: Proyecto
        modem_label_proyecto = QLabel("Proyecto:")
        modem_label_proyecto.setFixedSize(140, 30)
        modem_label_proyecto.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.modem_str_proyecto = QLineEdit()
        self.modem_str_proyecto.setObjectName("modem_str_proyecto")
        self.modem_str_proyecto.setFixedHeight(35)
        self.modem_str_proyecto.setPlaceholderText("Ingresar proyecto")
        self.modem_str_proyecto.setAlignment(Qt.AlignmentFlag.AlignCenter)

        form_layout.addWidget(modem_label_proyecto, 2, 0)
        form_layout.addWidget(self.modem_str_proyecto, 2, 1)

        # Fila 2: Ubicación
        modem_label_ubicacion = QLabel("Ubicación:")
        modem_label_ubicacion.setFixedSize(140, 30)
        modem_label_ubicacion.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.modem_str_ubicacion = QComboBox()
        self.modem_str_ubicacion.setObjectName("modem_str_ubicacion")
        self.modem_str_ubicacion.setFixedHeight(35)
        self.modem_str_ubicacion.addItems(["Almacén", "En campo"])
        self.modem_str_ubicacion.setCursor(Qt.CursorShape.PointingHandCursor)

        self.modem_btn_imagen = QPushButton()
        self.modem_btn_imagen.setObjectName("modem_btn_imagen")
        self.modem_btn_imagen.setFixedSize(45, 35)
        self.modem_btn_imagen.setCursor(Qt.CursorShape.PointingHandCursor)
        self.modem_btn_imagen.setToolTip("Cargar imagen")
        self.modem_btn_imagen.setIcon(QIcon("assets/icons/foto.svg"))
        self.modem_btn_imagen.setIconSize(QSize(16, 16))

        form_layout.addWidget(modem_label_ubicacion, 3, 0)
        form_layout.addWidget(self.modem_str_ubicacion, 3, 1)
        form_layout.addWidget(self.modem_btn_imagen, 3, 2)

        # Fila 3: Expediente Técnico
        modem_label_expediente = QLabel("Expediente Técnico:")
        modem_label_expediente.setFixedSize(145, 30)
        modem_label_expediente.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.modem_str_exptec = QComboBox()
        self.modem_str_exptec.setObjectName("modem_str_exptec")
        self.modem_str_exptec.setFixedHeight(35)
        self.modem_str_exptec.setToolTip("Seleccionar expediente técnico")
        self.modem_str_exptec.addItems(
            ["Seleccionar", "Seleccione un Área y COPE"])
        self.modem_str_exptec.setCursor(Qt.CursorShape.PointingHandCursor)

        form_layout.addWidget(modem_label_expediente, 4, 0)
        form_layout.addWidget(self.modem_str_exptec, 4, 1)

        main_layout.addLayout(form_layout)

        # QLabel para imagen
        self.modem_label_imagen = QLabel()
        self.modem_label_imagen.setObjectName("modem_label_imagen")
        self.modem_label_imagen.setMinimumHeight(250)
        self.modem_label_imagen.setStyleSheet("""
            QLabel {
                background-color: rgba(255, 255, 255, 20);
                border: 2px dashed rgba(255, 255, 255, 60);
                border-radius: 8px;
                padding: 12px;
            }
        """)
        self.modem_label_imagen.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.modem_label_imagen.setText(
            "Vista previa de imagen/etiqueta\n\nHaga clic en el botón de cámara para cargar una imagen")
        self.modem_label_imagen.setWordWrap(True)
        main_layout.addWidget(self.modem_label_imagen)

        # Botones de acción
        button_layout = QHBoxLayout()
        button_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.modem_btn_guardar = QPushButton(" Guardar")
        self.modem_btn_guardar.setObjectName("modem_btn_guardar")
        self.modem_btn_guardar.setFixedSize(130, 36)
        self.modem_btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.modem_btn_guardar.setToolTip("Guardar registro de MODEM")
        self.modem_btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.modem_btn_guardar.setIconSize(QSize(16, 16))

        button_layout.addWidget(self.modem_btn_guardar)
        button_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        main_layout.addLayout(button_layout)

        # Espaciador final
        main_layout.addItem(QSpacerItem(
            20, 5, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_panels.addWidget(widget)

    def setup_almacen_panel(self):
        """
        Configura el panel para registro en almacén
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)

        # Título principal
        title_layout = QVBoxLayout()

        # Subtítulo
        subtitle = QLabel("Entrada en almacén")
        subtitle.setFont(QFont("MS Shell Dlg 2", 12, QFont.Weight.Bold))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: white; margin: 5px;")
        title_layout.addWidget(subtitle)

        main_layout.addLayout(title_layout)

        # Formulario principal
        form_container = QHBoxLayout()
        form_container.setSpacing(20)

        # Columna izquierda - Campos del formulario
        left_form_layout = QVBoxLayout()
        left_form_layout.setSpacing(15)

        # Proyecto
        proyecto_layout = QHBoxLayout()
        proyecto_label = QLabel("Proyecto:")
        proyecto_label.setMinimumSize(130, 30)
        proyecto_label.setMaximumSize(130, 30)
        proyecto_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_str_proyecto = QLineEdit()
        self.almacen_str_proyecto.setObjectName("almacen_str_proyecto")
        self.almacen_str_proyecto.setFixedHeight(35)
        self.almacen_str_proyecto.setPlaceholderText("Ingresar Proyecto")
        self.almacen_str_proyecto.setAlignment(Qt.AlignmentFlag.AlignCenter)

        proyecto_layout.addWidget(proyecto_label)
        proyecto_layout.addWidget(self.almacen_str_proyecto)
        left_form_layout.addLayout(proyecto_layout)

        # Número de Serie
        serie_layout = QHBoxLayout()
        serie_label = QLabel("Número de Serie:")
        serie_label.setMinimumSize(130, 30)
        serie_label.setMaximumSize(130, 30)
        serie_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_ln_ns = QLineEdit()
        self.almacen_ln_ns.setObjectName("almacen_ln_ns")
        self.almacen_ln_ns.setPlaceholderText("Número de Serie")
        self.almacen_ln_ns.setFixedHeight(35)
        self.almacen_ln_ns.setAlignment(Qt.AlignmentFlag.AlignCenter)

        serie_layout.addWidget(serie_label)
        serie_layout.addWidget(self.almacen_ln_ns)
        left_form_layout.addLayout(serie_layout)

        # Código Ax
        codigoax_layout = QHBoxLayout()
        codigoax_label = QLabel("Código Ax:")
        codigoax_label.setMinimumSize(130, 30)
        codigoax_label.setMaximumSize(130, 30)
        codigoax_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_str_codigoax = QComboBox()
        self.almacen_str_codigoax.setObjectName("almacen_str_codigoax")
        self.almacen_str_codigoax.setFixedHeight(35)
        self.almacen_str_codigoax.setCursor(Qt.CursorShape.PointingHandCursor)
        self.almacen_str_codigoax.setToolTip("Seleccionar Código Ax")
        self.almacen_str_codigoax.addItems(
            ["Seleccionar"])

        codigoax_layout.addWidget(codigoax_label)
        codigoax_layout.addWidget(self.almacen_str_codigoax)
        left_form_layout.addLayout(codigoax_layout)

        # Codigo SAP
        codigosap_layout = QHBoxLayout()
        codigosap_label = QLabel("Código SAP:")
        codigosap_label.setMinimumSize(130, 30)
        codigosap_label.setMaximumSize(130, 30)
        codigosap_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_str_codigosap = QLineEdit()
        self.almacen_str_codigosap.setObjectName("almacen_str_codigosap")
        self.almacen_str_codigosap.setFixedHeight(35)
        self.almacen_str_codigosap.setPlaceholderText("Ingresar Código SAP")
        self.almacen_str_codigosap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        codigosap_layout.addWidget(codigosap_label)
        codigosap_layout.addWidget(self.almacen_str_codigosap)
        left_form_layout.addLayout(codigosap_layout)

        # Cantidad
        cantidad_layout = QHBoxLayout()
        cantidad_label = QLabel("Cantidad:")
        cantidad_label.setMinimumSize(130, 30)
        cantidad_label.setMaximumSize(130, 30)
        cantidad_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_ln_cantidad = QLineEdit()
        self.almacen_ln_cantidad.setObjectName("almacen_ln_cantidad")
        self.almacen_ln_cantidad.setFixedHeight(35)
        self.almacen_ln_cantidad.setPlaceholderText("Ingresar Cantidad")
        self.almacen_ln_cantidad.setAlignment(Qt.AlignmentFlag.AlignCenter)

        cantidad_layout.addWidget(cantidad_label)
        cantidad_layout.addWidget(self.almacen_ln_cantidad)
        left_form_layout.addLayout(cantidad_layout)

        # Unidad
        unidad_layout = QHBoxLayout()
        unidad_label = QLabel("Unidad:")
        unidad_label.setMinimumSize(130, 30)
        unidad_label.setMaximumSize(130, 30)
        unidad_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        self.almacen_str_unidad = QComboBox()
        self.almacen_str_unidad.setObjectName("almacen_str_unidad")
        self.almacen_str_unidad.setFixedHeight(35)
        self.almacen_str_unidad.setCursor(Qt.CursorShape.PointingHandCursor)
        self.almacen_str_unidad.setToolTip("Seleccionar Unidad")
        self.almacen_str_unidad.addItems(
            ["Seleccionar", "Pieza(s)", "Metro(s)"])

        unidad_layout.addWidget(unidad_label)
        unidad_layout.addWidget(self.almacen_str_unidad)
        left_form_layout.addLayout(unidad_layout)

        # Descripción
        descripcion_layout = QHBoxLayout()
        descripcion_label = QLabel("Descripción:")
        descripcion_label.setMinimumSize(130, 30)
        descripcion_label.setMaximumSize(130, 30)
        descripcion_label.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        self.almacen_texedit_descripcion = QTextEdit()
        self.almacen_texedit_descripcion.setObjectName(
            "almacen_texedit_descripcion")
        self.almacen_texedit_descripcion.setMaximumHeight(80)
        self.almacen_texedit_descripcion.setPlaceholderText(
            "Descripción del material")

        descripcion_layout.addWidget(descripcion_label)
        descripcion_layout.addWidget(self.almacen_texedit_descripcion)
        left_form_layout.addLayout(descripcion_layout)

        form_container.addLayout(left_form_layout)

        # form_container.addLayout(right_buttons_layout)
        main_layout.addLayout(form_container)

        # Botón guardar (centrado)
        save_layout = QHBoxLayout()
        save_layout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.almacen_btn_guardar = QPushButton(" Guardar")
        self.almacen_btn_guardar.setObjectName("almacen_btn_guardar")
        self.almacen_btn_guardar.setFixedSize(120, 40)
        self.almacen_btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.almacen_btn_guardar.setToolTip("Guardar registro en almacén")
        self.almacen_btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.almacen_btn_guardar.setIconSize(QSize(18, 18))
        save_layout.addWidget(self.almacen_btn_guardar)

        save_layout.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        main_layout.addLayout(save_layout)

        # Espaciador final
        main_layout.addItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_panels.addWidget(widget)

    def setup_catalogo_panel(self):
        """
        Configura el panel para catálogo formulario interactivo, la tabla se renderiza en el panel central
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)

        # Título principal
        subtitle = QLabel("Catálogo de Materiales")
        subtitle.setFont(QFont("MS Shell Dlg 2", 14, QFont.Weight.Bold))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)

        # Controles superiores (búsqueda y botones)
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10)

        # Buscador con Botón
        search_layout = QHBoxLayout()

        self.catalogo_ln_buscar = QLineEdit()
        self.catalogo_ln_buscar.setObjectName("catalogo_ln_buscar")
        self.catalogo_ln_buscar.setFixedHeight(35)
        self.catalogo_ln_buscar.setPlaceholderText(
            "Código AX o Descripción...")

        self.catalogo_btn_buscar = QPushButton()
        self.catalogo_btn_buscar.setObjectName("catalogo_btn_buscar")
        self.catalogo_btn_buscar.setFixedSize(45, 35)
        self.catalogo_btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.catalogo_btn_buscar.setToolTip("Buscar material")
        self.catalogo_btn_buscar.setIcon(QIcon("assets/icons/buscar.svg"))
        self.catalogo_btn_buscar.setIconSize(QSize(18, 18))

        search_layout.addWidget(self.catalogo_ln_buscar)
        search_layout.addWidget(self.catalogo_btn_buscar)
        controls_layout.addLayout(search_layout)

        # Botones
        btn_layout = QHBoxLayout()

        self.catalogo_btn_actualizar = QPushButton(" Actualizar")
        self.catalogo_btn_actualizar.setObjectName("catalogo_btn_actualizar")
        self.catalogo_btn_actualizar.setFixedHeight(35)
        self.catalogo_btn_actualizar.setCursor(
            Qt.CursorShape.PointingHandCursor)
        self.catalogo_btn_actualizar.setIcon(
            QIcon("assets/icons/sincronizar_1.svg"))

        self.catalogo_btn_nuevo = QPushButton(" Nuevo")
        self.catalogo_btn_nuevo.setObjectName("catalogo_btn_nuevo")
        self.catalogo_btn_nuevo.setFixedHeight(35)
        self.catalogo_btn_nuevo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.catalogo_btn_nuevo.setIcon(QIcon("assets/icons/plus.svg"))

        btn_layout.addWidget(self.catalogo_btn_actualizar)
        btn_layout.addWidget(self.catalogo_btn_nuevo)
        controls_layout.addLayout(btn_layout)

        main_layout.addLayout(controls_layout)

        # Formulario de catálogo (inicialmente oculto)
        self.catalogo_form_container = QFrame()
        self.catalogo_form_container.setObjectName(
            "catalogo_form_container")  # <-- ESTA LÍNEA FALTABA
        self.catalogo_form_container.setVisible(False)
        self.catalogo_form_container.setFrameShape(QFrame.Shape.StyledPanel)
        self.catalogo_form_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 30);
                border: 2px solid rgba(255, 255, 255, 80);
                border-radius: 8px;
                padding: 10px;
            }
        """)

        form_layout = QVBoxLayout(self.catalogo_form_container)
        form_layout.setSpacing(15)

        # Campos del formulario
        form_grid = QGridLayout()
        form_grid.setSpacing(10)

        self.catalogo_ln_codigoax = QLineEdit()
        self.catalogo_ln_codigoax.setObjectName("catalogo_ln_codigoax")
        self.catalogo_ln_codigoax.setPlaceholderText("Código AX")
        self.catalogo_ln_codigoax.setFixedHeight(35)
        form_grid.addWidget(QLabel("Código AX:"), 0, 0)
        form_grid.addWidget(self.catalogo_ln_codigoax, 0, 1)

        self.catalogo_tex_descripcion = QTextEdit()
        self.catalogo_tex_descripcion.setObjectName("catalogo_tex_descripcion")
        self.catalogo_tex_descripcion.setMaximumHeight(60)
        self.catalogo_tex_descripcion.setPlaceholderText("Descripción")
        form_grid.addWidget(QLabel("Descripción:"), 1, 0)
        form_grid.addWidget(self.catalogo_tex_descripcion, 1, 1)

        form_layout.addLayout(form_grid)

        # Botones del formulario
        form_buttons_layout = QHBoxLayout()

        self.catalogo_btn_cancelar = QPushButton(" Cancelar")
        self.catalogo_btn_cancelar.setObjectName("catalogo_btn_cancelar")
        self.catalogo_btn_cancelar.setFixedHeight(35)
        self.catalogo_btn_cancelar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.catalogo_btn_cancelar.setIcon(QIcon("assets/icons/cancel.png"))

        self.catalogo_btn_guardar = QPushButton(" Guardar")
        self.catalogo_btn_guardar.setObjectName("catalogo_btn_guardar")
        self.catalogo_btn_guardar.setFixedHeight(35)
        self.catalogo_btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.catalogo_btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))

        form_buttons_layout.addWidget(self.catalogo_btn_cancelar)
        form_buttons_layout.addWidget(self.catalogo_btn_guardar)
        form_layout.addLayout(form_buttons_layout)

        main_layout.addWidget(self.catalogo_form_container)

        # Espaciador final
        main_layout.addItem(QSpacerItem(
            20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.stacked_panels.addWidget(widget)

    def toggle_catalogo_form(self):
        """Muestra u oculta el formulario de catálogo"""
        is_visible = self.catalogo_form_container.isVisible()
        self.catalogo_form_container.setVisible(not is_visible)

        if not is_visible:
            # Limpiar formulario al mostrar
            self.catalogo_ln_codigoax.clear()
            self.catalogo_ln_codigosap.clear()
            self.catalogo_ln_serie.clear()
            self.catalogo_tex_descripcion.clear()
            self.catalogo_btn_nuevo.setText(" Ocultar Formulario")
        else:
            self.catalogo_btn_nuevo.setText(" Nuevo Registro")

    def setup_movimiento_panel(self):
        """Configura el panel para movimiento entre almacenes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Movimiento entre Almacenes")
        title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Formulario de movimiento
        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        lbl_origen = QLabel("Almacén Origen:")
        self.mov_origen = QComboBox()
        form_layout.addWidget(lbl_origen, 0, 0)
        form_layout.addWidget(self.mov_origen, 0, 1)

        lbl_destino = QLabel("Almacén Destino:")
        self.mov_destino = QComboBox()
        form_layout.addWidget(lbl_destino, 1, 0)
        form_layout.addWidget(self.mov_destino, 1, 1)

        layout.addLayout(form_layout)

        # Después de los combos de origen y destino:
        self.mov_ln_serie = QLineEdit()
        self.mov_ln_serie.setPlaceholderText("Número de Serie")
        self.mov_ln_cantidad = QLineEdit()
        self.mov_ln_cantidad.setPlaceholderText("Cantidad")
        self.mov_btn_mover = QPushButton("Mover Material")

        form_layout.addWidget(QLabel("Número de Serie:"), 2, 0)
        form_layout.addWidget(self.mov_ln_serie, 2, 1)
        form_layout.addWidget(QLabel("Cantidad:"), 3, 0)
        form_layout.addWidget(self.mov_ln_cantidad, 3, 1)
        layout.addWidget(self.mov_btn_mover)

        self.stacked_panels.addWidget(widget)

    def setup_entrega_panel(self):
        """
        Configura el panel para entrega a técnicos con diseño mejorado
        """
        widget = QWidget()
        main_layout = QVBoxLayout(widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)

        subtitle = QLabel("Entrega a Personal Operativo")
        subtitle.setFont(QFont("MS Shell Dlg 2", 14, QFont.Weight.Bold))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(subtitle)

        # Técnico
        tecnico_layout = QVBoxLayout()
        tecnico_layout.addWidget(QLabel("Técnico:"))

        self.entrega_str_tecnico = QComboBox()
        self.entrega_str_tecnico.setObjectName(
            "entrega_str_tecnico")  # <-- ASIGNADO
        self.entrega_str_tecnico.setFixedHeight(35)
        self.entrega_str_tecnico.addItem("Seleccionar")
        tecnico_layout.addWidget(self.entrega_str_tecnico)
        main_layout.addLayout(tecnico_layout)

        # Inputs de escaneo
        scan_layout = QGridLayout()
        scan_layout.setSpacing(10)

        scan_layout.addWidget(QLabel("Número de Serie:"), 0, 0)

        self.entrega_ln_serie = QLineEdit()
        self.entrega_ln_serie.setObjectName("entrega_ln_serie")  # <-- ASIGNADO
        self.entrega_ln_serie.setPlaceholderText("Escanear código")
        self.entrega_ln_serie.setFixedHeight(35)
        scan_layout.addWidget(self.entrega_ln_serie, 0, 1)

        scan_layout.addWidget(QLabel("Cantidad:"), 1, 0)

        self.entrega_ln_cantidad = QLineEdit()
        self.entrega_ln_cantidad.setObjectName(
            "entrega_ln_cantidad")  # <-- ASIGNADO
        self.entrega_ln_cantidad.setText("1")
        self.entrega_ln_cantidad.setFixedHeight(35)
        scan_layout.addWidget(self.entrega_ln_cantidad, 1, 1)

        main_layout.addLayout(scan_layout)

        # Botones de gestión
        btn_add_layout = QHBoxLayout()

        self.entrega_btn_agregar_item = QPushButton(" Agregar a la lista")
        self.entrega_btn_agregar_item.setObjectName(
            "entrega_btn_agregar_item")  # <-- ASIGNADO
        self.entrega_btn_agregar_item.setFixedHeight(35)
        self.entrega_btn_agregar_item.setCursor(
            Qt.CursorShape.PointingHandCursor)
        self.entrega_btn_agregar_item.setIcon(QIcon("assets/icons/plus.svg"))

        self.entrega_btn_eliminar = QPushButton(" Quitar")
        self.entrega_btn_eliminar.setObjectName(
            "entrega_btn_eliminar")  # <-- ASIGNADO
        self.entrega_btn_eliminar.setFixedHeight(35)
        self.entrega_btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.entrega_btn_eliminar.setIcon(QIcon("assets/icons/trash.png"))

        btn_add_layout.addWidget(self.entrega_btn_agregar_item)
        btn_add_layout.addWidget(self.entrega_btn_eliminar)
        main_layout.addLayout(btn_add_layout)

        main_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Botones finales
        self.entrega_btn_guardar = QPushButton(" Guardar Entrega")
        self.entrega_btn_guardar.setObjectName(
            "entrega_btn_guardar")  # <-- ASIGNADO
        self.entrega_btn_guardar.setFixedHeight(45)
        self.entrega_btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.entrega_btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        main_layout.addWidget(self.entrega_btn_guardar)

        self.entrega_btn_imprimir = QPushButton(" Imprimir Reporte")
        self.entrega_btn_imprimir.setObjectName(
            "entrega_btn_imprimir")  # <-- ASIGNADO
        self.entrega_btn_imprimir.setFixedHeight(45)
        self.entrega_btn_imprimir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.entrega_btn_imprimir.setIcon(QIcon("assets/icons/imprimir.svg"))
        main_layout.addWidget(self.entrega_btn_imprimir)

        self.stacked_panels.addWidget(widget)

    def apply_entrega_styles(self):
        """Aplica estilos específicos a los componentes del panel de entrega"""
        # Estilo para las tablas de entrega
        table_style = """
            QTableWidget {
                font: 10pt "MS Shell Dlg 2";
                background-color: #3F4847;
                gridline-color: #50736E;
                border: 2px solid #50736E;
                border-radius: 8px;
                color: white;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #50736E;
                color: white;
            }
            QTableWidget::item:alternate {
                background-color: #3F4847;
            }
            QTableWidget::item:selected {
                background-color: #50736E;
                color: white;
            }
            QHeaderView::section {
                background-color: #50736E;
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
                font-size: 11pt;
                border-right: 1px solid #3F4847;
            }
            QTableWidget QScrollBar:vertical {
                background: #3F4847;
                width: 15px;
                margin: 0px;
                border-radius: 5px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background: #50736E;
                border-radius: 5px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background: #5A827A;
            }
            QTableWidget QScrollBar:horizontal {
                background: #3F4847;
                height: 15px;
                margin: 0px;
                border-radius: 5px;
            }
            QTableWidget QScrollBar::handle:horizontal {
                background: #50736E;
                border-radius: 5px;
                min-width: 20px;
            }
            QTableWidget QScrollBar::handle:horizontal:hover {
                background: #5A827A;
            }
            QTableWidget::item:nth-child(even) {
                background-color: #3F4847;
            }
            QTableWidget::item:nth-child(odd) {
                background-color: #50736E;
            }
        """

        self.tabla_entrega.setStyleSheet(table_style)
        self.tabla_reportes.setStyleSheet(table_style)

    def setup_recibir_panel(self):
        """Configura el panel para recibir material"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        title = QLabel("Recibir Material")
        title.setFont(QFont("Times New Roman", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin-bottom: 15px;")
        layout.addWidget(title)

        # Formulario de recepción
        form_layout = QGridLayout()
        form_layout.setSpacing(10)

        self.rec_ln_serie = QLineEdit()
        self.rec_ln_serie.setPlaceholderText("Escanear Número de Serie")
        self.rec_btn_agregar_item = QPushButton("Agregar a la lista")

        lbl_proveedor = QLabel("Proveedor:")
        self.rec_proveedor = QLineEdit()
        form_layout.addWidget(lbl_proveedor, 0, 0)
        form_layout.addWidget(self.rec_proveedor, 0, 1)

        lbl_factura = QLabel("N° Factura:")
        self.rec_factura = QLineEdit()
        form_layout.addWidget(lbl_factura, 1, 0)
        form_layout.addWidget(self.rec_factura, 1, 1)

        layout.addLayout(form_layout)

        self.stacked_panels.addWidget(widget)

    def connect_signals(self):
        """Conecta todas las señales de los botones"""
        # Botones de acción principal
        self.btn_ont.clicked.connect(
            lambda: self.show_panel(0, "Registro de ONT"))
        self.btn_modem.clicked.connect(
            lambda: self.show_panel(1, "Registro de MODEM"))
        self.btn_almacen.clicked.connect(
            lambda: self.show_panel(2, "Registro en Almacén"))
        self.btn_catalogo.clicked.connect(
            lambda: self.show_panel(3, "Catálogo de Materiales"))
        self.btn_movalmacen.clicked.connect(
            lambda: self.show_panel(4, "Movimiento entre Almacenes"))
        self.btn_almacentecnico.clicked.connect(
            lambda: self.show_panel(5, "Entrega a Personal Operativo"))
        self.btn_recibir.clicked.connect(
            lambda: self.show_panel(6, "Recibir Material"))

        # Botón cerrar panel
        self.btn_close_panel.clicked.connect(self.hide_panel)

    def show_panel(self, panel_index, title):
        """Muestra el panel lateral con la sección específica"""
        self.stacked_panels.setCurrentIndex(panel_index)
        self.panel_title.setText(title)
        self.current_panel = panel_index

        # Animación para mostrar el panel
        self.right_panel_animation.setStartValue(self.right_panel.width())
        self.right_panel_animation.setEndValue(450)  # Ancho del panel
        self.right_panel_animation.start()

    def hide_panel(self):
        """Oculta el panel lateral"""
        self.right_panel_animation.setStartValue(self.right_panel.width())
        self.right_panel_animation.setEndValue(0)
        self.right_panel_animation.start()
        self.current_panel = None

    def apply_styles(self):
        """Aplica los estilos CSS modernos a los componentes"""
        try:
            # Estilo principal del widget central
            self.centralwidget.setStyleSheet("""
                QWidget#centralwidget {
                    background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1,
                                              stop:0 rgba(1, 70, 67, 255),
                                              stop:0.5 rgba(1, 85, 82, 255),
                                              stop:1 rgba(1, 100, 97, 255));
                }
            """)

            # Estilo del título principal
            self.Titulo.setStyleSheet("""
                QLabel {
                    font: 28pt "Times New Roman";
                    color: rgba(239, 191, 188, 255);
                    padding: 10px;
                    margin: 5px;
                }
            """)

            # Estilo para botones rojos (salir, regresar, cerrar)
            red_button_style = """
                QPushButton {
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgb(255,0,0);
                    color: white;
                    border-radius: 8px;
                    padding: 8px;
                    border: 2px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                    border: 2px solid #a93226;
                }
                QPushButton:pressed {
                    background-color: #a93226;
                }
            """

            # Aplicar estilos a botones rojos
            self.btn_salir.setStyleSheet(red_button_style)
            self.btn_regresar.setStyleSheet(red_button_style)
            self.btn_close_panel.setStyleSheet(red_button_style)

            # Estilo para botones de acción principales
            action_button_style = """
                QPushButton {
                    font: 11pt "MS Shell Dlg 2";
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(1, 59, 61, 255),
                                              stop:1 rgba(1, 59, 61, 255));
                    color: white;
                    border-radius: 8px;
                    padding: 10px 5px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(52, 73, 94, 255),
                                              stop:1 rgba(44, 62, 80, 255));
                    border: 2px solid rgba(255, 255, 255, 100);
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                              stop:0 rgba(34, 47, 62, 255),
                                              stop:1 rgba(44, 62, 80, 255));
                }
            """

            # Aplicar a botones de acción principales
            # Aplicar a botones de acción principales
            action_buttons = [
                self.btn_buscar, self.btn_ont, self.btn_modem,
                self.btn_almacen, self.btn_catalogo, self.btn_movalmacen,
                self.btn_almacentecnico, self.btn_recibir,
                self.ont_btn_guardar, self.modem_btn_guardar, self.almacen_btn_guardar,
                self.catalogo_btn_guardar, self.catalogo_btn_actualizar, self.catalogo_btn_nuevo,
                self.catalogo_btn_buscar,  # <-- Agregado el nuevo botón de buscar en catálogo
                self.entrega_btn_agregar_item, self.entrega_btn_eliminar,  # <-- Nombres corregidos
                self.entrega_btn_guardar, self.entrega_btn_imprimir
            ]

            for button in action_buttons:
                if button:
                    button.setStyleSheet(action_button_style)

            # Estilo para botones secundarios en el panel ONT
            secondary_button_style = """
                QPushButton {
                    font: 10pt "MS Shell Dlg 2";
                    background-color: rgb(70, 70, 70);
                    color: rgb(255, 255, 255);
                    border-radius: 6px;
                    padding: 6px 5px;
                }
                QPushButton:hover {
                    background-color: rgb(90, 90, 90);
                    border: 1px solid rgba(255, 255, 255, 100);
                }
            """

            # Aplicar a botones secundarios de los paneles
            secondary_buttons = [
                self.ont_btn_codebar, self.ont_btn_imagen,
                self.modem_btn_codebar, self.modem_btn_imagen,
                self.catalogo_btn_cancelar
            ]

            for button in secondary_buttons:
                if button:
                    button.setStyleSheet(secondary_button_style)

            # Estilo para etiquetas
            label_style = """
                QLabel {
                    color: rgb(255, 255, 255);
                    font: 11pt "MS Shell Dlg 2";
                    background: transparent;
                    padding: 3px;
                }
            """

            # Aplicar estilo a todas las etiquetas
            for label in self.centralwidget.findChildren(QLabel):
                if label != self.Titulo and label != self.panel_title:
                    label.setStyleSheet(label_style)

            # Estilo moderno para combobox
            combo_style = """
                QComboBox {
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgb(255, 255, 255);
                    color: rgb(0, 0, 0);
                    border-radius: 6px;
                    padding: 4px 8px;
                    border: 1px solid rgba(255, 255, 255, 80);
                    min-height: 25px;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: px;
                    border-left: 1px solid rgba(0, 0, 0, 50);
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: rgba(1, 59, 61, 200);
                    selection-color: white;
                    border: 1px solid rgba(0, 0, 0, 40);
                    border-radius: 4px;
                    padding: 4px;
                }
                QComboBox:hover {
                    border: 1px solid rgba(255, 255, 255, 120);
                }
            """

            # Aplicar estilo a combobox
            for combo in self.centralwidget.findChildren(QComboBox):
                combo.setStyleSheet(combo_style)

            # Estilo moderno para campos de texto
            line_edit_style = """
                QLineEdit, QTextEdit {
                    font: 10pt "MS Shell Dlg 2";
                    background-color: rgba(255, 255, 255, 250);
                    color: rgb(0, 0, 0);
                    border-radius: 4px;
                    padding: 6px 10px;
                    border: 1px solid rgba(255, 255, 255, 80);
                    selection-background-color: rgba(1, 85, 82, 200);
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 1px solid rgba(239, 191, 188, 180);
                    background-color: rgba(255, 255, 255, 255);
                }
                QLineEdit:hover, QTextEdit:hover {
                    border: 1px solid rgba(255, 255, 255, 120);
                }
            """

            for line_edit in self.centralwidget.findChildren(QLineEdit):
                line_edit.setStyleSheet(line_edit_style)

            for text_edit in self.centralwidget.findChildren(QTextEdit):
                text_edit.setStyleSheet(line_edit_style)

            # Estilo moderno para la tabla principal
            self.tablaalmacen.setStyleSheet("""
                QTableWidget {
                    font: 10pt "MS Shell Dlg 2";
                    color: rgb(1, 59, 61);
                    background-color: white;
                    gridline-color: #d0d0d0;
                    border: 2px solid #cccccc;
                    border-radius: 8px;
                }
                QTableWidget::item {
                    padding: 8px;
                    border-bottom: 1px solid #e0e0e0;
                }
                QTableWidget::item:selected {
                    background-color: rgb(1, 59, 61);
                    color: white;
                }
                QHeaderView::section {
                    background-color: rgb(1, 59, 61);
                    color: white;
                    font-weight: bold;
                    padding: 8px;
                    border: none;
                    font-size: 11pt;
                }
                QTableWidget QScrollBar:vertical {
                    background: rgba(255, 255, 255, 100);
                    width: 15px;
                    margin: 0px;
                    border-radius: 5px;
                }
                QTableWidget QScrollBar::handle:vertical {
                    background: rgba(1, 59, 61, 150);
                    border-radius: 5px;
                    min-height: 20px;
                }
                QTableWidget QScrollBar::handle:vertical:hover {
                    background: rgba(1, 59, 61, 200);
                }
            """)

            # Estilo moderno para el panel lateral derecho
            self.right_panel.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                              stop:0 rgba(1, 59, 61, 255),
                                              stop:0.5 rgba(1, 79, 81, 255),
                                              stop:1 rgba(1, 99, 101, 255));
                    border-radius: 12px;
                    border: 1px solid rgba(255, 255, 255, 60);
                }
            """)

            # Estilo moderno para QGroupBox
            group_box_style = """
                QGroupBox {
                    color: white;
                    font: bold 12pt "MS Shell Dlg 2";
                    background: rgba(255, 255, 255, 30);
                    border: 2px solid rgba(255, 255, 255, 80);
                    border-radius: 8px;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top center;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """

            for group_box in self.centralwidget.findChildren(QGroupBox):
                group_box.setStyleSheet(group_box_style)

        except Exception as e:
            print(f"Error aplicando estilos: {e}")
