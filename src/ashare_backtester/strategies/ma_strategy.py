import pandas as pd

from ashare_backtester.indicators.ma import add_moving_averages
from ashare_backtester.strategies.base import Strategy, cross_down, cross_up


class MAStrategy(Strategy):
    def __init__(self, mode: str):
        self.mode = mode
        self.name = {
            "ma5_ma10": "MA5上穿MA10",
            "ma5_ma20": "MA5上穿MA20",
            "bullish": "MA5/MA10/MA20多头排列",
        }[mode]

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        result = add_moving_averages(df)
        result["signal"] = 0
        if self.mode == "ma5_ma10":
            result.loc[cross_up(result["MA5"], result["MA10"]), "signal"] = 1
            result.loc[cross_down(result["MA5"], result["MA10"]), "signal"] = -1
        elif self.mode == "ma5_ma20":
            result.loc[cross_up(result["MA5"], result["MA20"]), "signal"] = 1
            result.loc[cross_down(result["MA5"], result["MA20"]), "signal"] = -1
        else:
            bullish = (result["MA5"] > result["MA10"]) & (result["MA10"] > result["MA20"])
            was_bullish = bullish.shift(1, fill_value=False)
            result.loc[(~was_bullish) & bullish, "signal"] = 1
            result.loc[was_bullish & (~bullish), "signal"] = -1
        return result
