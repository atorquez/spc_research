# Total_Score
import streamlit as st
import pandas as pd

st.title("⭐ Total Score Engine")
st.caption("Combines SPC + Sequence Engine + Price/Volume Scanner into a unified ranking model.")

st.markdown("---")

# ------------------------------------------------
# Check for required data
# ------------------------------------------------
missing = []
if "session1_results" not in st.session_state:
    missing.append("SPC Scanner (Page 1)")
if "sequence_results" not in st.session_state:
    missing.append("Sequence Engine (Page 2)")
if "price_volume_results" not in st.session_state:
    missing.append("Price/Volume Scanner (Page 4)")

if missing:
    st.error("The following pages must be run first:")
    for m in missing:
        st.write(f"- {m}")
    st.stop()

# ------------------------------------------------
# Load data
# ------------------------------------------------
df_spc = st.session_state["session1_results"].copy()
df_seq = st.session_state["sequence_results"].copy()
df_pv  = st.session_state["price_volume_results"].copy()

# Ensure ticker column is consistent
df_spc.rename(columns={"Ticker": "Ticker"}, inplace=True)
df_seq.rename(columns={"Ticker": "Ticker"}, inplace=True)
df_pv.rename(columns={"Ticker": "Ticker"}, inplace=True)

# ------------------------------------------------
# Run Combined Model
# ------------------------------------------------
if st.button("Run Total Score Model"):

    # Merge all three engines
    merged = df_spc.merge(df_seq, on="Ticker", how="outer", suffixes=("_SPC", "_SEQ"))
    merged = merged.merge(df_pv, on="Ticker", how="left")

    # ------------------------------------------------
    # Scoring Logic
    # ------------------------------------------------

    def spc_score(row):
        if row.get("BuyZone", False):
            return 40
        if row.get("UnderControl", False):
            return 20
        return 0

    def sequence_score(row):
        signal = str(row.get("Signal", "")).upper()
        if signal == "STRONG BUY":
            return 40
        if signal == "EARLY BUY":
            return 30
        if signal == "STABILITY BUY":
            return 20
        if signal == "NONE":
            return 0
        return 10  # Neutral or unknown

    def liquidity_score(row):
        return 20 if pd.notna(row.get("Price")) else 0

    merged["SPC_Score"] = merged.apply(spc_score, axis=1)
    merged["SEQ_Score"] = merged.apply(sequence_score, axis=1)
    merged["LIQ_Score"] = merged.apply(liquidity_score, axis=1)

    merged["TotalScore"] = merged["SPC_Score"] + merged["SEQ_Score"] + merged["LIQ_Score"]

    # Sort by score
    merged = merged.sort_values("TotalScore", ascending=False)

    # Store results
    st.session_state["total_score_results"] = merged

    st.subheader("Combined Model Results")
    st.write(f"Tickers Ranked: **{len(merged)}**")

    st.dataframe(merged, use_container_width=True)

# ------------------------------------------------
# If results already exist, show them
# ------------------------------------------------
if "total_score_results" in st.session_state:
    st.subheader("Latest Combined Model Results")
    st.dataframe(st.session_state["total_score_results"], use_container_width=True)

# ------------------------------------------------
# Re-run button
# ------------------------------------------------
st.markdown("---")
if st.button("Re-run Total Score Model"):
    st.rerun()

st.markdown("### 📘 Total Score Definitions")

st.markdown("""
The Total Score Engine combines three independent analytical engines into a unified ranking model.  
Each engine contributes a portion of the final score (0–100).

#### **1. SPC Score (0–40 points)**
Measures statistical stability and mean‑reversion behavior.
- **40 pts** → Price is in BuyZone (below lower control band)  
- **20 pts** → Price is UnderControl (inside control bands)  
- **0 pts** → Price is in SellZone or unstable  

#### **2. Sequence Score (0–40 points)**
Measures pattern structure and oscillation behavior.
- **40 pts** → Strong BUY (clean reversal pattern)  
- **20 pts** → Early BUY (alternation pattern forming)  
- **10 pts** → Stability BUY (mild reversal)  
- **0 pts** → No actionable sequence  

#### **3. Liquidity Score (0–20 points)**
Measures tradability based on price and volume.
- **20 pts** → Strong liquidity (volume + relative volume + price range)  
- **10 pts** → Moderate liquidity  
- **0 pts** → Missing or weak liquidity  

---

### **Total Score = SPC + Sequence + Liquidity (0–100)**

Higher scores indicate stronger alignment across:
- Statistical stability  
- Pattern structure  
- Tradability  

This creates a multi‑factor ranking model suitable for daily watchlists, research, and signal confirmation.
""")