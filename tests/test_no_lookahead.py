import pandas as pd

from ashare_backtester.engine.backtest_engine import BacktestEngine
from ashare_backtester.engine.broker import BrokerConfig
from ashare_backtester.strategies.base import Strategy


class BuyLastDayStrategy(Strategy):
    name = "buy-last-day"

    def generate_signals(self, df):
        result = df.copy()
        result["signal"] = 0
        result.loc[result.index[-1], "signal"] = 1
        return result


def test_no_future_function_last_day_signal_cannot_trade_same_day():
    df = pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=3, freq="D"),
            "open": [10, 11, 12],
            "high": [10, 11, 12],
            "low": [10, 11, 12],
            "close": [10, 11, 12],
            "volume": 1000,
            "amount": 10000,
        }
    )
    result = BacktestEngine(100000, BrokerConfig(slippage_rate=0)).run(df, BuyLastDayStrategy())
    assert result.trades.empty
