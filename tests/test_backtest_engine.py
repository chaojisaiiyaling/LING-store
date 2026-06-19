import pandas as pd

from ashare_backtester.engine.backtest_engine import BacktestEngine
from ashare_backtester.engine.broker import BrokerConfig, buy_commission, sell_costs
from ashare_backtester.strategies.base import Strategy


class FixedSignalStrategy(Strategy):
    name = "fixed"

    def __init__(self, signals):
        self.signals = signals

    def generate_signals(self, df):
        result = df.copy()
        result["signal"] = self.signals
        return result


def sample_df():
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=5, freq="D"),
            "open": [10, 11, 12, 13, 14],
            "high": [10, 11, 12, 13, 14],
            "low": [10, 11, 12, 13, 14],
            "close": [10, 11, 12, 13, 14],
            "volume": 1000,
            "amount": 10000,
        }
    )


def test_signal_executes_at_next_day_open():
    result = BacktestEngine(100000, BrokerConfig(slippage_rate=0)).run(sample_df(), FixedSignalStrategy([1, 0, 0, -1, 0]))
    assert result.trades.loc[0, "signal_date"] == pd.Timestamp("2024-01-01")
    assert result.trades.loc[0, "trade_date"] == pd.Timestamp("2024-01-02")
    assert result.trades.loc[0, "price"] == 11
    assert result.trades.loc[1, "trade_date"] == pd.Timestamp("2024-01-05")
    assert result.trades.loc[1, "price"] == 14


def test_buy_quantity_is_100_share_lot():
    result = BacktestEngine(100000, BrokerConfig(slippage_rate=0)).run(sample_df(), FixedSignalStrategy([1, 0, 0, 0, 0]))
    assert result.trades.loc[0, "shares"] % 100 == 0


def test_costs_min_commission_and_stamp_tax_correct():
    config = BrokerConfig(buy_commission_rate=0.0003, sell_commission_rate=0.0003, min_commission=5, stamp_tax_rate=0.001)
    assert buy_commission(1000, config) == 5
    commission, stamp_tax = sell_costs(10000, config)
    assert commission == 5
    assert stamp_tax == 10


def test_stop_loss_executes_next_day_open_without_lookahead():
    df = pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=4, freq="D"),
            "open": [10, 10, 9, 8],
            "high": [10, 10, 9, 8],
            "low": [10, 10, 9, 8],
            "close": [10, 9, 8, 8],
            "volume": 1000,
            "amount": 10000,
        }
    )
    result = BacktestEngine(100000, BrokerConfig(slippage_rate=0), stop_loss_pct=0.1).run(
        df,
        FixedSignalStrategy([1, 0, 0, 0]),
    )
    assert result.trades.loc[1, "signal_date"] == pd.Timestamp("2024-01-02")
    assert result.trades.loc[1, "trade_date"] == pd.Timestamp("2024-01-03")
    assert result.trades.loc[1, "price"] == 9
    assert result.trades.loc[1, "reason"] == "STOP_LOSS"
