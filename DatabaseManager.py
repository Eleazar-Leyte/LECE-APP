import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()


class DatabaseManager:
    # Configuración centralizada de las bases de datos
    # _db_configs = {
    #     'Personal': {
    #         'dbname': 'Personal',
    #         'user': "postgres",
    #         'password': 'Leyte13579',
    #         'host': 'localhost',
    #         'port': 5432
    #     },
    #     'Áreas': {
    #         'dbname': 'areas',
    #         'user': "postgres",
    #         'password': 'Leyte13579',
    #         'host': 'localhost',
    #         'port': 5432
    #     },
    #     'Almacen_construcción': {
    #         'dbname': 'almacen_construccion',
    #         'user': "postgres",
    #         'password': 'Leyte13579',
    #         'host': 'localhost',
    #         'port': 5432
    #     },
    #     'Producción': {
    #         'dbname': 'produccion',
    #         'user': "postgres",
    #         'password': 'Leyte13579',
    #         'host': 'localhost',
    #         'port': 5432
    #     },
    # }
    _db_configs = {
        'Personal': {
            'dsn': os.getenv('DB_PERSONAL_URL')
        },
        'Áreas': {
            'dsn': os.getenv('DB_AREAS_URL')
        },
        'Almacen_construcción': {
            'dsn': os.getenv('DB_ALMACEN_URL')
        },
        'Producción': {
            'dsn': os.getenv('DB_PRODUCCION_URL')
        },
    }

    def __init__(self, db_name):
        """
        Inicializa la conexión a la base de datos según el nombre especificado.
        :param db_name: Nombre lógico de la base de datos (clave en _db_configs)
        """
        if db_name not in self._db_configs:
            raise ValueError(
                f"La base de datos '{db_name}' no está configurada.")
        self.db_config = self._db_configs[db_name]
        self.connection = None

    def connect(self):
        """
        Establece la conexión a la base de datos si aún no está conectada.
        """
        if not self.connection:
            try:
                # Conexión con SSL obligatorio
                self.connection = psycopg2.connect(
                    dsn=self.db_config['dsn'],
                    sslmode='require'
                )
                # Metodo para conexion local
                # self.connection = psycopg2.connect(**self.db_config)
            except psycopg2.Error as e:
                print(
                    f"Error de conexión a la base de datos '{self.db_config['dbname']}': {e}")
                raise

    def execute_query(self, query, params=(), fetch=True):
        """
        Ejecuta una consulta SQL y devuelve los resultados si fetch=True.
        :param query: Consulta SQL a ejecutar.
        :param params: Parámetros de la consulta (tupla o lista).
        :param fetch: Si es True, devuelve los resultados de la consulta.
        :return: Resultados de la consulta como lista de diccionarios (si fetch=True).
        """
        try:
            # Asegura que los parámetros son una tupla
            if isinstance(params, list):
                params = tuple(params)

            self.connect()  # Asegura que la conexión está activa
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch:
                    results = cursor.fetchall()  # Solo si se esperan resultados
                    self.connection.commit()
                    return results
                else:
                    self.connection.commit()  # Solo confirma la operación
                    return None
        except psycopg2.Error as e:
            print(f"Database error: {e}")
            if self.connection:
                self.connection.rollback()  # Revertir cambios en caso de error
            raise

    def close(self):
        """
        Cierra la conexión a la base de datos.
        """
        if self.connection:
            self.connection.close()
            self.connection = None

    def is_connected(self):
        """
        Verifica si la conexión a la base de datos está activa.
        """
        return self.connection and not self.connection.closed

    def execute_many(self, query, params_list):
        try:
            self.connect()
            cursor = self.connection.cursor()
            cursor.executemany(query, params_list)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            print(f"Database error: {e}")
            self.connection.rollback()
            raise
