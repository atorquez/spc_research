import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="2-Year Candlestick Chart", layout="wide")

st.title("📉 2-Year Candlestick Chart")

tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "TSLA"]
ticker = st.selectbox("Select ticker:", tickers, index=2)

df = yf.Ticker(ticker).history(period="2y", interval="1d")

if df.empty:
    st.error("No data returned.")
    st.stop()

df.index = df.index.tz_localize(None)
df = df.sort_index()
df = df[["Open", "High", "Low", "Close"]].astype(float)

st.write("### Debug — df.head()")
st.table(df.head())

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df.index.to_pydatetime(),
    open=df["Open"].tolist(),
    high=df["High"].tolist(),
    low=df["Low"].tolist(),
    close=df["Close"].tolist(),
    name=ticker
))

fig.update_layout(
    title=f"2-Year Candlestick Chart — {ticker}",
    xaxis_rangeslider_visible=False,
    height=600
)

st.plotly_chart(fig, use_container_width=True)