import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import requests

# ---------------------------------------------
# PAGE TITLE
# ---------------------------------------------
st.title("📈 TSQ Model — Polygon.io Intraday EMA Signals")
st.write("Real-time 1‑minute EMA‑9 / EMA‑20 crossover engine using Polygon.io data")

# ---------------------------------------------
# USER INPUT
# ---------------------------------------------
ticker = st.text_input("Enter Ticker", "QQQ").upper()

# ---------------------------------------------
# TEMPORARY DATE FIX (because BIOS is stuck in 2026)
# ---------------------------------------------
system_today = dt.date.today()
st.write(f"System date: {system_today}")

# Start approx 2 years back
initial_adjusted = system_today - dt.timedelta(days=729)

# ---------------------------------------------
# FIND NEAREST VALID INTRADAY DATE (600-day search)
# ---------------------------------------------
api_key = "YOUR_POLYGON_KEY_HERE"

def find_valid_date(start_date):
    for i in range(600):  # search up to 600 days back
        test_date = start_date - dt.timedelta(days=i)
        date_str = test_date.strftime("%Y-%m-%d")

        url_test = (
            f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/"
            f"{date_str}/{date_str}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
        )

        r = requests.get(url_test).json()

        if "results" in r:
            return test_date

    return None

today = find_valid_date(initial_adjusted)

if today is None:
    st.error("Could not find intraday data in the last 600 days of the adjusted window.")
    st.stop()

st.write(f"Adjusted date sent to Polygon: {today}")

# ---------------------------------------------
# POLYGON API CALL
# ---------------------------------------------
date_str = today.strftime("%Y-%m-%d")

url = (
    f"https://api.polygon.io/v2/aggs/ticker/{ticker}/range/1/minute/"
    f"{date_str}/{date_str}?adjusted=true&sort=asc&limit=50000&apiKey={api_key}"
)

st.write(f"Fetching Polygon intraday data for {ticker}...")

response = requests.get(url)
data = response.json()

if "results" not in data:
    st.error("Polygon returned no intraday data. Market may be closed or API key invalid.")
    st.stop()

df = pd.DataFrame(data["results"])

# ---------------------------------------------
# CLEAN DATA
# ---------------------------------------------
df["timestamp"] = pd.to_datetime(df["t"], unit="ms")
df = df.rename(columns={"o": "Open", "h": "High", "l": "Low", "c": "Close", "v": "Volume"})
df = df[["timestamp", "Open", "High", "Low", "Close", "Volume"]]
df = df.set_index("timestamp")

# ---------------------------------------------
# EMA CALCULATIONS
# ---------------------------------------------
df["EMA_9"] = df["Close"].ewm(span=9, adjust=False).mean()
df["EMA_20"] = df["Close"].ewm(span=20, adjust=False).mean()

# ---------------------------------------------
# PHASE II — CROSSOVER LOGIC
# ---------------------------------------------
df["ema_diff"] = df["EMA_9"] - df["EMA_20"]
df["ema_diff_prev"] = df["ema_diff"].shift(1)
df["signal_phase"] = None

# Approaching crossover (within ±0.02%)
df.loc[df["ema_diff"].abs() < df["Close"] * 0.0002, "signal_phase"] = "approaching"

# Slightly crossed (crossed but small separation)
df.loc[
    (df["ema_diff"] * df["ema_diff_prev"] < 0) &
    (df["ema_diff"].abs() < df["Close"] * 0.001),
    "signal_phase"
] = "slightly_crossed"

# Confirmed crossover (crossed + separation > 0.1%)
df.loc[
    (df["ema_diff"] * df["ema_diff_prev"] < 0) &
    (df["ema_diff"].abs() >= df["Close"] * 0.001),
    "signal_phase"
] = "confirmed"

latest_phase = df["signal_phase"].iloc[-1]

# ---------------------------------------------
# DISPLAY PHASE II SIGNAL
# ---------------------------------------------
if latest_phase == "approaching":
    st.warning("⚠️ EMA‑9 and EMA‑20 are approaching a crossover.")
elif latest_phase == "slightly_crossed":
    st.info("🔄 EMAs have slightly crossed — early signal.")
elif latest_phase == "confirmed":
    st.success("✅ Confirmed EMA‑9 / EMA‑20 crossover!")
else:
    st.write("No crossover activity detected.")

# ---------------------------------------------
# DISPLAY DATAFRAME
# ---------------------------------------------
st.subheader("Intraday Data (Adjusted)")
st.dataframe(df.tail(20))



