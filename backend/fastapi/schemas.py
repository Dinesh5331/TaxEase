from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


# ── Auth ────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    debug: bool = False


class ChatResponse(BaseModel):
    answer: str


# ── Health ───────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    chunk_count: int
    forms_indexed: list[str]
