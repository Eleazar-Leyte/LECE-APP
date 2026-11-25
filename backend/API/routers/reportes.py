from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from .auth import current_user
from db.database_Manager import DatabaseManager

router = APIRouter(
    prefix="/reportes",
    tags=["reportes"]
)

@router.get("/dashboard")
async def obtener_datos_dashboard(
    area: str,
    fecha_ini: str,
    fecha_fin: str,
    user: dict = Depends(current_user)
):
    """Obtiene estadísticas agrupadas para el dashboard de reportes."""
    db = None
    try:
        db = DatabaseManager('Producción')
        
        # Filtro de fechas para todas las consultas
        filtro_fechas = f"AND fecha_posteo BETWEEN '{fecha_ini} 00:00:00' AND '{fecha_fin} 23:59:59' AND area = '{area}'"

        # 1. Producción por Técnico (Barras)
        q_tecnicos = f"""
            SELECT exp_tecnico, COUNT(*) as total_trabajos
            FROM (
                SELECT exp_tecnico, fecha_posteo, area FROM fibra_optica
                UNION ALL SELECT exp_tecnico, fecha_posteo, area FROM cobre
                UNION ALL SELECT exp_tecnico, fecha_posteo, area FROM quejas
                UNION ALL SELECT exp_tecnico, fecha_posteo, area FROM a4_incentivos
            ) AS produccion
            WHERE 1=1 {filtro_fechas}
            GROUP BY exp_tecnico
            ORDER BY total_trabajos DESC
            LIMIT 10
        """
        tecnicos = db.execute_query(q_tecnicos)

        # 2. Distribución por Tecnología (Pastel)
        q_tecnologias = []
        for tabla in ["fibra_optica", "cobre", "quejas", "a4_incentivos"]:
            q = f"SELECT COUNT(*) as total FROM {tabla} WHERE 1=1 {filtro_fechas}"
            res = db.execute_query(q)
            q_tecnologias.append({"tecnologia": tabla, "total": res[0]['total'] if res else 0})

        # 3. Tendencia en el tiempo (Líneas)
        q_tendencia = f"""
            SELECT fecha_posteo::date as fecha, COUNT(*) as total
            FROM (
                SELECT fecha_posteo, area FROM fibra_optica
                UNION ALL SELECT fecha_posteo, area FROM cobre
                UNION ALL SELECT fecha_posteo, area FROM quejas
                UNION ALL SELECT fecha_posteo, area FROM a4_incentivos
            ) AS produccion
            WHERE 1=1 {filtro_fechas}
            GROUP BY fecha_posteo::date
            ORDER BY fecha_posteo::date ASC
        """
        tendencia = db.execute_query(q_tendencia)

        return {
            "tecnicos": tecnicos,
            "tecnologias": q_tecnologias,
            "tendencia": tendencia
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if db: db.close()