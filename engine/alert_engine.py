import json
from pathlib import Path
from datetime import datetime
from engine.spc_core import compute_spc_for_ticker

TRACKED_FILE = Path("data/tracked_tickers.json")

# ---------------------------------------------------------
# Load / Save helpers
# ---------------------------------------------------------

def load_tracked():
    if not TRACKED_FILE.exists():
        return {"tracked": []}
    with open(TRACKED_FILE, "r") as f:
        return json.load(f)

def save_tracked(data):
    with open(TRACKED_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ---------------------------------------------------------
# Core alert evaluation
# ---------------------------------------------------------

def evaluate_alerts(entry, current):
    """
    Compare stored entry SPC state vs. current SPC state.
    Return a list of alert messages (strings).
    """

    alerts = []

    # -----------------------------
    # 1. Trend flip
    # -----------------------------
    if entry["entry_trend"] != current["trend"]:
        alerts.append(f"Trend changed from {entry['entry_trend']} to {current['trend']}.")

    # -----------------------------
    # 2. Under-control → Out-of-control
    # -----------------------------
    if entry.get("entry_under_control", True) and not current["under_control"]:
        alerts.append("Price moved out of control limits.")

    # -----------------------------
    # 3. Buy zone / Sell zone flips
    # -----------------------------
    if entry.get("entry_buy_zone") != current["buy_zone"]:
        if current["buy_zone"]:
            alerts.append("Price entered BUY zone.")
        else:
            alerts.append("Price exited BUY zone.")

    if entry.get("entry_sell_zone") != current["sell_zone"]:
        if current["sell_zone"]:
            alerts.append("Price entered SELL zone.")
        else:
            alerts.append("Price exited SELL zone.")

    # -----------------------------
    # 4. Large deviation from entry mean
    # -----------------------------
    entry_mean = entry["entry_mean"]
    current_price = current["last_price"]
    deviation = abs(current_price - entry_mean)

    if deviation > 2 * entry["entry_sigma"]:
        alerts.append("Price deviated more than 2σ from entry mean.")

    return alerts

# ---------------------------------------------------------
# Daily alert engine
# ---------------------------------------------------------

def run_daily_alerts():
    """
    Load tracked tickers, compute current SPC metrics,
    evaluate alerts, and return a list of alert objects.
    """

    data = load_tracked()
    tracked = data.get("tracked", [])
    all_alerts = []

    for entry in tracked:
        ticker = entry["ticker"]

        # Compute today's SPC metrics
        current = compute_spc_for_ticker(ticker)
        if current is None:
            continue

        # Evaluate alerts
        alerts = evaluate_alerts(entry, current)

        if alerts:
            all_alerts.append({
                "ticker": ticker,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "alerts": alerts,
                "details": current
            })

        # Update stored entry state for next day
        entry["entry_mean"] = current["mean"]
        entry["entry_sigma"] = current["sigma"]
        entry["entry_trend"] = current["trend"]
        entry["entry_ucl"] = current["ucl"]
        entry["entry_lcl"] = current["lcl"]
        entry["entry_last_price"] = current["last_price"]
        entry["entry_buy_zone"] = current["buy_zone"]
        entry["entry_sell_zone"] = current["sell_zone"]
        entry["entry_under_control"] = current["under_control"]

    # Save updated state
    data["tracked"] = tracked
    save_tracked(data)

    return all_alerts