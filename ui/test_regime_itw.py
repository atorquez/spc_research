import sys
import os

# Ensure project root is on sys.path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from analysis.regime_history import build_regime_history
from engine.spc_core import compute_spc_metrics

# Build regime history first
df = build_regime_history("ITW", window_size=10, lookback_days=180)

print("\n=== ITW Regime History (Last 10 rows) ===\n")
print(df.tail(10)[["Price", "UnderControl"]])

# Now inspect SPC metrics for each rolling window
print("\n=== SPC Window Diagnostics ===\n")

print("\n=== SPC Window Diagnostics ===\n")

for i in range(len(df)):
    window = df["Price"].iloc[max(0, i-9):i+1].tolist()
    metrics = compute_spc_metrics(window)

    if metrics is None:
        print(df.index[i], "window too small → skipping")
        continue

    print(
        df.index[i],
        "UCL=", round(metrics["ucl"], 4),
        "LCL=", round(metrics["lcl"], 4),
        "Last=", round(metrics["last_price"], 4),
        "UnderControl=", metrics["under_control"]
    )