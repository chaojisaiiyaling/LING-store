import pandas as pd

from ashare_backtester.indicators.ma import add_moving_averages
from ashare_backtester.strategies.base import Strategy, cross_down, cross_up


class MAStrategy(Strategy):
    def __init__(self, mode: str):
        self.mode = mode
        self.name = {
            "ma5_ma10": "MA5/MA10短线金叉",
            "ma5_ma20": "MA5/MA20趋势突破",
            "bullish": "MA5/MA10/MA20多头排列",
            "bias_rebound": "乖离率超跌反弹",
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
        elif self.mode == "bullish":
            bullish = (result["MA5"] > result["MA10"]) & (result["MA10"] > result["MA20"]) & (result["close"] > result["MA5"])
            was_bullish = bullish.shift(1, fill_value=False)
            result.loc[(~was_bullish) & bullish, "signal"] = 1
            result.loc[(result["close"] < result["MA20"]) | cross_down(result["MA5"], result["MA10"]), "signal"] = -1
        else:
            result["BIAS20"] = (result["close"] - result["MA20"]) / result["MA20"]
            result.loc[(result["BIAS20"] < -0.08) & cross_up(result["close"], result["MA5"]), "signal"] = 1
            result.loc[(result["BIAS20"] > 0.08) | (result["close"] < result["MA10"]), "signal"] = -1
        return result
