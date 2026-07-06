# under_control_explorer.py
import numpy as np
import pandas as pd
import yfinance as yf
from engine.spc_core import compute_spc_metrics
from engine.spc_layers import layer1_under_control


def analyze_universe(tickers: list[str], price_fetcher) -> pd.DataFrame:
    results = []

    for symbol in tickers:
        closes = price_fetcher(symbol)
        if closes is None or len(closes) == 0:
            continue

        metrics = compute_spc_metrics(closes)
        if not metrics:
            continue

        # --- NEW: Fetch company name ---------------------------------------
        try:
            info = yf.Ticker(symbol).info
            company_name = info.get("longName") or info.get("shortName") or symbol
        except Exception:
            company_name = symbol
        # -------------------------------------------------------------------

        row = {
            "Ticker": str(symbol),
            "CompanyName": company_name,   # <-- NEW FIELD (right after Ticker)
            "Price": float(metrics["last_price"]),
            "Mean": float(metrics["mean"]),
            "Sigma": float(metrics["sigma"]),
            "UCL": float(metrics["ucl"]),
            "LCL": float(metrics["lcl"]),
            "Slope_5d": float(metrics["slope"]),
            "Trend_5d": str(metrics["trend"]),
            "Violations": int(
                len(metrics["violations"]["above_ucl"]) +
                len(metrics["violations"]["below_lcl"])
            ),
            "BuyZone": bool(metrics["buy_zone"]),
            "SellZone": bool(metrics["sell_zone"])
        }

        results.append(row)

    df = pd.DataFrame(results)
    if df.empty:
        return df

    # Apply Layer‑1 logic ONCE
    df = layer1_under_control(df)

    # Reset index AFTER layer1 modifies the DataFrame
    df = df.reset_index(drop=True)

    # Cast ALL columns to Arrow‑safe dtypes
    df = df.astype({
        "Ticker": "string[pyarrow]",
        "CompanyName": "string[pyarrow]",   # <-- NEW CAST
        "Price": "float64",
        "Mean": "float64",
        "Sigma": "float64",
        "UCL": "float64",
        "LCL": "float64",
        "Slope_5d": "float64",
        "Trend_5d": "string[pyarrow]",
        "Violations": "int64",
        "BuyZone": "boolean",
        "SellZone": "boolean",
        "Cond_NoViolations": "boolean",
        "Cond_SigmaOK": "boolean",
        "Cond_PriceInBand": "boolean",
        "Cond_DataOK": "boolean",
        "UnderControl": "boolean"
    })

    # Final cleanup: eliminate any remaining object columns
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype("string[pyarrow]")

    return df