"""
Runs the HOD/LOD session model over the last ~60 days of 5M data for each
instrument, computes stats, and returns a results card for Telegram.

News filter: pass a list of high-impact event datetimes (tz-aware). Entries
whose fill time is within +/-15 min of an event are dropped. With no events
supplied it runs RAW (conservative) — the news filter only ever removes
losers around releases, so your filtered numbers will be >= these.
"""
from config import (INSTRUMENTS, ENTRY_CUTOFF_MIN, CLOSE_MIN,
                    DATA_SOURCE, DUKAS_WEEKS)
from data import get_5m, get_5m_dukascopy
from backtest_engine import find_day_setup, simulate

RISK_PCT = 0.5          # % risked per trade
NEWS_BUFFER_MIN = 15


def _blocked_by_news(ts, events):
    if ts is None or not events:
        return False
    for ev in events:
        if abs((ts - ev).total_seconds()) <= NEWS_BUFFER_MIN * 60:
            return True
    return False


def _load(name, symbol):
    if DATA_SOURCE == "dukascopy":
        return get_5m_dukascopy(name, weeks=DUKAS_WEEKS)
    return get_5m(symbol)


def backtest_symbol(name, symbol, events=None, cutoff_hour=10):
    df = _load(name, symbol)
    if df is None or df.empty:
        return None
    trades = []
    for day, day_df in df.groupby(df.index.date):
        if len(day_df) < 12:
            continue
        setup = find_day_setup(day_df, cutoff_hour=cutoff_hour,
                               entry_cutoff_min=ENTRY_CUTOFF_MIN)
        if not setup:
            continue
        R, fill_t = simulate(day_df, setup,
                             entry_cutoff_min=ENTRY_CUTOFF_MIN, close_min=CLOSE_MIN)
        if R is None:
            continue
        if _blocked_by_news(fill_t, events):
            continue
        trades.append({"date": str(day), "dir": setup["dir"], "R": R})
    return trades


def stats(trades):
    n = len(trades)
    if n == 0:
        return {"n": 0}
    wins = [t for t in trades if t["R"] > 0]
    total_r = sum(t["R"] for t in trades)
    mcl = cur = 0
    for t in trades:
        cur = cur + 1 if t["R"] < 0 else 0
        mcl = max(mcl, cur)
    return {
        "n": n,
        "wins": len(wins),
        "losses": n - len(wins),
        "wr": 100.0 * len(wins) / n,
        "total_r": total_r,
        "exp": total_r / n,
        "mcl": mcl,
        "pnl_pct": total_r * RISK_PCT,
    }


def _fmt(s):
    if s["n"] == 0:
        return "  niciun trade in fereastra"
    return (f"  {s['n']} trades | WR {s['wr']:.0f}% ({s['wins']}W/{s['losses']}L)\n"
            f"  expectancy {s['exp']:+.2f}R | total {s['total_r']:+.1f}R "
            f"({s['pnl_pct']:+.1f}% la {RISK_PCT}%/trade)\n"
            f"  max losing streak: {s['mcl']}")


def run_backtest(events=None, cutoff_hour=10):
    src = "dukascopy ~%dw" % DUKAS_WEEKS if DATA_SOURCE == "dukascopy" else "yfinance ~60z"
    lines = [f"\U0001F9EA Backtest — HOD/LOD sweep (5M, {src})",
             "entry 10:00–17:00, hold pana la 22:00, stop la wick sweep", ""]
    all_trades = []
    for name, symbol in INSTRUMENTS.items():
        try:
            trades = backtest_symbol(name, symbol, events=events, cutoff_hour=cutoff_hour)
        except Exception as ex:
            lines.append(f"{name}: eroare ({ex})")
            lines.append("")
            continue
        if trades is None:
            lines.append(f"{name}: date indisponibile")
            lines.append("")
            continue
        all_trades += trades
        lines.append(f"{name}")
        lines.append(_fmt(stats(trades)))
        lines.append("")

    lines.append("———")
    lines.append("TOTAL (toate instrumentele)")
    lines.append(_fmt(stats(all_trades)))
    if not events:
        lines.append("")
        lines.append("(raw, fara filtru de stiri — cifrele filtrate vor fi >= astea)")
    return "\n".join(lines)
