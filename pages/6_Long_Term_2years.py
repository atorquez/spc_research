import streamlit as st
import yfinance as yf
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
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

# 👉 Table version: formatted dates
table_df = merged.copy()
table_df.index = table_df.index.strftime("%Y-%m-%d")

st.subheader("Full Data Table")
st.dataframe(table_df)

# 👉 Chart version: keep datetime index
fig, ax = plt.subplots(figsize=(12, 6))
merged.plot(ax=ax)

ax.set_title('2-Year Close Price History', fontsize=12)
ax.set_xlabel('Date', fontsize=10)
ax.set_ylabel('Price (USD)', fontsize=10)

import matplotlib.ticker as mticker
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.2f'))

ax.xaxis.set_major_locator(mdates.MonthLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45)

ax.tick_params(axis='x', labelsize=8)
ax.tick_params(axis='y', labelsize=8)
ax.grid(True, alpha=0.3)

st.subheader("Chart")
st.pyplot(fig)