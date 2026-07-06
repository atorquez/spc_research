import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

from data.long_term_tickers import LONG_TERM_TICKERS

st.set_page_config(page_title="Long-Term Valuation Explorer", layout="wide")

st.title("📘 Long-Term Valuation Explorer")

# ---------------------------------------------------------
# Ticker selection (UNIQUE KEY)
# ---------------------------------------------------------
tickers = st.multiselect(
    "Select tickers to analyze:",
    LONG_TERM_TICKERS,
    default=["NVDA"],
    key="lt_ticker_selector"
)

if not tickers:
    st.stop()

# ---------------------------------------------------------
# Current price panel (uses first selected ticker)
# ---------------------------------------------------------
primary = tickers[0]
info = yf.Ticker(primary).fast_info

current_price = info["last_price"]
day_change = info["last_price"] - info["previous_close"]
pct_change = (day_change / info["previous_close"]) * 100

col1, col2, col3 = st.columns(3)
col1.metric("Current Price", f"${current_price:,.2f}")
col2.metric("Day Change", f"${day_change:,.2f}", f"{pct_change:.2f}%")
col3.metric("52-Week Range", f"${info['year_low']:,.2f} - ${info['year_high']:,.2f}")

# ---------------------------------------------------------
# Build LT snapshot table
# ---------------------------------------------------------
rows = []

for t in tickers:
    df = yf.Ticker(t).history(period="2y", interval="1d")
    if df.empty:
        continue

    df.index = df.index.tz_localize(None)
    df = df.sort_index()

    price = float(df["Close"].iloc[-1])
    date = df.index[-1]

    rows.append({
        "Ticker": t,
        "Price": price,
        "Snapshot Date": date
    })

lt_df = pd.DataFrame(rows)

st.markdown("### 📄 Long-Term Snapshot Table")
st.dataframe(lt_df, use_container_width=True)

# ---------------------------------------------------------
# Candlestick chart section
# ---------------------------------------------------------
st.markdown("### 📈 2-Year Candlestick Chart with Buy Zones (50-Day & 1-Year MAs)")

chart_ticker = st.selectbox(
    "Select ticker to chart:",
    tickers,
    key="lt_chart_selector"
)

df = yf.Ticker(chart_ticker).history(period="2y", interval="1d")

if df.empty:
    st.error("No data returned.")
    st.stop()

# Clean index
df.index = df.index.tz_localize(None)
df = df.sort_index()

# Ensure OHLC exists
df = df[["Open", "High", "Low", "Close"]].astype(float)

# ---- Moving Averages ----
df["MA_50"] = df["Close"].rolling(window=50).mean()
df["MA_1Y"] = df["Close"].rolling(window=252).mean()

# ---- Buy Zones ----
df["BuyZone_50"] = df["Close"] < df["MA_50"]
df["BuyZone_1Y"] = df["Close"] < df["MA_1Y"]

# ---------------------------------------------------------
# Candlestick chart (Arrow-safe)
# ---------------------------------------------------------
fig = go.Figure()

# Candles
fig.add_trace(go.Candlestick(
    x=df.index.to_pydatetime(),
    open=df["Open"].tolist(),
    high=df["High"].tolist(),
    low=df["Low"].tolist(),
    close=df["Close"].tolist(),
    name=chart_ticker
))

# 50-day MA
fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["MA_50"].tolist(),
    mode="lines",
    line=dict(color="dodgerblue", width=2),
    name="50-Day MA"
))

# 1-year MA
fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["MA_1Y"].tolist(),
    mode="lines",
    line=dict(color="gold", width=2),
    name="1-Year MA (252d)"
))

# ---- Buy Zone Shading ----

# Light green: price < 50-day MA
fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["MA_50"].tolist(),
    fill=None,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["Close"].tolist(),
    fill="tonexty",
    mode="lines",
    line=dict(width=0),
    fillcolor="rgba(0, 255, 0, 0.10)",
    name="Buy Zone (Price < 50d MA)"
))

# Dark green: price < 1-year MA
fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["MA_1Y"].tolist(),
    fill=None,
    mode="lines",
    line=dict(width=0),
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=df.index.to_pydatetime(),
    y=df["Close"].tolist(),
    fill="tonexty",
    mode="lines",
    line=dict(width=0),
    fillcolor="rgba(0, 128, 0, 0.20)",
    name="Deep Buy Zone (Price < 1Y MA)"
))

fig.update_layout(
    title=f"2-Year Candlestick Chart — {chart_ticker}",
    xaxis_rangeslider_visible=False,
    height=650
)

st.plotly_chart(fig, use_container_width=True)