from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.settings import get_settings
from app.models.base import Base

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db() -> None:
    """Create all tables if the configured database exists."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_database_connection():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            print("✅ Database connected successfully")
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session