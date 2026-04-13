import pandas as pd


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    close_col = "Close" if "Close" in df.columns else "close"
    open_col = "Open" if "Open" in df.columns else "open"

    df["daily_return"] = (df[close_col] - df[open_col]) / df[open_col]

    df["moving_avg_7d"] = df[close_col].rolling(window=7, min_periods=1).mean()

    df["week52_high"] = df[close_col].rolling(window=252, min_periods=1).max()

    df["week52_low"] = df[close_col].rolling(window=252, min_periods=1).min()

    df["volatility_score"] = df["daily_return"].rolling(30, min_periods=1).std() * (
        30**0.5
    )

    df = df.ffill()

    return df
