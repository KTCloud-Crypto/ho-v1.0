# Cryptrade (KTcloud_Crypto)

주식(암호화폐) 매매 신호와 거래 내역을 관리하는 웹 프로그램의 백엔드.
FastAPI + PostgreSQL 기반으로, 사용자별 거래소 API Key 등록, 자신의 웹훅 URL을 통한 TradingView 신호 수신, 거래 내역/포지션 조회, 텔레그램 알림을 제공한다.

## Docker 실행

FastAPI 서버와 PostgreSQL DB를 Docker Compose로 함께 실행합니다.

```bash
cp .env_example .env
# .env에 TELEGRAM_BOT_TOKEN, JWT_SECRET, MASTER_ENCRYPTION_KEY 입력
docker compose up --build -d
```

실행 확인:

```bash
docker compose ps
curl http://localhost:8000/health
```

정상 응답:

```json
{"status":"ok"}
```

## 자주 쓰는 명령어

```bash
# 컨테이너 상태 확인
docker compose ps

# 로그 확인
docker compose logs -f app
docker compose logs -f db

# 컨테이너 중지
docker compose down

# 컨테이너와 DB 볼륨까지 삭제
docker compose down -v
```

DB 테이블 확인:

```bash
docker compose exec db psql -U postgres -d cryptrade -c '\dt'
```

## API 개요

- `POST /auth/signup`, `POST /auth/login` — 회원가입/로그인 (JWT 발급)
- `GET/PUT /users/me` — 내 프로필 조회/수정 (`telegram_chat_id`, `bot_enabled`)
- `POST /users/me/exchange-key` — Upbit API Key 등록 (서버에 암호화 저장)
- `GET /users/me/webhook-url` — 내 전용 TradingView 웹훅 URL 조회
- `POST /webhook/{token}` — TradingView 웹훅 수신 (사용자별 고유 URL)
- `GET /positions`, `GET /trades` — 내 포지션 / 거래 내역 조회

모든 `/users/*`, `/positions`, `/trades` 요청은 `Authorization: Bearer <JWT>` 헤더가 필요합니다.

## TradingView 웹훅 설정

1. 로그인 후 `GET /users/me/webhook-url`로 본인 웹훅 URL을 확인한다.
2. TradingView 알림(Alert) 설정의 웹훅 URL에 `https://<서버주소>/webhook/{내 토큰}`을 입력한다.
3. 메시지 형식(JSON, 둘 다 지원):

```json
{"action": "buy", "ticker": "KRW-BTC"}
{"action": "sell", "ticker": "KRW-BTC"}
```

또는 TradingView 기본 plain text 템플릿(한국어/영어)도 자동 인식된다.

## 텔레그램 연동

1. 텔레그램에서 봇과 대화를 시작해 본인 chat_id를 확인한다.
2. `PUT /users/me` 요청으로 `telegram_chat_id`를 등록한다.
3. 이후 `/start`, `/stop`, `/status`, `/balance`, `/help` 명령으로 본인 계정만 제어/조회할 수 있다.
