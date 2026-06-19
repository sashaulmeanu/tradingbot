"""
SMC primitive detectors — deterministic, no LLM, no lookahead in the values
themselves (each event is decided from candles at or before its own index).
These are the building blocks for both the backtester and live alerts.

  find_swings -> fractal pivot highs/lows
  detect_fvg  -> 3-candle Fair Value Gaps (imbalance zones)
  detect_sweep-> liquidity sweep: take out a prior swing then close back
  detect_mss  -> market structure shift: close breaks the last opposing swing
"""
import pandas as pd


def find_swings(df, strength=2):
    """Fractal pivots. A swing high is the unique max of a (2*strength+1) window."""
    h = df["high"].values
    l = df["low"].values
    swings = []
    for i in range(strength, len(df) - strength):
        wh = h[i - strength:i + strength + 1]
        wl = l[i - strength:i + strength + 1]
        if h[i] == wh.max() and (wh == h[i]).sum() == 1:
            swings.append({"i": i, "price": float(h[i]), "kind": "high"})
        if l[i] == wl.min() and (wl == l[i]).sum() == 1:
            swings.append({"i": i, "price": float(l[i]), "kind": "low"})
    swings.sort(key=lambda s: s["i"])
    return swings


def detect_fvg(df):
    """3-candle Fair Value Gaps. Bullish: candle1.high < candle3.low (gap up).
    Bearish: candle1.low > candle3.high (gap down). Index = candle3."""
    h = df["high"].values
    l = df["low"].values
    out = []
    for i in range(2, len(df)):
        if l[i] > h[i - 2]:
            out.append({"i": i, "type": "bull",
                        "bottom": float(h[i - 2]), "top": float(l[i])})
        if h[i] < l[i - 2]:
            out.append({"i": i, "type": "bear",
                        "bottom": float(h[i]), "top": float(l[i - 2])})
    return out


def _recent_prior(swings, i, kind, max_age):
    cands = [s for s in swings if s["kind"] == kind and s["i"] < i
             and (i - s["i"]) <= max_age]
    return cands[-1] if cands else None


def detect_sweep(df, swings, max_age=40):
    """Liquidity sweep. Bullish (sell-side taken): low pierces the most recent
    prior swing low but the candle closes back ABOVE it. Bearish mirror."""
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    out = []
    for i in range(len(df)):
        slow = _recent_prior(swings, i, "low", max_age)
        if slow and l[i] < slow["price"] and c[i] > slow["price"]:
            out.append({"i": i, "type": "bull",
                        "level": slow["price"], "swing_i": slow["i"]})
        shigh = _recent_prior(swings, i, "high", max_age)
        if shigh and h[i] > shigh["price"] and c[i] < shigh["price"]:
            out.append({"i": i, "type": "bear",
                        "level": shigh["price"], "swing_i": shigh["i"]})
    return out


def detect_mss(df, swings):
    """Market structure shift / break of structure. Bullish: close breaks above
    the most recent prior swing high. Bearish: close breaks below the most
    recent prior swing low. De-duplicated per swing level."""
    c = df["close"].values
    out = []
    used_bull = set()
    used_bear = set()
    for i in range(len(df)):
        highs = [s for s in swings if s["kind"] == "high" and s["i"] < i]
        lows = [s for s in swings if s["kind"] == "low" and s["i"] < i]
        if highs:
            sh = highs[-1]
            if c[i] > sh["price"] and sh["i"] not in used_bull:
                out.append({"i": i, "type": "bull",
                            "level": sh["price"], "swing_i": sh["i"]})
                used_bull.add(sh["i"])
        if lows:
            sl = lows[-1]
            if c[i] < sl["price"] and sl["i"] not in used_bear:
                out.append({"i": i, "type": "bear",
                            "level": sl["price"], "swing_i": sl["i"]})
                used_bear.add(sl["i"])
    return out
