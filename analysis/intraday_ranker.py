from analysis.under_control_explorer import intraday_buy_zone
from data.core_lists import CORE_ETFS, CORE_AI, CORE_SPACE

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA


# ---------------------------------------------------------
# COMPANY NAME LOOKUP
# ---------------------------------------------------------
def get_company_name(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName", ticker)
    except Exception:
        return ticker


# ---------------------------------------------------------
# FETCH DAILY DATA
# ---------------------------------------------------------
def fetch_daily(ticker):
    df = yf.download(ticker, period="3mo", interval="1d", progress=False)
    if df is None or df.empty:
        return None

    # Normalize MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # Drop incomplete rows
    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])

    return df


# ---------------------------------------------------------
# EXTRA INDICATORS FOR PCA
# ---------------------------------------------------------
def compute_extra_indicators(df):
    df = df.copy()

    # RSI (manual)
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    # Bollinger Band Width
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["STD20"] = df["Close"].rolling(20).std()
    df["BB_Width"] = (df["STD20"] * 2) / df["SMA20"]

    # Rate of Change
    df["ROC"] = df["Close"].pct_change(5)

    # Stochastic %K
    low_min = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()
    df["StochK"] = (df["Close"] - low_min) / (high_max - low_min)

    # Volume Delta
    df["VolDelta"] = df["Volume"].pct_change()

    # ⭐ FIX: Drop NaNs AFTER indicator calculations
    df = df.dropna()

    return df


# ---------------------------------------------------------
# PCA COMPONENTS
# ---------------------------------------------------------
def compute_pca_components(df):
    df = compute_extra_indicators(df)

    pca_features = df[["RSI", "BB_Width", "ROC", "StochK", "VolDelta"]].dropna()

    # ⭐ FIX: Reduce minimum requirement from 20 → 10
    if len(pca_features) < 10:
        return None, None, None

    pca = PCA(n_components=3)
    components = pca.fit_transform(pca_features)

    # Today's PCA values (last row)
    pca1, pca2, pca3 = components[-1]
    return pca1, pca2, pca3


# ---------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------
def calculate_indicators(df):
    df = df.copy()

    # Normalize MultiIndex columns if present
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # EMAs
    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    # ATR%
    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = (df["High"] - df["Close"].shift(1)).abs()
    df["L-PC"] = (df["Low"] - df["Close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    df["ATR%"] = (df["ATR"] / df["Close"]) * 100

    # RVOL
    df["RVOL"] = df["Volume"] / df["Volume"].rolling(20).mean()

    # Gap%
    df["Gap%"] = ((df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)) * 100

    # Trend
    last = df.iloc[-1]
    if last["EMA9"] > last["EMA20"] > last["EMA50"]:
        trend = "UP"
    elif last["EMA9"] < last["EMA20"] < last["EMA50"]:
        trend = "DOWN"
    else:
        trend = "FLAT"

    return {
        "Close": round(last["Close"], 2),
        "ATR%": round(last["ATR%"], 2),
        "RVOL": round(last["RVOL"], 2),
        "Gap%": round(last["Gap%"], 2),
        "EMA9": last["EMA9"],
        "EMA20": last["EMA20"],
        "EMA50": last["EMA50"],
        "Trend": trend
    }


# ---------------------------------------------------------
# SCORING ENGINE
# ---------------------------------------------------------
def score_stock(ind):
    score = 0

    # Trend alignment
    if ind["EMA9"] > ind["EMA20"]:
        score += 10
    if ind["EMA20"] > ind["EMA50"]:
        score += 10

    # Volume
    if ind["RVOL"] > 2:
        score += 20

    # Gap
    if 2 <= ind["Gap%"] <= 5:
        score += 10

    # ATR%
    if ind["ATR%"] > 5:
        score += 15

    # Inside daily resistance
    score += 5

    return score


# ---------------------------------------------------------
# RANK UNIVERSE (patched with PCA + BuyZones)
# ---------------------------------------------------------
def rank_universe(symbols):
    results = []

    for ticker in symbols:
        df = fetch_daily(ticker)

        # CORE tickers bypass the 50-day requirement
        if ticker in CORE_ETFS or ticker in CORE_AI or ticker in CORE_SPACE:
            if df is None or len(df) < 50:
                results.append({
                    "Ticker": ticker,
                    "Name": get_company_name(ticker),
                    "Score": 5,
                    "Price": None,
                    "ATR%": None,
                    "RVOL": None,
                    "Gap%": None,
                    "Trend": "UNKNOWN",
                    "BuyZone10": None,
                    "BuyZone5": None,
                    "PCA1": None,
                    "PCA2": None,
                    "PCA3": None
                })
                continue

        # Normal tickers must have valid data
        if df is None or len(df) < 50:
            continue

        ind = calculate_indicators(df)
        score = score_stock(ind)

        # BuyZones
        buyzone10 = intraday_buy_zone(df, lookback=10, percentile=0.15)
        buyzone5 = intraday_buy_zone(df, lookback=5, percentile=0.15)
        if buyzone5 is not None and ind["Close"] is not None:
            distance5 = ((ind["Close"] - buyzone5) / ind["Close"]) * 100
        else:
            distance5 = None

        # PCA Components
        pca1, pca2, pca3 = compute_pca_components(df)

        results.append({
            "Ticker": ticker,
            "Name": get_company_name(ticker),
            "Score": score,
            "Price": ind["Close"],
            "ATR%": ind["ATR%"],
            "RVOL": ind["RVOL"],
            "Gap%": ind["Gap%"],
            "Trend": ind["Trend"],
            "BuyZone10": buyzone10,
            "BuyZone5": buyzone5,
            "BuyZone5_Distance%": round(distance5, 2) if distance5 is not None else None,
            "PCA1": pca1,
            "PCA2": pca2,
            "PCA3": pca3
        })

    ranking = (
        pd.DataFrame(results)
        .sort_values("Score", ascending=False)
        .reset_index(drop=True)
    )

    return ranking






