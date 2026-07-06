import streamlit as st
import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

st.title("🌏 Global Penny Stock Scanner (US + Asia)")
st.caption("Automatically scans US, Hong Kong, China, Japan, Korea, Taiwan")

# ------------------------------------------------
# Filters
# ------------------------------------------------
MIN_PRICE = 0.30
MAX_PRICE = 10.00
MIN_VOL = 100_000

st.info(
    f"Filters:\n"
    f"- Price: {MIN_PRICE} to {MAX_PRICE}\n"
    f"- Volume: > {MIN_VOL:,}"
)

# ------------------------------------------------
# Base tickers (no suffixes)
# ------------------------------------------------
BASE_TICKERS = [
    "SBFM", "PLUG", "SOFI", "AMC", "GME", "IDEX", "CEI",
    "0700", "9988", "3690", "1211", "1810",
    "600519", "000001",
    "7203", "6758",
    "005930", "000660",
    "2330", "2454"
]

st.write(f"Base Universe Size: **{len(BASE_TICKERS)}**")

# ------------------------------------------------
# Exchange suffixes to try
# ------------------------------------------------
SUFFIXES = [
    "",        # US
    ".HK",     # Hong Kong
    ".SS",     # Shanghai
    ".SZ",     # Shenzhen
    ".T",      # Tokyo
    ".KS",     # Korea
    ".TW"      # Taiwan
]

# ------------------------------------------------
# Resolve ticker to working exchange
# ------------------------------------------------
def resolve_ticker(base):
    for suffix in SUFFIXES:
        t = base + suffix
        try:
            data = yf.Ticker(t).history(period="5d")
            if not data.empty:
                return t
        except:
            pass
    return None

# ------------------------------------------------
# Worker Function
# ------------------------------------------------
def scan_ticker(base):
    resolved = resolve_ticker(base)
    if not resolved:
        return None

    try:
        data = yf.Ticker(resolved).history(period="21d")
        if data.empty:
            return None

        price = data["Close"].iloc[-1]
        volume = data["Volume"].iloc[-1]

        if price < MIN_PRICE or price > MAX_PRICE:
            return None

        if volume < MIN_VOL:
            return None

        return {
            "Base": base,
            "Resolved": resolved,
            "Price": round(price, 3),
            "Volume": int(volume)
        }

    except:
        return None

# ------------------------------------------------
# Run Scanner
# ------------------------------------------------
if st.button("Run Global Scanner"):
    st.write("Scanning US + Asia...")

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(scan_ticker, t) for t in BASE_TICKERS]

        for f in as_completed(futures):
            r = f.result()
            if r:
                results.append(r)

    df = pd.DataFrame(results)

    st.subheader("Results")
    st.write(f"Tickers Passing Filters: **{len(df)}**")

    if df.empty:
        st.warning("No penny stocks found in US + Asia.")
    else:
        df = df.sort_values("Volume", ascending=False)
        st.dataframe(df, width="stretch")

st.markdown("---")

