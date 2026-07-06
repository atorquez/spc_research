import numpy as np
import pandas as pd
import yfinance as yf

def compute_spc_metrics(closes: list[float]) -> dict:
    if closes is None or len(closes) < 5:
        return None

    prices = np.array(closes, dtype=float)

    mean = float(np.mean(prices))
    sigma = float(np.std(prices, ddof=1))

    ucl = mean + 2 * sigma
    lcl = mean - 2 * sigma

    violations = {
        "above_ucl": np.where(prices > ucl)[0].tolist(),
        "below_lcl": np.where(prices < lcl)[0].tolist()
    }

    under_control = (
        len(violations["above_ucl"]) == 0 and
        len(violations["below_lcl"]) == 0
    )

    x = np.arange(len(prices))
    slope = float(np.polyfit(x, prices, 1)[0])
    trend = "UP" if slope > 0 else "DOWN"

    k = 1.0
    buy_zone = prices[-1] <= (mean - k * sigma)
    sell_zone = prices[-1] >= (mean + k * sigma)

    return {
        "mean": float(mean),
        "sigma": float(sigma),
        "ucl": float(ucl),
        "lcl": float(lcl),
        "violations": {
            "above_ucl": [int(i) for i in violations["above_ucl"]],
            "below_lcl": [int(i) for i in violations["below_lcl"]],
    },
    "under_control": bool(under_control),
    "slope": float(slope),
    "trend": str(trend),
    "buy_zone": bool(buy_zone),
    "sell_zone": bool(sell_zone),
    "last_price": float(prices[-1])
    }

def compute_spc_for_ticker(ticker: str) -> dict:
    df = yf.download(ticker, period="6mo", progress=False)

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    if "Close" not in df.columns:
        return None

    closes = df["Close"].dropna().tolist()

    if len(closes) < 5:
        return None

    return compute_spc_metrics(closes)