from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    fullname: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr

    class Config:
        from_attributes = True
