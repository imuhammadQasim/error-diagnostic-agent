import os

from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.config import get_settings

settings = get_settings()

# LangSmith reads its config from the environment, not from our Settings
# object directly - this is the one place we bridge the two, so tracing
# turns on/off purely by editing .env, no code change needed.
if settings.langsmith_tracing:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project

app = FastAPI(
    title=settings.app_name,
    description="Investigates production incidents using a LangChain tool-using agent.",
)
app.include_router(api_v1_router)
