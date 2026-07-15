# 모듈 연동 규약

`app/routers/webhook.py`, `app/routers/trades.py`, `app/telegram_bot.py`, `app/upbit_service.py`는 인증/DB 계층이 아래 인터페이스만 만족하면 구현 방식이 바뀌어도 그대로 동작한다. 로그인/회원가입/DB 구조를 다시 설계하는 경우 이 문서 기준으로 맞추면 연동 지점에서 충돌이 나지 않는다.

## 1. User 모델 필수 필드

DB 모델(테이블명·ORM 방식은 무관)이 아래 컬럼을 제공해야 한다.

| 필드 | 타입 | 용도 |
|---|---|---|
| `id` | int/PK | FK 참조 기준 |
| `webhook_token` | str, unique | `/webhook/{token}` 라우팅에서 사용자 식별 |
| `bot_enabled` | bool | 매매 신호 수신 여부 on/off |
| `telegram_chat_id` | str, nullable | 텔레그램 알림 발송 대상, 봇 명령어 사용자 식별 |
| `exchange_key` | 연관 객체 (1:1) | 아래 2번 참고 |

## 2. ExchangeKey (거래소 API Key)

- `user_id`로 `User`와 1:1 관계
- `encrypted_access_key`, `encrypted_secret_key` — 저장 시 반드시 암호화. 복호화 함수는 `app/crypto.py`의 `encrypt(str) -> str` / `decrypt(str) -> str` 시그니처를 그대로 쓰거나, 동일 시그니처로 교체
- `webhook.py`, `telegram_bot.py`에서 `user.exchange_key.encrypted_access_key` / `encrypted_secret_key` 형태로 접근하므로, 필드명을 바꾸면 두 파일의 접근 코드도 같이 수정해야 함

## 3. Position / Trade 모델

포지션 중복 매수/매도 방지 및 거래내역 조회에 필요. `user_id`, `ticker` 조합으로 조회 가능해야 함(현재는 `(user_id, ticker)` unique).

- `Position.status`: `"long"` 또는 `None`
- `Trade`: `user_id`, `ticker`, `action`(buy/sell), `price`, `volume`, `status`(success/failed), `created_at`

## 4. 인증 의존성 (`get_current_user`)

FastAPI `Depends`로 주입되는 함수가 다음 시그니처를 유지해야 `app/routers/users.py`, `app/routers/trades.py`가 그대로 동작한다.

```python
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    ...
```

- 반환값은 위 1번 필드를 가진 `User` ORM 인스턴스(또는 동일 속성을 가진 객체)
- 인증 실패 시 `HTTPException(status_code=401)`

## 5. DB 세션 의존성 (`get_db`)

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

SQLAlchemy `Session`을 yield하는 형태를 유지하면 라우터 코드 수정 없이 그대로 재사용 가능.

## 6. 변경 시 체크리스트

인증/DB를 새로 구현했다면 아래만 확인하면 됨:

- [ ] `POST /webhook/{token}` 호출 시 `token`으로 사용자 조회가 되는가
- [ ] `user.exchange_key`로 암/복호화된 키에 접근 가능한가
- [ ] `get_current_user`가 `/users/me`, `/positions`, `/trades`에서 정상 동작하는가
- [ ] 텔레그램 `chat_id` → `User` 역조회가 되는가 (`app/telegram_bot.py`)
