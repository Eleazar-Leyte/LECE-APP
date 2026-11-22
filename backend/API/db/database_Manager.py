import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from contextlib import contextmanager
from fastapi import HTTPException, status

# Cargar variables del archivo .env
load_dotenv()


class DatabaseManager:
    def __init__(self, db_name: str):
        self.db_name = db_name
        self.connection = None
    # Configuración centralizada de las bases de datos
    _db_configs = {
        'Personal': {
            'dbname': 'Personal',
            'user': "postgres",
            'password': 'Leyte13579',
            'host': 'localhost',
            'port': 5432
        },
        'Áreas': {
            'dbname': 'areas',
            'user': "postgres",
            'password': 'Leyte13579',
            'host': 'localhost',
            'port': 5432
        },
        'Almacen_construcción': {
            'dbname': 'almacen_construccion',
            'user': "postgres",
            'password': 'Leyte13579',
            'host': 'localhost',
            'port': 5432
        },
        'Producción': {
            'dbname': 'produccion',
            'user': "postgres",
            'password': 'Leyte13579',
            'host': 'localhost',
            'port': 5432
        },
    }

    # _db_configs = {
    #     'Personal': {
    #         'dsn': os.getenv('DB_PERSONAL_URL')
    #     },
    #     'Áreas': {
    #         'dsn': os.getenv('DB_AREAS_URL')
    #     },
    #     'Almacen_construcción': {
    #         'dsn': os.getenv('DB_ALMACEN_URL')
    #     },
    #     'Producción': {
    #         'dsn': os.getenv('DB_PRODUCCION_URL')
    #     },
    # }

    def connect(self):
        """Establece la conexión a la base de datos"""
        try:
            if not self.connection or self.connection.closed:
                self.connection = psycopg2.connect(
                    **self._db_configs[self.db_name])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error conectando a {self.db_name}: {e}'
            )

    @contextmanager
    def get_cursor(self, db_name: str):
        """
        Context manager para manejo seguro de conexiones
        """
        try:
            self.connect()
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                yield cursor
            self.connection.commit()
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Database error: {e}'
            )

    def get_user(self, username: str):
        """
        Obtiene un usuario de la base de datos por su nombre de usuario.
        """
        with self.get_cursor('Personal') as cursor:
            cursor.execute(
                "SELECT * FROM usuarios WHERE usuario =%s", (username,)
            )
            return cursor.fetchone()

    def execute_query(self, query, params=(), fetch=True):
        """
        Ejecuta una consulta SQL y devuelve los resultados
        """
        try:
            self.connect()
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params)
                if fetch and query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return results
                elif fetch:
                    return None
        except Exception as e:
            if self.connection:
                self.connection.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'Error ejecutando consulta: {e}'
            )

    def close(self):
        """Cierra la conexión"""
        if self.connection and not self.connection.closed:
            self.connection.close()

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
