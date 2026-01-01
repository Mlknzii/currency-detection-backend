from fastapi import FastAPI

# from app.routers import currency
from fastapi.middleware.cors import CORSMiddleware
from app.database import test_connection
from app.database import engine, Base
from app.auth.routes import router as auth_router
# Ensure models are imported
from app.models import prediction, system_log, user
from app.prediction.routes import router as predict_router
# import asyncio
from fastapi.staticfiles import StaticFiles
from pathlib import Path


app = FastAPI(title="AI Currency Detector API", docs_url="/docs")

# Always resolve the absolute path of "static" folder
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "uploads").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Allow frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later replace with your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # test_connection()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database and tables created successfully")


@app.get("/")
def home():
    return {"message": "Currency Recognition API running"}


# Authentication and Prediction Routers
app.include_router(auth_router)
app.include_router(predict_router)

# for Render
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
    )
