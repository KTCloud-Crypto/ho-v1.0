# 서버 배포 순서 (Ubuntu, 네이버 클라우드)

## 1. 코드 받기
```bash
git clone https://github.com/KTCloud-Crypto/cryptrade.git
cd cryptrade
```

## 2. Docker / Docker Compose 설치
```bash
apt update && apt install -y docker.io docker-compose-plugin
```

## 3. .env 파일 생성
```bash
cp .env_example .env
nano .env
```
아래 내용 입력:
```
TELEGRAM_BOT_TOKEN=봇토큰

DATABASE_URL=postgresql://postgres:postgres@db:5432/cryptrade
JWT_SECRET=랜덤한_긴_문자열
MASTER_ENCRYPTION_KEY=파이썬에서_Fernet.generate_key()로_생성한_값
```

`MASTER_ENCRYPTION_KEY` 생성:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 4. 실행
```bash
docker compose up --build -d
docker compose ps
curl http://localhost:8000/health
```

## 5. 트레이딩뷰 웹훅 URL

각 사용자는 회원가입/로그인 후 `GET /users/me/webhook-url`로 자신의 웹훅 URL을 확인해서 사용한다.
```
https://<서버주소>/webhook/{본인 토큰}
```
웹훅 메시지 형식:
```json
{"action": "buy", "ticker": "KRW-BTC"}
{"action": "sell", "ticker": "KRW-BTC"}
```

## 로그 확인
```bash
docker compose logs -f app
```
