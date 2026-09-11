from sqlalchemy import text
from app.config.settings import get_settings
from sqlalchemy.ext.asyncio import (AsyncSession,async_sessionmaker, create_async_engine)

settings = get_settings()
print(settings.DATABASE_URL)

engine = create_async_engine(settings.DATABASE_URL, echo=True)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

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