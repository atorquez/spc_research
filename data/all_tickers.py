# data/all_tickers.py

from data.sp500_list import sp500
from data.nasdaq100_list import nasdaq100
from data.russell1000_list import russell1000

# ---------------------------------------------------------------------------
# Consolidated, deduplicated universe
# ---------------------------------------------------------------------------
ALL_TICKERS = sorted(list(set(sp500 + nasdaq100 + russell1000)))

# ---------------------------------------------------------------------------
# Optional: index membership map for filtering and tagging
# ---------------------------------------------------------------------------
INDEX_MAP = {
    "S&P 500": set(sp500),
    "NASDAQ 100": set(nasdaq100),
    "Russell 1000": set(russell1000),
}

# Convenience: reverse lookup for a single ticker
def get_index_membership(ticker: str):
    """Return a list of index names the ticker belongs to."""
    return [name for name, members in INDEX_MAP.items() if ticker in members]