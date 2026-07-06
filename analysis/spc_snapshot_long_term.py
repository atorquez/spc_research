# spc_snapshot_long_term.py
import datetime
import pandas as pd
from utils.data_fetch import get_last_n_closes

def compute_long_term_snapshot(ticker: str) -> dict:
    closes = get_last_n_closes(ticker, n=250)

    if len(closes) == 0:
        return {
            "Ticker": ticker,
            "lt_date": datetime.date.today().isoformat(),
            "Price": None,
            "DaysAvailable": 0
        }

    df = pd.DataFrame({"Close": closes})

    return {
        "Ticker": ticker,
        "lt_date": datetime.date.today().isoformat(),
        "Price": float(df["Close"].iloc[-1]),
        "DaysAvailable": len(df),
        "FirstPrice": float(df["Close"].iloc[0]),
        "PriceChangePct": float((df["Close"].iloc[-1] / df["Close"].iloc[0] - 1) * 100)
    }