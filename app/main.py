import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.config import get_settings
from app.config.database import check_database_connection, init_db

settings = get_settings()


if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    db_connected = await check_database_connection()
    if not db_connected:
        raise RuntimeError("Database connection failed. Exiting.")
    await init_db()
    yield
    # Shutdown code (if any) can go here
    print("Application shutting down...")
    
    
app = FastAPI(
    title=settings.app_name,
    description="Investigates production incidents using a LangChain tool-using agent.",
    lifespan=lifespan
)

@app.get("/")
def read_root():
    return {
        "status": "running",
        "app_name": settings.app_name,
        "docs": "/docs"
    }

app.include_router(api_v1_router)
