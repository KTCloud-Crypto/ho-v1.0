import asyncio
import pyupbit
from app.config import settings

BUY_RATIO = 0.9995  # 수수료 고려 99.95%

_upbit: pyupbit.Upbit | None = None


def get_upbit() -> pyupbit.Upbit:
    global _upbit
    if _upbit is None:
        _upbit = pyupbit.Upbit(settings.upbit_access_key, settings.upbit_secret_key)
    return _upbit


async def get_balance_krw() -> float:
    loop = asyncio.get_event_loop()
    upbit = get_upbit()
    result = await loop.run_in_executor(None, lambda: upbit.get_balance("KRW"))
    return float(result or 0)


async def get_balance_coin(ticker: str) -> float:
    loop = asyncio.get_event_loop()
    upbit = get_upbit()
    coin = ticker.replace("KRW-", "")
    result = await loop.run_in_executor(None, lambda: upbit.get_balance(coin))
    return float(result or 0)


async def get_current_price(ticker: str) -> float:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: pyupbit.get_current_price(ticker))
    return float(result or 0)


async def buy_market_order(ticker: str) -> dict:
    loop = asyncio.get_event_loop()
    upbit = get_upbit()
    krw = await get_balance_krw()
    amount = krw * BUY_RATIO
    result = await loop.run_in_executor(None, lambda: upbit.buy_market_order(ticker, amount))
    return result


async def sell_market_order(ticker: str) -> dict:
    loop = asyncio.get_event_loop()
    upbit = get_upbit()
    coin = ticker.replace("KRW-", "")
    qty = await get_balance_coin(ticker)
    result = await loop.run_in_executor(None, lambda: upbit.sell_market_order(ticker, qty))
    return result


async def get_all_balances() -> list[dict]:
    loop = asyncio.get_event_loop()
    upbit = get_upbit()
    result = await loop.run_in_executor(None, upbit.get_balances)
    return result or []
