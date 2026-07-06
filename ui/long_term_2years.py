import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd

st.title("📈 2-Year Close Price History")

tickers = ['TQQQ', 'SQQQ']

dfs = []

for t in tickers:
    df = yf.Ticker(t).history(period="2y", interval="1d")
    if df.empty:
        st.warning(f"No data for {t}")
        continue

    df = df[['Close']].rename(columns={'Close': t})
    dfs.append(df)

merged = pd.concat(dfs, axis=1)

st.write("Shape:", merged.shape)
st.dataframe(merged.head())

# Plot
fig, ax = plt.subplots(figsize=(12, 6))
merged.plot(ax=ax)
ax.set_title('2-Year Close Price History')
ax.set_xlabel('Date')
ax.set_ylabel('Price (USD)')
ax.grid(True, alpha=0.3)

st.pyplot(fig)
