from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import psycopg2
from psycopg2 import sql

from .auth import current_user
from db.database_Manager import DatabaseManager

router = APIRouter(
    prefix="/produccion",
    tags=["produccion"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)


class RegistroProduccion(BaseModel):
    tipo_produccion: str
    exp_tecnico: str       # <-- MOVIDO AQUÍ
    tecnico_id: Optional[int] = None  # <-- MOVIDO AQUÍ
    folio_pisa: str
    telefono: str
    tipo_tarea: str
    cantidad_mts: str
    numero_serie: str
    modelo: str
    fecha_posteo: str


class ProduccionCreate(BaseModel):
    area: str
    cope: str
    registros: List[RegistroProduccion]


def obtener_imagen_almacen(db_almacen: DatabaseManager, numero_serie: str, tipo_produccion: str) -> bytes:
    """Busca la imagen del equipo ÚNICAMENTE en las tablas de campo."""
    if not numero_serie:
        return b""

    tablas_a_buscar = []
    if tipo_produccion in ["fibra_optica", "quejas"]:
        tablas_a_buscar = ['"ONT en Campo"']
    elif tipo_produccion in ["cobre", "a4_incentivos"]:
        tablas_a_buscar = ['modem_en_campo']

    for tabla in tablas_a_buscar:
        try:
            query = f'SELECT imagen FROM {tabla} WHERE "Numero de Serie" = %s LIMIT 1'
            resultado = db_almacen.execute_query(query, (numero_serie,))
            if resultado and resultado[0]["imagen"]:
                return bytes(resultado[0]["imagen"])
        except Exception:
            continue
    return b""  # Retorna bytes vacíos si no encuentra imagen


@router.post("/guardar", status_code=status.HTTP_201_CREATED)
async def guardar_produccion(payload: ProduccionCreate, user: dict = Depends(current_user)):
    """
    Guarda la producción enviada por el técnico en las tablas correspondientes.
    """
    if not payload.registros:
        raise HTTPException(
            status_code=400, detail="No hay registros para guardar")

    db_produccion = None
    db_almacen = None
    try:
        db_produccion = DatabaseManager('Producción')
        db_almacen = DatabaseManager('Almacen_construcción')

        registros_guardados = 0
        errores = []

        for reg in payload.registros:
            # Validar tipo de producción
            if reg.tipo_produccion not in ["fibra_optica", "cobre", "quejas", "a4_incentivos"]:
                errores.append(
                    f"Tipo de producción inválido: {reg.tipo_produccion}")
                continue

            # Formatear fecha (de dd/MM/yyyy a datetime)
            try:
                fecha_dt = datetime.strptime(reg.fecha_posteo, "%d/%m/%Y")
            except ValueError:
                errores.append(
                    f"Fecha inválida en folio {reg.folio_pisa}: {reg.fecha_posteo}")
                continue

            # Obtener imagen (si aplica)
            imagen_bytes = obtener_imagen_almacen(
                db_almacen, reg.numero_serie, reg.tipo_produccion)

            # Configurar columnas
            col_modelo = "modelo"
            if reg.tipo_produccion == "fibra_optica":
                col_modelo = "modelo_ont"
            elif reg.tipo_produccion in ["cobre", "a4_incentivos"]:
                col_modelo = "modelo_modem"

            columnas = [
                "folio_pisa", "telefono_asignado", "tipo_tarea",
                "cantidad_mts", "numero_serie", col_modelo,
                "imagen", "exp_tecnico", "area", "cope", "fecha_posteo"
            ]

            valores = [
                reg.folio_pisa, reg.telefono, reg.tipo_tarea,
                reg.cantidad_mts, reg.numero_serie if reg.numero_serie else None,
                reg.modelo if reg.modelo else None,
                imagen_bytes, reg.exp_tecnico, payload.area,  # <-- USAMOS reg.exp_tecnico
                payload.cope, fecha_dt
            ]

            query = sql.SQL("INSERT INTO {table} ({fields}) VALUES ({values})").format(
                table=sql.Identifier(reg.tipo_produccion),
                fields=sql.SQL(', ').join(map(sql.Identifier, columnas)),
                values=sql.SQL(', ').join(sql.Placeholder() * len(valores))
            )

            # Ejecutar Inserción
            try:
                with db_produccion.get_cursor('Producción') as cursor:
                    cursor.execute(query, tuple(valores))
                registros_guardados += 1
            except Exception as e:
                errores.append(
                    f"Error en folio {reg.folio_pisa} ({reg.tipo_produccion}): {str(e)}")

        if errores:
            # Si hubo errores pero también éxitos, informamos
            raise HTTPException(
                status_code=status.HTTP_207_MULTI_STATUS,
                detail={
                    "message": f"Se guardaron {registros_guardados} registros, pero ocurrieron errores.", "errores": errores}
            )

        return {"message": f"{registros_guardados} registros guardados exitosamente."}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar producción: {str(e)}"
        )
    finally:
        if db_produccion:
            db_produccion.close()
        if db_almacen:
            db_almacen.close()


# =============================================================================
# ENDPOINTS PARA EQUIPOS EN CAMPO (Custodia de Técnicos)
# =============================================================================

@router.get("/campo/ont/{numero_serie}")
async def obtener_ont_campo(numero_serie: str, user: dict = Depends(current_user)):
    """Obtiene un equipo ONT que está en custodia de un técnico."""
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM "ONT en Campo" WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados:
            raise HTTPException(
                status_code=404, detail="ONT no encontrado en campo")

        row = resultados[0]
        return {
            "numero_serie": row["Numero de Serie"],
            "modelo": row["modelo"],
            "area": row["area"],
            "centro_trabajo": row["Centro de Trabajo"],
            "expediente_tecnico": row["Expediente Técnico"],
            "imagen": "Si" if row["imagen"] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/campo/ont/{numero_serie}/imagen")
async def obtener_imagen_ont_campo(numero_serie: str, user: dict = Depends(current_user)):
    """Obtiene la imagen de un ONT en campo."""
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT imagen FROM "ONT en Campo" WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados or not resultados[0]["imagen"]:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
        return Response(content=bytes(resultados[0]["imagen"]), media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/campo/modem/{numero_serie}")
async def obtener_modem_campo(numero_serie: str, user: dict = Depends(current_user)):
    """Obtiene un equipo MODEM que está en custodia de un técnico."""
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM modem_en_campo WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados:
            raise HTTPException(
                status_code=404, detail="MODEM no encontrado en campo")

        row = resultados[0]
        return {
            "numero_serie": row["Numero de Serie"],
            "modelo": row["modelo"],
            "area": row["area"],
            "centro_trabajo": row["Centro de Trabajo"],
            "expediente_tecnico": row["Expediente Técnico"],
            "imagen": "Si" if row["imagen"] else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/campo/modem/{numero_serie}/imagen")
async def obtener_imagen_modem_campo(numero_serie: str, user: dict = Depends(current_user)):
    """Obtiene la imagen de un MODEM en campo."""
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT imagen FROM modem_en_campo WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados or not resultados[0]["imagen"]:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
        return Response(content=bytes(resultados[0]["imagen"]), media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()
