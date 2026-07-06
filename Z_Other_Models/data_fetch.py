# ---------------------------------------------------------
# LOAD UNIVERSE (SP500 + NASDAQ100)
# ---------------------------------------------------------
def load_universe():
    from data.sp500_list import SP500
    from data.nasdaq100_list import NASDAQ100
    from data.other_list import OTHER

    universe = list(set(SP500 + NASDAQ100 + OTHER))
    return universe

