from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .auth import current_user, User
from db.database_Manager import DatabaseManager

router = APIRouter(
    prefix="/personal",
    tags=["personal"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)


class PersonalBase(BaseModel):
    id: Optional[int] = None
    apellido_paterno: str
    apellido_materno: str
    nombre: str
    id_puesto: Optional[int] = None
    expediente_tecnico_cobre: Optional[str] = None
    expediente_tecnico_fo: Optional[str] = None
    id_area: int
    cope: str
    nss: Optional[str] = None
    rfc: Optional[str] = None
    direccion: Optional[str] = None


class PersonalCreate(PersonalBase):
    pass


class PersonalResponse(PersonalBase):
    class Config:
        orm_mode = True


class AreaBase(BaseModel):
    id: int
    nombre: str


class CopeBase(BaseModel):
    cope: str

# Improved error handling for all endpoints


@router.get("/areas", response_model=List[AreaBase])
async def obtener_areas(user: dict = Depends(current_user)):
    """
    Obtener áreas disponibles según el rol del usuario
    """
    db_manager = None
    try:
        db_manager = DatabaseManager('Personal')
        if user.rol != "Admin":
            # Para usuarios no Admin, devolver solo su área
            query = '''
                SELECT id, "Nombre del Área" as nombre 
                FROM areas 
                WHERE id = %s AND "Estado" = TRUE
            '''
            resultados = db_manager.execute_query(query, (user.id_area,))

            if resultados:
                return resultados
            else:
                return [{"id": user.id_area, "nombre": f"Área {user.id_area}"}]
        else:
            # Para Admin: consultar todas las áreas
            query = '''
                SELECT id, "Nombre del Área" as nombre 
                FROM areas 
                WHERE "Estado" = TRUE 
                ORDER BY "Nombre del Área"
            '''
            resultados = db_manager.execute_query(query)
            return resultados

    except HTTPException:
        # Re-lanzar HTTPExceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener áreas: {str(e)}"
        )
    finally:
        # Manejo seguro en el bloque finally :cite[3]:cite[6]
        if db_manager is not None:
            db_manager.close()

# Endpoints para copes por área


@router.get("/areas/{area_id}/copes", response_model=List[CopeBase])
async def obtener_copes_por_area(area_id: int, user: dict = Depends(current_user)):
    """
    Obtener copes disponibles para un área específica
    """
    db_manager_personal = None
    db_manager_areas = None
    try:
        # Primero obtener el nombre del área desde la base de datos Personal
        db_manager_personal = DatabaseManager('Personal')
        query_area = 'SELECT "Nombre del Área" FROM Areas WHERE id = %s'
        area_result = db_manager_personal.execute_query(query_area, (area_id,))

        if not area_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Área no encontrada"
            )

        nombre_area = area_result[0]["Nombre del Área"]

        # Conectar a la base de datos de Áreas para obtener copes
        db_manager_areas = DatabaseManager('Áreas')
        query_copes = f'SELECT DISTINCT "Copé" as cope FROM "{nombre_area}"'
        resultados = db_manager_areas.execute_query(query_copes)

        return resultados if resultados else []

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener copes: {str(e)}"
        )
    finally:
        # Cerrar ambas conexiones de manera segura
        if db_manager_personal is not None:
            db_manager_personal.close()
        if db_manager_areas is not None:
            db_manager_areas.close()

# Endpoints para personal


@router.get("/", response_model=List[PersonalResponse])
async def obtener_personal_por_area_cope(
    area_id: int,
    cope: str,
    user: dict = Depends(current_user)
):
    """Obtener personal filtrado por área y cope"""
    try:
        db_manager = DatabaseManager('Personal')
        query = '''
            SELECT id, "Apellido Paterno" as apellido_paterno, 
                   "Apellido Materno" as apellido_materno, "Nombre (s)" as nombre,
                   "Expediente Técnico Cobre" as expediente_tecnico_cobre,
                   "Expediente Técnico F.O." as expediente_tecnico_fo,
                   id_area, "Cope" as cope, "N.S.S." as nss,
                   "R.F.C." as rfc, "Dirección" as direccion
            FROM personal_o
            WHERE id_area = %s AND "Cope" = %s
        '''
        resultados = db_manager.execute_query(query, (area_id, cope))
        return resultados
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener personal: {str(e)}"
        )
    finally:
        db_manager.close()


@router.post("/", response_model=PersonalResponse)
async def crear_personal(
    personal: PersonalCreate,
    user: dict = Depends(current_user)
):
    """Crear nuevo registro de personal"""
    db_manager = None
    try:
        db_manager = DatabaseManager('Personal')

        # Usar get_cursor para manejo automático de commit
        with db_manager.get_cursor('Personal') as cursor:
            # Primero insertar
            query_insert = '''
                INSERT INTO personal_o 
                ("Apellido Paterno", "Apellido Materno", "Nombre (s)", "id_puesto",
                 "Expediente Técnico Cobre", "Expediente Técnico F.O.", 
                 id_area, "Cope", "N.S.S.", "R.F.C.", "Dirección")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''
            params = (
                personal.apellido_paterno, personal.apellido_materno, personal.nombre, personal.id_puesto,
                personal.expediente_tecnico_cobre, personal.expediente_tecnico_fo,
                personal.id_area, personal.cope, personal.nss, personal.rfc, personal.direccion
            )

            # Ejecutar la inserción
            cursor.execute(query_insert, params)

            # Ahora obtener el último ID insertado
            query_last_id = '''
                SELECT id FROM personal_o 
                WHERE "Apellido Paterno" = %s AND "Apellido Materno" = %s AND "Nombre (s)" = %s
                AND id_area = %s AND "Cope" = %s
                ORDER BY id DESC LIMIT 1
            '''
            params_last_id = (
                personal.apellido_paterno, personal.apellido_materno, personal.nombre,
                personal.id_area, personal.cope
            )

            cursor.execute(query_last_id, params_last_id)
            resultado = cursor.fetchall()
            print(f"Resultado de la consulta del último ID: {resultado}")

            if not resultado or len(resultado) == 0:
                personal.id = None
                print("Advertencia: No se pudo obtener el ID del registro insertado")
            else:
                personal.id = resultado[0]['id']

        return personal

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error completo en crear_personal: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear personal: {str(e)}"
        )
    finally:
        if db_manager is not None:
            db_manager.close()


@router.post("/importar-excel")
async def importar_personal_excel(
    datos: List[PersonalCreate],
    user: dict = Depends(current_user)
):
    """Importar personal desde Excel"""
    db_manager = None
    try:
        db_manager = DatabaseManager('Personal')

        # Usar get_cursor para manejo automático de commit
        with db_manager.get_cursor('Personal') as cursor:
            query = '''
                INSERT INTO personal_o 
                ("Apellido Paterno", "Apellido Materno", "Nombre (s)", "id_puesto",
                 "Expediente Técnico Cobre", "Expediente Técnico F.O.", 
                 id_area, "Cope", "N.S.S.", "R.F.C.", "Dirección")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            '''

            for personal in datos:
                params = (
                    personal.apellido_paterno, personal.apellido_materno, personal.nombre,
                    personal.id_puesto or 1,
                    personal.expediente_tecnico_cobre, personal.expediente_tecnico_fo,
                    personal.id_area, personal.cope, personal.nss, personal.rfc, personal.direccion
                )
                cursor.execute(query, params)

        return {"message": f"{len(datos)} registros importados correctamente"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al importar personal: {str(e)}"
        )
    finally:
        if db_manager is not None:
            db_manager.close()
