import uuid
import os
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.user import User
from app.models.prediction import Prediction
from app.auth.utils import get_current_user
from app.utils.logger import create_log

# Import AI model and utilities
# from ai.evaluate import load_model, predict_image
from ai.gimini_client import analyze_currency

router = APIRouter(prefix="/predict", tags=["Prediction"])

UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Load model ONCE
# model, device = load_model()


# ------------------------------------
# Predict Currency Endpoint
# ------------------------------------
@router.post("/")
async def predict_currency(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        # ✅ Save uploaded file
        file_ext = os.path.splitext(file.filename)[1]
        file_name = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(UPLOAD_DIR, file_name)
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

         # ✅ Run AI prediction
        try:
            # Run model
            with open(file_path, "rb") as img_file:
                image_bytes = img_file.read()
            result = analyze_currency(image_bytes)
            # result = extract_json_from_gemini(response.text)

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"AI prediction failed: {e}")

        # ✅ Create prediction record
        new_prediction = Prediction(
            user_id=current_user.id,
            currency_code=result["currency_code"],
            confidence=result["confidence"],
            name_en=result["name_en"],
            name_ar=result["name_ar"],
            denomination_value=result["denomination_value"],
            is_counterfeit=result["is_counterfeit"],
            image_path=f"/static/uploads/{file_name}",
            timestamp=datetime.utcnow(),
        )

        db.add(new_prediction)
        await db.commit()
        await db.refresh(new_prediction)

        # ✅ Log the action
        await create_log(
            db,
            action="PREDICT",
            message=f"User {current_user.full_name} predicted {result["name_en"]} ({result["confidence"]}%)",
            user_id=current_user.id
        )

        # ✅ Return response
        return {
            "id": new_prediction.id,
            "status": "success",
            "currency_code": result["currency_code"],
            "name_en": result["name_en"],
            "name_ar": result["name_ar"],
            "confidence": result["confidence"],
            "denomination_value": result["denomination_value"],
            "is_counterfeit": result["is_counterfeit"],
            "image_url": f"/static/uploads/{file_name}"

        }

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------
# Get Prediction History
# ------------------------------------
@router.get("/history")
async def get_user_predictions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(
        select(Prediction).where(Prediction.user_id == current_user.id)
    )
    predictions = query.scalars().all()

    return [
        {
            "id": p.id,
            "currency_code": p.currency_code,
            "name_en": p.name_en,
            "name_ar": p.name_ar,
            "confidence": p.confidence,
            "denomination_value": p.denomination_value,
            "is_counterfeit": p.is_counterfeit,
            "image_url": p.image_path,
            "timestamp": p.timestamp,
        }
        for p in predictions
    ]


# ------------------------------------
# Get Single Prediction
# ------------------------------------
@router.get("/{prediction_id}")
async def get_single_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = await db.execute(
        select(Prediction).filter(
            Prediction.id == prediction_id,
            Prediction.user_id == current_user.id
        )
    )
    prediction = query.scalar_one_or_none()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction


# ------------------------------------
# Clear History
# ------------------------------------
@router.delete("/clear")
async def clear_prediction_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await db.execute(
        Prediction.__table__.delete().where(Prediction.user_id == current_user.id)
    )
    await db.commit()

    # Log action
    await create_log(
        db,
        action="CLEAR_HISTORY",
        message=f"User {current_user.full_name} cleared prediction history",
        user_id=current_user.id
    )

    return {"message": "Prediction history cleared successfully"}
