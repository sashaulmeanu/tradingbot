"""
Backtest for the HOD/LOD session-reversal model:

  - Build HOD/LOD from candles before the cutoff hour (default 10:00 local).
  - After cutoff, take the FIRST sweep of LOD (-> long) or HOD (-> short):
    a candle that pierces the level but closes back inside.
  - Require an MSS (close breaks the last opposing swing) that leaves an FVG.
  - Enter on the pullback into that FVG. Stop beyond the sweep extreme.
  - Target = 2R. Max 1 trade/day.
  - Optional news filter: block entries within +/-15 min of a high-impact event.

Everything is deterministic and walks candles strictly forward (no lookahead
in outcomes). Data: 5M from yfinance (last ~60 days). For the full multi-month
sample we swap the loader for dukascopy later — the engine stays the same.
"""
import numpy as np
from smc import find_swings, detect_fvg


# ---------- single-day setup detection ----------

def _last_swing_before(swings, idx, kind):
    cands = [s for s in swings if s["kind"] == kind and s["i"] < idx]
    return cands[-1] if cands else None


def _build_long(day, s, level, swings):
    h = day["high"].values
    l = day["low"].values
    c = day["close"].values
    n = len(day)
    ref = _last_swing_before(swings, s, "high")
    if ref is None:
        return None
    m = None
    for i in range(s + 1, n):
        if c[i] > ref["price"]:
            m = i
            break
    if m is None:
        return None
    fvgs = [f for f in detect_fvg(day)
            if f["type"] == "bull" and s < f["i"] <= m + 1]
    if not fvgs:
        return None
    fvg = fvgs[-1]
    entry = fvg["top"]
    stop = float(l[s])                      # tight: just the sweep wick low
    if entry - stop <= 0:
        return None
    target = entry + 2.0 * (entry - stop)
    return {"dir": "long", "sweep_i": s, "mss_i": m, "entry": entry,
            "stop": stop, "target": target, "watch_from": m}


def _build_short(day, s, level, swings):
    h = day["high"].values
    l = day["low"].values
    c = day["close"].values
    n = len(day)
    ref = _last_swing_before(swings, s, "low")
    if ref is None:
        return None
    m = None
    for i in range(s + 1, n):
        if c[i] < ref["price"]:
            m = i
            break
    if m is None:
        return None
    fvgs = [f for f in detect_fvg(day)
            if f["type"] == "bear" and s < f["i"] <= m + 1]
    if not fvgs:
        return None
    fvg = fvgs[-1]
    entry = fvg["bottom"]
    stop = float(h[s])                      # tight: just the sweep wick high
    if stop - entry <= 0:
        return None
    target = entry - 2.0 * (stop - entry)
    return {"dir": "short", "sweep_i": s, "mss_i": m, "entry": entry,
            "stop": stop, "target": target, "watch_from": m}


def find_day_setup(day, cutoff_hour=10, entry_cutoff_min=17 * 60, strength=2):
    times = day.index
    hours = np.array([t.hour for t in times])
    tmin = np.array([t.hour * 60 + t.minute for t in times])
    pre_n = int((hours < cutoff_hour).sum())
    if pre_n < 3 or (len(day) - pre_n) < 5:
        return None
    pre = day.iloc[:pre_n]
    HOD = float(pre["high"].max())
    LOD = float(pre["low"].min())
    h = day["high"].values
    l = day["low"].values
    c = day["close"].values
    swings = find_swings(day, strength)
    for i in range(pre_n, len(day)):
        if tmin[i] >= entry_cutoff_min:      # no new setups past the entry window
            break
        if l[i] < LOD and c[i] > LOD:
            st = _build_long(day, i, LOD, swings)
            if st:
                return st
        if h[i] > HOD and c[i] < HOD:
            st = _build_short(day, i, HOD, swings)
            if st:
                return st
    return None


# ---------- outcome simulation (strictly forward) ----------

def simulate(day, setup, entry_cutoff_min=17 * 60, close_min=22 * 60):
    h = day["high"].values
    l = day["low"].values
    c = day["close"].values
    tmin = [t.hour * 60 + t.minute for t in day.index]
    n = len(day)
    e, stop, tgt = setup["entry"], setup["stop"], setup["target"]
    is_long = setup["dir"] == "long"

    def r_at(price):
        return (price - e) / (e - stop) if is_long else (e - price) / (stop - e)

    filled_at = None
    for i in range(setup["watch_from"], n):
        # past the hold-until time -> close at market (last candle close)
        if tmin[i] > close_min:
            if filled_at is None:
                return None, None
            return round(r_at(c[i - 1]), 2), day.index[filled_at]

        if filled_at is None:
            if tmin[i] >= entry_cutoff_min:      # entry window closed, never filled
                return None, None
            if is_long and l[i] <= e:
                filled_at = i
            elif (not is_long) and h[i] >= e:
                filled_at = i
            else:
                continue

        # filled: stop first if both touched in the same candle (conservative)
        if is_long:
            if l[i] <= stop:
                return -1.0, day.index[filled_at]
            if h[i] >= tgt:
                return 2.0, day.index[filled_at]
        else:
            if h[i] >= stop:
                return -1.0, day.index[filled_at]
            if l[i] <= tgt:
                return 2.0, day.index[filled_at]

    # day ended before close time
    if filled_at is None:
        return None, None
    return round(r_at(c[-1]), 2), day.index[filled_at]
