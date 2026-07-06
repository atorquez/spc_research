# SPC Scanner — Streamlit App (Optimized Session 1)
import sys, os
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt   # <-- REQUIRED FOR st.pyplot()
from ui.components.charts import plot_spc_chart

# -------------------------------------------------------------------------
# PATH FIX — ensures Streamlit can import from project root
# -------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.append(ROOT)

# -------------------------------------------------------------------------
# PROJECT IMPORTS
# -------------------------------------------------------------------------
from data.sp500_list import sp500
from data.nasdaq100_list import nasdaq100
from data.russell1000_list import russell1000
from analysis.under_control_explorer import analyze_universe

# -------------------------------------------------------------------------
# UNIVERSE (deduplicated + sorted)
# -------------------------------------------------------------------------
combined_universe = sorted(list(set(sp500 + nasdaq100 + russell1000)))

# -------------------------------------------------------------------------
# STREAMLIT CONFIG
# -------------------------------------------------------------------------
st.set_page_config(page_title="SPC Scanner", layout="wide")
st.title("📊 SPC Scanner")

# -------------------------------------------------------------------------
# FETCH LAST 10 DAYS (Close + Volume)
# -------------------------------------------------------------------------
def get_last_10_closes(symbol: str):
    try:
        df = yf.download(
            symbol,
            period="15d",
            interval="1d",
            progress=False,
            threads=False,
            quiet=True   # <-- suppresses yfinance noise
        )
    except Exception:
        return None

    if df is None or df.empty:
        return None

    # Normalize MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0] for c in df.columns]

    if "Close" not in df.columns or "Volume" not in df.columns:
        return None

    df = df[["Close", "Volume"]].dropna()
    df = df.tail(10)

    if len(df) < 10:
        return None

    return df

# -------------------------------------------------------------------------
# PRICE + VOLUME FILTERS (updated: volume < 50M)
# -------------------------------------------------------------------------
def passes_filters(df):
    if df is None or len(df) == 0:
        return False

    if not isinstance(df, pd.DataFrame):
        return False

    if "Close" not in df.columns or "Volume" not in df.columns:
        return False

    last_close = df["Close"].iloc[-1]

    # Price filter only
    if last_close < 5 or last_close > 100:
        return False

    return True

# -------------------------------------------------------------------------
# CACHED DATA ACCESS
# -------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def cached_get_last_10_closes(ticker: str):
    return get_last_10_closes(ticker)

@st.cache_data(ttl=900, show_spinner=True)
def run_spc_cached(filtered_tickers):
    return analyze_universe(filtered_tickers, cached_get_last_10_closes)

# -------------------------------------------------------------------------
# CONTROLLED EXECUTION — RUN ONLY WHEN USER TRIGGERS
# -------------------------------------------------------------------------
st.markdown("### ⚙️ Run SPC Scan")

run_scan = st.button("Run Session 1 Scan")

if run_scan:
    with st.spinner("Running SPC scan across universe..."):

        # Apply price + volume filters BEFORE SPC engine
        filtered_universe = []
        for ticker in combined_universe:
            df_temp = cached_get_last_10_closes(ticker)
            if passes_filters(df_temp):
                filtered_universe.append(ticker)

        st.write("Filtered universe size:", len(filtered_universe))

        df = run_spc_cached(filtered_universe).copy(deep=True)

        if df is None or df.empty:
            st.error("No tickers passed the price/volume filters. Adjust filters or verify data.")
            st.stop()

        df.to_csv("cache/session1_results.csv", index=False)

    st.success("Session 1 scan completed.")

else:
    try:
        df = pd.read_csv("cache/session1_results.csv")

        if df is None or df.empty:
            st.error("Cached results file is empty. Please run a new scan.")
            st.stop()

        st.info("Loaded cached Session 1 results. Click **Run Session 1 Scan** to refresh.")
    except Exception:
        st.warning("No cached results found. Click **Run Session 1 Scan** to begin.")
        st.stop()

# -------------------------------------------------------------------------
# CLEANUP
# -------------------------------------------------------------------------
if "Ticker" in df.columns:
    df["Ticker"] = df["Ticker"].astype(str)

# -------------------------------------------------------------------------
# SESSION 1 — MARKET OVERVIEW & DEEP DIVE
# -------------------------------------------------------------------------
st.markdown("## 🔍 Session 1 — Market Overview & Deep Dive")

# SUMMARY PANEL
total_tickers = len(df)
under_control_df = df[df["UnderControl"] == True]
num_under_control = len(under_control_df)

col1, col2, col3 = st.columns(3)
col1.metric("Total Tickers Scanned", total_tickers)
col2.metric("Under Control", num_under_control)
col3.metric(
    "Percent Under Control",
    f"{(num_under_control / total_tickers) * 100:.2f}%" if total_tickers > 0 else "0.00%"
)

# OPPORTUNITY ZONES
buy_candidates = under_control_df[under_control_df["BuyZone"] == True]
sell_candidates = under_control_df[under_control_df["SellZone"] == True]

num_buy = len(buy_candidates)
num_sell = len(sell_candidates)
num_neutral = max(num_under_control - num_buy - num_sell, 0)

st.markdown("### Opportunity Zones")
colA, colB, colC = st.columns(3)
colA.metric("BUY Zone", num_buy)
colB.metric("SELL Zone", num_sell)
colC.metric("Neutral", num_neutral)

# ACTIONABILITY TABLE
action_df = under_control_df.copy()

if "Slope_5d" in action_df.columns and "Sigma" in action_df.columns:
    slope = action_df["Slope_5d"]
    sigma = action_df["Sigma"]
    threshold = 0.25 * sigma

    trend_robust = pd.Series("FLAT", index=action_df.index)
    trend_robust = trend_robust.mask(slope > threshold, "UP")
    trend_robust = trend_robust.mask(slope < -threshold, "DOWN")

    action_df["Trend_Robust"] = trend_robust.astype(str)
else:
    action_df["Trend_Robust"] = "UNKNOWN"

def classify_actionability(row):
    buy_zone = bool(row.get("BuyZone", False))
    sell_zone = bool(row.get("SellZone", False))
    trend = row.get("Trend_Robust", "UNKNOWN")

    if trend == "UP" and buy_zone:
        return "Confirmed BUY"
    if trend == "DOWN" and buy_zone:
        return "Early BUY"
    if trend == "DOWN" and sell_zone:
        return "Confirmed SELL"
    if trend == "UP" and sell_zone:
        return "Early SELL"
    return "Neutral"

action_df["Actionability"] = action_df.apply(classify_actionability, axis=1)

action_df["Actionability"] = pd.Categorical(
    action_df["Actionability"],
    categories=[
        "Confirmed BUY",
        "Early BUY",
        "Confirmed SELL",
        "Early SELL",
        "Neutral",
    ],
    ordered=True,
)

sort_cols = ["Actionability"]
if "CompanyName" in action_df.columns:
    sort_cols.append("CompanyName")
sort_cols.append("Ticker")

action_df = action_df.sort_values(sort_cols).reset_index(drop=True)

# Display Actionability Table
st.markdown("### 📄 Actionability Table")
display_cols = [
    "Ticker",
    "Trend_Robust",
    "BuyZone",
    "SellZone",
    "UnderControl",
    "Actionability"
]

st.dataframe(
    action_df[display_cols],
    width="stretch",
    hide_index=True
)

# EXPORT SESSION 1 RESULTS
try:
    action_df.to_csv("cache/session1_results.csv", index=False)
except Exception:
    pass

# -------------------------------------------------------------------------
# SPC CHART — FIXED
# -------------------------------------------------------------------------
st.markdown("### 📈 SPC Chart — Selected Ticker")

if not action_df.empty:
    selected_for_chart = st.selectbox(
        "Choose a ticker to visualize:",
        action_df["Ticker"].tolist(),
        key="spc_chart_selector"
    )

    try:
        fig = plot_spc_chart(str(selected_for_chart))
        st.pyplot(fig, clear_figure=True, use_container_width=True)
    except Exception as e:
        st.error(f"Chart error: {e}")
else:
    st.info("No UnderControl tickers available to chart.")