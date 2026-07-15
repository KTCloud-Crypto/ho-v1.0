import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.db import Base, engine
from app.routers.auth import router as auth_router
from app.routers.users import router as users_router
from app.routers.webhook import router as webhook_router
from app.routers.trades import router as trades_router
from app.telegram_bot import build_app

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

logger = logging.getLogger(__name__)
_tg_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app
    Base.metadata.create_all(bind=engine)

    _tg_app = build_app()
    await _tg_app.initialize()
    await _tg_app.start()
    await _tg_app.updater.start_polling()
    yield
    await _tg_app.updater.stop()
    await _tg_app.stop()
    await _tg_app.shutdown()


app = FastAPI(title="Cryptrade", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(webhook_router)
app.include_router(trades_router)


@app.get("/health")
def health():
    return {"status": "ok"}
