# ============================================================
# UNDER CONTROL EXPLORER — INTRADAY BUY ZONE + PCA + RANKER
# ============================================================

import yfinance as yf
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data.core_lists import CORE_ETFS, CORE_AI, CORE_SPACE


# ---------------------------------------------------------
# INTRADAY BUY ZONE
# ---------------------------------------------------------
def intraday_buy_zone(df, lookback=10, percentile=0.15):
    if df is None or df.empty:
        return None

    closes = df["Close"].tail(lookback)
    if len(closes) < lookback:
        return None

    return np.percentile(closes, percentile * 100)


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

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
    return df


# ---------------------------------------------------------
# EXTRA INDICATORS FOR PCA
# ---------------------------------------------------------
def compute_extra_indicators(df):
    df = df.copy()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df["RSI"] = 100 - (100 / (1 + rs))

    df["SMA20"] = df["Close"].rolling(20).mean()
    df["STD20"] = df["Close"].rolling(20).std()
    df["BB_Width"] = (df["STD20"] * 2) / df["SMA20"]

    df["ROC"] = df["Close"].pct_change(10)

    low_min = df["Low"].rolling(14).min()
    high_max = df["High"].rolling(14).max()
    df["StochK"] = (df["Close"] - low_min) / (high_max - low_min)

    df["EMA_Curve"] = df["Close"].ewm(span=9).mean() - df["Close"].ewm(span=20).mean()

    df["VolDelta"] = df["Volume"].diff()

    df["VWAP"] = (df["Volume"] * df["Close"]).cumsum() / df["Volume"].cumsum()
    df["VWAP_Dist"] = df["Close"] - df["VWAP"]

    df = df.dropna()
    return df


# ---------------------------------------------------------
# PCA COMPONENTS
# ---------------------------------------------------------
def compute_pca_components(df):
    df = compute_extra_indicators(df)

    pca_features = df[[
        "RSI",
        "BB_Width",
        "ROC",
        "StochK",
        "EMA_Curve",
        "VolDelta",
        "VWAP_Dist"
    ]].dropna()

    if len(pca_features) < 10:
        return None, None, None

    scaler = StandardScaler()
    scaled = scaler.fit_transform(pca_features)

    pca = PCA(n_components=3)
    components = pca.fit_transform(scaled)

    pca1, pca2, pca3 = components[-1]
    return float(pca1), float(pca2), float(pca3)


# ---------------------------------------------------------
# INDICATORS
# ---------------------------------------------------------
def calculate_indicators(df):
    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df["EMA9"] = df["Close"].ewm(span=9).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    df["H-L"] = df["High"] - df["Low"]
    df["H-PC"] = (df["High"] - df["Close"].shift(1)).abs()
    df["L-PC"] = (df["Low"] - df["Close"].shift(1)).abs()
    df["TR"] = df[["H-L", "H-PC", "L-PC"]].max(axis=1)
    df["ATR"] = df["TR"].rolling(14).mean()
    df["ATR%"] = (df["ATR"] / df["Close"]) * 100

    df["RVOL"] = df["Volume"] / df["Volume"].rolling(20).mean()
    df["Gap%"] = ((df["Open"] - df["Close"].shift(1)) / df["Close"].shift(1)) * 100

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

    if ind["EMA9"] > ind["EMA20"]:
        score += 10
    if ind["EMA20"] > ind["EMA50"]:
        score += 10

    if ind["RVOL"] > 2:
        score += 20

    if 2 <= ind["Gap%"] <= 5:
        score += 10

    if ind["ATR%"] > 5:
        score += 15

    score += 5
    return score


# ---------------------------------------------------------
# VMAS
# ---------------------------------------------------------
def compute_vmas(price, buyzone10, pca1):
    if price is None or buyzone10 is None or pca1 is None:
        return None

    dist = (price - buyzone10) / buyzone10
    return (1 - dist) * pca1


# ---------------------------------------------------------
# BUYZONE HEATMAP
# ---------------------------------------------------------
def buyzone_heatmap(price, bz10, bz5, dist10):
    if price is None or bz10 is None or bz5 is None:
        return "Unknown"

    if price <= bz5:
        return "Inside_5"

    if price <= bz10:
        return "Inside_10"

    if dist10 is not None and dist10 < 3:
        return "Near_Value"

    if dist10 is not None and dist10 > 10:
        return "Extended"

    return "Normal"


# ---------------------------------------------------------
# RANK UNIVERSE
# ---------------------------------------------------------
def rank_universe(symbols):
    results = []

    for ticker in symbols:
        df = fetch_daily(ticker)

        if df is None or len(df) < 50:
            results.append({
                "Ticker": ticker,
                "Name": get_company_name(ticker),
                "Score": None,
                "Price": None,
                "ATR%": None,
                "RVOL": None,
                "Gap%": None,
                "Trend": "UNKNOWN",
                "BuyZone10": None,
                "BuyZone5": None,
                "BuyZone10_Distance%": None,
                "BuyZone5_Distance%": None,
                "PCA1": None,
                "PCA2": None,
                "PCA3": None,
                "VMAS": None,
                "BuyZone_Heatmap": "Unknown"
            })
            continue

        ind = calculate_indicators(df)
        score = score_stock(ind)

        buyzone10 = intraday_buy_zone(df, lookback=10, percentile=0.15)
        buyzone5 = intraday_buy_zone(df, lookback=5, percentile=0.15)

        distance10 = ((ind["Close"] - buyzone10) / buyzone10 * 100) if buyzone10 else None
        distance5 = ((ind["Close"] - buyzone5) / buyzone5 * 100) if buyzone5 else None

        pca1, pca2, pca3 = compute_pca_components(df)

        vmas = compute_vmas(ind["Close"], buyzone10, pca1)

        heatmap = buyzone_heatmap(ind["Close"], buyzone10, buyzone5, distance10)

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
            "BuyZone10_Distance%": round(distance10, 2) if distance10 else None,
            "BuyZone5_Distance%": round(distance5, 2) if distance5 else None,
            "PCA1": pca1,
            "PCA2": pca2,
            "PCA3": pca3,
            "VMAS": vmas,
            "BuyZone_Heatmap": heatmap
        })

    ranking = (
        pd.DataFrame(results)
        .sort_values("Score", ascending=False)
        .reset_index(drop=True)
    )

    return ranking


