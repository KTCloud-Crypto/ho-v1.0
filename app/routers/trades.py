from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Position, Trade
from app.schemas import PositionOut, TradeOut
from app.security import get_current_user

router = APIRouter(tags=["trades"])


@router.get("/positions", response_model=list[PositionOut])
def list_positions(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Position)
        .filter(Position.user_id == current_user.id)
        .order_by(Position.updated_at.desc())
        .all()
    )


@router.get("/trades", response_model=list[TradeOut])
def list_trades(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return (
        db.query(Trade)
        .filter(Trade.user_id == current_user.id)
        .order_by(Trade.created_at.desc())
        .limit(200)
        .all()
    )
