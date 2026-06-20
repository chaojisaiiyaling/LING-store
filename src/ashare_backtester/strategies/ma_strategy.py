import pandas as pd

from ashare_backtester.indicators.ma import add_moving_averages
from ashare_backtester.strategies.base import Strategy, cross_down, cross_up


BIAS_CONFIGS = {
    "bias_conservative": {
        "name": "BIAS20超跌反弹-保守",
        "lookback": 3,
        "buy_threshold": -5.0,
        "sell_threshold": 5.0,
        "sell_ma": "MA10",
        "max_hold_days": 10,
        "profit_trigger": None,
        "drawdown_limit": None,
    },
    "bias_standard": {
        "name": "BIAS20超跌反弹-标准",
        "lookback": 3,
        "buy_threshold": -5.0,
        "sell_threshold": 8.0,
        "sell_ma": "MA10",
        "max_hold_days": 15,
        "profit_trigger": 0.12,
        "drawdown_limit": 0.05,
    },
    "bias_aggressive": {
        "name": "BIAS20超跌反弹-激进",
        "lookback": 5,
        "buy_threshold": -8.0,
        "sell_threshold": 10.0,
        "sell_ma": "MA20",
        "max_hold_days": 20,
        "profit_trigger": 0.15,
        "drawdown_limit": 0.06,
    },
}


class MAStrategy(Strategy):
    def __init__(self, mode: str):
        self.mode = mode
        self.name = {
            "ma5_ma10": "MA5/MA10短线金叉",
            "ma5_ma20": "MA5/MA20趋势突破",
            "bullish": "MA5/MA10/MA20多头排列",
            "bullish_pullback": "均线多头缩量回踩MA5",
            **{mode_name: config["name"] for mode_name, config in BIAS_CONFIGS.items()},
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
        elif self.mode == "bullish_pullback":
            result = self._generate_bullish_pullback_signals(result)
        else:
            result = self._generate_bias_signals(result)
        return result

    def _generate_bullish_pullback_signals(self, result: pd.DataFrame) -> pd.DataFrame:
        result["VOL5"] = result["volume"].rolling(5, min_periods=1).mean()
        result["BIAS20"] = (result["close"] - result["MA20"]) / result["MA20"] * 100

        bullish = (result["MA5"] > result["MA10"]) & (result["MA10"] > result["MA20"])
        touched_ma5 = result["low"] <= result["MA5"] * 1.02
        recent_touched_ma5 = touched_ma5.rolling(3, min_periods=1).max().astype(bool)
        close_near_ma5 = result["close"] >= result["MA5"] * 0.99
        shrink_volume = result["volume"] <= result["VOL5"].shift(1) * 1.10
        not_weak = result["close"] >= result["close"].shift(1) * 0.995
        not_extended = result["BIAS20"] <= 12
        raw_buy = bullish & recent_touched_ma5 & close_near_ma5 & shrink_volume & not_weak & not_extended

        daily_return = result["close"] / result["close"].shift(1) - 1
        volume_surge = result["volume"] > result["VOL5"].shift(1) * 1.5
        price_stall = daily_return < 0.01
        raw_sell = (
            (volume_surge & price_stall)
            | (result["BIAS20"] > 12)
            | (result["close"] < result["MA10"])
            | cross_down(result["MA5"], result["MA10"])
        )

        result.loc[raw_buy, "signal"] = 1
        result.loc[raw_sell & ~raw_buy, "signal"] = -1
        return result

    def _generate_bias_signals(self, result: pd.DataFrame) -> pd.DataFrame:
        config = BIAS_CONFIGS[self.mode]
        result["BIAS20"] = (result["close"] - result["MA20"]) / result["MA20"] * 100
        recent_oversold = result["BIAS20"].rolling(config["lookback"], min_periods=1).min() < config["buy_threshold"]
        close_cross_ma5 = cross_up(result["close"], result["MA5"])
        close_up = result["close"] > result["close"].shift(1)
        raw_buy = recent_oversold & close_cross_ma5 & close_up

        in_position = False
        entry_close = 0.0
        peak_return = 0.0
        hold_days = 0
        signals = []

        for i, row in result.iterrows():
            signal = 0
            close = float(row["close"])
            if in_position:
                hold_days += 1
                current_return = close / entry_close - 1 if entry_close > 0 else 0.0
                peak_return = max(peak_return, current_return)
                trailing_exit = False
                if config["profit_trigger"] is not None and peak_return >= config["profit_trigger"]:
                    trailing_exit = peak_return - current_return > config["drawdown_limit"]
                if (
                    row["BIAS20"] > config["sell_threshold"]
                    or close < float(row[config["sell_ma"]])
                    or hold_days > config["max_hold_days"]
                    or trailing_exit
                ):
                    signal = -1
                    in_position = False
            elif bool(raw_buy.iloc[i]):
                signal = 1
                in_position = True
                entry_close = close
                peak_return = 0.0
                hold_days = 0
            signals.append(signal)

        result["signal"] = signals
        return result
