"""
Economic calendar via the free ForexFactory weekly JSON feed (FairEconomy).
Returns today's HIGH-impact events for the currencies we care about.
Degrades gracefully: returns None if the feed can't be reached so the
card still shows the bias.
"""
import requests
from datetime import datetime
from config import TZ, RELEVANT_CURRENCIES

FEED = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"


def get_today_high_impact():
    try:
        r = requests.get(FEED, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        data = r.json()
    except Exception as ex:
        print("Calendar fetch failed:", ex)
        return None

    today = datetime.now(TZ).date()
    events = []
    for e in data:
        if str(e.get("impact", "")).lower() != "high":
            continue
        cur = e.get("country") or e.get("currency")
        if cur not in RELEVANT_CURRENCIES:
            continue
        raw = e.get("date")
        try:
            dt = datetime.fromisoformat(raw).astimezone(TZ)
        except Exception:
            continue
        if dt.date() != today:
            continue
        events.append({"time": dt, "title": e.get("title", ""), "currency": cur})

    events.sort(key=lambda x: x["time"])
    return events
