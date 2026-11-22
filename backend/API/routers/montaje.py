from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import json
import base64
import psycopg2
from typing import Dict, Any

from .auth import current_user
from db.database_Manager import DatabaseManager

router = APIRouter(
    prefix="/montaje",
    tags=["montaje"]
)

# --- MODELOS PYDANTIC ---


class FolioPendiente(BaseModel):
    folio: str
    tabla: str
    numero_serie: Optional[str] = None


class MaterialConsumo(BaseModel):
    tipo: str  # "ONT", "MODEM", "Misceláneo"
    numero_serie: Optional[str] = None
    descripcion: str
    cantidad: int


class CuadreRequest(BaseModel):
    tabla_origen: str
    folio: str
    area: str
    cope: str
    exp_tecnico: str
    consumos: List[MaterialConsumo]

# --- ENDPOINTS ---


@router.get("/folios", response_model=List[FolioPendiente])
async def obtener_folios_pendientes(area: str, cope: str, exp_tecnico: str, user: dict = Depends(current_user)):
    """Obtiene los folios de producción que aún no han sido cuadrados."""
    db_produccion = None
    try:
        db_produccion = DatabaseManager('Producción')
        tablas = ["fibra_optica", "cobre", "quejas", "a4_incentivos"]
        folios_totales = []

        for tabla in tablas:
            # Usamos f-string para la tabla (es seguro porque está hardcodeada) y %s para los valores
            query = f"""
                SELECT folio_pisa, numero_serie
                FROM public.{tabla}
                WHERE area = %s AND cope = %s AND exp_tecnico = %s
                AND estatus IS NULL
            """

            resultados = db_produccion.execute_query(
                query, (area, cope, exp_tecnico))

            for row in resultados:
                folios_totales.append({
                    "folio": row["folio_pisa"],
                    "tabla": tabla,
                    "numero_serie": row["numero_serie"]
                })

        return folios_totales
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_produccion:
            db_produccion.close()


@router.get("/materiales/{tabla_origen}/{folio}")
async def obtener_materiales_folio(
    tabla_origen: str,
    folio: str,
    area: str,
    cope: str,
    exp_tecnico: str,
    user: dict = Depends(current_user)
):
    """Obtiene los materiales en custodia del técnico relacionados al folio."""
    db_produccion = None
    db_almacen = None
    try:
        db_produccion = DatabaseManager('Producción')
        db_almacen = DatabaseManager('Almacen_construcción')

        # 1. Obtener el número de serie del folio (si tiene)
        query_prod = f"SELECT numero_serie FROM public.{tabla_origen} WHERE folio_pisa = %s"

        res_prod = db_produccion.execute_query(query_prod, (folio,))
        numero_serie_prod = res_prod[0]["numero_serie"] if res_prod and res_prod[0]["numero_serie"] else None

        materiales = []

        # 2. Consultar Equipo Principal (ONT o MODEM)
        if numero_serie_prod:
            tabla_equipo = '"ONT en Campo"' if tabla_origen in [
                "fibra_optica", "quejas"] else 'modem_en_campo'
            tipo_equipo = "ONT" if tabla_origen in [
                "fibra_optica", "quejas"] else "MODEM"

            query_eq = f"""
                SELECT "Numero de Serie" as n_serie, modelo as material, cantidad as asignado
                FROM public.{tabla_equipo}
                WHERE "Numero de Serie" = %s
            """

            res_eq = db_almacen.execute_query(query_eq, (numero_serie_prod,))
            if res_eq:
                materiales.append({
                    "tipo": tipo_equipo,
                    "numero_serie": res_eq[0]["n_serie"],
                    "material": res_eq[0]["material"],
                    "asignado": res_eq[0]["asignado"]
                })

        # 3. Consultar Misceláneos asignados al técnico
        query_misc = """
            SELECT "Numero de Serie" as n_serie, descripcion as material, SUM(cantidad) as asignado
            FROM public.miselaneo_en_campo
            WHERE "Expediente Técnico" ILIKE %s AND area ILIKE %s AND "Centro de Trabajo" ILIKE %s
            GROUP BY "Numero de Serie", descripcion
        """
        res_misc = db_almacen.execute_query(
            query_misc, (f"%{exp_tecnico}%", f"%{area}%", f"%{cope}%"))

        for row in res_misc:
            materiales.append({
                "tipo": "Misceláneo",
                "numero_serie": row["n_serie"],
                "material": row["material"],
                "asignado": row["asignado"]
            })

        return materiales

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_produccion:
            db_produccion.close()
        if db_almacen:
            db_almacen.close()


@router.post("/guardar")
async def guardar_cuadre(payload: CuadreRequest, user: dict = Depends(current_user)):
    """Descuenta el material del almacén y marca la producción como completada."""
    db_produccion = None
    db_almacen = None
    try:
        db_produccion = DatabaseManager('Producción')
        db_almacen = DatabaseManager('Almacen_construcción')

        consumos_guardados = []

        # 1. Procesar descuentos en Almacén (Usamos transacción manual)
        db_almacen.connect()
        cursor = db_almacen.connection.cursor()

        try:
            for item in payload.consumos:
                if item.cantidad <= 0:
                    continue

                if item.tipo in ["ONT", "MODEM"]:
                    tabla = '"ONT en Campo"' if item.tipo == "ONT" else 'modem_en_campo'
                    # Descontar
                    cursor.execute(
                        f'UPDATE {tabla} SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s',
                        (item.cantidad, item.numero_serie)
                    )
                    # Eliminar si llega a 0
                    cursor.execute(
                        f'DELETE FROM {tabla} WHERE "Numero de Serie" = %s AND cantidad <= 0',
                        (item.numero_serie,)
                    )
                else:
                    # Lógica FIFO para Misceláneos
                    cursor.execute(
                        """
                        SELECT "Numero de Serie", cantidad, "Fecha de surtido"
                        FROM miselaneo_en_campo
                        WHERE descripcion = %s AND area = %s AND "Centro de Trabajo" = %s AND "Expediente Técnico" = %s
                        ORDER BY "Fecha de surtido" ASC
                        """,
                        (item.descripcion, payload.area,
                         payload.cope, payload.exp_tecnico)
                    )
                    registros = cursor.fetchall()
                    restante = item.cantidad

                    for reg in registros:
                        if restante <= 0:
                            break
                        serie, cant_disp, fecha = reg
                        descuento = min(cant_disp, restante)

                        cursor.execute(
                            'UPDATE miselaneo_en_campo SET cantidad = cantidad - %s WHERE "Numero de Serie" = %s AND "Fecha de surtido" = %s',
                            (descuento, serie, fecha)
                        )
                        if (cant_disp - descuento) <= 0:
                            cursor.execute(
                                'DELETE FROM miselaneo_en_campo WHERE "Numero de Serie" = %s AND "Fecha de surtido" = %s',
                                (serie, fecha)
                            )
                        restante -= descuento

                consumos_guardados.append({
                    "tipo": item.tipo,
                    "numero_serie": item.numero_serie,
                    "descripcion": item.descripcion,
                    "cantidad": item.cantidad
                })

            db_almacen.connection.commit()

        except Exception as e:
            db_almacen.connection.rollback()
            raise HTTPException(
                status_code=500, detail=f"Error al descontar inventario: {str(e)}")

        # 2. Actualizar tabla de Producción
        query_prod = f"""
            UPDATE public.{payload.tabla_origen}
            SET consumo = %s::jsonb, estatus = 'Completado', fecha_cuadre = NOW()
            WHERE folio_pisa = %s
        """

        json_consumo = json.dumps({"items": consumos_guardados})

        # Usamos get_cursor para hacer el commit correctamente
        with db_produccion.get_cursor('Producción') as cur_prod:
            cur_prod.execute(query_prod, (json_consumo, payload.folio))

        return {"message": "Cuadre guardado exitosamente"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_produccion:
            db_produccion.close()
        if db_almacen:
            db_almacen.close()


@router.get("/exportar")
async def exportar_datos(
    area: str,
    cope: Optional[str] = None,
    fecha_ini: str = None,
    fecha_fin: str = None,
    user: dict = Depends(current_user)
):
    """Obtiene todos los datos de producción para exportar a Excel."""
    db_produccion = None
    try:
        db_produccion = DatabaseManager('Producción')
        tablas = ["fibra_optica", "cobre", "a4_incentivos", "quejas"]
        datos_totales = {}

        for tabla in tablas:
            query = f"""
                SELECT *, imagen 
                FROM public.{tabla}
                WHERE area ILIKE %s 
                AND fecha_posteo BETWEEN %s AND %s
            """
            params = [f"%{area}%", fecha_ini, f"{fecha_fin} 23:59:59"]

            if cope and cope != "Todos los COPE":
                query += " AND cope ILIKE %s"
                params.append(f"%{cope}%")

            resultados = db_produccion.execute_query(query, tuple(params))

            # Convertir imágenes a base64 para enviarlas por JSON
            for row in resultados:
                if row.get("imagen"):
                    row["imagen_b64"] = base64.b64encode(
                        bytes(row["imagen"])).decode('utf-8')
                else:
                    row["imagen_b64"] = None
                # Eliminar el binario original para evitar errores de serialización JSON
                if "imagen" in row:
                    del row["imagen"]

            datos_totales[tabla] = resultados

        return datos_totales
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db_produccion:
            db_produccion.close()
