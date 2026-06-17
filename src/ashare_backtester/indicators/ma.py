import pandas as pd


def add_moving_averages(df: pd.DataFrame, windows: tuple[int, ...] = (5, 10, 20)) -> pd.DataFrame:
    result = df.copy()
    for window in windows:
        result[f"MA{window}"] = result["close"].rolling(window, min_periods=window).mean()
    return result
