import json
from pathlib import Path

TRACKED_FILE = Path("data/tracked_tickers.json")

def load_tracked():
    if not TRACKED_FILE.exists():
        return {"tracked": []}
    with open(TRACKED_FILE, "r") as f:
        return json.load(f)

def save_tracked(data):
    with open(TRACKED_FILE, "w") as f:
        json.dump(data, f, indent=4)