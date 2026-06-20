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


def sample_ohlcv(close, volume, low=None):
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2024-01-01", periods=len(close), freq="D"),
            "open": close,
            "high": [price * 1.02 for price in close],
            "low": low if low is not None else [price * 0.995 for price in close],
            "close": close,
            "volume": volume,
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


def test_bullish_pullback_buy_correct():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.25, 12.35]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 700]
    result = MAStrategy("bullish_pullback").generate_signals(sample_ohlcv(close, volume))
    row = result.iloc[-1]
    assert row["MA5"] > row["MA10"] > row["MA20"]
    assert row["volume"] <= result["VOL5"].shift(1).iloc[-1] * 1.10
    assert row["signal"] == 1


def test_bullish_pullback_buy_after_recent_ma5_touch_correct():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.28, 12.3]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 1100]
    low = [price * 0.995 for price in close]
    low[-2] = 12.0
    low[-1] = 12.8
    result = MAStrategy("bullish_pullback").generate_signals(sample_ohlcv(close, volume, low=low))
    assert result["low"].iloc[-1] > result["MA5"].iloc[-1] * 1.02
    assert result["volume"].iloc[-1] <= result["VOL5"].shift(1).iloc[-1] * 1.10
    assert result["signal"].iloc[-1] == 1


def test_bullish_pullback_conservative_is_stricter_than_standard():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.28, 12.3]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 1100]
    low = [price * 0.995 for price in close]
    low[-2] = 12.0
    low[-1] = 12.8
    df = sample_ohlcv(close, volume, low=low)
    conservative = MAStrategy("bullish_pullback_conservative").generate_signals(df)
    standard = MAStrategy("bullish_pullback_standard").generate_signals(df)
    assert conservative["signal"].iloc[-1] == 0
    assert standard["signal"].iloc[-1] == 1


def test_bullish_pullback_aggressive_is_looser_than_standard():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.18, 12.22]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 1220]
    low = [price * 0.995 for price in close]
    low[-5] = 11.95
    low[-3] = 12.8
    low[-2] = 12.8
    low[-1] = 12.8
    df = sample_ohlcv(close, volume, low=low)
    standard = MAStrategy("bullish_pullback_standard").generate_signals(df)
    aggressive = MAStrategy("bullish_pullback_aggressive").generate_signals(df)
    assert standard["signal"].iloc[-1] == 0
    assert aggressive["signal"].iloc[-1] == 1


def test_bullish_pullback_sell_on_volume_stall_correct():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.25, 12.35, 12.42]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 700, 2200]
    result = MAStrategy("bullish_pullback").generate_signals(sample_ohlcv(close, volume))
    assert result["volume"].iloc[-1] > result["VOL5"].shift(1).iloc[-1] * 1.5
    assert result["close"].iloc[-1] / result["close"].iloc[-2] - 1 < 0.01
    assert result["signal"].iloc[-1] == -1


def test_bullish_pullback_sell_on_excessive_bias_correct():
    close = [10 + i * 0.08 for i in range(20)] + [11.7, 11.9, 12.1, 12.25, 12.4, 12.25, 12.35, 14.2]
    volume = [1000] * 20 + [1300, 1250, 1200, 1150, 1100, 900, 700, 900]
    result = MAStrategy("bullish_pullback").generate_signals(sample_ohlcv(close, volume))
    assert result["BIAS20"].iloc[-1] > 12
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
