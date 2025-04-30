import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()


class Conexion:
    def __init__(self):
        try:
            # self.con = psycopg2.connect(
            #     host="localhost",
            #     database="Personal",
            #     user="postgres",  # Cambia por tu usuario de PostgreSQL
            #     password="Leyte13579"  # Cambia por tu contraseña de PostgreSQL
            # )
            # Conexión usando variables de entorno con SSL
            self.con = psycopg2.connect(
                dsn=os.getenv('DB_PERSONAL_URL'),  # URL completa desde Railway
                sslmode='require'  # Obligatorio para conexiones seguras
            )
            self.crear_tablas()
        except Exception as ex:
            print(f"Error al conectar a PostgreSQL: {ex}")

    def crear_tablas(self):
        crear_tablas = """
        CREATE TABLE IF NOT EXISTS Usuarios (
            id SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            usuario VARCHAR(50) UNIQUE NOT NULL,
            contraseña VARCHAR(255) NOT NULL,
            rol VARCHAR(20) NOT NULL, -- Ejemplo: 'Admin', 'Supervisor', 'Usuario'
            estado BOOLEAN DEFAULT TRUE, -- Activo o Inactivo
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            cur = self.con.cursor()
            cur.execute(crear_tablas)
            self.con.commit()
            cur.close()
            self.crear_admin()
        except Exception as ex:
            print("Error al crear tablas:", ex)

    def crear_admin(self):
        try:
            cur = self.con.cursor()
            # Inserta el usuario admin si no existe
            query = """
            INSERT INTO Usuarios (nombre, usuario, contraseña, rol)
            SELECT %s, %s, %s, %s
            WHERE NOT EXISTS (
                SELECT 1 FROM Usuarios WHERE usuario = %s
            );
            """
            cur.execute(query, ("Administrador", "admin",
                        "admin123", "Admin", "admin"))
            self.con.commit()
            cur.close()
        except Exception as ex:
            print("Error al crear admin:", ex)

    def conectar(self):
        return self.con
