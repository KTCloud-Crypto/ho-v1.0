import logging
from fastapi import APIRouter, Request
from app.state import state
from app import upbit_service as upbit
from app.config import settings
from telegram import Bot

logger = logging.getLogger(__name__)
router = APIRouter()


async def _notify(text: str):
    try:
        bot = Bot(token=settings.telegram_bot_token)
        await bot.send_message(chat_id=settings.telegram_chat_id, text=text)
    except Exception as e:
        logger.error(f"텔레그램 알림 실패: {e}")


@router.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    action = body.get("action", "").lower()   # "buy" | "sell"
    ticker = body.get("ticker", "").upper()    # "KRW-BTC"

    if not action or not ticker:
        return {"status": "ignored", "reason": "action/ticker 누락"}

    if not state.enabled:
        return {"status": "ignored", "reason": "봇 비활성화 상태"}

    if action == "buy":
        if state.positions.get(ticker) == "long":
            return {"status": "ignored", "reason": f"{ticker} 이미 보유 중"}

        result = await upbit.buy_market_order(ticker)
        if result:
            state.positions[ticker] = "long"
            price = await upbit.get_current_price(ticker)
            await _notify(f"✅ 매수 완료\n{ticker}\n현재가: {price:,.0f}원")
            logger.info(f"매수 완료: {ticker} {result}")
        else:
            await _notify(f"❌ 매수 실패: {ticker}")
            logger.error(f"매수 실패: {ticker} {result}")

    elif action == "sell":
        if state.positions.get(ticker) != "long":
            return {"status": "ignored", "reason": f"{ticker} 보유 포지션 없음"}

        result = await upbit.sell_market_order(ticker)
        if result:
            state.positions[ticker] = None
            price = await upbit.get_current_price(ticker)
            await _notify(f"✅ 매도 완료\n{ticker}\n현재가: {price:,.0f}원")
            logger.info(f"매도 완료: {ticker} {result}")
        else:
            await _notify(f"❌ 매도 실패: {ticker}")
            logger.error(f"매도 실패: {ticker} {result}")

    else:
        return {"status": "ignored", "reason": f"알 수 없는 action: {action}"}

    return {"status": "ok", "action": action, "ticker": ticker}
