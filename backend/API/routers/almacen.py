
import base64
import os
import uuid
from fastapi.responses import Response, FileResponse
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from pydantic import BaseModel
from typing import List, Optional
from .auth import current_user
from db.database_Manager import DatabaseManager
from fastapi.responses import Response

router = APIRouter(
    prefix="/almacen",
    tags=["almacen"],
    responses={status.HTTP_404_NOT_FOUND: {"description": "Not found"}}
)


class AreaBase(BaseModel):
    id: int
    nombre: str


class CopeBase(BaseModel):
    cope: str


@router.get("/areas", response_model=List[AreaBase])
async def obtener_areas_almacen(user: dict = Depends(current_user)):
    """
    Obtener áreas disponibles para almacén
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

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener áreas: {str(e)}"
        )
    finally:
        if db_manager is not None:
            db_manager.close()


@router.get("/areas/{area_id}/copes", response_model=List[CopeBase])
async def obtener_copes_almacen(area_id: int, user: dict = Depends(current_user)):
    """
    Obtener copes disponibles para un área en almacén
    """
    db_manager_personal = None
    db_manager_areas = None
    try:
        # Primero obtener el nombre del área
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
        if db_manager_personal is not None:
            db_manager_personal.close()
        if db_manager_areas is not None:
            db_manager_areas.close()


class ONTBase(BaseModel):
    numero_serie: str
    cantidad: int
    unidad: str
    modelo: str
    area: str
    centro_trabajo: str
    ubicacion: str
    imagen: Optional[str] = None   # ← str base64


class ONTCreate(ONTBase):
    pass


class ONTResponse(ONTBase):
    fecha_registro: Optional[str] = None

    class Config:
        from_attributes = True


class MODEMBase(BaseModel):
    numero_serie: str
    cantidad: int
    unidad: str
    modelo: str
    area: str
    centro_trabajo: str
    ubicacion: str
    imagen: Optional[str] = None


class MODEMCreate(MODEMBase):
    pass


class MODEMResponse(MODEMBase):
    fecha_registro: Optional[str] = None

    class Config:
        from_attributes = True


class AlmacenBase(BaseModel):
    cantidad: int
    unidad: str
    descripcion: str
    numero_serie: Optional[str] = None
    area: str
    cope: str
    codigo_ax: Optional[str] = None
    codigo_catalogo: Optional[str] = None
    proyecto: Optional[str] = None


class AlmacenCreate(AlmacenBase):
    pass


class AlmacenResponse(AlmacenBase):
    id: int
    fecha_registro: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("/ont", response_model=List[ONTResponse])
async def listar_ont(
    area: Optional[str] = None,
    cope: Optional[str] = None,
    user: dict = Depends(current_user)
):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM ont'
        params = []
        condiciones = []
        if area:
            condiciones.append('area = %s')
            params.append(area)
        if cope:
            condiciones.append('"Centro de Trabajo" = %s')
            params.append(cope)
        if condiciones:
            query += ' WHERE ' + ' AND '.join(condiciones)
        query += ' ORDER BY "Fecha de Registro" DESC'
        resultados = db_manager.execute_query(
            query, tuple(params) if params else ())

        # Mapear resultados a los nombres de campo del modelo
        ont_list = []
        for row in resultados:
            imagen_b64 = None
            if row["imagen"]:
                try:
                    imagen_bytes = bytes(row["imagen"])
                    imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
                except Exception:
                    imagen_b64 = None  # Si hay error al codificar, dejamos como None
            ont_list.append({
                "numero_serie": row["Numero de Serie"],
                "cantidad": row["cantidad"],
                "unidad": row["unidad"],
                "modelo": row["modelo"],
                "area": row["area"],
                "centro_trabajo": row["Centro de Trabajo"],
                "ubicacion": row["ubicacion"],
                # No enviamos la imagen en listados para evitar tamaño
                "imagen": "Si" if row["imagen"] else None,
                "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
            })
        return ont_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al listar ONT: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()

# Endpoint para obtener la imagen de una ONT específica


@router.get("/ont/{numero_serie}/imagen")
async def obtener_imagen_ont(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT imagen FROM ont WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados or not resultados[0]["imagen"]:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
        imagen_bytes = bytes(resultados[0]["imagen"])
        return Response(content=imagen_bytes, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener imagen: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/ont/{numero_serie}", response_model=ONTResponse)
async def obtener_ont(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM ont WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados:
            raise HTTPException(status_code=404, detail="ONT no encontrado")
        return resultados[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener ONT: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.post("/ont", response_model=ONTResponse, status_code=201)
async def crear_ont(ont: ONTCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        # Verificar duplicado
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM ont WHERE "Numero de Serie" = %s',
            (ont.numero_serie,)
        )
        if check:
            raise HTTPException(
                status_code=400, detail="Ya existe un ONT con ese número de serie")

        # Convertir imagen base64 a bytes
        imagen_bytes = None
        if ont.imagen:
            if 'base64,' in ont.imagen:
                imagen_bytes = base64.b64decode(ont.imagen.split('base64,')[1])
            else:
                imagen_bytes = base64.b64decode(ont.imagen)

        query = '''
            INSERT INTO ont ("Numero de Serie", cantidad, unidad, modelo, area, "Centro de Trabajo", ubicacion, imagen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = (
            ont.numero_serie, ont.cantidad, ont.unidad, ont.modelo,
            ont.area, ont.centro_trabajo, ont.ubicacion, imagen_bytes
        )
        # Usar get_cursor para asegurar commit
        with db_manager.get_cursor('Almacen_construcción') as cursor:
            cursor.execute(query, params)

        # Recuperar el registro insertado y mapear
        nuevo = db_manager.execute_query(
            'SELECT * FROM ont WHERE "Numero de Serie" = %s',
            (ont.numero_serie,)
        )
        row = nuevo[0]
        imagen_b64 = None
        if row["imagen"]:
            imagen_b64 = base64.b64encode(bytes(row["imagen"])).decode('utf-8')
        return {
            "numero_serie": row["Numero de Serie"],
            "cantidad": row["cantidad"],
            "unidad": row["unidad"],
            "modelo": row["modelo"],
            "area": row["area"],
            "centro_trabajo": row["Centro de Trabajo"],
            "ubicacion": row["ubicacion"],
            "imagen": imagen_b64,
            "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al crear ONT: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.put("/ont/{numero_serie}", response_model=ONTResponse)
async def actualizar_ont(numero_serie: str, ont: ONTCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        # Verificar existencia
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM ont WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="ONT no encontrado")

        query = '''
            UPDATE ont SET cantidad = %s, unidad = %s, modelo = %s, area = %s,
                "Centro de Trabajo" = %s, ubicacion = %s, imagen = %s
            WHERE "Numero de Serie" = %s
        '''
        params = (
            ont.cantidad, ont.unidad, ont.modelo, ont.area,
            ont.centro_trabajo, ont.ubicacion, ont.imagen, numero_serie
        )
        db_manager.execute_query(query, params, fetch=False)
        # Recuperar actualizado
        actualizado = db_manager.execute_query(
            'SELECT * FROM ont WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        return actualizado[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar ONT: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.delete("/ont/{numero_serie}")
async def eliminar_ont(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM ont WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="ONT no encontrado")
        db_manager.execute_query(
            'DELETE FROM ont WHERE "Numero de Serie" = %s',
            (numero_serie,),
            fetch=False
        )
        return {"message": "ONT eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar ONT: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/modem", response_model=List[MODEMResponse])
async def listar_modem(
    area: Optional[str] = None,
    cope: Optional[str] = None,
    user: dict = Depends(current_user)
):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM modem'
        params = []
        condiciones = []
        if area:
            condiciones.append('area = %s')
            params.append(area)
        if cope:
            condiciones.append('"Centro de Trabajo" = %s')
            params.append(cope)
        if condiciones:
            query += ' WHERE ' + ' AND '.join(condiciones)
        query += ' ORDER BY "Fecha de Registro" DESC'
        resultados = db_manager.execute_query(
            query, tuple(params) if params else ())

        # Mapear resultados a los nombres de campo del modelo
        modem_list = []
        for row in resultados:
            imagen_b64 = None
            if row["imagen"]:
                try:
                    imagen_bytes = bytes(row["imagen"])
                    imagen_b64 = base64.b64encode(imagen_bytes).decode('utf-8')
                except Exception:
                    imagen_b64 = None  # Si hay error al codificar, dejamos como None

            modem_list.append({
                "numero_serie": row["Numero de Serie"],
                "cantidad": row["cantidad"],
                "unidad": row["unidad"],
                "modelo": row["modelo"],
                "area": row["area"],
                "centro_trabajo": row["Centro de Trabajo"],
                "ubicacion": row["ubicacion"],
                # No enviamos la imagen en listados para evitar tamaño
                "imagen": "Si" if row["imagen"] else None,
                "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
            })
        return modem_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al listar MODEM: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/modem/{numero_serie}/imagen")
async def obtener_imagen_modem(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT imagen FROM modem WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados or not resultados[0]["imagen"]:
            raise HTTPException(status_code=404, detail="Imagen no encontrada")
        imagen_bytes = bytes(resultados[0]["imagen"])
        return Response(content=imagen_bytes, media_type="image/jpeg")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener imagen: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/modem/{numero_serie}", response_model=MODEMResponse)
async def obtener_modem(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM modem WHERE "Numero de Serie" = %s'
        resultados = db_manager.execute_query(query, (numero_serie,))
        if not resultados:
            raise HTTPException(status_code=404, detail="MODEM no encontrado")
        return resultados[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener MODEM: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.post("/modem", response_model=MODEMResponse, status_code=201)
async def crear_modem(modem: MODEMCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM modem WHERE "Numero de Serie" = %s',
            (modem.numero_serie,)
        )
        if check:
            raise HTTPException(
                status_code=400, detail="Ya existe un MODEM con ese número de serie")

        # Convertir imagen base64 a bytes
        imagen_bytes = None
        if modem.imagen:
            if 'base64,' in modem.imagen:
                imagen_bytes = base64.b64decode(
                    modem.imagen.split('base64,')[1])
            else:
                imagen_bytes = base64.b64decode(modem.imagen)

        query = '''
            INSERT INTO modem ("Numero de Serie", cantidad, unidad, modelo, area, "Centro de Trabajo", ubicacion, imagen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        '''
        params = (
            modem.numero_serie, modem.cantidad, modem.unidad, modem.modelo,
            modem.area, modem.centro_trabajo, modem.ubicacion, imagen_bytes
        )
        # Usar get_cursor para asegurar commit
        with db_manager.get_cursor('Almacen_construcción') as cursor:
            cursor.execute(query, params)

        # Recuperar el registro insertado y mapear
        nuevo = db_manager.execute_query(
            'SELECT * FROM modem WHERE "Numero de Serie" = %s',
            (modem.numero_serie,)
        )
        row = nuevo[0]
        imagen_b64 = None
        if row["imagen"]:
            imagen_b64 = base64.b64encode(bytes(row["imagen"])).decode('utf-8')
        return {
            "numero_serie": row["Numero de Serie"],
            "cantidad": row["cantidad"],
            "unidad": row["unidad"],
            "modelo": row["modelo"],
            "area": row["area"],
            "centro_trabajo": row["Centro de Trabajo"],
            "ubicacion": row["ubicacion"],
            "imagen": imagen_b64,
            "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al crear MODEM: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.put("/modem/{numero_serie}", response_model=MODEMResponse)
async def actualizar_modem(numero_serie: str, modem: MODEMCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM modem WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="MODEM no encontrado")

        query = '''
            UPDATE modem SET cantidad = %s, unidad = %s, modelo = %s, area = %s,
                "Centro de Trabajo" = %s, ubicacion = %s, imagen = %s
            WHERE "Numero de Serie" = %s
        '''
        params = (
            modem.cantidad, modem.unidad, modem.modelo, modem.area,
            modem.centro_trabajo, modem.ubicacion, modem.imagen, numero_serie
        )
        db_manager.execute_query(query, params, fetch=False)
        actualizado = db_manager.execute_query(
            'SELECT * FROM modem WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        return actualizado[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar MODEM: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.delete("/modem/{numero_serie}")
async def eliminar_modem(numero_serie: str, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT "Numero de Serie" FROM modem WHERE "Numero de Serie" = %s',
            (numero_serie,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="MODEM no encontrado")
        db_manager.execute_query(
            'DELETE FROM modem WHERE "Numero de Serie" = %s',
            (numero_serie,),
            fetch=False
        )
        return {"message": "MODEM eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar MODEM: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/almacen", response_model=List[AlmacenResponse])
async def listar_almacen(
    area: Optional[str] = None,
    cope: Optional[str] = None,
    numero_serie: Optional[str] = None,
    user: dict = Depends(current_user)
):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM almacen'
        params = []
        condiciones = []
        if area:
            condiciones.append('area = %s')
            params.append(area)
        if cope:
            condiciones.append('cope = %s')
            params.append(cope)
        if numero_serie:
            condiciones.append('"Numero de Serie" = %s')
            params.append(numero_serie)
        if condiciones:
            query += ' WHERE ' + ' AND '.join(condiciones)
        query += ' ORDER BY "Fecha de Registro" DESC'
        resultados = db_manager.execute_query(
            query, tuple(params) if params else ())

        almacen_list = []
        for row in resultados:
            almacen_list.append({
                "id": row["id"],
                "cantidad": row["cantidad"],
                "unidad": row["unidad"],
                "descripcion": row["descripcion"],
                "numero_serie": row["Numero de Serie"],
                "area": row["area"],
                "cope": row["cope"],
                "codigo_ax": row["codigo_ax"],
                "codigo_catalogo": row["Codigo_catalogo"],
                "proyecto": row["proyecto"],
                "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
            })
        return almacen_list
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al listar almacén: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.get("/almacen/{id}", response_model=AlmacenResponse)
async def obtener_almacen(id: int, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = 'SELECT * FROM almacen WHERE id = %s'
        resultados = db_manager.execute_query(query, (id,))
        if not resultados:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        return resultados[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener item: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.post("/almacen", response_model=AlmacenResponse, status_code=201)
async def crear_almacen(item: AlmacenCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        # 1. Verificar si YA EXISTE EN ESTA MISMA ÁREA Y COPE
        if item.numero_serie:
            existente = db_manager.execute_query(
                'SELECT id, cantidad FROM almacen WHERE "Numero de Serie" = %s AND area = %s AND cope = %s',
                (item.numero_serie, item.area, item.cope)
            )

            if existente:
                # Si existe, sumamos la cantidad
                nueva_cantidad = existente[0]['cantidad'] + item.cantidad
                query_update = '''
                    UPDATE almacen SET cantidad = %s
                    WHERE id = %s
                '''
                db_manager.execute_query(
                    query_update, (nueva_cantidad, existente[0]['id']), fetch=False)

                # Recuperar el registro actualizado
                actualizado = db_manager.execute_query(
                    'SELECT * FROM almacen WHERE id = %s',
                    (existente[0]['id'],)
                )
                row = actualizado[0]
                return {
                    "id": row["id"], "cantidad": row["cantidad"], "unidad": row["unidad"],
                    "descripcion": row["descripcion"], "numero_serie": row["Numero de Serie"],
                    "area": row["area"], "cope": row["cope"], "codigo_ax": row["codigo_ax"],
                    "codigo_catalogo": row["Codigo_catalogo"], "proyecto": row["proyecto"],
                    "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
                }

        # 2. Si no existe en esta área/cope, INSERTAR un nuevo registro (aunque el serial exista en otra área)
        query = '''
            INSERT INTO almacen (cantidad, unidad, descripcion, "Numero de Serie", area, cope, codigo_ax, "Codigo_catalogo", proyecto)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        '''
        params = (
            item.cantidad, item.unidad, item.descripcion, item.numero_serie,
            item.area, item.cope, item.codigo_ax, item.codigo_catalogo, item.proyecto
        )
        with db_manager.get_cursor('Almacen_construcción') as cursor:
            cursor.execute(query, params)
            id_result = cursor.fetchone()['id']

        # Recuperar el registro completo
        nuevo = db_manager.execute_query(
            'SELECT * FROM almacen WHERE id = %s', (id_result,))
        row = nuevo[0]
        return {
            "id": row["id"], "cantidad": row["cantidad"], "unidad": row["unidad"],
            "descripcion": row["descripcion"], "numero_serie": row["Numero de Serie"],
            "area": row["area"], "cope": row["cope"], "codigo_ax": row["codigo_ax"],
            "codigo_catalogo": row["Codigo_catalogo"], "proyecto": row["proyecto"],
            "fecha_registro": row["Fecha de Registro"].isoformat() if row["Fecha de Registro"] else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al crear item en almacén: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.put("/almacen/{id}", response_model=AlmacenResponse)
async def actualizar_almacen(id: int, item: AlmacenCreate, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT id FROM almacen WHERE id = %s',
            (id,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="Item no encontrado")

        query = '''
            UPDATE almacen SET cantidad = %s, unidad = %s, descripcion = %s,
                "Numero de Serie" = %s, area = %s, cope = %s,
                codigo_ax = %s, "Codigo_catalogo" = %s, proyecto = %s
            WHERE id = %s
        '''
        params = (
            item.cantidad, item.unidad, item.descripcion, item.numero_serie,
            item.area, item.cope, item.codigo_ax, item.codigo_catalogo, item.proyecto,
            id
        )
        db_manager.execute_query(query, params, fetch=False)
        actualizado = db_manager.execute_query(
            'SELECT * FROM almacen WHERE id = %s',
            (id,)
        )
        return actualizado[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar item: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()


@router.delete("/almacen/{id}")
async def eliminar_almacen(id: int, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        check = db_manager.execute_query(
            'SELECT id FROM almacen WHERE id = %s',
            (id,)
        )
        if not check:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        db_manager.execute_query(
            'DELETE FROM almacen WHERE id = %s',
            (id,),
            fetch=False
        )
        return {"message": "Item eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al eliminar item: {str(e)}")
    finally:
        if db_manager:
            db_manager.close()

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

# =============================================================================
# MÓDULO CATÁLOGO
# =============================================================================


class CatalogoBase(BaseModel):
    codigo_ax: str
    codigo_sap: Optional[str] = None
    numero_serie: Optional[str] = None
    descripcion: str


@router.get("/catalogo")
async def listar_catalogo(busqueda: Optional[str] = None, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        # Asumiendo que esta es tu tabla de catálogo
        query = "SELECT * FROM articulos_estandar"
        params = []
        if busqueda:
            query += " WHERE nombre_articulo ILIKE %s OR codigo_ax ILIKE %s"
            params.extend([f"%{busqueda}%", f"%{busqueda}%"])

        resultados = db_manager.execute_query(query, tuple(params))
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


@router.post("/catalogo", status_code=201)
async def crear_catalogo(item: CatalogoBase, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = """
            INSERT INTO articulos_estandar (codigo_ax, nombre_articulo, unidad)
            VALUES (%s, %s, 'Pieza') RETURNING codigo_ax
        """
        with db_manager.get_cursor('Almacen_construcción') as cursor:
            cursor.execute(query, (item.codigo_ax, item.descripcion))
        return {"message": "Elemento agregado al catálogo correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


@router.put("/catalogo/{codigo_ax}")
async def actualizar_catalogo(codigo_ax: str, item: CatalogoBase, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        query = """
            UPDATE articulos_estandar
            SET nombre_articulo = %s
            WHERE codigo_ax = %s
        """
        # Como es un UPDATE, usamos fetch=False
        db_manager.execute_query(
            query, (item.descripcion, codigo_ax), fetch=False)
        return {"message": "Elemento del catálogo actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


# =============================================================================
# MÓDULO MOVIMIENTO ENTRE ALMACENES
# =============================================================================
class MovimientoRequest(BaseModel):
    origen: str
    destino: str
    numero_serie: str
    cantidad: int


@router.post("/movimiento")
async def mover_almacen(payload: MovimientoRequest, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')

        with db_manager.get_cursor('Almacen_construcción') as cursor:
            # Buscar si existe en el origen (lógica simplificada para tabla almacen)
            cursor.execute('SELECT id, cantidad FROM almacen WHERE "Numero de Serie" = %s AND area = %s',
                           (payload.numero_serie, payload.origen))
            res = cursor.fetchone()

            if not res or res['cantidad'] < payload.cantidad:
                raise HTTPException(
                    status_code=400, detail="No hay suficiente stock en el origen o el equipo no existe.")

            # Descontar del origen
            cursor.execute(
                'UPDATE almacen SET cantidad = cantidad - %s WHERE id = %s', (payload.cantidad, res['id']))

            # Agregar al destino (si ya existe se suma, si no se inserta)
            cursor.execute('SELECT id FROM almacen WHERE "Numero de Serie" = %s AND area = %s',
                           (payload.numero_serie, payload.destino))
            res_dest = cursor.fetchone()

            if res_dest:
                cursor.execute(
                    'UPDATE almacen SET cantidad = cantidad + %s WHERE id = %s', (payload.cantidad, res_dest['id']))
            else:
                # Insertar copiando los datos del origen
                cursor.execute("""
                    INSERT INTO almacen (cantidad, unidad, descripcion, "Numero de Serie", area, cope, codigo_ax)
                    SELECT %s, unidad, descripcion, "Numero de Serie", %s, cope, codigo_ax
                    FROM almacen WHERE id = %s
                """, (payload.cantidad, payload.destino, res['id']))

        return {"message": "Movimiento realizado con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


# =============================================================================
# MÓDULO ENTREGA (Almacén a Técnico en Campo)
# =============================================================================
class EntregaItem(BaseModel):
    numero_serie: str
    tipo: str  # "ONT", "MODEM", "Misceláneo"
    cantidad: int
    modelo_desc: str
    unidad: str


class EntregaRequest(BaseModel):
    area: str
    cope: str
    exp_tecnico: str
    items: list[EntregaItem]


@router.post("/entrega")
async def procesar_entrega(payload: EntregaRequest, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        id_entrega = str(uuid.uuid4())

        with db_manager.get_cursor('Almacen_construcción') as cursor:
            # 1. Registrar la entrega
            cursor.execute('''
                INSERT INTO entregas (id_entrega, area, cope, expediente_tecnico, "Fecha de Entrega")
                VALUES (%s, %s, %s, %s, NOW())
            ''', (id_entrega, payload.area, payload.cope, payload.exp_tecnico))

            for item in payload.items:

                if item.tipo == "Misceláneo":
                    tabla_origen = 'almacen'
                    col_cope = 'cope'

                    # Validar stock (SIN IMAGEN porque la tabla no tiene esa columna)
                    cursor.execute(f'SELECT cantidad FROM {tabla_origen} WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s',
                                   (item.numero_serie, payload.area, payload.cope))
                    res = cursor.fetchone()

                    if not res or res['cantidad'] < item.cantidad:
                        raise HTTPException(
                            status_code=400, detail=f"Stock insuficiente para {item.numero_serie}")

                    # Descontar del origen
                    cursor.execute(f'UPDATE {tabla_origen} SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s',
                                   (item.cantidad, item.numero_serie, payload.area, payload.cope))
                    cursor.execute(f'DELETE FROM {tabla_origen} WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s AND cantidad <= 0',
                                   (item.numero_serie, payload.area, payload.cope))

                    # Insertar en misceláneos
                    cursor.execute('''
                        INSERT INTO miselaneo_en_campo (cantidad, unidad, descripcion, "Numero de Serie", area, "Centro de Trabajo", "Fecha de surtido", "Expediente Técnico")
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
                    ''', (item.cantidad, item.unidad, item.modelo_desc, item.numero_serie, payload.area, payload.cope, payload.exp_tecnico))

                elif item.tipo in ["ONT", "MODEM"]:
                    if item.tipo == "ONT":
                        tabla_origen = 'ont'
                        tabla_destino = '"ONT en Campo"'
                    else:
                        tabla_origen = 'modem'
                        tabla_destino = 'modem_en_campo'

                    col_cope = '"Centro de Trabajo"'

                    # Validar stock y EXTRAER LA IMAGEN
                    cursor.execute(f'SELECT cantidad, imagen FROM {tabla_origen} WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s',
                                   (item.numero_serie, payload.area, payload.cope))
                    res = cursor.fetchone()

                    if not res or res['cantidad'] < item.cantidad:
                        raise HTTPException(
                            status_code=400, detail=f"Stock insuficiente para {item.numero_serie}")

                    imagen_bytes = res['imagen']  # Extraemos la imagen binaria

                    # Descontar del origen
                    cursor.execute(f'UPDATE {tabla_origen} SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s',
                                   (item.cantidad, item.numero_serie, payload.area, payload.cope))
                    cursor.execute(f'DELETE FROM {tabla_origen} WHERE "Numero de Serie" = %s AND area = %s AND {col_cope} = %s AND cantidad <= 0',
                                   (item.numero_serie, payload.area, payload.cope))

                    # Insertar en tabla de campo CON imagen y fecha de movimiento
                    cursor.execute(f'''
                        INSERT INTO {tabla_destino} ("Numero de Serie", cantidad, unidad, modelo, area, "Centro de Trabajo", "Expediente Técnico", imagen, "Fecha de Registro", "Fecha de Movimiento")
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                    ''', (item.numero_serie, item.cantidad, item.unidad, item.modelo_desc, payload.area, payload.cope, payload.exp_tecnico, imagen_bytes))

        return {"id_entrega": id_entrega, "message": "Entrega procesada con éxito"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


@router.get("/entregas")
async def obtener_historial_entregas(tecnico: str, user: dict = Depends(current_user)):
    """Obtiene el historial de entregas de un técnico."""
    db = None
    try:
        db = DatabaseManager('Almacen_construcción')
        query = """
            SELECT id_entrega, area, cope, "Fecha de Entrega", reporte_path
            FROM entregas
            WHERE expediente_tecnico = %s
            ORDER BY "Fecha de Entrega" DESC
        """
        resultados = db.execute_query(query, (tecnico,))
        return resultados
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()


@router.get("/buscar_global")
async def buscar_global(area: str, cope: str, numero_serie: str, user: dict = Depends(current_user)):
    db = None
    try:
        db = DatabaseManager('Almacen_construcción')

        # 1. Buscar en almacén (Misceláneos)
        q_alm = 'SELECT "Numero de Serie", cantidad, unidad, descripcion, NULL as imagen FROM almacen WHERE area = %s AND cope = %s AND "Numero de Serie" = %s'
        res = db.execute_query(q_alm, (area, cope, numero_serie))
        if res:
            return {"tipo": "Misceláneo", "data": res[0]}

        # 2. Buscar en ONT
        q_ont = 'SELECT "Numero de Serie", cantidad, unidad, modelo as descripcion, imagen FROM ont WHERE area = %s AND "Centro de Trabajo" = %s AND "Numero de Serie" = %s'
        res = db.execute_query(q_ont, (area, cope, numero_serie))
        if res:
            img = "Si" if res[0]['imagen'] else None  # Simulamos el indicador
            return {"tipo": "ONT", "data": {**res[0], "imagen": img}}

        # 3. Buscar en MODEM
        q_mod = 'SELECT "Numero de Serie", cantidad, unidad, modelo as descripcion, imagen FROM modem WHERE area = %s AND "Centro de Trabajo" = %s AND "Numero de Serie" = %s'
        res = db.execute_query(q_mod, (area, cope, numero_serie))
        if res:
            img = "Si" if res[0]['imagen'] else None
            return {"tipo": "MODEM", "data": {**res[0], "imagen": img}}

        raise HTTPException(
            status_code=404, detail="Equipo no encontrado en el almacén actual.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db:
            db.close()

# =============================================================================
# MÓDULO RECIBIR (De Técnico/Proveedor a Almacén)
# =============================================================================


class RecibirRequest(BaseModel):
    area: str
    cope: str
    exp_tecnico: Optional[str] = None
    items: list[EntregaItem]


@router.post("/recibir")
async def recibir_material(payload: RecibirRequest, user: dict = Depends(current_user)):
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')

        with db_manager.get_cursor('Almacen_construcción') as cursor:
            for item in payload.items:
                if item.tipo in ["ONT", "MODEM"]:
                    tabla_origen = '"ONT en Campo"' if item.tipo == "ONT" else 'modem_en_campo'

                    # 1. Quitar de campo
                    cursor.execute(f'UPDATE {tabla_origen} SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s AND "Expediente Técnico" = %s',
                                   (item.cantidad, item.numero_serie, payload.exp_tecnico))

                    # 2. Sumar al almacén (si existe) o insertar
                    cursor.execute('UPDATE almacen SET cantidad = cantidad + %s WHERE "Numero de Serie" = %s AND area = %s',
                                   (item.cantidad, item.numero_serie, payload.area))
                else:
                    cursor.execute('UPDATE miselaneo_en_campo SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s AND "Expediente Técnico" = %s',
                                   (item.cantidad, item.numero_serie, payload.exp_tecnico))
                    cursor.execute('UPDATE almacen SET cantidad = cantidad + %s WHERE "Numero de Serie" = %s AND area = %s',
                                   (item.cantidad, item.numero_serie, payload.area))

        return {"message": "Material recibido y reingresado al almacén"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


# Carpeta en el servidor donde se guardarán los PDFs
REPORTES_DIR = os.path.join(os.getcwd(), "reportes_entregas")
os.makedirs(REPORTES_DIR, exist_ok=True)


@router.post("/entregas/{id_entrega}/guardar_reporte")
async def subir_reporte(id_entrega: str, payload: dict, user: dict = Depends(current_user)):
    """Recibe el PDF en Base64 desde la app, lo guarda en el servidor y actualiza la BD."""
    db_manager = None
    try:
        pdf_b64 = payload.get("pdf_b64")
        if not pdf_b64:
            raise HTTPException(
                status_code=400, detail="No se recibió el archivo PDF")

        # Decodificar y guardar el archivo en el servidor
        pdf_bytes = base64.b64decode(pdf_b64)
        nombre_archivo = f"reporte_{id_entrega}.pdf"
        ruta_servidor = os.path.join(REPORTES_DIR, nombre_archivo)

        with open(ruta_servidor, "wb") as f:
            f.write(pdf_bytes)

        # Actualizar la base de datos (USANDO get_cursor PARA QUE HAGA COMMIT)
        db_manager = DatabaseManager('Almacen_construcción')
        with db_manager.get_cursor('Almacen_construcción') as cursor:
            cursor.execute(
                "UPDATE entregas SET reporte_path = %s WHERE id_entrega = %s",
                (nombre_archivo, id_entrega)
            )

        return {"message": "Reporte guardado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()


@router.get("/entregas/{id_entrega}/descargar_reporte")
async def descargar_reporte(id_entrega: str, user: dict = Depends(current_user)):
    """Devuelve el archivo PDF para que la app pueda abrirlo."""
    db_manager = None
    try:
        db_manager = DatabaseManager('Almacen_construcción')
        res = db_manager.execute_query(
            "SELECT reporte_path FROM entregas WHERE id_entrega = %s",
            (id_entrega,)
        )

        if not res or not res[0]['reporte_path']:
            raise HTTPException(
                status_code=404, detail="No hay PDF registrado para esta entrega")

        nombre_archivo = res[0]['reporte_path']
        ruta_servidor = os.path.join(REPORTES_DIR, nombre_archivo)

        if not os.path.exists(ruta_servidor):
            raise HTTPException(
                status_code=404, detail="El archivo PDF no existe en el servidor")

        return FileResponse(ruta_servidor, media_type="application/pdf", filename=nombre_archivo)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_manager:
            db_manager.close()
