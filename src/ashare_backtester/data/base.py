from abc import ABC, abstractmethod

import pandas as pd


REQUIRED_COLUMNS = ["trade_date", "open", "high", "low", "close", "volume", "amount"]


class DataProvider(ABC):
    @abstractmethod
    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Return A-share daily bars with unified columns."""


def normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    missing = [col for col in ["trade_date", "open", "high", "low", "close"] if col not in df.columns]
    if missing:
        raise ValueError(f"数据缺少必要字段: {', '.join(missing)}")

    result = df.copy()
    for col in ["volume", "amount"]:
        if col not in result.columns:
            result[col] = 0.0

    result = result[REQUIRED_COLUMNS]
    result["trade_date"] = pd.to_datetime(result["trade_date"])
    numeric_cols = ["open", "high", "low", "close", "volume", "amount"]
    result[numeric_cols] = result[numeric_cols].apply(pd.to_numeric, errors="coerce")
    result = result.dropna(subset=["trade_date", "open", "high", "low", "close"])
    return result.sort_values("trade_date").reset_index(drop=True)
