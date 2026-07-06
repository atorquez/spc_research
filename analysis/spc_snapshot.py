#spc_snapshot.py
import datetime
import numpy as np
from utils.data_fetch import get_last_10_closes

def compute_spc_snapshot(ticker: str) -> dict:
    """
    Computes the SPC snapshot for a ticker so it can be added to tracked_tickers.json.
    Mirrors the logic used in the tracking manager.
    """

    closes = get_last_10_closes(ticker)
    if len(closes) < 5:
        raise ValueError(f"Not enough data to compute SPC snapshot for {ticker}")

    closes_arr = np.array(closes, dtype=float)

    mean = float(np.mean(closes_arr))
    sigma = float(np.std(closes_arr, ddof=1))  # sample std
    last_price = float(closes_arr[-1])

    ucl = mean + 2.5 * sigma
    lcl = mean - 2.5 * sigma

    # Trend: compare last 5 closes
    if len(closes_arr) >= 5:
        slope = float(closes_arr[-1] - closes_arr[-5])
        trend = "UP" if slope > 0 else "DOWN" if slope < 0 else "FLAT"
    else:
        trend = "UNKNOWN"

    buy_zone = last_price < lcl
    sell_zone = last_price > ucl
    under_control = (lcl <= last_price <= ucl)

    snapshot = {
        "ticker": ticker,
        "added": datetime.date.today().isoformat(),
        "entry_price": last_price,
        "entry_mean": mean,
        "entry_sigma": sigma,
        "entry_ucl": ucl,
        "entry_lcl": lcl,
        "entry_last_price": last_price,
        "entry_trend": trend,
        "entry_buy_zone": buy_zone,
        "entry_sell_zone": sell_zone,
        "entry_under_control": under_control,
    }

    return snapshot