import psycopg2
from model.user import Usuario
from conexion import Conexion


class UsuarioData:
    def login(self, usuario: Usuario):
        try:
            # Crear conexión usando la clase Conexion
            self.conexion = Conexion()
            db = self.conexion.conectar()
            cursor = db.cursor()

            # Consulta que incluye la relación con la tabla Areas
            query = """
            SELECT u.id, u.nombre, u.usuario, u.contraseña, u.rol, a."Nombre del Área"
            FROM Usuarios u
            LEFT JOIN Areas a ON u.id_area = a.id
            WHERE u.usuario = %s AND u.contraseña = %s
            """

            # Ejecutar la consulta con parámetros
            cursor.execute(
                query, (usuario._usuario, usuario._contraseña))
            resultado = cursor.fetchone()

            cursor.close()
            db.close()  # Cerramos explícitamente la conexión

            if resultado:
                usuario = Usuario(
                    nombre=resultado[1],
                    usuario=resultado[2],
                    contraseña=resultado[3],
                    rol=resultado[4],
                    area=resultado[5]  # Accedemos por nombre
                )
                return usuario
            else:
                return None

        except Exception as e:
            print(f"Error en login: {e}")
            raise

    def obtener_usuarios(self):
        """Retorna una lista de todos los usuarios registrados."""
        try:
            # Crear conexión usando la clase Conexion
            conexion = Conexion()
            db = conexion.conectar()
            cur = db.cursor()

            # Consulta para obtener todos los usuarios
            query = "SELECT id, nombre, usuario, rol, estado FROM Usuarios;"
            cur.execute(query)
            usuarios = cur.fetchall()
            db.close()
            return usuarios

        except Exception as ex:
            print("Error al obtener usuarios:", ex)
            return []

    def cambiar_estado_usuario(self, usuario_id, nuevo_estado):
        """Habilita o deshabilita a un usuario."""
        try:
            # Crear conexión usando la clase Conexion
            conexion = Conexion()
            db = conexion.conectar()
            cur = db.cursor()

            # Consultamos el estado del usuario
            query = "UPDATE Usuarios SET estado = %s WHERE id = %s;"
            cur.execute(query, (nuevo_estado, usuario_id))
            db.commit()

            cur.close()
            db.close()
            return True

        except Exception as ex:
            print("Error al cambiar estado del usuario:", ex)
            return False

    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos."""
        try:
            conexion = Conexion()
            conexion.conectar().close()
        except Exception as e:
            print("Error al cerrar la conexión:", e)
