from datetime import datetime
from pydantic import BaseModel, EmailStr


class SignupIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    telegram_chat_id: str | None
    bot_enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdateIn(BaseModel):
    telegram_chat_id: str | None = None
    bot_enabled: bool | None = None


class ExchangeKeyIn(BaseModel):
    access_key: str
    secret_key: str


class WebhookUrlOut(BaseModel):
    webhook_token: str
    webhook_path: str


class PositionOut(BaseModel):
    ticker: str
    status: str | None
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeOut(BaseModel):
    ticker: str
    action: str
    price: float | None
    volume: float | None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
