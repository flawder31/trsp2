from pydantic import BaseModel, Field, EmailStr, validator
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(...)
    age: Optional[int] = Field(None, ge=1, le=150)
    is_subscribed: Optional[bool] = Field(False)
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Имя не может быть пустым')
        return v.strip()


class Product(BaseModel):
    product_id: int
    name: str
    category: str
    price: float
    
    @validator('price')
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError('Цена должна быть положительной')
        return v


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class SessionData(BaseModel):
    user_id: str
    timestamp: int


class UserProfile(BaseModel):
    user_id: str
    username: str
    email: str