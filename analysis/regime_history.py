#regime_history.py
import pandas as pd
import yfinance as yf
from engine.spc_core import compute_spc_metrics

def get_price_history(ticker: str, lookback_days: int = 180) -> pd.Series:
    df = yf.download(ticker, period=f"{lookback_days}d", interval="1d", progress=False)

    if df is None or df.empty:
        return None

    closes = df["Close"].dropna()

    # Force to Series (fixes the (10,1) shape issue)
    if isinstance(closes, pd.DataFrame):
        closes = closes.iloc[:, 0]

    if closes.empty:
        return None

    return closes


def build_regime_history(ticker: str,
                         window_size: int = 10,
                         lookback_days: int = 180) -> pd.DataFrame:

    closes = get_price_history(ticker, lookback_days=lookback_days)
    if closes is None or len(closes) < window_size:
        return pd.DataFrame()

    records = []

    for end_idx in range(window_size - 1, len(closes)):
        # Force window to be a clean Series
        window = closes.iloc[end_idx - window_size + 1 : end_idx + 1]
        end_date = window.index[-1]

        metrics = compute_spc_metrics(window)

        record = {
            "Date": end_date,
            "Price": float(window.iloc[-1]),   # ensure float
            "Mean": metrics["mean"],
            "UCL": metrics["ucl"],
            "LCL": metrics["lcl"],
            "UnderControl": metrics.get("under_control"),
            "Trend_Robust": metrics.get("trend"),
            "BuyZone": metrics.get("buy_zone"),
            "SellZone": metrics.get("sell_zone"),
            "Actionability": metrics.get("actionability"),
            "Violations": metrics.get("violations"),
        }
        records.append(record)

    regime_df = pd.DataFrame(records).set_index("Date").sort_index()
    regime_df["Price"] = regime_df["Price"].astype(float)

    return regime_df