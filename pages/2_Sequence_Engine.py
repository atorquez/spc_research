#sequence_engine.py — Market Pattern Scanner (Dynamic Oscillation Model)
import sys, os
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import warnings
import logging

# ---------------------------------------------------------
# SUPPRESS YFINANCE & URLLIB3 LOGGING (NO TERMINAL NOISE)
# ---------------------------------------------------------
warnings.filterwarnings("ignore", category=UserWarning, module="yfinance")
logging.getLogger("yfinance").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# ---------------------------------------------------------
# FIX PYTHON PATH FOR PROJECT ROOT
# ---------------------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

# ---------------------------------------------------------
# IMPORT TICKER LISTS
# ---------------------------------------------------------
from data.sp500_list import TICKERS as SP500
from data.nasdaq100_list import TICKERS as NASDAQ100
#from data.russell1000_list import TICKERS as R1000   # <-- new

# ---------------------------------------------------------
# UNIVERSE (deduplicated)
# ---------------------------------------------------------
tickers = sorted(list(set(SP500 + NASDAQ100)))
# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Market Pattern Scanner", layout="wide")
st.title("📈 UPs and Downs Sequence Model")

# ---------------------------------------------------------
# PARAMETERS
# ---------------------------------------------------------
cycle = st.slider("Cycle Length (days)", 10, 30, 14)
sigma_level = st.slider("Sigma Level", 1.0, 2.5, 1.2)
min_segments = st.slider("Minimum Alternations", 2, 5, 3)

# ---------------------------------------------------------
# COMPANY NAME LOOKUP
# ---------------------------------------------------------
@st.cache_data(ttl=3600)
def get_company_name(ticker: str):
    try:
        info = yf.Ticker(ticker).info
        return info.get("shortName") or info.get("longName") or "N/A"
    except Exception:
        return "N/A"

# ---------------------------------------------------------
# DYNAMIC OSCILLATION LOGIC
# ---------------------------------------------------------
def detect_dynamic_pattern(window, sigma_level=1.2, min_segments=3):
    prices = pd.to_numeric(window["Close"], errors="coerce").dropna()
    if len(prices) < 5:
        return "NONE"

    mean = prices.mean()
    std = prices.std()

    upper = mean + sigma_level * std
    lower = mean - sigma_level * std

    raw_states = []
    for p in prices:
        if p > upper:
            raw_states.append("UP")
        elif p < lower:
            raw_states.append("DOWN")
        else:
            raw_states.append("NORMAL")

    states = []
    for s in raw_states:
        if not states or states[-1] != s:
            states.append(s)

    states = [s for s in states if s != "NORMAL"]

    if len(states) < min_segments + 1:
        return "NONE"

    alternations = sum(1 for i in range(1, len(states)) if states[i] != states[i - 1])
    last_state = states[-1]

    if last_state == "DOWN" and alternations >= min_segments:
        return "BUY"

    if last_state == "UP" and alternations >= min_segments:
        return "SELL"

    return "NONE"

# ---------------------------------------------------------
# FETCH & CLEAN DATA
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def fetch_data(ticker: str, period="60d"):
    try:
        df = yf.download(ticker, period=period, interval="1d", progress=False)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    if "Close" not in df.columns:
        return None

    df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
    df = df.dropna(subset=["Close"])

    return df

# ---------------------------------------------------------
# CACHED FULL ENGINE EXECUTION
# ---------------------------------------------------------
@st.cache_data(ttl=900)
def run_sequence_engine(tickers, cycle, sigma_level, min_segments):
    signals = []

    for ticker in tickers:
        data = fetch_data(ticker)

        if data is None or len(data) < cycle:
            continue

        window = data.tail(cycle)
        signal = detect_dynamic_pattern(
            window,
            sigma_level=sigma_level,
            min_segments=min_segments
        )

        signals.append({
            "Ticker": ticker,
            "Name": get_company_name(ticker),
            "Price": round(data["Close"].iloc[-1], 2),
            "Signal": signal
        })

    df = pd.DataFrame(signals)
    df.to_csv("cache/sequence_results.csv", index=False)
    return df

# ---------------------------------------------------------
# CONTROLLED EXECUTION
# ---------------------------------------------------------
st.markdown("### ⚙️ Run Sequence Engine")

run_engine = st.button("Run Sequence Scan")

if run_engine:
    with st.spinner("Running dynamic oscillation scan..."):
        df = run_sequence_engine(
            tickers,
            cycle,
            sigma_level,
            min_segments
        )

    # ⭐ REQUIRED FOR PAGE 5 ⭐
    st.session_state["sequence_results"] = df

    st.success("Sequence Engine scan completed.")

else:
    try:
        df = pd.read_csv("cache/sequence_results.csv")
        st.info("Loaded cached Sequence Engine results. Click **Run Sequence Scan** to refresh.")
    except FileNotFoundError:
        st.warning("No cached results found. Click **Run Sequence Scan** to begin.")
        st.stop()

# ---------------------------------------------------------
# SUMMARY PANEL
# ---------------------------------------------------------
total = len(df)
buy_count = (df["Signal"] == "BUY").sum()
sell_count = (df["Signal"] == "SELL").sum()
neutral_count = (df["Signal"] == "NONE").sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Tickers", total)
col2.metric("BUY", buy_count)
col3.metric("SELL", sell_count)
col4.metric("Neutral", neutral_count)

# ---------------------------------------------------------
# DISPLAY TABLE
# ---------------------------------------------------------
st.subheader("📊 Signal Table")
st.dataframe(df, width="stretch", hide_index=True)

# ---------------------------------------------------------
# PLOTLY CHART
# ---------------------------------------------------------
st.subheader("📈 Price & Control Bands")

ticker_labels = {t: f"{t} — {get_company_name(t)}" for t in tickers}
ticker_choice = st.selectbox("Select ticker for chart", list(ticker_labels.keys()), format_func=lambda x: ticker_labels[x])

chart_data = fetch_data(ticker_choice, period="6mo")
company = get_company_name(ticker_choice)

if chart_data is not None:

    mean = chart_data["Close"].rolling(cycle).mean()
    std = chart_data["Close"].rolling(cycle).std()

    upper = mean + sigma_level * std
    lower = mean - sigma_level * std

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=chart_data["Close"],
        mode="lines",
        line=dict(color="white", width=2.0),
        name="Price"
    ))

    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=upper,
        mode="lines",
        line=dict(color="red", width=1),
        name=f"Upper (+{sigma_level}σ)"
    ))

    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=lower,
        mode="lines",
        line=dict(color="blue", width=1),
        name=f"Lower (-{sigma_level}σ)"
    ))

    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=upper,
        mode="lines",
        line=dict(width=0),
        showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=chart_data.index,
        y=lower,
        fill="tonexty",
        mode="lines",
        line=dict(width=0),
        fillcolor="rgba(0, 150, 255, 0.08)",
        name="Control Band"
    ))

    fig.update_layout(
        title=dict(
            text=f"{ticker_choice} — {company} — {cycle}-Day Control Bands",
            font=dict(size=16)
        ),
        xaxis=dict(
            title=dict(text="Date", font=dict(size=12)),
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title=dict(text="Price", font=dict(size=12)),
            tickfont=dict(size=10)
        ),
        legend=dict(
            font=dict(size=10),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=450,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data available for this ticker.")

# ---------------------------------------------------------
# EXPORT SEQUENCE ENGINE RESULTS
# ---------------------------------------------------------
try:
    df.to_csv("cache/sequence_results.csv", index=False)
except Exception:
    pass