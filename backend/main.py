import psutil
import asyncio
import logging
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from core.database import engine, Base
from routes.health      import router as health_router
from routes.auth        import router as auth_router
from routes.zones       import router as zones_router
from routes.predictions import router as predictions_router
from routes.chat        import router as chat_router
from routes.weather     import router as weather_router
from routes.alerts      import router as alerts_router
from routes.users       import router as users_router
from services.metrics   import cpu_usage_gauge, ram_usage_gauge, ram_used_bytes_gauge

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="ClimaRisk API", version="0.1.0")

Instrumentator().instrument(app).expose(app)


async def collect_system_metrics():

    while True:
        try:
            cpu_usage_gauge.set(psutil.cpu_percent(interval=1))
            mem = psutil.virtual_memory()
            ram_usage_gauge.set(mem.percent)
            ram_used_bytes_gauge.set(mem.used)
        except Exception:
            pass
        await asyncio.sleep(30)


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables ready!")
    print("📊 Metrics at http://localhost:8000/metrics")
    asyncio.create_task(collect_system_metrics())


app.include_router(health_router,      prefix="/api")
app.include_router(auth_router,        prefix="/api/auth",        tags=["Auth"])
app.include_router(zones_router,       prefix="/api/zones",       tags=["Zones"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(chat_router,        prefix="/api/chat",        tags=["Chat"])
app.include_router(alerts_router,      prefix="/api/alerts",      tags=["Alerts"])
app.include_router(weather_router,     prefix="/api/weather",     tags=["Weather"])
app.include_router(users_router,       prefix="/api/users",       tags=["Users"])