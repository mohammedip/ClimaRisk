from fastapi import FastAPI
from core.database import engine, Base
from routes.health import router as health_router
from routes.auth   import router as auth_router
from routes.zones  import router as zones_router
from routes.predictions import router as predictions_router
from routes.chat import router as chat_router
from routes.weather import router as weather_router
from routes.alerts import router as alerts_router
from services.scheduler import start_scheduler
import logging
logging.basicConfig(level=logging.INFO)


app = FastAPI(title="ClimaRisk API", version="0.1.0")


@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables ready!")
    print("🚀 Starting scheduler...")
    start_scheduler()
    print("✅ Scheduler started!")


app.include_router(health_router, prefix="/api")
app.include_router(auth_router,   prefix="/api/auth", tags=["Auth"])
app.include_router(zones_router,  prefix="/api/zones", tags=["Zones"])
app.include_router(predictions_router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(chat_router,   prefix="/api/chat",        tags=["Chat"])
app.include_router(alerts_router, prefix="/api/alerts",      tags=["Alerts"])
app.include_router(weather_router,prefix="/api/weather",     tags=["Weather"])