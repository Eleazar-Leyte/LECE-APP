from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

app = FastAPI()

oauth2 = OAuth2PasswordBearer(tokenUrl="login")


class User(BaseModel):
    """Modelo para representar un usuario"""
    username: str
    name: str
    rol: str
    estado: bool
    id_area: int


class UserDB(User):
    """Modelo para representar un usuario con contraseña"""
    password: str


users_db = {
    "Eleyte": {
        "username": "Eleyte",
        "name": "Eleazar Francisco Leyte Zarate",
        "rol": "Admin",
        "estado": True,
        "id_area": 1,
        "password": "12345678"
    },
    "alez": {
        "username": "alez",
        "name": "Alejandro",
        "rol": "User",
        "estado": True,
        "id_area": 2,
        "password": "87654321"
    }
}


def search_user_db(username: str):
    """
    Buscar un usuario por su nombre de usuario
    """

    if username in users_db:
        return UserDB(**users_db[username])
    else:
        return {"error": "Usuario no encontrado"}


def search_user(username: str):
    """
    Buscar un usuario por su nombre de usuario
    """

    if username in users_db:
        return User(**users_db[username])
    else:
        return {"error": "Usuario no encontrado"}


async def current_user(token: str = Depends(oauth2)):
    """
    Dependencia para obtener el usuario actual a partir del token
    """
    user = search_user(token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Usuario no encontrado o no autorizado", headers={"WWW-Authenticate": "Bearer"})

    if user.estado is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Usuario inactivo", headers={"WWW-Authenticate": "Bearer"})

    return user


@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para iniciar sesión con un usuario y contraseña
    """
    user_db = users_db.get(form.username)
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    user = search_user_db(form.username)
    if not form.password == user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña incorrecta")

    return {"access_token": user.username, "token_type": "bearer"}


@app.get("/users/me")
async def me(user: User = Depends(current_user)):
    return user
