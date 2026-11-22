from fastapi import APIRouter, Depends, HTTPException, status, Security
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import List

from db.models.user import User
from db.database_Manager import DatabaseManager

router = APIRouter(prefix="/users",
                   tags=["users"],
                   responses={status.HTTP_404_NOT_FOUND: {
                       "message": "No encontrado"}}
                   )
db_manager = DatabaseManager('Personal')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# Obtener todos los usuarios
def get_all_users():
    query = "SELECT * FROM usuarios"
    return db_manager.execute_query(query)


# Obtener usuario por username
def get_user_by_username(username: str):
    return db_manager.get_user(username)


# Crear usuario
@router.post("/", response_model=User)
async def create_user(user: User):
    query = """
        INSERT INTO usuarios (usuario, password, rol, estado, id_area)
        VALUES (%s, %s, %s, %s, %s) RETURNING *
    """
    params = (user.usuario, user.password, user.rol, user.estado, user.id_area)
    result = db_manager.execute_query(query, params)
    if not result:
        raise HTTPException(
            status_code=400, detail="No se pudo crear el usuario")
    return result[0]


# Listar todos los usuarios
@router.get("/", response_model=List[User])
async def list_users():
    users = get_all_users()
    return users


# Obtener usuario por nombre de usuario
@router.get("/{username}", response_model=User)
async def get_user(username: str):
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user


# Actualizar usuario
@router.put("/{username}", response_model=User)
async def update_user(username: str, user: User):
    query = """
        UPDATE usuarios SET password=%s, rol=%s, estado=%s, id_area=%s WHERE usuario=%s RETURNING *
    """
    params = (user.password, user.rol, user.estado, user.id_area, username)
    result = db_manager.execute_query(query, params)
    if not result:
        raise HTTPException(
            status_code=404, detail="Usuario no encontrado para actualizar")
    return result[0]


# Eliminar usuario
@router.delete("/{username}")
async def delete_user(username: str):
    query = "DELETE FROM usuarios WHERE usuario=%s RETURNING *"
    params = (username,)
    result = db_manager.execute_query(query, params)
    if not result:
        raise HTTPException(
            status_code=404, detail="Usuario no encontrado para eliminar")
    return {"detail": "Usuario eliminado"}


# Endpoint protegido para obtener el usuario actual
@router.get("/me", response_model=User)
async def get_me(token: str = Security(oauth2_scheme)):
    try:
        payload = jwt.decode(
            token, "3923c28b3ade829521125680bf68e946e763db30f9126471f1076874757a2381", algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return user
