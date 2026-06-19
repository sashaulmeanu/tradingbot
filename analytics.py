"""
Backtest analytics: profit factor, RR, drawdown, equity curve, performance by
year and by month, Monte Carlo robustness, and a train/test (out-of-sample)
split. Works on a list of trades: each {"date": "YYYY-MM-DD", "R": float}.
"""
import numpy as np

RISK_PCT = 0.5   # each R == this % of account


def max_drawdown(equity):
    peak = equity[0] if len(equity) else 0.0
    mdd = 0.0
    for x in equity:
        peak = max(peak, x)
        mdd = max(mdd, peak - x)
    return mdd


def analyze(trades):
    n = len(trades)
    if n == 0:
        return {"n": 0}
    trades = sorted(trades, key=lambda t: t["date"])
    R = np.array([t["R"] for t in trades], dtype=float)
    wins = R[R > 0]
    losses = R[R < 0]
    gross_win = float(wins.sum())
    gross_loss = float(-losses.sum())
    equity = np.cumsum(R)
    mdd_r = max_drawdown(equity)

    mcl = cur = 0
    for r in R:
        cur = cur + 1 if r < 0 else 0
        mcl = max(mcl, cur)

    avg_win = float(wins.mean()) if len(wins) else 0.0
    avg_loss = float(losses.mean()) if len(losses) else 0.0

    return {
        "n": n,
        "wr": 100.0 * len(wins) / n,
        "expectancy": float(R.mean()),
        "total_r": float(R.sum()),
        "profit_factor": (gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_rr": (avg_win / abs(avg_loss)) if avg_loss != 0 else float("inf"),
        "mdd_r": mdd_r,
        "mdd_pct": mdd_r * RISK_PCT,
        "pnl_pct": float(R.sum()) * RISK_PCT,
        "mcl": mcl,
        "equity": equity,
    }


def by_period(trades, key_fn):
    groups = {}
    for t in trades:
        groups.setdefault(key_fn(t), []).append(t)
    out = {}
    for k in sorted(groups):
        a = analyze(groups[k])
        out[k] = {"n": a["n"], "wr": a["wr"], "exp": a["expectancy"],
                  "total_r": a["total_r"]}
    return out


def monte_carlo(trades, n_sims=2000, seed=7):
    R = np.array([t["R"] for t in trades], dtype=float)
    if len(R) == 0:
        return {}
    rng = np.random.default_rng(seed)
    finals, dds = [], []
    for _ in range(n_sims):
        sample = rng.choice(R, size=len(R), replace=True)
        eq = np.cumsum(sample)
        finals.append(eq[-1])
        dds.append(max_drawdown(eq))
    finals = np.array(finals)
    dds = np.array(dds)
    return {
        "pct_profitable": 100.0 * float((finals > 0).mean()),
        "median_final": float(np.median(finals)),
        "p5_final": float(np.percentile(finals, 5)),
        "p95_final": float(np.percentile(finals, 95)),
        "median_mdd": float(np.median(dds)),
        "p95_mdd": float(np.percentile(dds, 95)),
    }


def split_traintest(trades, frac_train=0.7):
    """Split chronologically: first frac_train as train, rest as out-of-sample."""
    trades = sorted(trades, key=lambda t: t["date"])
    k = int(len(trades) * frac_train)
    return trades[:k], trades[k:]


def equity_png(per_instrument, path):
    """Plot cumulative-R equity curves: total + each instrument."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9, 4.5))
    all_trades = []
    for name, trades in per_instrument.items():
        if not trades:
            continue
        all_trades += trades
        eq = np.cumsum([t["R"] for t in sorted(trades, key=lambda t: t["date"])])
        ax.plot(eq, linewidth=1.0, alpha=0.7, label=name)
    if all_trades:
        eq = np.cumsum([t["R"] for t in sorted(all_trades, key=lambda t: t["date"])])
        ax.plot(eq, linewidth=2.0, color="black", label="TOTAL")
    ax.set_title("Equity curve — R cumulat")
    ax.set_xlabel("trade #")
    ax.set_ylabel("R")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
