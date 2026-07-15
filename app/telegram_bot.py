import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from app.config import settings
from app.db import SessionLocal
from app.models import User
from app.crypto import decrypt
from app import upbit_service as upbit

logger = logging.getLogger(__name__)


def _get_user(update: Update) -> User | None:
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        return db.query(User).filter(User.telegram_chat_id == chat_id).first()
    finally:
        db.close()


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user is None:
            return
        user.bot_enabled = True
        db.commit()
    finally:
        db.close()
    await update.message.reply_text("✅ 봇 활성화됨\n트레이딩뷰 신호 수신 시 매매를 실행합니다.")


async def cmd_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user is None:
            return
        user.bot_enabled = False
        db.commit()
    finally:
        db.close()
    await update.message.reply_text("⛔ 봇 비활성화됨\n신호가 와도 매매하지 않습니다.")


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user is None:
            return
        status = "✅ 활성화" if user.bot_enabled else "⛔ 비활성화"
        active = [p.ticker for p in user.positions if p.status == "long"]
    finally:
        db.close()

    lines = [f"상태: {status}", ""]
    if active:
        lines.append("📌 보유 포지션:")
        for ticker in active:
            price = await upbit.get_current_price(ticker)
            lines.append(f"  {ticker}: {price:,.0f}원")
    else:
        lines.append("포지션 없음")

    await update.message.reply_text("\n".join(lines))


async def cmd_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_chat_id == chat_id).first()
        if user is None:
            return
        if not user.exchange_key:
            await update.message.reply_text("거래소 API Key가 등록되어 있지 않습니다")
            return
        access_key = decrypt(user.exchange_key.encrypted_access_key)
        secret_key = decrypt(user.exchange_key.encrypted_secret_key)
    finally:
        db.close()

    balances = await upbit.get_all_balances(access_key, secret_key)
    if not balances:
        await update.message.reply_text("잔고 조회 실패")
        return

    lines = ["💰 잔고"]
    total_krw = 0.0
    for b in balances:
        currency = b.get("currency", "")
        balance = float(b.get("balance", 0))
        avg_buy = float(b.get("avg_buy_price", 0))
        if balance <= 0:
            continue
        if currency == "KRW":
            lines.append(f"  KRW: {balance:,.0f}원")
            total_krw += balance
        else:
            ticker = f"KRW-{currency}"
            price = await upbit.get_current_price(ticker)
            value = balance * price
            total_krw += value
            lines.append(f"  {currency}: {balance:.6f} ({value:,.0f}원, 평균매수 {avg_buy:,.0f}원)")

    lines.append(f"\n총 평가금액: {total_krw:,.0f}원")
    await update.message.reply_text("\n".join(lines))


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = _get_user(update)
    if user is None:
        return
    text = (
        "/start — 봇 활성화 (매매 시작)\n"
        "/stop  — 봇 비활성화 (매매 중단)\n"
        "/status — 현재 상태 및 포지션\n"
        "/balance — 업비트 잔고 조회\n"
        "/help — 도움말"
    )
    await update.message.reply_text(text)


def build_app() -> Application:
    app = Application.builder().token(settings.telegram_bot_token).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("stop", cmd_stop))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("balance", cmd_balance))
    app.add_handler(CommandHandler("help", cmd_help))
    return app
