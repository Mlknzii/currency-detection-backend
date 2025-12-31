from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv
import os

# Load .env for local development only
load_dotenv()

# Base for declarative models
Base = declarative_base()

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Check your Railway environment variables."
    )

# Automatically create async engine on import
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True,
)

# Create sessionmaker for dependency injection
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Dependency for FastAPI routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# Optional: test connection
async def test_connection():
    try:
        async with engine.connect() as connection:
            await connection.execute("SELECT 1")
            print("✅ Database connection successful!")
    except SQLAlchemyError as e:
        print("❌ Database connection failed:", e)


