# 설계 문서 (Cryptrade 백엔드)

TradingView 웹훅 기반 Upbit 자동매매 봇을 멀티유저 구조로 확장한 FastAPI 백엔드의 설계, API, 진행 상태를 정리한 문서.

## 1. 전체 구조

```
main.py                  FastAPI 앱, lifespan(DB 테이블 생성, 텔레그램 봇 폴링), 라우터 등록
app/
  config.py               환경변수 설정 (pydantic-settings)
  db.py                   SQLAlchemy engine/session, get_db 의존성
  models.py               User / ExchangeKey / Position / Trade
  schemas.py               Pydantic 요청/응답 스키마
  security.py              비밀번호 해시, JWT 발급/검증, get_current_user 의존성
  crypto.py                Fernet 암복호화 (거래소 API Key 저장용)
  upbit_service.py         Upbit 매수/매도/잔고 조회 (유저별 access/secret key 인자로 받음)
  telegram_bot.py          텔레그램 명령(/start /stop /status /balance /help), chat_id로 유저 조회
  routers/
    auth.py                 회원가입/로그인
    users.py                 프로필, 거래소 API Key 등록, 웹훅 URL 발급
    webhook.py                TradingView 웹훅 수신 → 매매 실행
    trades.py                  거래내역/포지션 조회
```

DB는 PostgreSQL, ORM은 SQLAlchemy. 실행은 Docker Compose(`app` + `db` 2개 서비스).

모듈 간 연동 규약(인증/DB를 다시 구현할 때 지켜야 할 인터페이스)은 [`INTEGRATION.md`](./INTEGRATION.md) 참고.

## 2. 데이터 모델

| 테이블 | 주요 컬럼 | 설명 |
|---|---|---|
| `users` | `email`, `hashed_password`, `telegram_chat_id`, `webhook_token`, `bot_enabled` | 계정. `webhook_token`은 가입 시 자동 발급(uuid4) |
| `exchange_keys` | `user_id`(1:1), `encrypted_access_key`, `encrypted_secret_key` | Fernet으로 암호화해 저장 |
| `positions` | `user_id`, `ticker`, `status`("long"/None) | `(user_id, ticker)` unique. 중복 매수/매도 방지용 |
| `trades` | `user_id`, `ticker`, `action`, `price`, `volume`, `status`, `raw_response` | 매매 실행 이력 |

## 3. API 목록

인증이 필요한 엔드포인트는 `Authorization: Bearer <JWT>` 헤더 필요.

| Method | Path | 인증 | 설명 |
|---|---|---|---|
| POST | `/auth/signup` | X | 회원가입, JWT 반환 |
| POST | `/auth/login` | X | 로그인, JWT 반환 |
| GET | `/users/me` | O | 내 프로필 조회 |
| PUT | `/users/me` | O | `telegram_chat_id`, `bot_enabled` 수정 |
| POST | `/users/me/exchange-key` | O | Upbit API Key 등록/갱신 (암호화 저장) |
| GET | `/users/me/webhook-url` | O | 내 전용 웹훅 URL 조회 |
| POST | `/webhook/{token}` | X (토큰이 인증 역할) | TradingView 신호 수신 → 매수/매도 실행 |
| GET | `/positions` | O | 내 포지션 목록 |
| GET | `/trades` | O | 내 거래내역 (최근 200건) |
| GET | `/health` | X | 헬스체크 |

Swagger UI: `http://localhost:8000/docs`

### 웹훅 요청 형식
```json
{"action": "buy", "ticker": "KRW-BTC"}
{"action": "sell", "ticker": "KRW-BTC"}
```
JSON 파싱 실패 시 TradingView 기본 plain text 템플릿(한국어/영어)도 정규식으로 파싱해서 처리한다.

## 4. 완성된 부분

- 회원가입/로그인 (JWT, bcrypt 해시)
- 사용자별 Upbit API Key 등록/암호화 저장(Fernet)
- 사용자별 고유 웹훅 URL로 TradingView 신호 라우팅
- 웹훅 수신 → Upbit 매수/매도(호가 기반 지정가 주문) → 포지션/거래내역 DB 기록 → 텔레그램 알림
- 포지션 DB화로 서버 재시작 시에도 상태 유지 (기존 in-memory 방식 대체)
- 텔레그램 명령(`/start /stop /status /balance /help`)이 chat_id 기준으로 사용자별 동작
- Docker Compose로 FastAPI + PostgreSQL 통합 실행
- TradingView 중복 신호(동일 신호가 IP 2개에서 전송되는 문제) 자동 방지 (포지션 상태 체크)

## 5. 안 된 부분 / 알려진 제약

- **React 프론트엔드 없음** — 모든 기능은 API로만 존재, UI 없음
- **텔레그램 chat_id 연결 UX 없음** — `PUT /users/me`로 수동 입력해야 함. 연결 코드/딥링크 같은 플로우 없음
- **예약 매수/매도 없음** — 텔레그램에서 즉시 명령만 가능, 스케줄링 기능 없음
- **가격 알람 기능 없음** — 순수 알림용 웹훅(매매 없이 알림만)은 미구현, 현재 웹훅은 항상 매매를 시도함
- **DB 마이그레이션 도구 없음** — `Base.metadata.create_all()`로 앱 시작 시 테이블 생성. 컬럼 추가/변경 시 수동 처리 필요 (Alembic 미도입)
- **자동 테스트 없음** — 전부 수동(Postman/Swagger)으로 검증
- **Docker 빌드 실사용 테스트 미완료** — `docker compose up --build`로 로컬 구동까지는 확인 안 됨
- **거래소는 Upbit만 지원** — 계획서의 "거래소 API Key 등록"이 다중 거래소를 뜻한다면 확장 필요
- **레이트리밋/재시도 로직 없음** — Upbit API 호출 실패 시 단순 실패 처리, 재시도 없음

## 6. 앞으로 해야 할 것 (우선순위 제안)

1. **Docker Compose 실제 구동 검증** — `docker compose up --build -d` 후 `/health`, signup→login→exchange-key→webhook 전체 플로우 확인
2. **React 프론트엔드** — 로그인/회원가입, API Key 등록, 웹훅 URL 확인, 거래내역/포지션 조회 화면
3. **텔레그램 연결 플로우** — 프론트에서 chat_id 등록 UX 설계 (예: 봇이 `/myid` 명령으로 chat_id 알려주면 프론트에서 붙여넣기)
4. **텔레그램 예약 매수/매도** — 명령 파싱 + 스케줄러(APScheduler 등) 도입 검토
5. **트레이딩뷰 가격 알람** — 매매 없이 알림만 보내는 별도 웹훅 엔드포인트 또는 `action` 값에 `alert` 추가
6. **Alembic 도입** — 스키마 변경이 잦아지기 전에 마이그레이션 체계 준비
7. **테스트 코드** — 최소한 웹훅 파싱 로직(plain text fallback, suffix 제거)에 대한 단위 테스트

## 7. 보안 주의사항

- 과거 커밋 히스토리에 실제 Upbit API 키, 텔레그램 봇 토큰이 평문으로 남아있던 적이 있음 → **해당 키들은 재발급 필요**, 신뢰할 수 없는 것으로 간주
- `.env`는 절대 커밋하지 말 것 (`.env_example`만 커밋)
- `MASTER_ENCRYPTION_KEY`가 유출되면 모든 사용자의 거래소 키가 복호화 가능해지므로, 서버 환경변수로만 관리하고 별도 채널(예: 팀 시크릿 매니저)로 공유할 것
- JWT `JWT_SECRET`도 동일하게 취급
