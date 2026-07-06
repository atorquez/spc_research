import numpy as np
import pandas as pd

def compute_spc_metrics(closes: list[float]) -> dict:
    """
    Compute core SPC metrics from a list of closing prices.
    Pure function: no UI, no filtering, no external dependencies.
    """

    if closes is None or len(closes) < 5:
        return None

    prices = np.array(closes, dtype=float)

    mean = float(np.mean(prices))
    sigma = float(np.std(prices, ddof=1))

    ucl = mean + 2 * sigma
    lcl = mean - 2 * sigma

    # Violations: price outside ±3σ
    violations = {
        "above_ucl": np.where(prices > ucl)[0].tolist(),
        "below_lcl": np.where(prices < lcl)[0].tolist()
    }

    # Under-control condition
    under_control = (
        len(violations["above_ucl"]) == 0 and
        len(violations["below_lcl"]) == 0
    )

    # Trend slope (simple linear regression)
    x = np.arange(len(prices))
    slope = float(np.polyfit(x, prices, 1)[0])
    trend = "UP" if slope > 0 else "DOWN"

    # BUY/SELL boolean zones
    k = 1.0  # sensitivity factor
    buy_zone = prices[-1] <= (mean - k * sigma)
    sell_zone = prices[-1] >= (mean + k * sigma)

    return {
        "mean": mean,
        "sigma": sigma,
        "ucl": ucl,
        "lcl": lcl,
        "violations": violations,
        "under_control": under_control,   # <-- FIXED
        "slope": slope,
        "trend": trend,
        "buy_zone": buy_zone,
        "sell_zone": sell_zone,
        "last_price": float(prices[-1])
    }