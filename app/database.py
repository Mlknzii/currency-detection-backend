from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv
import os

# Load .env ONLY for local development
load_dotenv()

Base = declarative_base()

_engine = None
AsyncSessionLocal = None


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Check Render/Railway environment variables."
        )
    return db_url


def init_engine():
    global _engine, AsyncSessionLocal

    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=True,
            future=True,
        )

        AsyncSessionLocal = sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _engine


# ✅ Dependency for FastAPI routes
async def get_db():
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_engine() first.")

    async with AsyncSessionLocal() as session:
        yield session


# ✅ Safe async connection test
async def test_connection():
    engine = init_engine()
    try:
        async with engine.connect() as connection:
            await connection.execute("SELECT 1")
            print("✅ Database connection successful!")
    except SQLAlchemyError as e:
        print("❌ Database connection failed:", e)

