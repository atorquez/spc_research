# Comparison Dashboard: Session 1 vs Sequence Engine
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Model Comparison Dashboard", layout="wide")
st.title("📊 Model Comparison — Session 1 vs Sequence Engine")

# ---------------------------------------------------------
# LOAD EXPORTED RESULTS
# ---------------------------------------------------------
try:
    session1 = pd.read_csv("cache/session1_results.csv")
except Exception:
    st.error("Session 1 results not found. Run the SPC Scanner first.")
    st.stop()

try:
    sequence = pd.read_csv("cache/sequence_results.csv")
except Exception:
    st.error("Sequence Engine results not found. Run the Sequence Engine first.")
    st.stop()

st.markdown("### ⚙️ Run Comparison")

run_compare = st.button("Run Comparison Merge")

if not run_compare:
    st.info("Click **Run Comparison Merge** to refresh the combined model view.")

    # Try loading cached merged results
    try:
        merged = pd.read_csv("cache/merged_results.csv")
    except FileNotFoundError:
        st.warning("No cached comparison found. Click **Run Comparison Merge** to generate it.")
        st.stop()
else:
    # Load fresh inputs
    try:
        session1 = pd.read_csv("cache/session1_results.csv")
    except Exception:
        st.error("Session 1 results not found. Run the SPC Scanner first.")
        st.stop()

    try:
        sequence = pd.read_csv("cache/sequence_results.csv")
    except Exception:
        st.error("Sequence Engine results not found. Run the Sequence Engine first.")
        st.stop()

    # Merge fresh data
    merged = session1.merge(sequence, on="Ticker", how="outer", suffixes=("_SPC", "_SEQ"))

    # Save merged output
    merged.to_csv("cache/merged_results.csv", index=False)

    st.success("Comparison updated.")

# ---------------------------------------------------------
# MERGE BOTH MODELS
# ---------------------------------------------------------
merged = session1.merge(sequence, on="Ticker", how="outer", suffixes=("_SPC", "_SEQ"))

# ---------------------------------------------------------
# AGREEMENT CLASSIFICATION
# ---------------------------------------------------------
def classify(row):
    buyzone = row.get("BuyZone", False)
    sellzone = row.get("SellZone", False)
    signal = row.get("Signal", "NONE")

    if buyzone and signal == "BUY":
        return "Strong BUY"
    if buyzone and signal == "NONE":
        return "Stability BUY"
    if (not buyzone) and signal == "BUY":
        return "Early BUY"
    if sellzone and signal == "SELL":
        return "Strong SELL"
    return "No Agreement"

merged["Agreement"] = merged.apply(classify, axis=1)

# ---------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------
total_spc = len(session1)
total_seq = len(sequence)
intersection = merged["Ticker"].isin(session1["Ticker"]).sum()

strong_buy = (merged["Agreement"] == "Strong BUY").sum()
early_buy = (merged["Agreement"] == "Early BUY").sum()
stability_buy = (merged["Agreement"] == "Stability BUY").sum()
strong_sell = (merged["Agreement"] == "Strong SELL").sum()

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Session 1 Tickers", total_spc)
col2.metric("Sequence Engine Tickers", total_seq)
col3.metric("Intersection", intersection)
col4.metric("Strong BUY", strong_buy)
col5.metric("Early BUY", early_buy)
col6.metric("Stability BUY", stability_buy)

# ---------------------------------------------------------
# DISPLAY MERGED TABLE
# ---------------------------------------------------------
st.subheader("📘 Combined Model View")

# Reorder columns for clarity
cols = [
    "Ticker",
    "Name",
    "Price",
    "UnderControl",
    "BuyZone",
    "SellZone",
    "Trend_Robust",
    "Actionability",
    "Signal",
    "Agreement"
]

existing_cols = [c for c in cols if c in merged.columns]
st.dataframe(merged[existing_cols], hide_index=True, use_container_width=True)

st.markdown("## Agreement Definitions")

st.markdown("""
| **Agreement** | **Meaning** | **Interpretation** |
|---------------|-------------|--------------------|
| **Strong BUY** | Session 1: UnderControl + Buy Zone; Sequence Engine: BUY | Engines fully aligned. Highest‑conviction BUY setup. |
| **Stability BUY** | Session 1: UnderControl + Buy Zone; Sequence Engine: NONE | Stable and discounted, but reversal not confirmed. Watchlist or early entry. |
| **Early BUY** | Session 1: Early BUY; Sequence Engine: NONE | Trend turning but oscillation not confirmed. Early setup with more uncertainty. |
| **Strong SELL** | Session 1: Sell Zone + Trend DOWN; Sequence Engine: SELL | Engines aligned on downside. High‑conviction SELL or exit. |
| **Early SELL** | Session 1: Early SELL; Sequence Engine: NONE | Weakening trend but no oscillation confirmation. Caution signal. |
| **No Agreement** | Engines disagree | No action. Signals not aligned. |
""")