from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_log import SystemLog


async def create_log(db: AsyncSession, action: str, message: str, user_id: int | None = None):
    """
    Stores a log entry in the database.
    Can be called from any route (e.g., login, prediction).
    """
    try:
        log_entry = SystemLog(
            user_id=user_id,
            action=action,
            message=message,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
    except Exception as e:
        # Optional: print or log to file if DB logging fails
        print(f"[SystemLog] Failed to save log: {e}")
