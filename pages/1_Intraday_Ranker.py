import streamlit as st
from analysis.intraday_ranker import rank_universe, fetch_daily
from utils.data_fetch import load_universe
from data.core_lists import CORE_ETFS, CORE_AI, CORE_SPACE

st.set_page_config(layout="wide")
st.caption("SPC Version: 2026-08-08")
st.title("📈 Intraday Readiness Ranker")

# ---------------------------------------------------------
# PRICE FILTERS
# ---------------------------------------------------------
st.markdown("### 🔍 Price Filter")
min_price = st.number_input("Minimum Price", value=5.0)
max_price = st.number_input("Maximum Price", value=100.0)

# ---------------------------------------------------------
# OPTIONAL CLUSTERS
# ---------------------------------------------------------
st.markdown("### 🧩 Optional Clusters")

include_ai = st.checkbox("Include AI Cluster", value=True)
include_space = st.checkbox("Include Space Exploration Cluster", value=True)

# Core leveraged ETFs always included (bypass filters)
CORE_ETFS = ["TQQQ", "SQQQ", "SOXL", "SOXS", "TECL", "SPXL"]

# AI Related (bypass filters)
CORE_AI = ["SPCE", "SPCX", "RKLB", "ASTS", "LUNR", "RDW", "PL"]

# Space Exploration (bypass filters)
CORE_SPACE = ["FLY", "WEAV", "ALAB", "TEM", "RDDT", "CBRS"]

# ---------------------------------------------------------
# RUN RANKER
# ---------------------------------------------------------
if st.button("Run Intraday Ranker", key="run_intraday_ranker_btn_page11"):

    # Load main universe (SP500 + NASDAQ500 + OTHER_LIST)
    base_universe = load_universe()

    # Always-include tickers (bypass price filter AND fetch failures)
    always_include = CORE_ETFS.copy()

    if include_ai:
        always_include += CORE_AI
    if include_space:
        always_include += CORE_SPACE

    always_include = list(set(always_include))

    # Apply price filter ONLY to base_universe
    filtered = []
    for ticker in base_universe:
        df = fetch_daily(ticker)

        # CORE tickers bypass fetch failures AND price filter
        if ticker in always_include:
            filtered.append(ticker)
            continue

        # Normal tickers must have valid data
        if df is None or len(df) < 1:
            continue

        last_close = df["Close"].iloc[-1]
        if min_price <= last_close <= max_price:
            filtered.append(ticker)

    # Merge filtered universe + always-include universe
    final_universe = list(set(filtered + always_include))

    # Run ranker
    ranking = rank_universe(final_universe)

    # --- PCA DIAGNOSTIC BLOCK ---
    if "PCA1" in ranking.columns:
        pca1_null_ratio = ranking["PCA1"].isnull().mean()
        st.markdown("#### 🔍 PCA1 Diagnostic")
        st.write("Fraction of tickers with PCA1 = None:", pca1_null_ratio)

        if pca1_null_ratio > 0.5 and len(ranking) > 0:
            sample_ticker = ranking["Ticker"].iloc[0]
            st.write(f"Inspecting raw data for sample ticker: {sample_ticker}")
            sample_df = fetch_daily(sample_ticker)

            if sample_df is not None and len(sample_df) > 0:
                st.write("Last row of sample_df:")
                st.write(sample_df.iloc[-1])

                st.write("Missing fields in last row (True = missing):")
                st.write(sample_df.iloc[-1].isnull())
            else:
                st.write("Sample ticker has no data returned by fetch_daily().")
    else:
        st.markdown("#### 🔍 PCA1 Diagnostic")
        st.write("Column 'PCA1' not found in ranking DataFrame.")

    # Split into primary vs exploration universes
    primary_df = ranking[
        ~ranking["Ticker"].isin(CORE_ETFS + CORE_AI + CORE_SPACE)
    ]
    exploration_df = ranking[
        ranking["Ticker"].isin(CORE_ETFS + CORE_AI + CORE_SPACE)
    ]

    st.subheader("🏆 Primary Universe — SP500 & NASDAQ500")
    st.dataframe(primary_df.head(30), hide_index=True, width="stretch")

    st.subheader("🚀 Exploration Universe — High-Opportunity Tickers")
    st.dataframe(exploration_df, hide_index=True, width="stretch")

    # Show key columns including BuyZone + Buy_Signal
    st.subheader("🔎 Key Intraday Fields")
    st.dataframe(
        ranking[[
            "Ticker", "Price", "BuyZone10", "BuyZone5",
            "BuyZone10_Distance%", "BuyZone5_Distance%",
            "BuyZone_Heatmap", "PCA1", "Trend",
            "VMAS", "Buy_Signal"
        ]].head(25),
        hide_index=True,
        width="stretch"
    )

# ---------------------------------------------------------
# PARAMETER DEFINITIONS
# ---------------------------------------------------------
st.markdown("### 📘 Intraday Ranker — Parameter Definitions (2026 Edition)")

st.markdown("""
---

## 🏛 Daily Structure (Value + Trend Foundation)

### **BuyZone10 / BuyZone5**
Rolling percentile-based value zones computed from 3 months of daily data:
- **BuyZone10:** 10th percentile of closing prices  
- **BuyZone5:** 5th percentile of closing prices  

### **BuyZone Distance%**
Measures how far current price is from the BuyZone:
- **Distance < 0%:** Inside BuyZone  
- **0–3%:** Near Value  
- **3–10%:** Normal  
- **>10%:** Extended  

---

## 🎨 BuyZone Heatmap Classification

| State | Meaning |
|-------|---------|
| **Inside_5** | Deepest value zone |
| **Inside_10** | Broad value zone |
| **Near_Value** | Within 3% of BuyZone10 |
| **Normal** | 3–10% above BuyZone10 |
| **Extended** | >10% above BuyZone10 |

---

## 📈 Trend Structure (EMA9 / EMA20 / EMA50)

- **Bullish:** EMA9 > EMA20 > EMA50  
- **Bearish:** EMA9 < EMA20 < EMA50  
- **Flat:** No clear alignment  

**Trend Score:**  
- EMA9 > EMA20 → +10  
- EMA20 > EMA50 → +10  
(Max = 20)

---

## 🔥 Volatility & Participation

### **ATR% (14‑period)**
- ATR% > 5% → +15 points  

### **RVOL**
- RVOL > 2 → +20 points  

### **Gap%**
- 2%–5% gap → +10 points  

---

## 🧮 Baseline Readiness
Every ticker receives **+5 points**.

---

## 🧠 PCA Engine (Momentum + Volatility + Participation)

### **PCA1 — Momentum**
RSI, MACD, ROC, Stochastics, EMA curvature.

### **PCA2 — Volatility**
BBW, ATR, range expansion.

### **PCA3 — Participation**
RVOL trend, VWAP distance, volume delta.

---

## 🔗 VMAS — Value–Momentum Alignment Score
Measures whether momentum aligns with value proximity.

---

## 🚦 Buy_Signal Engine

| Signal | Meaning |
|--------|---------|
| **Strong Buy Zone** | Inside BuyZone5/10 + strong momentum |
| **Buy Zone** | Near value + improving momentum |
| **Neutral** | Mixed signals |
| **Avoid** | Weak momentum or extended |
| **Extended** | Price too far above value |

---

## 🧮 Total Score Formula (0–70)

**Score = Trend (0–20) + RVOL (0–20) + Gap (0–10) + ATR (0–15) + Baseline (5)**  

PCA, VMAS, and BuyZone logic determine **readiness state** and **Buy_Signal**.

---

## 🌐 Universe Logic

### **Primary Universe**
SP500 + NASDAQ500 + price-filtered tickers.

### **Exploration Universe**
Always included:
- Leveraged ETFs  
- AI cluster  
- Space cluster  

Shown separately for high-opportunity monitoring.
""")
