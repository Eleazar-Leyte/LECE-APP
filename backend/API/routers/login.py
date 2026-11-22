from fastapi import APIRouter
from pydantic import BaseModel


class User(BaseModel):
    """Modelo para representar un usuario"""
    id: int
    usuario: str
    password: str
    rol: str
    estado: bool
    id_area: int


users_list = [User(id=1, usuario="admin", password="",
              rol="", estado=True, id_area=1)]

login = APIRouter(prefix="/login",
                  tags=["login"],
                  responses={404: {"description": "Not found"}})


@login.get("/users/")
async def get_users(usuario: str):
    return search_user(usuario)


@login.post("/users/")
async def user(user: User):
    """Crear un nuevo usuario"""
    users_list.append(user)
    return user


def search_user(usuario: str):
    """Buscar un usuario por su nombre de usuario"""
    users = filter(lambda user: user.usuario == usuario, users_list)
    try:
        return list(users)[0]
    except:
        return {"error": "Usuario no encontrado"}
