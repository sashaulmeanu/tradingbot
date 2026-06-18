"""
1H structural bias — fully deterministic. Same candles in -> same bias out.

Logic (SMC/ICT flavoured):
  1. Find swing highs/lows (fractal pivots).
  2. Classify market structure: bullish (HH/HL), bearish (LH/LL), or range.
  3. Draw on liquidity = nearest un-taken opposing pool in the trend direction.
  4. Dealing range -> OTE zone (62%-79% retrace) = where you hunt 5M/1M entries.
"""
from dataclasses import dataclass
from config import SWING_STRENGTH


@dataclass
class Bias:
    direction: str            # 'long' | 'short' | 'neutral'
    structure: str            # 'bullish' | 'bearish' | 'range'
    reason: str
    draw: float = None        # draw-on-liquidity target price
    eq: float = None          # equilibrium (50%) of the dealing range
    zone_low: float = None    # OTE hunt zone bounds
    zone_high: float = None
    price: float = None       # latest close
    in_zone: bool = False     # is price already inside the OTE zone?
    range_high: float = None
    range_low: float = None


def _find_swings(df, strength=SWING_STRENGTH):
    highs, lows = [], []
    h = df["high"].values
    l = df["low"].values
    idx = df.index
    n = len(df)
    for i in range(strength, n - strength):
        wh = h[i - strength:i + strength + 1]
        wl = l[i - strength:i + strength + 1]
        # strict pivot: this candle is the unique max/min of its window
        if h[i] == wh.max() and (wh == h[i]).sum() == 1:
            highs.append((idx[i], float(h[i])))
        if l[i] == wl.min() and (wl == l[i]).sum() == 1:
            lows.append((idx[i], float(l[i])))
    return highs, lows


def _classify(highs, lows):
    if len(highs) < 2 or len(lows) < 2:
        return "range"
    sh_prev, sh_last = highs[-2][1], highs[-1][1]
    sl_prev, sl_last = lows[-2][1], lows[-1][1]
    if sh_last > sh_prev and sl_last > sl_prev:
        return "bullish"
    if sh_last < sh_prev and sl_last < sl_prev:
        return "bearish"
    return "range"


def compute_bias(df):
    price = float(df["close"].iloc[-1])
    highs, lows = _find_swings(df)
    structure = _classify(highs, lows)

    if structure == "range" or not highs or not lows:
        return Bias("neutral", "range",
                    reason="structura neclara / range - stai pe maini pana se rupe",
                    price=price)

    last_high = highs[-1][1]
    last_low = lows[-1][1]

    if structure == "bullish":
        direction = "long"
        # current impulse leg: from the last protected swing low up to the
        # running high (price may have extended beyond the last swing high)
        leg_low = last_low
        leg_high = max(last_high, price)
        rng = max(leg_high - leg_low, 1e-9)
        # draw = nearest buy-side liquidity resting ABOVE price; None if price
        # is already above every mapped high (discovery / at the extreme)
        above = [hv for _, hv in highs if hv > price]
        draw = min(above) if above else None
        zone_high = leg_high - 0.62 * rng                   # discount OTE
        zone_low = leg_high - 0.79 * rng
        reason = "bullish (HH/HL)"
    else:
        direction = "short"
        leg_high = last_high
        leg_low = min(last_low, price)
        rng = max(leg_high - leg_low, 1e-9)
        below = [lv for _, lv in lows if lv < price]
        draw = max(below) if below else None                # sell-side liquidity
        zone_low = leg_low + 0.62 * rng                     # premium OTE
        zone_high = leg_low + 0.79 * rng
        reason = "bearish (LH/LL)"

    range_high, range_low = leg_high, leg_low
    eq = (leg_high + leg_low) / 2.0
    in_zone = zone_low <= price <= zone_high

    return Bias(direction, structure, reason,
                draw=draw, eq=eq,
                zone_low=zone_low, zone_high=zone_high,
                price=price, in_zone=in_zone,
                range_high=range_high, range_low=range_low)
