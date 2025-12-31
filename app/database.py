from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set.")


# Create SQLAlchemy engine
# engine = create_engine(DATABASE_URL)
engine = create_async_engine(DATABASE_URL, echo=True, future=True)

# Create SessionLocal class for database sessions
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False)

# Base class for all ORM models
Base = declarative_base()

# ✅ Dependency for FastAPI routes


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Test the connection


async def test_connection():
    try:
        with engine.connect() as connection:
            print("✅ Database connection successful!")
    except SQLAlchemyError as e:
        print("❌ Database connection failed:", e)
