import pandas as pd

from ashare_backtester.indicators.kdj import calculate_kdj
from ashare_backtester.strategies.base import Strategy, cross_down, cross_up


class KDJStrategy(Strategy):
    name = "KDJ低位金叉"

    def __init__(self, period: int = 9, k_smooth: int = 3, d_smooth: int = 3):
        self.period = period
        self.k_smooth = k_smooth
        self.d_smooth = d_smooth

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        result = calculate_kdj(df, self.period, self.k_smooth, self.d_smooth)
        result["signal"] = 0
        result.loc[cross_up(result["K"], result["D"]) & (result["K"] < 30), "signal"] = 1
        result.loc[cross_down(result["K"], result["D"]) | (result["K"] > 80), "signal"] = -1
        return result
