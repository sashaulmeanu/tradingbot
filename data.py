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


DUKAS_INSTRUMENTS = {
    "GBPUSD": "INSTRUMENT_FX_MAJORS_GBP_USD",
    "UK100": "INSTRUMENT_IDX_EUROPE_E_FUTSEE_100",
    "DAX": "INSTRUMENT_IDX_EUROPE_E_DAAX",
}


def get_5m_dukascopy(name, weeks=16):
    """Fetch ~`weeks` of 5M candles from Dukascopy (covers indices with
    pre-10:00 data, unlike the Yahoo cash index). Indexed in Europe/Bucharest."""
    import dukascopy_python
    from dukascopy_python import instruments as inst
    from datetime import datetime, timedelta

    const = DUKAS_INSTRUMENTS.get(name)
    if const is None:
        return None
    instrument = getattr(inst, const)
    end = datetime.utcnow()
    start = end - timedelta(weeks=weeks)
    df = dukascopy_python.fetch(
        instrument, dukascopy_python.INTERVAL_MIN_5,
        dukascopy_python.OFFER_SIDE_BID, start, end,
    )
    if df is None or len(df) == 0:
        return None
    df.columns = [str(c).lower() for c in df.columns]
    keep = [c for c in ["open", "high", "low", "close"] if c in df.columns]
    df = df[keep].dropna()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Europe/Bucharest")
    return df if len(df) else None


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
