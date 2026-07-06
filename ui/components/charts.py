import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

from utils.data_fetch import get_last_10_closes
from analysis.under_control_explorer import compute_spc_metrics

def plot_spc_chart(ticker):
    ticker = str(ticker)

    plt.style.use("default")

    df = get_last_10_closes(ticker)

    if df is None or len(df) < 5:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"No price data for {ticker}", ha="center")
        plt.close(fig)
        return fig

    closes = pd.to_numeric(df["Close"], errors="coerce").dropna()

    metrics = compute_spc_metrics(df)
    if metrics is None:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, f"SPC metrics unavailable for {ticker}", ha="center")
        plt.close(fig)
        return fig

    mean = metrics["Mean"]
    ucl = metrics["Upper"]
    lcl = metrics["Lower"]

    mean_series = pd.Series([mean] * len(closes), index=closes.index)
    ucl_series = pd.Series([ucl] * len(closes), index=closes.index)
    lcl_series = pd.Series([lcl] * len(closes), index=closes.index)

    fig, ax = plt.subplots(figsize=(10, 4))

    ax.set_facecolor("#f7f7f7")
    ax.grid(axis="y", color="#e0e0e0", linewidth=0.7, linestyle="-", alpha=0.6)
    ax.grid(axis="x", visible=False)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#cccccc")
    ax.spines["bottom"].set_color("#cccccc")

    slope = metrics["Slope_5d"]
    if slope > 0:
        trend = "UP"
        trend_color = "#2ca02c"
    elif slope < 0:
        trend = "DOWN"
        trend_color = "#d62728"
    else:
        trend = "FLAT"
        trend_color = "gray"

    ax.plot(closes.index, closes.values, label=f"Price ({trend})",
            color=trend_color, linewidth=1.4)

    ax.plot(mean_series.index, mean_series.values, label="Mean",
            color="#1f77b4", linewidth=1.0)
    ax.plot(ucl_series.index, ucl_series.values, label="UCL",
            color="#d62728", linestyle="--", linewidth=0.9)
    ax.plot(lcl_series.index, lcl_series.values, label="LCL",
            color="#2ca02c", linestyle="--", linewidth=0.9)

    ax.set_title(f"SPC Chart for {ticker}", fontsize=14, fontweight="bold")
    ax.set_xlabel("")
    ax.set_ylabel("Price", fontsize=9)

    ax.tick_params(axis="x", labelsize=8)
    ax.tick_params(axis="y", labelsize=8)

    ax.legend(fontsize=8, loc="upper right", frameon=False)

    fig.autofmt_xdate()
    fig.canvas.draw()
    plt.close(fig)

    return fig