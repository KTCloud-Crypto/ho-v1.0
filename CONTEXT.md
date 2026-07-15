# Cryptrade 현재 상태 컨텍스트

## 프로젝트 개요
FastAPI 기반 Upbit 자동매매 봇. TradingView 웹훅 수신 → Upbit 주문 → 텔레그램 알림.
멀티유저 구조로 전환됨: 회원가입/로그인(JWT), 사용자별 Upbit API Key(암호화 저장), 사용자별 웹훅 URL, PostgreSQL 기반 포지션/거래내역 관리.

> ⚠️ 과거 이 문서에는 실제 Upbit API 키·시크릿, 텔레그램 봇 토큰이 평문으로 기록되어 있었습니다.
> 유출 위험이 있으므로 **해당 키들은 즉시 재발급하고**, git 히스토리에서도 제거하는 것을 권장합니다.
> 이 문서에는 더 이상 실제 인증정보를 기록하지 않습니다.

---

## 인증 정보 (.env)
`.env_example` 참고. 실제 값은 `.env`에만 저장하고 절대 커밋하지 않는다.
```
TELEGRAM_BOT_TOKEN=
DATABASE_URL=
JWT_SECRET=
MASTER_ENCRYPTION_KEY=
```

---

## 핵심 아키텍처 변경 사항 (멀티유저 전환)

### DB 모델 (`app/models.py`)
- `User`: 이메일/비밀번호, `telegram_chat_id`, `webhook_token`(사용자별 고유 웹훅), `bot_enabled`
- `ExchangeKey`: 사용자별 Upbit access/secret key (Fernet 암호화 저장, `app/crypto.py`)
- `Position`: 기존 in-memory `state.positions` 대체. `(user_id, ticker)`별 보유 상태
- `Trade`: 매수/매도 실행 결과 이력

### 인증 (`app/security.py`)
- bcrypt 비밀번호 해시, JWT 발급/검증
- `get_current_user` 의존성으로 `/users/*`, `/positions`, `/trades` 보호

### 웹훅 (`app/routers/webhook.py`)
- URL 경로에 `{token}`을 받아 `User.webhook_token`으로 사용자 식별
- 파싱 로직(JSON/plain text fallback, suffix 제거)은 기존과 동일
  - 정규식: `(?:order|오더)\s+(buy|sell).*?(?:on|필드 온)\s+(\w+)`
  - 제거 suffix 목록: `("USDT", "USD", "BUSD", "PERP", "KRW")`
- 매수: `Position.status == "long"` 이면 무시 (중복 방지)
- 매도: `Position.status != "long"` 이면 무시
- 매수/매도 성공/실패 모두 `Trade` 테이블에 기록

### app/upbit_service.py (호가 기반 지정가)
- 함수들이 전역 키 대신 `access_key`/`secret_key`를 인자로 받도록 변경 (사용자별 키 사용)
```python
BUY_RATIO = 0.9995

# 매수: 매도1호가로 지정가 주문
async def buy_market_order(ticker, access_key, secret_key): ...

# 매도: 매수1호가로 지정가 주문
async def sell_market_order(ticker, access_key, secret_key): ...
```
- pyupbit `get_orderbook()` 반환 타입 호환 처리 (신버전 dict, 구버전 list) 유지

### 텔레그램 (`app/telegram_bot.py`)
- 고정 `chat_id` 비교 대신, `update.effective_chat.id`로 `User` 테이블 조회 후 해당 유저 컨텍스트로 명령 실행
- `/start /stop /status /balance /help` — 모두 본인 계정 데이터만 조작/조회

---

## TradingView 웹훅 설정

### 지원하는 메시지 포맷 (둘 다 자동 처리)

**JSON 형식**:
```json
{"action":"{{strategy.order.action}}","symbol":"{{ticker}}","price":"{{close}}"}
```

**Plain text 기본 템플릿** (한국어/영어 둘 다 OK):
```
Date RSI Strategy v3: 오더 {{strategy.order.action}} @ {{strategy.order.contracts}} 필드 온 {{ticker}}. 뉴 스트래티지 포지션은 {{strategy.position_size}}
```
- `price` 필드는 사용 안 함 (orderbook에서 직접 조회하므로 불필요)
- 사용자는 `GET /users/me/webhook-url`로 발급받은 URL을 TradingView 알림 웹훅에 등록한다.

### 제외된 티커
| 티커 | 이유 |
|------|------|
| KRW-AI | `not_supported_ord_type` (신규 코인 Upbit 제한) → 모니터링 안 함 |

### TradingView 중복 신호 문제
- TradingView가 동일 신호를 IP 2개에서 각각 전송 (`52.32.178.7`, `34.212.75.30`)
- `Position` 테이블 체크로 자동 중복 방지됨

---

## 알려진 이슈 및 해결 내역

| 이슈 | 원인 | 해결 |
|------|------|------|
| 405 Method Not Allowed | nginx에 /webhook location 없음 | nginx config에 proxy_pass 추가 |
| ONGKRW → KRW-ONGKRW 오변환 | suffix 목록에 KRW 없음 | `("USDT","USD","BUSD","PERP","KRW")` 추가 |
| KRW-AI 매수 실패 | `not_supported_ord_type` (Upbit 제한) | AI 티커 모니터링 제외 |
| 슬리피지 문제 | 시장가 주문 | 호가 기반 지정가 주문으로 변경 |
| 500 에러 (KRW-AHT, KRW-MOC 등 신규 티커) | pyupbit get_orderbook() dict 반환으로 변경 | isinstance 체크로 list/dict 모두 처리 |
| 서버 재시작 포지션 초기화 → sell 무시, KRW 묶임 | in-memory state | PostgreSQL `Position` 테이블로 영구 저장하여 근본 해결 |
| plain text 파싱 실패 (0G, MIRA 등) | 정규식이 영어 "order"만 처리 | 한국어 "오더", "필드 온"도 포함하도록 정규식 수정 |
| UnderMinTotalBid | 포지션 초기화로 KRW 묶임 → 잔고 없이 매수 시도 | Position DB화로 근본 원인 해결 |
| **API 키 평문 커밋 (해결됨)** | CONTEXT.md에 실키 기록 | 문서에서 제거, `.env`로만 관리 + DB 저장 시 Fernet 암호화 |

---

## 서버 재시작 방법 (Docker Compose)
```bash
docker compose down
docker compose up --build -d
docker compose logs -f app
```

## 주의사항
- 포지션은 이제 PostgreSQL에 영구 저장되므로 서버/컨테이너 재시작 시에도 유실되지 않음
- `locked` 잔고(미체결 지정가 주문)는 `get_balance()` 기준으로 잡히지 않을 수 있음
- KRW 잔고 부족 시 `UnderMinTotalBid` 에러로 매수 실패 (Upbit 최소 주문 5,000원)
