import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------
# Configuration
# -------------------------------------------------

TQQQ_TICKER = "TQQQ"
SQQQ_TICKER = "SQQQ"

START_DATE = "2018-01-01"

SHORT_MA = 40
LONG_MA = 120
VOL_WINDOW = 30

TRANSACTION_COST = 0.0005   # 0.05%

SIGNAL_CONFIRM_DAYS = 2

# -------------------------------------------------
# Data Loader
# -------------------------------------------------

def load_data():

    df_tqqq = yf.download(TQQQ_TICKER, start=START_DATE)
    df_sqqq = yf.download(SQQQ_TICKER, start=START_DATE)

    df = pd.DataFrame()
    df["tqqq_close"] = df_tqqq["Close"]
    df["sqqq_close"] = df_sqqq["Close"]

    df.dropna(inplace=True)

    return df

# -------------------------------------------------
# Feature Engine
# -------------------------------------------------

def build_features(df):

    df = df.copy()

    # Proxy market signal using Nasdaq ETF correlation structure
    df["market_return"] = df["tqqq_close"].pct_change().rolling(3).mean()

    df["MA_short"] = df["market_return"].rolling(SHORT_MA).mean()
    df["MA_long"] = df["market_return"].rolling(LONG_MA).mean()

    df["volatility"] = df["market_return"].rolling(VOL_WINDOW).std()

    # Base signal
    df["raw_signal"] = np.where(
        df["MA_short"] > df["MA_long"],
        1,
        np.where(df["MA_short"] < df["MA_long"], -1, 0)
    )

    # Signal confirmation smoothing
    df["signal"] = df["raw_signal"].rolling(
        SIGNAL_CONFIRM_DAYS
    ).mean().apply(lambda x: np.sign(x))

    # Volatility regime filter
    vol_threshold = df["volatility"].quantile(0.65)

    df.loc[df["volatility"] > vol_threshold, "signal"] = 0

    df.fillna(0, inplace=True)

    return df

# -------------------------------------------------
# Backtest Engine (Realistic Compounding)
# -------------------------------------------------

def backtest(df):

    df = df.copy()

    df["strategy_return"] = 0.0

    for i in range(1, len(df)):

        signal = df["signal"].iloc[i]
        market_ret = df["market_return"].iloc[i]

        # Leveraged exposure approximation
        if signal == 1:
            ret = 3 * market_ret
        elif signal == -1:
            ret = -3 * market_ret
        else:
            ret = 0

        # Transaction cost penalty when signal changes
        if df["signal"].iloc[i] != df["signal"].iloc[i-1]:
            ret -= TRANSACTION_COST

        df.iloc[i, df.columns.get_loc("strategy_return")] = ret

    df["equity"] = (1 + df["strategy_return"]).cumprod()

    return df

# -------------------------------------------------
# Visualization
# -------------------------------------------------

def plot_equity(df):

    plt.figure(figsize=(12,6))
    plt.plot(df.index, df["equity"], label="Strategy Equity")
    plt.title("Realistic Leveraged Trend Strategy Simulation")
    plt.xlabel("Date")
    plt.ylabel("Growth")
    plt.grid()
    plt.legend()
    plt.show()

# -------------------------------------------------
# Main
# -------------------------------------------------

if __name__ == "__main__":

    df = load_data()
    df = build_features(df)
    df = backtest(df)

    print(df.tail())
    plot_equity(df)