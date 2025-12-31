from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.auth.models import User
from app.auth.utils import get_current_user
from app.auth.schemas import UserCreate, UserLogin, UserOut, UserUpdate
from app.auth.hashing import hash_password, verify_password
from app.auth.utils import create_access_token
from app.utils.logger import create_log

router = APIRouter(prefix="/auth", tags=["Authentication"])

# -----------------------------
# Register
# -----------------------------


@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="Eready registered")

    pw = hash_password(user.password)
    new_user = User(full_name=user.full_name,
                    email=user.email, hashed_password=pw,
                    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log registration
    await create_log(db, action="REGISTER", message=f"User {new_user.full_name} registered", user_id=new_user.id)

    return new_user


# -----------------------------
# Login
# -----------------------------
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).filter(User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if not existing_user or not verify_password(user.password, existing_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": str(existing_user.id)})
    # Log login
    await create_log(db, action="LOGIN", message=f"User {existing_user.full_name} logged in", user_id=existing_user.id)
    return {"access_token": access_token, "token_type": "bearer"}


# Get current user
@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "fullname": current_user.full_name,
        "created_at": current_user.created_at
    }


# Delete user
@router.delete("/me")
async def delete_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:

        # Log action
        await create_log(db, action="DELETE_PROFILE", message=f"User {current_user.full_name} deleted profile", user_id=current_user.id)

        await db.delete(current_user)
        await db.commit()

        return {"message": "Profile deleted successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
