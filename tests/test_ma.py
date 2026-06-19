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
    assert (result["close"] > result["MA5"]).iloc[-1]
    assert (result["signal"] == 1).any()


def test_bullish_sell_on_close_below_ma20_or_ma5_cross_ma10():
    df = sample_df([10] * 20 + [12, 14, 16, 18, 20, 8])
    result = MAStrategy("bullish").generate_signals(df)
    assert result["close"].iloc[-1] < result["MA20"].iloc[-1]
    assert result["signal"].iloc[-1] == -1


def test_bias_conservative_buy_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75, 80, 85])
    result = MAStrategy("bias_conservative").generate_signals(df)
    buy_rows = result[result["signal"] == 1]
    assert not buy_rows.empty
    assert "BIAS20" in result.columns
    assert (buy_rows["BIAS20"] < -5).all()


def test_bias_conservative_sell_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75, 80, 90, 105])
    result = MAStrategy("bias_conservative").generate_signals(df)
    assert (result["BIAS20"] > 5).any()
    assert (result.loc[result["BIAS20"] > 5, "signal"] == -1).any()


def test_bias_standard_buy_and_time_exit_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75] + [76] * 16)
    result = MAStrategy("bias_standard").generate_signals(df)
    buy_index = result.index[result["signal"] == 1][0]
    sell_index = result.index[result["signal"] == -1][-1]
    assert result.loc[buy_index, "BIAS20"] < -5
    assert sell_index - buy_index == 16


def test_bias_standard_trailing_exit_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75, 84, 86, 80])
    result = MAStrategy("bias_standard").generate_signals(df)
    assert (result["signal"] == 1).any()
    assert result["signal"].iloc[-1] == -1


def test_bias_aggressive_buy_and_time_exit_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75] + [88] * 24)
    result = MAStrategy("bias_aggressive").generate_signals(df)
    buy_index = result.index[result["signal"] == 1][0]
    sell_index = result.index[result["signal"] == -1][-1]
    assert result.loc[buy_index, "BIAS20"] < -8
    assert sell_index - buy_index == 21


def test_bias_aggressive_trailing_exit_correct():
    df = sample_df([100] * 20 + [70] * 8 + [75, 88, 90, 84])
    result = MAStrategy("bias_aggressive").generate_signals(df)
    assert (result["signal"] == 1).any()
    assert result["signal"].iloc[-1] == -1
