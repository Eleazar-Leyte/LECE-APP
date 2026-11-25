from fastapi import FastAPI
# Asegúrate de importar el router de producción correctamente
from routers import (auth, users, personal, almacen,
                     produccion, montaje, reportes)

app = FastAPI()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(personal.router)
app.include_router(almacen.router)
app.include_router(produccion.router)
app.include_router(montaje.router)
app.include_router(reportes.router)
