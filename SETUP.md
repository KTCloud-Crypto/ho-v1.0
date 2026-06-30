# 서버 배포 순서 (Ubuntu, 네이버 클라우드 101.79.23.117)

## 1. 코드 받기
```bash
git clone https://github.com/DeanJun/hohoupbit.git
cd hohoupbit
```

## 2. Python 환경 세팅
```bash
apt update && apt install -y python3 python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. .env 파일 생성
```bash
cp .env_example .env
nano .env
```
아래 내용 입력:
```
UPBIT_ACCESS_KEY=발급받은키
UPBIT_SECRET_KEY=발급받은키
TELEGRAM_BOT_TOKEN=봇토큰
TELEGRAM_CHAT_ID=채팅ID
```

## 4. 실행 테스트
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 5. systemd 서비스 등록 (자동 실행)
```bash
nano /etc/systemd/system/hohoupbit.service
```
아래 내용 입력:
```ini
[Unit]
Description=HohoUpbit Trading Bot
After=network.target

[Service]
User=root
WorkingDirectory=/root/hohoupbit
ExecStart=/root/hohoupbit/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload
systemctl enable hohoupbit
systemctl start hohoupbit
systemctl status hohoupbit
```

## 6. 트레이딩뷰 웹훅 URL
```
http://101.79.23.117:8000/webhook
```
웹훅 메시지 형식:
```json
{"action": "buy", "ticker": "KRW-BTC"}
{"action": "sell", "ticker": "KRW-BTC"}
```

## 로그 확인
```bash
journalctl -u hohoupbit -f
```
