from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QPushButton, QTableWidget, QComboBox,
                             QLineEdit, QTextEdit, QFrame, QSpacerItem, QSizePolicy,
                             QScrollArea, QGridLayout)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QPixmap, QIcon, QFont


class PersonalUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Inicializar todos los widgets como None primero
        self.btn_guardar_form = None
        self.btn_cancelar_form = None
        self.ln_apaterno = None
        self.ln_materno = None
        self.ln_nombre = None
        self.ln_expediente_c = None
        self.ln_expediente_fo = None
        self.ln_nss = None
        self.ln_rfc = None
        self.ln_direccion = None
        self.str_area_form = None
        self.str_cope_form = None
        self.form_panel = None

        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("Personal")
        self.setWindowTitle("Personal")
        self.resize(1400, 800)

        # Widget central
        self.centralwidget = QWidget()
        self.centralwidget.setObjectName("centralwidget")
        self.setCentralWidget(self.centralwidget)

        # Layout principal
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setSpacing(10)
        self.verticalLayout.setContentsMargins(10, 10, 10, 10)

        # BARRA SUPERIOR
        self.setup_header()

        # BARRA DE HERRAMIENTAS
        self.setup_toolbar()

        # CONTENIDO PRINCIPAL (Tabla + Formulario + Botones laterales)
        self.setup_main_content()

        # Conectar señales para sincronizar ComboBox
        self.connect_combobox_signals()

        # Aplicar estilos
        self.apply_styles()

    def setup_header(self):
        """Configura la barra superior con logo, título y botón salir"""
        horizontalLayout_2 = QHBoxLayout()
        horizontalLayout_2.setSpacing(10)

        # Logo
        self.Logo = QLabel()
        self.Logo.setMinimumSize(80, 70)
        self.Logo.setMaximumSize(80, 70)
        self.Logo.setPixmap(QPixmap("assets/images/Nuevo aspecto.png"))
        self.Logo.setScaledContents(True)
        horizontalLayout_2.addWidget(self.Logo)

        # Espaciador
        horizontalLayout_2.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Título
        self.Titulo = QLabel("Comercializadora LECE Comunicaciones")
        self.Titulo.setFont(QFont("Times New Roman", 25))
        self.Titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        horizontalLayout_2.addWidget(self.Titulo)

        # Espaciador
        horizontalLayout_2.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Botón salir
        self.btn_salir = QPushButton()
        self.btn_salir.setFixedSize(45, 35)
        self.btn_salir.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salir.setToolTip("Salir")
        self.btn_salir.setIcon(QIcon("assets/icons/salir.svg"))
        self.btn_salir.setIconSize(QSize(20, 20))
        horizontalLayout_2.addWidget(self.btn_salir)

        self.verticalLayout.addLayout(horizontalLayout_2)

    def setup_toolbar(self):
        """Configura la barra de herramientas con botones y filtros"""
        horizontalLayout_5 = QHBoxLayout()
        horizontalLayout_5.setSpacing(15)

        # Botón regresar
        self.btn_regresar = QPushButton()
        self.btn_regresar.setFixedSize(45, 35)
        self.btn_regresar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_regresar.setToolTip("Regresar")
        self.btn_regresar.setIcon(QIcon("assets/icons/atras_bc.svg"))
        self.btn_regresar.setIconSize(QSize(20, 20))
        horizontalLayout_5.addWidget(self.btn_regresar)

        # Espaciador
        horizontalLayout_5.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Botones agregar y eliminar
        self.btn_agregar = QPushButton(" Agregar")
        self.btn_agregar.setFixedSize(120, 35)
        self.btn_agregar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar.setToolTip("Ingresar personal")
        self.btn_agregar.setIcon(QIcon("assets/icons/apersonal.svg"))
        self.btn_agregar.setIconSize(QSize(16, 16))
        horizontalLayout_5.addWidget(self.btn_agregar)

        self.btn_eliminar = QPushButton(" Eliminar")
        self.btn_eliminar.setFixedSize(120, 35)
        self.btn_eliminar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_eliminar.setToolTip("Quitar personal")
        self.btn_eliminar.setIcon(QIcon("assets/icons/qpersonal.svg"))
        self.btn_eliminar.setIconSize(QSize(16, 16))
        horizontalLayout_5.addWidget(self.btn_eliminar)

        # Espaciador
        horizontalLayout_5.addItem(QSpacerItem(
            40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        # Filtros (Área y Cope)
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(10)

        # Área
        label_area = QLabel("Área:")
        label_area.setFixedSize(40, 30)
        filter_layout.addWidget(label_area)

        self.str_area = QComboBox()
        self.str_area.setFixedSize(180, 30)
        self.str_area.setCursor(Qt.CursorShape.PointingHandCursor)
        self.str_area.addItem("Seleccionar")
        # Agregar algunas áreas de ejemplo para demostración
        self.str_area.addItems(
            ["Operaciones", "Técnica", "Administración", "Ventas"])
        filter_layout.addWidget(self.str_area)

        # Cope
        label_cope = QLabel("Cope:")
        label_cope.setFixedSize(40, 30)
        filter_layout.addWidget(label_cope)

        self.str_cope = QComboBox()
        self.str_cope.setFixedSize(180, 30)
        self.str_cope.setCursor(Qt.CursorShape.PointingHandCursor)
        self.str_cope.addItem("Seleccionar")
        # Agregar algunos copes de ejemplo para demostración
        self.str_cope.addItems(
            ["COPE-001", "COPE-002", "COPE-003", "COPE-004"])
        filter_layout.addWidget(self.str_cope)

        # Botón buscar
        self.btn_buscar = QPushButton()
        self.btn_buscar.setFixedSize(50, 30)
        self.btn_buscar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_buscar.setToolTip("Buscar")
        self.btn_buscar.setIcon(QIcon("assets/icons/buscar.svg"))
        self.btn_buscar.setIconSize(QSize(16, 16))
        filter_layout.addWidget(self.btn_buscar)

        horizontalLayout_5.addLayout(filter_layout)

        self.verticalLayout.addLayout(horizontalLayout_5)

    def connect_combobox_signals(self):
        """Conectar señales para sincronizar los ComboBox entre formulario y UI principal"""
        # Cuando se muestre el formulario, sincronizar los ComboBox
        self.btn_agregar.clicked.connect(self.sync_combobox_data)

        # También conectar para sincronizar cuando cambien los datos en los ComboBox principales
        self.str_area.currentTextChanged.connect(self.sync_area_to_form)
        self.str_cope.currentTextChanged.connect(self.sync_cope_to_form)

    def sync_combobox_data(self):
        """Sincroniza los datos de los ComboBox del formulario con los principales"""
        # Sincronizar Área
        current_area = self.str_area.currentText()
        self.str_area_form.clear()
        for i in range(self.str_area.count()):
            self.str_area_form.addItem(self.str_area.itemText(i))
        self.str_area_form.setCurrentText(current_area)

        # Sincronizar Cope
        current_cope = self.str_cope.currentText()
        self.str_cope_form.clear()
        for i in range(self.str_cope.count()):
            self.str_cope_form.addItem(self.str_cope.itemText(i))
        self.str_cope_form.setCurrentText(current_cope)

    def sync_area_to_form(self, text):
        """Sincroniza el área del ComboBox principal al del formulario"""
        if self.str_area_form and text:
            index = self.str_area_form.findText(text)
            if index >= 0:
                self.str_area_form.setCurrentIndex(index)

    def sync_cope_to_form(self, text):
        """Sincroniza el cope del ComboBox principal al del formulario"""
        if self.str_cope_form and text:
            index = self.str_cope_form.findText(text)
            if index >= 0:
                self.str_cope_form.setCurrentIndex(index)

    def setup_main_content(self):
        """Configura el área principal con tabla, formulario y botones laterales"""
        self.main_content_layout = QHBoxLayout()
        self.main_content_layout.setSpacing(10)
        self.main_content_layout.setContentsMargins(0, 0, 0, 0)

        # CONTENEDOR PRINCIPAL (Tabla + Botones laterales)
        self.main_container = QWidget()
        self.main_layout = QHBoxLayout(self.main_container)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # Tabla de personal - OCUPA TODO EL ESPACIO DISPONIBLE
        self.tablapersonal = QTableWidget()
        self.tablapersonal.setFont(QFont("MS Shell Dlg 2", 9))
        self.main_layout.addWidget(self.tablapersonal)

        # PANEL LATERAL DE BOTONES (siempre visible)
        self.setup_sidebar_buttons()

        self.main_content_layout.addWidget(self.main_container)

        # PANEL LATERAL DEL FORMULARIO (inicialmente oculto)
        self.setup_form_panel()

        self.verticalLayout.addLayout(self.main_content_layout)

    def setup_sidebar_buttons(self):
        """Configura los botones laterales derechos"""
        button_container = QFrame()
        button_container.setFixedWidth(120)
        button_container.setFrameShape(QFrame.Shape.StyledPanel)

        vertical_layout = QVBoxLayout(button_container)
        vertical_layout.setSpacing(8)
        vertical_layout.setContentsMargins(5, 10, 5, 10)

        # Botón sincronizar
        self.btn_sincronizar = QPushButton("Sincronizar")
        self.btn_sincronizar.setFixedHeight(35)
        self.btn_sincronizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_sincronizar.setToolTip("Sincronizar datos")
        self.btn_sincronizar.setIcon(
            QIcon("assets/icons/sincronizar.svg"))
        self.btn_sincronizar.setIconSize(QSize(16, 16))
        vertical_layout.addWidget(self.btn_sincronizar)

        # Botón cargar Excel
        self.btn_cargarexcel = QPushButton("Cargar Excel")
        self.btn_cargarexcel.setFixedHeight(35)
        self.btn_cargarexcel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cargarexcel.setToolTip("Cargar Layout desde Excel")
        self.btn_cargarexcel.setIcon(QIcon("assets/icons/cargar.svg"))
        self.btn_cargarexcel.setIconSize(QSize(16, 16))
        vertical_layout.addWidget(self.btn_cargarexcel)

        # Botón descargar Excel
        self.btn_descargarexcel = QPushButton("Descargar Excel")
        self.btn_descargarexcel.setFixedHeight(35)
        self.btn_descargarexcel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_descargarexcel.setToolTip("Descargar en formato Excel")
        self.btn_descargarexcel.setIcon(
            QIcon("assets/icons/descarga.svg"))
        self.btn_descargarexcel.setIconSize(QSize(16, 16))
        vertical_layout.addWidget(self.btn_descargarexcel)

        # Botón guardar
        self.btn_guardar = QPushButton("Guardar")
        self.btn_guardar.setFixedHeight(35)
        self.btn_guardar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar.setToolTip("Guardar cambios")
        self.btn_guardar.setIcon(QIcon("assets/icons/Guardar.svg"))
        self.btn_guardar.setIconSize(QSize(16, 16))
        vertical_layout.addWidget(self.btn_guardar)

        # Botón leyaut
        self.btn_leyaut = QPushButton("Leyaut")
        self.btn_leyaut.setFixedHeight(35)
        self.btn_leyaut.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_leyaut.setToolTip("Descargar Leyaut")
        self.btn_leyaut.setIcon(QIcon("assets/icons/credit-card.svg"))
        self.btn_leyaut.setIconSize(QSize(16, 16))
        vertical_layout.addWidget(self.btn_leyaut)

        # Espacio flexible al final
        vertical_layout.addItem(QSpacerItem(
            20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self.main_layout.addWidget(button_container)

    def setup_form_panel(self):
        """Configura el panel lateral del formulario"""
        # CORRECCIÓN: Asignar directamente a self.form_panel
        self.form_panel = QFrame()
        self.form_panel.setFixedWidth(0)  # Inicialmente oculto (ancho 0)
        self.form_panel.setFrameShape(QFrame.Shape.StyledPanel)
        self.form_panel.setFrameShadow(QFrame.Shadow.Raised)

        # Layout principal del formulario
        form_layout = QVBoxLayout(self.form_panel)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(15, 15, 15, 15)

        # Título del formulario
        self.title_label = QLabel("Alta de Personal Operativo")
        self.title_label.setFont(
            QFont("Times New Roman", 18, QFont.Weight.Bold))
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.title_label)

        # Área desplazable para el formulario
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Widget contenedor del formulario
        form_widget = QWidget()
        form_scroll_layout = QVBoxLayout(form_widget)
        form_scroll_layout.setSpacing(10)

        # Campos del formulario usando GridLayout
        grid_layout = QGridLayout()
        grid_layout.setSpacing(12)
        grid_layout.setColumnStretch(0, 0)
        grid_layout.setColumnStretch(1, 1)

        # Apellido Paterno
        self.label_apaterno = QLabel("Apellido Paterno:")
        self.ln_apaterno = QLineEdit()
        self.ln_apaterno.setPlaceholderText("Ingresar apellido")
        grid_layout.addWidget(self.label_apaterno, 0, 0)
        grid_layout.addWidget(self.ln_apaterno, 0, 1)

        # Apellido Materno
        self.label_amaterno = QLabel("Apellido Materno:")
        self.ln_materno = QLineEdit()
        self.ln_materno.setPlaceholderText("Ingresar apellido")
        grid_layout.addWidget(self.label_amaterno, 1, 0)
        grid_layout.addWidget(self.ln_materno, 1, 1)

        # Nombre(s)
        self.label_nombre = QLabel("Nombre(s):")
        self.ln_nombre = QLineEdit()
        self.ln_nombre.setPlaceholderText("Ingresar nombre")
        grid_layout.addWidget(self.label_nombre, 2, 0)
        grid_layout.addWidget(self.ln_nombre, 2, 1)

        # Expediente Técnico Cobre
        self.label_expediente_c = QLabel("E. Técnico Cobre:")
        self.ln_expediente_c = QLineEdit()
        self.ln_expediente_c.setPlaceholderText("No. de Expediente")
        grid_layout.addWidget(self.label_expediente_c, 3, 0)
        grid_layout.addWidget(self.ln_expediente_c, 3, 1)

        # Expediente Técnico F.O.
        self.label_expediente_fo = QLabel("E. Técnico F.O.:")
        self.ln_expediente_fo = QLineEdit()
        self.ln_expediente_fo.setPlaceholderText("No. de Expediente")
        grid_layout.addWidget(self.label_expediente_fo, 4, 0)
        grid_layout.addWidget(self.ln_expediente_fo, 4, 1)

        # N.S.S.
        self.label_nss = QLabel("N.S.S.:")
        self.ln_nss = QLineEdit()
        self.ln_nss.setPlaceholderText("No. de Seguro Social")
        grid_layout.addWidget(self.label_nss, 5, 0)
        grid_layout.addWidget(self.ln_nss, 5, 1)

        # R.F.C.
        self.label_rfc = QLabel("R.F.C.:")
        self.ln_rfc = QLineEdit()
        self.ln_rfc.setPlaceholderText("Registro Federal")
        grid_layout.addWidget(self.label_rfc, 6, 0)
        grid_layout.addWidget(self.ln_rfc, 6, 1)

        # Área
        self.label_area_form = QLabel("Área:")
        self.str_area_form = QComboBox()
        self.str_area_form.addItem("Seleccionar")
        grid_layout.addWidget(self.label_area_form, 7, 0)
        grid_layout.addWidget(self.str_area_form, 7, 1)

        # Cope
        self.label_cope_form = QLabel("Cope:")
        self.str_cope_form = QComboBox()
        self.str_cope_form.addItem("Seleccionar")
        grid_layout.addWidget(self.label_cope_form, 8, 0)
        grid_layout.addWidget(self.str_cope_form, 8, 1)

        form_scroll_layout.addLayout(grid_layout)

        # Dirección
        self.label_direccion = QLabel("Dirección:")
        self.ln_direccion = QTextEdit()
        self.ln_direccion.setPlaceholderText("Dirección completa")
        self.ln_direccion.setMaximumHeight(80)
        form_scroll_layout.addWidget(self.label_direccion)
        form_scroll_layout.addWidget(self.ln_direccion)

        # Espacio flexible
        form_scroll_layout.addItem(QSpacerItem(
            20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        # Botones del formulario
        button_layout = QHBoxLayout()
        self.btn_guardar_form = QPushButton("Guardar")
        self.btn_guardar_form.setFixedHeight(35)
        self.btn_cancelar_form = QPushButton("Cancelar")
        self.btn_cancelar_form.setFixedHeight(35)

        button_layout.addWidget(self.btn_guardar_form)
        button_layout.addWidget(self.btn_cancelar_form)

        form_scroll_layout.addLayout(button_layout)

        scroll_area.setWidget(form_widget)
        form_layout.addWidget(scroll_area)

        # Agregar el panel del formulario al layout principal
        self.main_content_layout.addWidget(self.form_panel)

    def show_form_panel(self):
        """Muestra el panel del formulario"""
        # Sincronizar ComboBox antes de mostrar
        self.sync_combobox_data()
        self.form_panel.setFixedWidth(450)

    def hide_form_panel(self):
        """Oculta el panel del formulario"""
        self.form_panel.setFixedWidth(0)

    def apply_styles(self):
        """Aplica los estilos CSS a los componentes"""
        try:
            # Estilo del widget central
            self.centralwidget.setStyleSheet("""
                QWidget#centralwidget {
                    background-color: qlineargradient(spread:pad, x1:0.488444, y1:0.392, x2:0.483241, y2:1, 
                                                    stop:0.266917 rgba(1, 59, 61, 255), stop:1 rgba(255, 255, 255, 244));
                }
            """)

            # Estilo del título principal
            self.Titulo.setStyleSheet("""
                font: 25pt "Times New Roman";
                color: rgba(239, 191, 188, 255);
                padding: 5px;
            """)

            # Estilo para el título del formulario - CORREGIDO
            self.title_label.setStyleSheet("""
                        color: rgb(255, 255, 255);
                        font: 18pt "Times New Roman";
                        font-weight: bold;
                        padding: 5px;
                        margin-bottom: 10px;
                        background-color: rgba(1, 59, 61, 180);
                        border-radius: 5px;
                    """)

            # Estilo para botones rojos (salir, regresar, cancelar)
            red_button_style = """
                QPushButton {
                    font: 12pt "MS Shell Dlg 2";
                    background-color: rgb(255, 0, 0);
                    color: rgb(255, 255, 255);
                    border-radius: 8px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: rgb(220, 0, 0);
                }
            """

            # Aplicar estilos a botones principales
            if hasattr(self, 'btn_salir') and self.btn_salir:
                self.btn_salir.setStyleSheet(red_button_style)
            if hasattr(self, 'btn_regresar') and self.btn_regresar:
                self.btn_regresar.setStyleSheet(red_button_style)

            # Estilo para botones azules/verdes (acción principal)
            action_button_style = """
                QPushButton {
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgb(1, 59, 61);
                    color: rgb(255, 255, 255);
                    border-radius: 8px;
                    padding: 8px 5px;
                }
                QPushButton:hover {
                    background-color: rgb(1, 79, 81);
                }
            """

            # Aplicar a botones de acción principales
            action_buttons = [
                'btn_agregar', 'btn_eliminar', 'btn_buscar',
                'btn_sincronizar', 'btn_cargarexcel', 'btn_descargarexcel',
                'btn_guardar', 'btn_leyaut'
            ]

            for btn_name in action_buttons:
                if hasattr(self, btn_name):
                    button = getattr(self, btn_name)
                    if button and button.isWidgetType():
                        button.setStyleSheet(action_button_style)

            # Aplicar estilos a botones del formulario si existen
            if self.btn_guardar_form and self.btn_guardar_form.isWidgetType():
                self.btn_guardar_form.setStyleSheet(action_button_style)

            if self.btn_cancelar_form and self.btn_cancelar_form.isWidgetType():
                self.btn_cancelar_form.setStyleSheet(red_button_style)

            # NUEVO ESTILO MEJORADO para etiquetas del formulario
            form_label_style = """
                QLabel {
                    color: rgb(255, 255, 255);
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgba(1, 59, 61, 160);
                    font-weight: bold;
                    padding: 4px 6px;
                    border-radius: 4px;
                    margin: 2px;
                }
            """

            # Estilo para etiquetas generales (no formulario)
            general_label_style = """
                QLabel {
                    color: rgb(255, 255, 255);
                    font: 11pt "MS Shell Dlg 2";
                    background: transparent;
                }
            """

            # Aplicar estilos específicos a las etiquetas del formulario
            form_labels = [
                'label_apaterno', 'label_amaterno', 'label_nombre',
                'label_expediente_c', 'label_expediente_fo', 'label_nss',
                'label_rfc', 'label_area_form', 'label_cope_form', 'label_direccion'
            ]

            for label_name in form_labels:
                if hasattr(self, label_name):
                    label = getattr(self, label_name)
                    if label and label.isWidgetType():
                        label.setStyleSheet(form_label_style)

            # Aplicar estilos al resto de las etiquetas
            for label in self.centralwidget.findChildren(QLabel):
                if (label != self.Titulo and label.isWidgetType() and
                        not hasattr(label, '_is_form_label')):
                    # Si la etiqueta no es del formulario, usar estilo general
                    if not any(label is getattr(self, ln, None) for ln in form_labels if hasattr(self, ln)):
                        label.setStyleSheet(general_label_style)

            # Estilo para combobox
            combo_style = """
                QComboBox {
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgb(255, 255, 255);
                    color: rgb(0, 0, 0);
                    border-radius: 6px;
                    padding: 3px 8px;
                    border: 1px solid #cccccc;
                }
                QComboBox::drop-down {
                    subcontrol-origin: padding;
                    subcontrol-position: top right;
                    width: 20px;
                    border-left: 1px solid #cccccc;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: black;
                    selection-background-color: rgb(1, 59, 61);
                    selection-color: white;
                }
            """
            for combo in self.centralwidget.findChildren(QComboBox):
                if combo.isWidgetType():
                    combo.setStyleSheet(combo_style)

            # Estilo para campos de texto
            line_edit_style = """
                QLineEdit, QTextEdit {
                    font: 11pt "MS Shell Dlg 2";
                    background-color: rgb(255, 255, 255);
                    color: rgb(0, 0, 0);
                    border-radius: 6px;
                    padding: 5px 8px;
                    border: 1px solid #cccccc;
                }
                QLineEdit:focus, QTextEdit:focus {
                    border: 2px solid rgb(1, 59, 61);
                }
            """
            for line_edit in self.centralwidget.findChildren(QLineEdit):
                if line_edit.isWidgetType():
                    line_edit.setStyleSheet(line_edit_style)

            if self.ln_direccion and self.ln_direccion.isWidgetType():
                self.ln_direccion.setStyleSheet(line_edit_style)

            # Estilo para la tabla
            if hasattr(self, 'tablapersonal') and self.tablapersonal.isWidgetType():
                self.tablapersonal.setStyleSheet("""
                    QTableWidget {
                        font: 9pt "MS Shell Dlg 2";
                        color: rgb(1, 59, 61);
                        background-color: white;
                        gridline-color: #d0d0d0;
                        border: 1px solid #cccccc;
                        border-radius: 6px;
                    }
                    QTableWidget::item {
                        padding: 4px;
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
                        padding: 6px;
                        border: none;
                    }
                """)

            # NUEVO ESTILO MEJORADO para el panel del formulario
            if self.form_panel and self.form_panel.isWidgetType():
                self.form_panel.setStyleSheet("""
                    QFrame {
                        background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, 
                                                    stop:0 rgba(1, 59, 61, 255), 
                                                    stop:0.5 rgba(1, 79, 81, 255),
                                                    stop:1 rgba(1, 99, 101, 255));
                        border-radius: 8px;
                        border: 2px solid rgba(255, 255, 255, 100);
                    }
                """)

            # Estilo para el área de scroll del formulario
            form_scroll_style = """
                QScrollArea {
                    border: none;
                    background: transparent;
                }
                QScrollBar:vertical {
                    background: transparent;
                    width: 12px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    border-radius: 6px;
                    min-height: 20px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
            """
            # Aplicar estilo específico al scroll area del formulario
            if hasattr(self, 'form_panel'):
                scroll_areas = self.form_panel.findChildren(QScrollArea)
                for scroll_area in scroll_areas:
                    if scroll_area.isWidgetType():
                        scroll_area.setStyleSheet(form_scroll_style)

        except Exception as e:
            print(f"Error aplicando estilos: {e}")
