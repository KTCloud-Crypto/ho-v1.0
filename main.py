import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.webhook import router as webhook_router
from app.telegram_bot import build_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

_tg_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app
    _tg_app = build_app()
    await _tg_app.initialize()
    await _tg_app.start()
    await _tg_app.updater.start_polling()
    yield
    await _tg_app.updater.stop()
    await _tg_app.stop()
    await _tg_app.shutdown()


app = FastAPI(title="HohoUpbit", lifespan=lifespan)
app.include_router(webhook_router)
