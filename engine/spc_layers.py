# engine/spc_layers.py

import pandas as pd

def layer1_under_control(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply SPC Layer 1: Under-Control logic.
    Adds boolean columns and a final UnderControl flag.
    """

    df["Cond_NoViolations"] = df["Violations"].apply(lambda v: v == 0)
    df["Cond_SigmaOK"] = df["Sigma"].apply(lambda s: 1.5 <= s <= 3.5)
    df["Cond_PriceInBand"] = (df["Price"] >= df["LCL"]) & (df["Price"] <= df["UCL"])
    df["Cond_DataOK"] = df[["Price", "Mean", "Sigma", "LCL", "UCL"]].notna().all(axis=1)

    df["UnderControl"] = (
        df["Cond_NoViolations"] &
        df["Cond_SigmaOK"] &
        df["Cond_PriceInBand"] &
        df["Cond_DataOK"]
    )

    # ⭐ Critical fix: ensure index is clean and Arrow‑safe
    df = df.reset_index(drop=True)

    return df