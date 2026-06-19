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


def _block(name, a):
    if a.get("n", 0) == 0:
        return f"{name}: niciun trade"
    pf = "inf" if a["profit_factor"] == float("inf") else f"{a['profit_factor']:.2f}"
    return (f"{name}: {a['n']} trades | WR {a['wr']:.0f}% | exp {a['expectancy']:+.2f}R | PF {pf}\n"
            f"  avgW {a['avg_win']:+.2f}R / avgL {a['avg_loss']:+.2f}R | RR {a['avg_rr']:.2f}\n"
            f"  total {a['total_r']:+.0f}R ({a['pnl_pct']:+.0f}%) | maxDD {a['mdd_r']:.0f}R "
            f"({a['mdd_pct']:.0f}%) | streak {a['mcl']}")


def _build_report(per_instrument, src):
    from analytics import analyze, by_period, monte_carlo, split_traintest

    lines = [f"\U0001F9EA Backtest — HOD/LOD sweep (5M, {src})",
             "entry 10:00–17:00, hold 22:00, stop wick | raw, fara filtru stiri", ""]

    all_trades = []
    for t in per_instrument.values():
        all_trades += (t or [])

    tot = analyze(all_trades)
    lines.append("═══ TOTAL ═══")
    lines.append(_block("TOTAL", tot))

    if all_trades:
        tr, te = split_traintest(all_trades, 0.7)
        at, ae = analyze(tr), analyze(te)
        def pf(a): return "inf" if a["profit_factor"] == float("inf") else f"{a['profit_factor']:.2f}"
        lines.append("")
        lines.append("Train/Test (out-of-sample, split 70/30 cronologic):")
        lines.append(f"  TRAIN: exp {at['expectancy']:+.2f}R | PF {pf(at)} | {at['n']} tr")
        lines.append(f"  TEST : exp {ae['expectancy']:+.2f}R | PF {pf(ae)} | {ae['n']} tr  <- contează")

        mc = monte_carlo(all_trades)
        lines.append("")
        lines.append(f"Monte Carlo (2000 sim, resampling):")
        lines.append(f"  {mc['pct_profitable']:.0f}% din simulari profitabile")
        lines.append(f"  final median {mc['median_final']:+.0f}R | p5 {mc['p5_final']:+.0f}R")
        lines.append(f"  worst-5% drawdown {mc['p95_mdd']:.0f}R")

        lines.append("")
        lines.append("Pe ani:")
        for y, s in by_period(all_trades, lambda t: t["date"][:4]).items():
            lines.append(f"  {y}: {s['n']:>4} tr | WR {s['wr']:.0f}% | exp {s['exp']:+.2f}R | {s['total_r']:+.0f}R")

        months = ["Ian", "Feb", "Mar", "Apr", "Mai", "Iun",
                  "Iul", "Aug", "Sep", "Oct", "Noi", "Dec"]
        bm = by_period(all_trades, lambda t: t["date"][5:7])
        lines.append("")
        lines.append("Pe luni (sezonalitate, total R):")
        seg = []
        for mm, s in bm.items():
            seg.append(f"{months[int(mm)-1]} {s['total_r']:+.0f}")
        lines.append("  " + " | ".join(seg))

    lines.append("")
    lines.append("─── pe instrument ───")
    from analytics import analyze as _an
    for name, trades in per_instrument.items():
        lines.append(_block(name, _an(trades or [])))

    return "\n".join(lines)


def run_backtest(events=None, cutoff_hour=10):
    from notify import send, send_photo
    from analytics import equity_png

    src = "dukascopy ~%dw" % DUKAS_WEEKS if DATA_SOURCE == "dukascopy" else "yfinance ~60z"
    per_instrument = {}
    for name, symbol in INSTRUMENTS.items():
        try:
            per_instrument[name] = backtest_symbol(name, symbol, events=events,
                                                   cutoff_hour=cutoff_hour) or []
        except Exception as ex:
            print(f"{name} backtest error:", ex)
            per_instrument[name] = []

    report = _build_report(per_instrument, src)
    send(report)

    try:
        path = equity_png(per_instrument, "/tmp/equity.png")
        send_photo(path, caption="Equity curve (R cumulat)")
    except Exception as ex:
        print("equity chart failed:", ex)

    return report
