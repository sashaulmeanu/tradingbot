import os
from zoneinfo import ZoneInfo

# --- Telegram (set these in Railway env vars, NOT in code) ---
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# --- Schedule ---
RUN_AT = os.getenv("RUN_AT", "09:00")            # HH:MM local, before London open
TIMEZONE = os.getenv("TIMEZONE", "Europe/Bucharest")
TEST_ON_START = os.getenv("TEST_ON_START", "true").lower() == "true"

# --- Backtest ---
RUN_BACKTEST = os.getenv("RUN_BACKTEST", "false").lower() == "true"
CUTOFF_HOUR = int(os.getenv("CUTOFF_HOUR", "10"))   # HOD/LOD built before this hour


def _to_min(s):
    hh, mm = s.split(":")
    return int(hh) * 60 + int(mm)


# Trading window: new entries only between CUTOFF_HOUR and ENTRY_CUTOFF;
# an open trade may run until CLOSE_AT, then it's closed at market.
ENTRY_CUTOFF_MIN = _to_min(os.getenv("ENTRY_CUTOFF", "17:00"))
CLOSE_MIN = _to_min(os.getenv("CLOSE_AT", "22:00"))

# Data source for backtest: "yfinance" (~60d, FX only useful) or
# "dukascopy" (months of history incl. indices). Dukascopy is slower to fetch.
DATA_SOURCE = os.getenv("DATA_SOURCE", "yfinance").lower()
DUKAS_WEEKS = int(os.getenv("DUKAS_WEEKS", "16"))

# Realistic round-trip cost per trade, in PRICE units (spread + commission +
# slippage). Set to match your broker. Converted to R per trade using each
# trade's own stop distance, then subtracted from the result.
APPLY_COSTS = os.getenv("APPLY_COSTS", "true").lower() == "true"
COST = {
    "GBPUSD": float(os.getenv("COST_GBPUSD", "0.00010")),   # ~1 pip
    "UK100": float(os.getenv("COST_UK100", "1.5")),          # ~1.5 index points
    "DAX": float(os.getenv("COST_DAX", "2.0")),              # ~2 index points
}

TZ = ZoneInfo(TIMEZONE)

# --- Instruments: friendly name -> Yahoo Finance symbol ---
# UK100 = FTSE 100 cash, DAX = GER40 cash. For BIAS (direction/structure)
# the cash index is fine; it tracks the CFD you trade closely enough.
INSTRUMENTS = {
    "GBPUSD": "GBPUSD=X",
    "UK100": "^FTSE",
    "DAX": "^GDAXI",
}

# Currencies whose high-impact news matters for the instruments above
RELEVANT_CURRENCIES = {"GBP", "USD", "EUR"}

# Swing detection: how many candles on each side define a pivot
SWING_STRENGTH = 2

# Minutes to avoid trading around a high-impact event
NEWS_BUFFER_MIN = 30
