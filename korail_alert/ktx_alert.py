"""코레일 KTX 빈자리 알림.

기본값: 2026-10-05, 남원 -> 오송, 15:00~17:00 출발 KTX 일반실.
조건에 맞는 일반실 좌석이 생기면 터미널 알림 + (설정 시) 휴대폰 푸시를 보낸다.

    pip install -r korail_alert/requirements.txt
    python korail_alert/ktx_alert.py

휴대폰 푸시 (선택):
    NTFY_TOPIC=<내-토픽>                      -> ntfy 앱에서 같은 토픽 구독
    TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=...  -> 텔레그램 봇 메시지
"""
import argparse
import os
import random
import sys
import time
from datetime import datetime

import requests
from korail2 import Korail, KorailError, NoResultsError, TrainType


def parse_args():
    p = argparse.ArgumentParser(description="KTX 일반실 빈자리 알림")
    p.add_argument("--dep", default="남원", help="출발역 (기본: 남원)")
    p.add_argument("--arr", default="오송", help="도착역 (기본: 오송)")
    p.add_argument("--date", default="20261005", help="출발일 yyyyMMdd (기본: 20261005)")
    p.add_argument("--start", default="1500", help="출발 시각 하한 HHMM (기본: 1500)")
    p.add_argument("--end", default="1700", help="출발 시각 상한 HHMM (기본: 1700)")
    p.add_argument("--interval", type=int, default=60, help="조회 간격(초), 너무 짧게 하지 말 것 (기본: 60)")
    p.add_argument("--once", action="store_true", help="한 번만 조회하고 종료")
    return p.parse_args()


def notify(message):
    print("\a" + message, flush=True)

    topic = os.environ.get("NTFY_TOPIC")
    if topic:
        try:
            requests.post(f"https://ntfy.sh/{topic}", data=message.encode("utf-8"),
                          headers={"Title": "KTX seat available", "Priority": "urgent"}, timeout=10)
        except requests.RequestException as e:
            print(f"[ntfy 전송 실패] {e}", file=sys.stderr)

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        try:
            requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          data={"chat_id": chat_id, "text": message}, timeout=10)
        except requests.RequestException as e:
            print(f"[텔레그램 전송 실패] {e}", file=sys.stderr)


def fmt(t):
    return f"{t[:2]}:{t[2:4]}"


def find_trains(korail, args):
    """시간대 안에 출발하는 KTX 목록을 (열차, 일반실 가능 여부)로 돌려준다."""
    try:
        trains = korail.search_train(args.dep, args.arr, args.date, args.start + "00",
                                     train_type=TrainType.KTX, include_no_seats=True)
    except NoResultsError:
        return []
    end = args.end + "00"
    return [(t, t.has_general_seat()) for t in trains if t.dep_time <= end]


def main():
    args = parse_args()
    korail = Korail("", "", auto_login=False)  # 조회만 하므로 로그인 불필요
    notified = set()

    print(f"{args.date} {args.dep}->{args.arr} {fmt(args.start)}~{fmt(args.end)} KTX 일반실 감시 시작 "
          f"({args.interval}초 간격, Ctrl+C로 종료)")

    while True:
        now = datetime.now()
        if now.strftime("%Y%m%d%H%M") > args.date + args.end:
            print("감시 시간대가 지나서 종료합니다.")
            return

        try:
            results = find_trains(korail, args)
            status = ", ".join(f"{t.train_type_name} {t.train_no} {fmt(t.dep_time)}"
                               f"{'(가능)' if ok else '(매진)'}" for t, ok in results) or "해당 시간대 열차 없음"
            print(f"[{now:%H:%M:%S}] {status}", flush=True)

            for t, ok in results:
                key = t.train_no
                if ok and key not in notified:
                    notify(f"🚄 {t.train_type_name} {t.train_no} {args.dep} {fmt(t.dep_time)} -> "
                           f"{args.arr} {fmt(t.arr_time)} 일반실 예매 가능! 코레일톡에서 바로 예매하세요.")
                    notified.add(key)
                elif not ok:
                    notified.discard(key)  # 다시 매진되면, 다음에 풀릴 때 또 알림
        except (KorailError, requests.RequestException, ValueError) as e:
            print(f"[{now:%H:%M:%S}] 조회 실패: {e}", file=sys.stderr, flush=True)

        if args.once:
            return
        time.sleep(args.interval + random.uniform(0, args.interval * 0.3))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n종료합니다.")
