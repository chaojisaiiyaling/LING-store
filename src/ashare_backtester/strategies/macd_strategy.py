import pandas as pd

from ashare_backtester.indicators.macd import calculate_macd
from ashare_backtester.strategies.base import Strategy, cross_down, cross_up


class MACDStrategy(Strategy):
    name = "MACD零轴上方金叉"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        result = calculate_macd(df, self.fast, self.slow, self.signal)
        result["signal"] = 0
        result.loc[cross_up(result["DIF"], result["DEA"]) & (result["DIF"] > 0) & (result["DEA"] > 0), "signal"] = 1
        result.loc[cross_down(result["DIF"], result["DEA"]), "signal"] = -1
        return result
