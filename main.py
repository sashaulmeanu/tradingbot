import time
from datetime import datetime

from config import INSTRUMENTS, RUN_AT, TZ, TEST_ON_START, RUN_BACKTEST, CUTOFF_HOUR
from data import get_1h
from bias import compute_bias
from news import get_today_high_impact
from card import build_card
from notify import send


def run_once():
    biases = {}
    for name, symbol in INSTRUMENTS.items():
        try:
            df = get_1h(symbol)
            biases[name] = compute_bias(df) if (df is not None and len(df) > 20) else None
        except Exception as ex:
            print(f"{name} bias failed:", ex)
            biases[name] = None

    events = get_today_high_impact()
    card = build_card(biases, events)
    send(card)
    print("Brief done at", datetime.now(TZ).isoformat())


def main():
    print(f"Trading brief bot up. Daily run at {RUN_AT} ({TZ}).")

    if RUN_BACKTEST:
        print("RUN_BACKTEST=true -> running backtest...")
        try:
            from backtest import run_backtest
            send(run_backtest(cutoff_hour=CUTOFF_HOUR))
        except Exception as ex:
            print("Backtest failed:", ex)

    if TEST_ON_START:
        print("TEST_ON_START=true -> sending one brief now...")
        run_once()

    last_run_date = None
    while True:
        now = datetime.now(TZ)
        if now.strftime("%H:%M") == RUN_AT and now.date() != last_run_date:
            run_once()
            last_run_date = now.date()
        time.sleep(20)


if __name__ == "__main__":
    main()
