import pandas as pd


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    result = df.copy()
    ema_fast = result["close"].ewm(span=fast, adjust=False).mean()
    ema_slow = result["close"].ewm(span=slow, adjust=False).mean()
    result["DIF"] = ema_fast - ema_slow
    result["DEA"] = result["DIF"].ewm(span=signal, adjust=False).mean()
    result["MACD"] = 2 * (result["DIF"] - result["DEA"])
    return result
