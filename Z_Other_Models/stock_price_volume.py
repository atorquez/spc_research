# ============================================
# Standalone Price / Volume Scanner
# SP500 + NASDAQ100 + Russell1000
# ============================================

import sys
import os

# ------------------------------------------------
# Make project root importable (fix for running inside Z_Other_Models)
# ------------------------------------------------
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import yfinance as yf
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# ------------------------------------------------
# Load universes
# ------------------------------------------------
from data.sp500_list import sp500
from data.nasdaq100_list import nasdaq100
from data.russell1000_list import russell1000

UNIVERSE = sorted(list(set(sp500 + nasdaq100 + russell1000)))

# ------------------------------------------------
# Filter parameters
# ------------------------------------------------
MIN_PRICE = 5
MAX_PRICE = 20          # <-- your request
MIN_VOL = 1_000_000
MAX_VOL = 10_000_000

results = []

# ------------------------------------------------
# Worker function
# ------------------------------------------------
def scan_stock(ticker):
    try:
        info = yf.Ticker(ticker).info

        price = info.get("currentPrice")
        volume = info.get("volume")
        avg_volume = info.get("averageVolume")

        if not price or not volume or not avg_volume:
            return None

        # Filter WITHOUT relative volume
        if (
            MIN_PRICE <= price <= MAX_PRICE and
            MIN_VOL <= volume <= MAX_VOL
        ):
            return {
                "Ticker": ticker,
                "Price": price,
                "Volume": volume,
                "AvgVolume": avg_volume
            }

    except:
        return None

# ------------------------------------------------
# Parallel execution
# ------------------------------------------------
with ThreadPoolExecutor(max_workers=20) as executor:
    futures = [executor.submit(scan_stock, t) for t in UNIVERSE]

    for future in as_completed(futures):
        result = future.result()
        if result:
            results.append(result)

# ------------------------------------------------
# Results
# ------------------------------------------------
df = pd.DataFrame(results)

print("\n=== FILTER RESULTS ===")
print(f"Total tickers in universe: {len(UNIVERSE)}")
print(f"Tickers passing filters: {len(df)}\n")

if df.empty:
    print("No tickers passed the filters today.")
else:
    print(df.sort_values("Volume", ascending=False))