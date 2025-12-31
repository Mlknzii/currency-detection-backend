from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey(
        "users.id", ondelete="CASCADE"), nullable=False)
    currency_code = Column(String(10), nullable=False)           # e.g., USD
    confidence = Column(Float, nullable=False)
    # English result
    name_en = Column(String(100), nullable=False)
    # Arabic result
    name_ar = Column(String(100), nullable=False)
    # denomination value, e.g., 100, 200, 500, 1000
    denomination_value = Column(Integer, nullable=True)
    is_counterfeit = Column(Boolean, nullable=False)  # 0 = False, 1 = True
    # stored file path
    image_path = Column(String(255), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
