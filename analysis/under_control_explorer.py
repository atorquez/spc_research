# analysis/under_control_explorer.py — Restored Stable Version
import pandas as pd
import numpy as np

def compute_spc_metrics(df):
    """
    Compute SPC metrics for a ticker:
    - Sigma (std dev)
    - Mean
    - Upper/Lower control bands
    - BuyZone / SellZone
    - UnderControl
    - Slope (5-day)
    """

    # ------------------------------------------------
    # 1. Validate Close column exists
    # ------------------------------------------------
    if "Close" not in df.columns:
        return None

    close_col = df["Close"]

    # ------------------------------------------------
    # 2. Normalize Close column
    #    Yahoo sometimes returns:
    #    - DataFrame instead of Series
    #    - Multi-index columns
    #    - Nested structures
    # ------------------------------------------------
    if isinstance(close_col, pd.DataFrame):
        # Case: Close is a DataFrame with its own Close column
        if "Close" in close_col.columns:
            close_col = close_col["Close"]
        else:
            # Fallback: take the first column
            close_col = close_col.iloc[:, 0]

    # Convert to numeric Series
    closes = pd.to_numeric(close_col, errors="coerce").dropna()

    # ------------------------------------------------
    # 3. Require minimum data
    # ------------------------------------------------
    if len(closes) < 5:
        return None

    # ------------------------------------------------
    # 4. Compute SPC metrics (same as your original logic)
    # ------------------------------------------------
    mean = closes.mean()
    sigma = closes.std()

    upper = mean + 1.0 * sigma
    lower = mean - 1.0 * sigma

    last_price = closes.iloc[-1]

    buy_zone = last_price < lower
    sell_zone = last_price > upper
    under_control = (lower <= last_price <= upper)

    # 5-day slope (simple linear regression)
    if len(closes) >= 5:
        y = closes.tail(5).values
        x = np.arange(len(y))
        slope = np.polyfit(x, y, 1)[0]
    else:
        slope = 0.0

    return {
        "Mean": mean,
        "Sigma": sigma,
        "Upper": upper,
        "Lower": lower,
        "LastPrice": last_price,
        "BuyZone": buy_zone,
        "SellZone": sell_zone,
        "UnderControl": under_control,
        "Slope_5d": slope,
    }

def analyze_universe(tickers, fetcher):
    """
    Run SPC analysis across a universe of tickers.
    - fetcher is get_last_10_closes (cached in scanner)
    - returns a DataFrame with SPC metrics
    """

    results = []

    for ticker in tickers:
        df = fetcher(ticker)

        if df is None or len(df) == 0:
            continue

        metrics = compute_spc_metrics(df)
        if metrics is None:
            continue

        row = {"Ticker": ticker}
        row.update(metrics)
        results.append(row)

    if not results:
        return pd.DataFrame()

    return pd.DataFrame(results)

def intraday_buy_zone(df, lookback=10, percentile=0.15):
    """
    Returns a statistical dip zone based on recent lows.
    """
    recent = df.tail(lookback)
    low_prices = recent["Low"]

    # Percentile dip zone (e.g., 15th percentile)
    buy_price = np.percentile(low_prices, percentile * 100)

    return round(buy_price, 2)
