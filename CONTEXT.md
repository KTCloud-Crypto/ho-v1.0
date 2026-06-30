# hohoupbit 현재 상태 컨텍스트

## 프로젝트 개요
FastAPI 기반 Upbit 자동매매 봇. TradingView 웹훅 수신 → Upbit 주문 → 텔레그램 알림.

---

## 서버 환경
- **서버 도메인**: `frontline.p-e.kr` (SSL 인증서 있음)
- **서버 IP**: `101.79.23.117`
- **FastAPI 포트**: `8000`
- **웹훅 URL**: `https://frontline.p-e.kr/webhook` 또는 `https://101.79.23.117/webhook` (둘 다 작동)
- **nginx**: `/etc/nginx/sites-available/frontline` (symlink) → `/webhook` location → `localhost:8000`
- **서버 실행**: `nohup uvicorn main:app --host 0.0.0.0 --port 8000 >> /tmp/hohoupbit.log 2>&1 &`
- **로그**: `/tmp/hohoupbit.log`

---

## 인증 정보 (.env)
```
UPBIT_ACCESS_KEY=x2cWwgqZQqlyeJxGTYpmJbN1wuRfb1lP3wDQsqz6
UPBIT_SECRET_KEY=w2dOUwdPxQSykGL9xd9uHt5fsBWjixzU6UMfiSKO
TELEGRAM_BOT_TOKEN=8639258768:AAGu3ap6L385YcZAvUOIfa0xWKN0xVWsfUk
TELEGRAM_CHAT_ID=5221080267
```

---

## 핵심 파일 현재 상태

### app/state.py
```python
@dataclass
class AppState:
    enabled: bool = True   # 서버 시작 시 자동 활성화
    positions: dict = field(default_factory=dict)  # {"KRW-BTC": "long"}
state = AppState()
```

### app/webhook.py 주요 로직
- `await request.body()` → raw body 로깅
- `json.loads(raw)` 로 파싱 (request.json() 사용 안 함 - 스트림 2중 소비 버그)
- symbol 변환: `body.get("ticker") or body.get("symbol")` → suffix 제거 → KRW- 접두사 추가
  - 제거 suffix 목록: `("USDT", "USD", "BUSD", "PERP", "KRW")`
  - 예: `ONGKRW` → `KRW-ONG`, `BTCUSDT` → `KRW-BTC`
- 매수: `state.positions.get(ticker) == "long"` 이면 무시 (중복 방지)
- 매도: `state.positions.get(ticker) != "long"` 이면 무시

### app/upbit_service.py 현재 상태 (호가 기반 지정가)
```python
BUY_RATIO = 0.9995

# 매수: 매도1호가로 지정가 주문
async def buy_market_order(ticker):
    ask_price = orderbook['orderbook_units'][0]['ask_price']
    volume = round(krw * BUY_RATIO / ask_price, 8)
    result = upbit.buy_limit_order(ticker, ask_price, volume)

# 매도: 매수1호가로 지정가 주문
async def sell_market_order(ticker):
    bid_price = orderbook['orderbook_units'][0]['bid_price']
    qty = get_balance_coin(ticker)
    result = upbit.sell_limit_order(ticker, bid_price, qty)
```
- 함수명은 `buy_market_order`/`sell_market_order` 그대로 유지 (webhook.py 호환)
- 실제로는 호가 기반 지정가 주문

### 텔레그램 알림 형식
```
✅ 매수 완료
KRW-ONG
현재가: 82.87원   ← 소수점 2자리
```

---

## TradingView 웹훅 설정

### 정상 작동 중인 티커
| 티커 | 웹훅 메시지 형식 | 변환 결과 |
|------|-----------------|-----------|
| ONGKRW | `{"action":"buy","symbol":"ONGKRW","price":"{{close}}"}` | KRW-ONG ✅ |
| TAIKOKRW | `{"action":"{{strategy.order.action}}","symbol":"TAIKOKRW","price":"{{close}}"}` | KRW-TAIKO ✅ |

### 제외된 티커
| 티커 | 이유 |
|------|------|
| AIKRW | Upbit KRW-AI 마켓이 시장가/지정가 지원 안 함 (신규 코인 제한) → 모니터링 안 함 |

### TradingView 중복 신호 문제
- TradingView가 동일 신호를 IP 2개에서 각각 전송 (`52.32.178.7`, `34.212.75.30`)
- `state.positions` 체크로 자동 중복 방지됨

---

## 알려진 이슈 및 해결 내역

| 이슈 | 원인 | 해결 |
|------|------|------|
| 405 Method Not Allowed | nginx에 /webhook location 없음 | nginx config에 proxy_pass 추가 |
| ONGKRW → KRW-ONGKRW 오변환 | suffix 목록에 KRW 없음 | `("USDT","USD","BUSD","PERP","KRW")` 추가 |
| 서버 재시작 시 포지션 초기화 | in-memory state | 현재 미해결, 주의 필요 |
| KRW-AI 매수 실패 | `not_supported_ord_type` (Upbit 제한) | AI 티커 모니터링 제외 |
| 슬리피지 문제 | 시장가 주문 | 호가 기반 지정가 주문으로 변경 |

---

## 서버 재시작 방법
```bash
pkill -f uvicorn
cd /root/hohoupbit
source venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 >> /tmp/hohoupbit.log 2>&1 &
```

## 주의사항
- 서버 재시작 시 `state.positions` 초기화됨 → 실제 코인 보유 중이면 sell 신호 무시될 수 있음
- TAIKO 알림 중 일부가 구포맷(plain text)으로 오는 경우 있음 → 트뷰 알림 설정 재확인 필요
