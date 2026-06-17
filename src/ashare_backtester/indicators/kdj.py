import pandas as pd


def calculate_kdj(df: pd.DataFrame, period: int = 9, k_smooth: int = 3, d_smooth: int = 3) -> pd.DataFrame:
    result = df.copy()
    low_min = result["low"].rolling(period, min_periods=period).min()
    high_max = result["high"].rolling(period, min_periods=period).max()
    rsv = (result["close"] - low_min) / (high_max - low_min) * 100
    rsv = rsv.replace([float("inf"), float("-inf")], pd.NA).fillna(50)
    result["K"] = rsv.ewm(alpha=1 / k_smooth, adjust=False).mean()
    result["D"] = result["K"].ewm(alpha=1 / d_smooth, adjust=False).mean()
    result["J"] = 3 * result["K"] - 2 * result["D"]
    return result
