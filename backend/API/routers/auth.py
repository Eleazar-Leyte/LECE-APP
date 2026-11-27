import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
import bcrypt
from db.database_Manager import DatabaseManager

load_dotenv()

ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_DURATION = int(os.getenv("ACCESS_TOKEN_DURATION", 60))
SECRET = os.getenv("SECRET", "clave_secreta_por_defecto")

router = APIRouter(prefix="/login",
                   tags=["login"],
                   responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}})
oauth2 = OAuth2PasswordBearer(tokenUrl="login")

# crypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


def search_user_db(username: str):
    """
    Buscar un usuario por su nombre de usuario
    """
    db_manager = None
    try:
        db_manager = DatabaseManager('Personal')
        query = '''
            SELECT u.*, a."Nombre del Área" 
            FROM usuarios u 
            LEFT JOIN areas a ON u.id_area = a.id 
            WHERE u.usuario = %s AND u.estado = TRUE
        '''
        user_data = db_manager.execute_query(query, (username,))

        if not user_data:
            return None

        return UserDB(
            username=user_data[0]['usuario'],
            name=user_data[0]['nombre'],
            rol=user_data[0]['rol'],
            estado=user_data[0]['estado'],
            id_area=user_data[0]['id_area'],
            password=user_data[0]['contraseña']
        )
    except Exception as e:
        print(f"Error en search_user_db: {str(e)}")
        return None
    finally:
        if db_manager:
            db_manager.close()


def search_user(username: str):
    """
    Buscar un usuario por su nombre de usuario
    """
    user_data = search_user_db(username)
    if not user_data:
        return {"error": "Usuario no encontrado"}

    return User(
        username=user_data.username,
        name=user_data.name,
        rol=user_data.rol,
        estado=user_data.estado,
        id_area=user_data.id_area
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña en texto plano coincide con la contraseña hasheada
    """
    try:
        if not plain_password or not hashed_password:
            return False

        # Asegurarse de que las contraseñas estén en bytes
        return bcrypt.checkpw(
            plain_password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        print(f"Error al verificar la contraseña: {str(e)}")
        return False


def get_area_info(area_id: int):
    """
    Obtener información del área por su ID
    """
    db_manager = None
    try:
        db_manager = DatabaseManager('Personal')
        query = 'SELECT id, "Nombre del Área" as nombre FROM areas WHERE id = %s'
        resultado = db_manager.execute_query(query, (area_id,))
        return resultado[0] if resultado else None
    except Exception as e:
        print(f"Error al obtener información del área: {e}")
        return None
    finally:
        if db_manager:
            db_manager.close()


@router.post("")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint para iniciar sesión con un usuario y contraseña
    """
    username = form.username
    user = search_user_db(username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    password = form.password
    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Contraseña incorrecta"
        )

    # Obtener información detallada del área
    area_info = get_area_info(user.id_area)
    area_name = area_info["nombre"] if area_info else f"Área {user.id_area}"

    # Add token expiration and use consistent field names
    access_token_expires = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_DURATION)

    access_token_payload = {
        "sub": user.username,
        "exp": access_token_expires,
        "name": user.name,
        "rol": user.rol,
        "area_id": user.id_area,
        "area_name": area_name
    }

    return {"access_token": jwt.encode(access_token_payload, SECRET, algorithm=ALGORITHM),
            "token_type": "bearer",
            "user_info": {
                "name": user.name,
                "rol": user.rol,
                "area": user.id_area,
                "area_name": area_name
    }
    }


async def auth_user(token: str = Depends(oauth2)):
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Usuario no encontrado o no autorizado",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, SECRET, algorithms=ALGORITHM)
        username: str = payload.get("sub")
        if username is None:
            raise exception
    except JWTError:
        raise exception

    user = search_user(username)
    if isinstance(user, dict) and "error" in user:
        raise exception
    return user


async def current_user(user: User = Depends(auth_user)):
    """
    Dependencia para obtener el usuario actual a partir del token
    """
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.get("/me")
async def me(user: User = Depends(current_user)):
    return user
