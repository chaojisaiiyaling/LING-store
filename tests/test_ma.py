import pandas as pd

from ashare_backtester.strategies.ma_strategy import MAStrategy


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


def test_ma5_cross_ma10_correct():
    df = sample_df([10, 10, 10, 10, 10, 9, 8, 7, 6, 5, 20, 20])
    result = MAStrategy("ma5_ma10").generate_signals(df)
    assert (result["signal"] == 1).any()


def test_ma5_cross_ma20_correct():
    df = sample_df([10] * 15 + [5] * 5 + [30] * 5)
    result = MAStrategy("ma5_ma20").generate_signals(df)
    assert (result["signal"] == 1).any()


def test_bullish_alignment_correct():
    df = sample_df([10] * 20 + [12, 14, 16, 18, 20])
    result = MAStrategy("bullish").generate_signals(df)
    assert (result["MA5"] > result["MA10"]).iloc[-1]
    assert (result["MA10"] > result["MA20"]).iloc[-1]
    assert (result["signal"] == 1).any()
