# KTX 빈자리 알림

2026-10-05 **남원 → 오송**, **15:00~17:00 출발** KTX **일반실**에 자리가 나면 알려주는 스크립트입니다.
조회만 하므로 코레일 로그인은 필요 없고, 예매는 알림을 받은 뒤 코레일톡에서 직접 하시면 됩니다.

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r korail_alert/requirements.txt
python korail_alert/ktx_alert.py
```

휴대폰으로 알림 받기 (선택):

- **ntfy** (가장 간단): 휴대폰에 ntfy 앱 설치 → 남이 추측하기 어려운 토픽 이름 구독 →
  `NTFY_TOPIC=그-토픽-이름 python korail_alert/ktx_alert.py`
- **텔레그램**: `TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... python korail_alert/ktx_alert.py`

다른 조건: `--dep 서울 --arr 부산 --date 20261010 --start 0800 --end 1000 --interval 90`

- 기본 60초(+랜덤) 간격으로 조회합니다. 너무 짧게 하면 코레일에서 차단될 수 있습니다.
- 같은 열차는 다시 매진됐다가 풀릴 때만 재알림합니다. 감시 시간대가 지나면 자동 종료합니다.
- 컴퓨터가 켜져 있고 스크립트가 실행 중이어야 동작합니다.
