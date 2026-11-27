import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from passlib.context import CryptContext

from .auth import current_user
from db.database_Manager import DatabaseManager

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


class UserCreate(BaseModel):
    nombre: str
    usuario: str
    password: str
    rol: str
    id_area: Optional[int] = None
    id_personal_admin: Optional[int] = None
    id_personal_operativo: Optional[int] = None


class ResetPasswordRequest(BaseModel):
    nueva_password: str


@router.get("/")
async def listar_usuarios(user: dict = Depends(current_user)):
    """Lista todos los usuarios registrados."""
    db = None
    try:
        db = DatabaseManager('Personal')
        query = """
            SELECT u.id, u.nombre, u.usuario, u.rol, u.estado, a."Nombre del Área" as area
            FROM usuarios u
            LEFT JOIN areas a ON u.id_area = a.id
            ORDER BY u.nombre
        """
        return db.execute_query(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


@router.get("/personal_disponible")
async def personal_sin_cuenta(user: dict = Depends(current_user)):
    """Obtiene el personal que aún no tiene un usuario asignado."""
    db = None
    try:
        db = DatabaseManager('Personal')

        # Buscar personal administrativo sin cuenta
        q_admin = """
            SELECT id, "Nombre (s)" as nombre, "Apellido Paterno" as apellido, 'Admin/Directivo' as tipo, id_area
            FROM personal_admin
            WHERE id NOT IN (SELECT id_personal_admin FROM usuarios WHERE id_personal_admin IS NOT NULL)
        """
        admins = db.execute_query(q_admin)

        # Buscar personal operativo sin cuenta
        q_op = """
            SELECT id, "Nombre (s)" as nombre, "Apellido Paterno" as apellido, 'Operativo' as tipo, id_area
            FROM personal_o
            WHERE id NOT IN (SELECT id_personal_operativo FROM usuarios WHERE id_personal_operativo IS NOT NULL)
        """
        operativos = db.execute_query(q_op)

        return {"admins": admins, "operativos": operativos}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


@router.post("/", status_code=201)
async def crear_usuario(usr: UserCreate, user: dict = Depends(current_user)):
    """Crea un nuevo usuario en el sistema."""
    db = None
    try:
        db = DatabaseManager('Personal')

        # Verificar que el nombre de usuario no exista
        check = db.execute_query(
            "SELECT id FROM usuarios WHERE usuario = %s", (usr.usuario,))
        if check:
            raise HTTPException(
                status_code=400, detail="El nombre de usuario ya está registrado.")

        # --- NUEVO MÉTODO DE ENCRIPTACIÓN ---
        password_bytes = usr.password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        # ------------------------------------

        query = """
            INSERT INTO usuarios (nombre, usuario, "contraseña", rol, id_personal_admin, id_personal_operativo, id_area)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (usr.nombre, usr.usuario, hashed_pw, usr.rol,
                  usr.id_personal_admin, usr.id_personal_operativo, usr.id_area)

        with db.get_cursor('Personal') as cursor:
            cursor.execute(query, params)

        return {"message": "Usuario creado exitosamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


@router.put("/{id_usuario}/reset-password")
async def resetear_password(id_usuario: int, req: ResetPasswordRequest, user: dict = Depends(current_user)):
    """Permite al administrador resetear la contraseña de un usuario."""
    db = None
    try:
        db = DatabaseManager('Personal')

        # --- NUEVO MÉTODO DE ENCRIPTACIÓN ---
        password_bytes = req.nueva_password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_pw = bcrypt.hashpw(password_bytes, salt).decode('utf-8')
        # ------------------------------------

        with db.get_cursor('Personal') as cursor:
            cursor.execute(
                'UPDATE usuarios SET "contraseña" = %s WHERE id = %s', (hashed_pw, id_usuario))

        return {"message": "Contraseña actualizada correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


@router.put("/{id_usuario}/toggle-status")
async def cambiar_estado(id_usuario: int, user: dict = Depends(current_user)):
    """Activa o desactiva el acceso de un usuario."""
    db = None
    try:
        db = DatabaseManager('Personal')
        with db.get_cursor('Personal') as cursor:
            cursor.execute(
                "UPDATE usuarios SET estado = NOT estado WHERE id = %s", (id_usuario,))
        return {"message": "Estado del usuario modificado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()
