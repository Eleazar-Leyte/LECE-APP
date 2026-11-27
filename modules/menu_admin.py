from PyQt6.QtCore import QObject
from .inicio import MainMenuUI
from modules.Almacenes.almacen import AlmacenController
from modules.A_P_Operativo.personal import Personal
from modules.Produccion.produccion_controler import ProduccionController
from modules.Montaje.montaje_controlador import MontajeController
from modules.reportes.reportes import ReportesController
from modules.ajustes.ajustes import AjustesController
from modules.usuarios.usuarios import UsuariosController
from modules.A_P_Administrativo.personal_admin import PersonalAdminController


class MenuAdmin(QObject):
    def __init__(self, usuario_actual):
        super().__init__()
        self.usuario_actual = usuario_actual
        self.ui = MainMenuUI()
        self.ui.show()

        # Configurar UI con datos del usuario
        self.setup_ui()

        # Conectar señales
        self.ui.btn_logout.clicked.connect(self.logout)
        self.ui.show()

    def setup_ui(self):
        """Configura la interfaz con datos del usuario"""
        # Configurar encabezado
        self.ui.setup_header(
            user_name=self.usuario_actual["name"],
            user_role=self.usuario_actual["rol"],
            user_area=self.usuario_actual["area"]
        )

        # Añadir tarjetas de menú según el rol
        menu_items = self.get_menu_items_by_role()

        for item in menu_items:
            card = self.ui.add_menu_card(
                icon=item["icon"],
                title=item["title"],
                description=item["desc"],
                card_id=item["id"]
            )
            card.clicked.connect(
                lambda _, i=item["id"]: self.handle_menu_click(i))

    def get_area_name(self, area_id):
        """Convierte el ID de área a nombre legible"""
        areas = {
            1: "Administración",
            2: "Producción",
            3: "Almacén",
            4: "Montaje",
            5: "Recursos Humanos"
        }
        return areas.get(area_id, f"Área {area_id}")

    def get_menu_items_by_role(self):
        """Devuelve los ítems de menú según el rol del usuario"""
        base_items = [
            {"id": "personal", "icon": "👷", "title": "Personal",
             "desc": "Gestión del personal operativo", "roles": ["Admin", "Personal Administrativo"]},
            {"id": "personal_admin", "icon": "💼", "title": "Personal Administrativo",
             "desc": "Gestión de oficinas y supervisores", "roles": ["Admin"]},
            {"id": "almacen", "icon": "📦", "title": "Almacén",
             "desc": "Gestión de inventario y materiales", "roles": ["Admin", "Personal Técnico"]},
            {"id": "produccion", "icon": "🏭", "title": "Producción",
             "desc": "Seguimiento de procesos productivos", "roles": ["Admin", "Personal Técnico"]},
            {"id": "montaje", "icon": "🔧", "title": "Montaje",
             "desc": "Gestión de ensamblaje final", "roles": ["Admin", "Personal Técnico"]},
            {"id": "reportes", "icon": "📊", "title": "Reportes",
             "desc": "Generar análisis detallados", "roles": ["Admin", "Personal Administrativo"]},
            {"id": "config", "icon": "⚙️", "title": "Configuración",
             "desc": "Ajustes del sistema", "roles": ["Admin"]},
            {"id": "users", "icon": "👤", "title": "Usuarios",
             "desc": "Ajustes del usuarios", "roles": ["Admin"]}
        ]

        # Filtrar por rol del usuario actual
        return [item for item in base_items
                if self.usuario_actual["rol"] in item["roles"]]

    def handle_menu_click(self, menu_id):
        """Maneja el clic en una tarjeta de menú"""
        self.ui.close()

        if menu_id == "personal":
            self.win = Personal(self.usuario_actual)
        elif menu_id == "personal_admin":
            self.win = PersonalAdminController(self.usuario_actual)
        elif menu_id == "almacen":
            self.win = AlmacenController(self.usuario_actual)
        elif menu_id == "produccion":
            self.win = ProduccionController(self.usuario_actual)
        elif menu_id == "montaje":
            self.win = MontajeController(self.usuario_actual)
        elif menu_id == "reportes":
            self.win = ReportesController(self.usuario_actual)
        elif menu_id == "config":
            self.win = AjustesController(self.usuario_actual)
        elif menu_id == "users":
            self.win = UsuariosController(self.usuario_actual)

    def logout(self):
        """Cierra sesión y vuelve al login"""
        self.ui.close()
