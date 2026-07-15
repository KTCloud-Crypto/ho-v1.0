from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, ExchangeKey
from app.schemas import UserOut, UserUpdateIn, ExchangeKeyIn, WebhookUrlOut
from app.security import get_current_user
from app.crypto import encrypt

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.telegram_chat_id is not None:
        current_user.telegram_chat_id = payload.telegram_chat_id
    if payload.bot_enabled is not None:
        current_user.bot_enabled = payload.bot_enabled
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/exchange-key", status_code=204)
def set_exchange_key(
    payload: ExchangeKeyIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    encrypted_access = encrypt(payload.access_key)
    encrypted_secret = encrypt(payload.secret_key)

    if current_user.exchange_key:
        current_user.exchange_key.encrypted_access_key = encrypted_access
        current_user.exchange_key.encrypted_secret_key = encrypted_secret
    else:
        db.add(
            ExchangeKey(
                user_id=current_user.id,
                encrypted_access_key=encrypted_access,
                encrypted_secret_key=encrypted_secret,
            )
        )
    db.commit()


@router.get("/me/webhook-url", response_model=WebhookUrlOut)
def get_webhook_url(current_user: User = Depends(get_current_user)):
    return WebhookUrlOut(
        webhook_token=current_user.webhook_token,
        webhook_path=f"/webhook/{current_user.webhook_token}",
    )
