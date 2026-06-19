import pandas as pd
import yfinance as yf


def get_5m(symbol, days=59):
    """Fetch up to ~59 days of 5M candles (yfinance caps intraday at 60d),
    indexed in Europe/Bucharest local time."""
    df = yf.download(symbol, period=f"{days}d", interval="5m",
                     auto_adjust=False, progress=False)
    if df is None or df.empty:
        return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [str(c).lower() for c in df.columns]
    keep = [c for c in ["open", "high", "low", "close"] if c in df.columns]
    df = df[keep].dropna()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Europe/Bucharest")
    return df if not df.empty else None


def get_1h(symbol, lookback_days=10):
    """Fetch ~10 days of 1H candles for a symbol. Returns a clean
    OHLC DataFrame or None if nothing came back."""
    df = yf.download(
        symbol,
        period=f"{lookback_days}d",
        interval="60m",
        auto_adjust=False,
        progress=False,
    )
    if df is None or df.empty:
        return None

    # yfinance sometimes returns multi-index columns; flatten them
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.columns = [str(c).lower() for c in df.columns]
    keep = [c for c in ["open", "high", "low", "close"] if c in df.columns]
    df = df[keep].dropna()
    return df if not df.empty else None
