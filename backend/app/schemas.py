from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: Literal["buyer", "seller"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    created_at: datetime


class StoreCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=2000)
    category: str = Field(min_length=1, max_length=80)
    personality: str = Field(default="Considered", max_length=80)
    accent: str = Field(default="#9b7bff", max_length=16)
    published: bool = True


class StoreResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    personality: str
    accent: str
    published: bool


class ProductCreate(BaseModel):
    store_id: str
    category: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=200)
    sku: str = Field(default="", max_length=100)
    description: str = Field(default="", max_length=5000)
    price: float = Field(gt=0)
    image_url: str = Field(default="", max_length=500)
    quantity: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=80)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    sku: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=5000)
    price: float | None = Field(default=None, gt=0)
    image_url: str | None = Field(default=None, max_length=500)
    quantity: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: str
    store_id: str
    store_name: str
    category: str
    name: str
    sku: str
    description: str
    price: float
    image_url: str
    quantity: int
    is_active: bool
