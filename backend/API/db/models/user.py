from pydantic import BaseModel


class User(BaseModel):
    """Modelo para representar un usuario"""
    id: int
    usuario: str
    password: str
    rol: str
    estado: bool
    id_area: int
