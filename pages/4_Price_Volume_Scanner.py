# Price & Volume Scanner (No Filter Panel)
import sys
import os
import streamlit as st
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------
# Fix import path so "data/" is accessible
# ------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from data.sp500_list import sp500
from data.nasdaq100_list import nasdaq100
from data.russell1000_list import russell1000

# ------------------------------------------------
# Page Title
# ------------------------------------------------
st.title("📊 Price & Volume Scanner")
st.caption("Standalone liquidity filter for SP500 + NASDAQ100 + Russell1000")

# ------------------------------------------------
# FIXED FILTER VALUES (no UI)
# ------------------------------------------------
MIN_PRICE = 0.30
MAX_PRICE = 10.0
MIN_VOL = 10_000
MAX_VOL = 10_000_000

st.info(
    f"Using fixed filters:\n"
    f"- Price: {MIN_PRICE} to {MAX_PRICE}\n"
    f"- Volume: {MIN_VOL:,} to {MAX_VOL:,}"
)

# ------------------------------------------------
# Universe
# ------------------------------------------------
#UNIVERSE = sorted(list(set(sp500 + nasdaq100 + russell1000)))
#UNIVERSE = sorted(list(set(sp500 + nasdaq100)))
# ------------------------------------------------
# Load ALL US tickers (NASDAQ + NYSE + AMEX)
# ------------------------------------------------
tickers_df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "all_tickers.csv"))
UNIVERSE = sorted(tickers_df["Symbol"].dropna().unique().tolist())


st.write(f"Total Universe Size: **{len(UNIVERSE)}**")

# ------------------------------------------------
# Worker Function (using .history() for reliability)
# ------------------------------------------------
def scan_stock(ticker):
    try:
        data = yf.Ticker(ticker).history(period="21d")

        if data.empty:
            return None

        price = data["Close"].iloc[-1]
        volume = data["Volume"].iloc[-1]
        avg_volume = data["Volume"].rolling(20).mean().iloc[-1]

        if pd.isna(price) or pd.isna(volume) or pd.isna(avg_volume):
            return None

        # Price filter
        if not (MIN_PRICE <= price <= MAX_PRICE):
            return None

        # Volume filter
        if not (MIN_VOL <= volume <= MAX_VOL):
            return None

        return {
            "Ticker": ticker,
            "Price": price,
            "Volume": volume,
            "AvgVolume": avg_volume,
            "RelVolume": round(volume / avg_volume, 2)
        }

    except:
        return None

# ------------------------------------------------
# Run Scanner
# ------------------------------------------------
if st.button("Run Scanner"):
    st.write("Scanning universe...")

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_stock, t) for t in UNIVERSE]

        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    df = pd.DataFrame(results)

    # Store results for Page 5
    st.session_state["price_volume_results"] = df

    st.subheader("Scanner Results")
    st.write(f"Tickers Passing Filters: **{len(df)}**")

    if df.empty:
        st.warning("No tickers passed the filters.")
    else:
        df = df.sort_values("Volume", ascending=False)
        st.dataframe(df, width="stretch")

# ------------------------------------------------
# Footer Divider
# ------------------------------------------------
st.markdown("---")