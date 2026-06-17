import pandas as pd

from ashare_backtester.indicators.kdj import calculate_kdj
from ashare_backtester.strategies.kdj_strategy import KDJStrategy


def sample_df(close):
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=len(close), freq="D"),
            "open": close,
            "high": [v + 1 for v in close],
            "low": [v - 1 for v in close],
            "close": close,
            "volume": 1000,
            "amount": 10000,
        }
    )


def test_kdj_calculation_correct():
    df = sample_df([10, 11, 12, 13, 14])
    result = calculate_kdj(df, period=3, k_smooth=3, d_smooth=3)
    assert {"K", "D", "J"}.issubset(result.columns)
    assert round(result.loc[2, "K"], 4) == 58.3333
    assert round(result.loc[2, "D"], 4) == 52.7778
    assert round(result.loc[2, "J"], 4) == 69.4444


def test_kdj_golden_cross_correct():
    df = sample_df([10, 9, 8, 9, 10, 11, 12])
    result = KDJStrategy(period=3).generate_signals(df)
    assert (result["signal"] == 1).any()


def test_kdj_death_cross_correct():
    df = sample_df([10, 11, 12, 11, 10, 9, 8])
    result = KDJStrategy(period=3).generate_signals(df)
    assert (result["signal"] == -1).any()
