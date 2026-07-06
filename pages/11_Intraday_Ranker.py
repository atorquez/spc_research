import streamlit as st
from analysis.intraday_ranker import rank_universe, fetch_daily
from utils.data_fetch import load_universe
from data.core_lists import CORE_ETFS, CORE_AI, CORE_SPACE

st.set_page_config(layout="wide")
st.title("📈 Intraday Readiness Ranker")


#st.text(load_universe())


# ---------------------------------------------------------
# PRICE FILTERS
# ---------------------------------------------------------
st.markdown("### 🔍 Price Filter")
min_price = st.number_input("Minimum Price", value=5.0)
max_price = st.number_input("Maximum Price", value=40.0)

# ---------------------------------------------------------
# OPTIONAL CLUSTERS
# ---------------------------------------------------------
st.markdown("### 🧩 Optional Clusters")

include_ai = st.checkbox("Include AI Cluster", value=True)
include_space = st.checkbox("Include Space Exploration Cluster", value=True)

# Core leveraged ETFs always included (bypass filters)
CORE_ETFS = ["TQQQ", "SQQQ", "SOXL", "SOXS", "TECL", "SPXL"]

# AI Related (bypass filters)
CORE_AI = ["SPCE", "SPCX", "RKLB", "ASTS", "LUNR", "RDW","PL"]

# Space Exploration (bypass filters)
CORE_SPACE = ["FLY", "WEAV", "ALAB", "TEM", "RDDT", "CBRS"]

# ---------------------------------------------------------
# RUN RANKER
# ---------------------------------------------------------
if st.button("Run Intraday Ranker", key="run_intraday_ranker_btn_page11"):
    # Load main universe (SP500 + NASDAQ100 + OTHER_LIST)
    base_universe = load_universe()

    # Always-include tickers (bypass price filter AND fetch failures)
    always_include = CORE_ETFS.copy()

    if include_ai:
        always_include += CORE_AI
    if include_space:
        always_include += CORE_SPACE

    # Remove duplicates
    always_include = list(set(always_include))

    # Apply price filter ONLY to base universe
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

    # Debug print to confirm RDW is included
    print("Final Universe:", final_universe)

    # Run ranker
    ranking = rank_universe(final_universe)
    
    primary_df = ranking[
    ~ranking["Ticker"].isin(CORE_ETFS + CORE_AI + CORE_SPACE)
    ]
    exploration_df = ranking[
    ranking["Ticker"].isin(CORE_ETFS + CORE_AI + CORE_SPACE)
    ]
       
    st.subheader("🏆 Primary Universe — SP500 & NASDAQ100")
    st.dataframe(primary_df.head(30), hide_index=True, width="stretch")

    st.subheader("🚀 Exploration Universe — High-Opportunity Tickers")
    st.dataframe(exploration_df, hide_index=True, width="stretch")

    #st.dataframe(ranking)
    #print(ranking)


# ---------------------------------------------------------
# PARAMETER DEFINITIONS
# ---------------------------------------------------------
st.markdown("### 📘 Intraday Ranker — Parameter Definitions")

st.markdown("""
**EMA9 / EMA20 / EMA50**  
Exponential moving averages used to classify short‑term, medium‑term, and long‑term trend alignment.  
- **Bullish alignment:** EMA9 > EMA20 > EMA50  
- **Bearish alignment:** EMA9 < EMA20 < EMA50  
- **Flat:** No clear alignment

**ATR% (14‑period)**  
Average True Range as a percentage of price. Measures volatility expansion.  
- **ATR% > 5%:** Strong volatility → +15 points  
- **ATR% < 5%:** Normal volatility → 0 points

**RVOL (Relative Volume)**  
Current volume divided by 20‑day average volume.  
- **RVOL > 2:** High participation → +20 points  
- **RVOL < 2:** Normal participation → 0 points

**Gap%**  
Percentage difference between today's open and yesterday's close.  
- **2% to 5% gap:** Actionable → +10 points  
- **Outside range:** 0 points

**Trend Score**  
Based on EMA alignment:  
- EMA9 > EMA20 → +10  
- EMA20 > EMA50 → +10  
- Max trend score: **20**

**Baseline Readiness**  
Every ticker receives **+5** points for being inside daily resistance.

---

### 🔢 **Total Score Formula**
**Score = Trend (0–20) + RVOL (0–20) + Gap (0–10) + ATR (0–15) + Baseline (5)**  
**Maximum possible score = 70**

---

### 🧠 **PCA (Principal Component Analysis)**  
Dimensionality‑reduction technique used to compress multiple correlated indicators into a small number of “super‑signals.”  
This allows the ranker to include dozens of indicators (RSI, MACD, Bollinger Bands, Stochastics, ROC, Volume Delta, etc.) **without distorting the score**.

---

### **PCA1 — Momentum Component**  
Captures the combined effect of:  
- RSI  
- MACD  
- Rate of Change (ROC)  
- Stochastic %K  
- EMA curvature  

High PCA1 → strong momentum cluster  
Low PCA1 → weak or negative momentum

---

### **PCA2 — Volatility Component**  
Captures the combined effect of:  
- Bollinger Band Width  
- ATR behavior  
- High‑Low range expansion  
- Volatility ratio  

High PCA2 → volatility expansion  
Low PCA2 → volatility contraction

---

### **PCA3 — Participation Component**  
Captures the combined effect of:  
- Volume Delta  
- RVOL behavior  
- VWAP distance  
- Volume trend stability  

High PCA3 → strong participation  
Low PCA3 → weak participation

---

### **Why PCA Matters**  
PCA allows the ranker to:  
- Use many indicators without noise  
- Avoid overweighting momentum  
- Avoid redundant indicators  
- Keep the score stable  
- Maintain strict readiness logic  
- Scale to dozens of signals without breaking the math  

PCA does **not** directly add points to the readiness score (0–70).  
Instead, PCA components provide **multi‑dimensional context** for interpreting trend stability, momentum decay, volatility expansion, and participation strength.
""")
