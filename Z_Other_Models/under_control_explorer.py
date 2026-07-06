#Price & Volume Scanner
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
# Sidebar Filters
# ------------------------------------------------
st.sidebar.header("Filter Settings")

MIN_PRICE = st.sidebar.number_input("Min Price", value=5.0)
MAX_PRICE = st.sidebar.number_input("Max Price", value=20.0)
MIN_VOL = st.sidebar.number_input("Min Volume", value=1_000_000)
MAX_VOL = st.sidebar.number_input("Max Volume", value=10_000_000)

include_rel_vol = st.sidebar.checkbox("Use Relative Volume Filter", value=False)
REL_VOL = st.sidebar.number_input("Min Relative Volume", value=1.5)

# ------------------------------------------------
# Universe
# ------------------------------------------------
UNIVERSE = sorted(list(set(sp500 + nasdaq100 + russell1000)))
st.write(f"Total Universe Size: **{len(UNIVERSE)}**")

# ------------------------------------------------
# Worker Function
# ------------------------------------------------
def scan_stock(ticker):
    try:
        info = yf.Ticker(ticker).info

        price = info.get("currentPrice")
        volume = info.get("volume")
        avg_volume = info.get("averageVolume")

        if not price or not volume or not avg_volume:
            return None

        if not (MIN_PRICE <= price <= MAX_PRICE):
            return None

        if not (MIN_VOL <= volume <= MAX_VOL):
            return None

        if include_rel_vol:
            rel_volume = volume / avg_volume
            if rel_volume < REL_VOL:
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
        sort_col = "RelVolume" if include_rel_vol else "Volume"
        df = df.sort_values(sort_col, ascending=False)
        st.dataframe(df, use_container_width=True)

# ------------------------------------------------
# Re-run Button
# ------------------------------------------------
st.markdown("---")
if st.button("Re-run Scanner"):
    st.experimental_rerun()