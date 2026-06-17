import pandas as pd

from ashare_backtester.indicators.macd import calculate_macd
from ashare_backtester.strategies.macd_strategy import MACDStrategy


def sample_df(close):
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=len(close), freq="D"),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 1000,
            "amount": 10000,
        }
    )


def test_macd_calculation_correct():
    df = sample_df([10, 11, 12, 13])
    result = calculate_macd(df, fast=2, slow=3, signal=2)
    assert {"DIF", "DEA", "MACD"}.issubset(result.columns)
    assert round(result.loc[1, "DIF"], 4) == 0.1667
    assert round(result.loc[1, "DEA"], 4) == 0.1111
    assert round(result.loc[1, "MACD"], 4) == 0.1111


def test_macd_golden_cross_correct():
    df = sample_df([10, 9, 8, 9, 10, 11, 12, 13])
    result = MACDStrategy(fast=2, slow=4, signal=2).generate_signals(df)
    assert (result["signal"] == 1).any()


def test_macd_death_cross_correct():
    df = sample_df([10, 11, 12, 13, 12, 11, 10, 9])
    result = MACDStrategy(fast=2, slow=4, signal=2).generate_signals(df)
    assert (result["signal"] == -1).any()
