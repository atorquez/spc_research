import streamlit as st
import pandas as pd
import yfinance as yf

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("📈 TSQ Model — Intraday EMA Crossover Signals (Smoothed + Confirmed)")
st.caption("1‑minute EMA‑9 / EMA‑20 crossover engine with noise filtering, 2‑bar confirmation, and 2‑day intraday fix")

# ------------------------------------------------
# User Input
# ------------------------------------------------
ticker = st.text_input("Enter Ticker", value="QQQ").upper()

if st.button("Run TSQ Model"):
    st.write(f"Fetching 1‑minute intraday data for **{ticker}**...")

    # ------------------------------------------------
    # FIX: Use 2 days of data to avoid Yahoo early-day truncation
    # ------------------------------------------------
    raw = yf.download(
        tickers=ticker,
        period="2d",
        interval="1m",
        progress=False
    )

    if raw.empty:
        st.error("No intraday data retrieved. Market may be closed or Yahoo returned no data.")
        st.stop()

    # Keep only today's data
    today = pd.Timestamp.today().date()
    data = raw[raw.index.date == today].copy()

    if data.empty:
        st.error("Yahoo Finance has not provided today's intraday data yet.")
        st.stop()

    # Flatten multi-index columns if needed
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    # ------------------------------------------------
    # Smooth the Close price to reduce noise
    # ------------------------------------------------
    data["Close_Smoothed"] = data["Close"].rolling(window=3, center=True).median()
    data["Close_Smoothed"].fillna(data["Close"], inplace=True)

    # ------------------------------------------------
    # Compute EMAs on smoothed data
    # ------------------------------------------------
    data["EMA_9"] = data["Close_Smoothed"].ewm(span=9, adjust=False).mean()
    data["EMA_20"] = data["Close_Smoothed"].ewm(span=20, adjust=False).mean()

    # Position: 1 if EMA9 > EMA20 else 0
    data["Position"] = (data["EMA_9"] > data["EMA_20"]).astype(int)

    # Raw crossover detection
    data["Crossover"] = data["Position"].diff()

    # ------------------------------------------------
    # 2‑Bar Confirmation Logic (Option B1)
    # ------------------------------------------------
    data["Confirm"] = data["Position"].rolling(window=2).sum()

    # Confirmed bullish crossover
    data["Bullish_Confirmed"] = (data["Crossover"] == 1) & (data["Confirm"] == 2)

    # Confirmed bearish crossover
    data["Bearish_Confirmed"] = (data["Crossover"] == -1) & (data["Confirm"] == 0)

    # Filter confirmed signals only
    confirmed = data[(data["Bullish_Confirmed"] | data["Bearish_Confirmed"])].copy()

    # ------------------------------------------------
    # Build signal table
    # ------------------------------------------------
    signals = []
    for timestamp, row in confirmed.iterrows():
        if row["Bullish_Confirmed"]:
            trend = "UP"
            action = "BUY TQQQ (Bullish)"
        elif row["Bearish_Confirmed"]:
            trend = "DOWN"
            action = "BUY SQQQ (Bearish)"
        else:
            continue

        signals.append({
            "Time": timestamp,
            "Close": round(float(row["Close"]), 2),
            "EMA_9": round(float(row["EMA_9"]), 2),
            "EMA_20": round(float(row["EMA_20"]), 2),
            "Trend": trend,
            "Action": action
        })

    signal_df = pd.DataFrame(signals)

    # ------------------------------------------------
    # Display Results
    # ------------------------------------------------
    st.subheader("📊 Intraday Crossover Signals (Confirmed)")

    if signal_df.empty:
        st.warning("No confirmed EMA crossovers detected yet during this session.")
    else:
        st.success(f"Detected **{len(signal_df)}** confirmed crossover signals today.")
        st.dataframe(signal_df, use_container_width=True)

    # ------------------------------------------------
    # Chart
    # ------------------------------------------------
    st.subheader("📉 Price + EMA Chart (Last 200 Minutes)")
    chart_data = data[["Close", "Close_Smoothed", "EMA_9", "EMA_20"]].tail(200)
    st.line_chart(chart_data)



