import pandas as pd
import pytest

from ashare_backtester.engine.atr_risk import calculate_atr_risk, calculate_true_range, volatility_level


def sample_df(high, low, close):
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2026-01-01", periods=len(close), freq="D"),
            "open": close,
            "high": high,
            "low": low,
            "close": close,
            "volume": 1000,
            "amount": 10000,
        }
    )


def test_true_range_calculation():
    df = sample_df(high=[11, 13, 12], low=[9, 10, 8], close=[10, 12, 9])
    tr = calculate_true_range(df)

    assert tr.tolist() == [2.0, 3.0, 4.0]


def test_atr_risk_prices_are_correct():
    df = sample_df(high=[11] * 15, low=[9] * 15, close=[10] * 15)
    result = calculate_atr_risk(df)

    assert result.close == 10
    assert result.atr14 == 2
    assert result.atr_pct == 20
    assert result.conservative_stop == 8
    assert result.standard_stop == 6
    assert result.loose_stop == 4
    assert result.short_take_profit == 14
    assert result.standard_take_profit == 18
    assert result.trend_take_profit == 22
    assert result.volatility_level == "极高波动"


def test_volatility_level_thresholds():
    assert volatility_level(1.99) == "低波动"
    assert volatility_level(2.0) == "中等波动"
    assert volatility_level(4.0) == "高波动"
    assert volatility_level(6.0) == "极高波动"


def test_atr_requires_enough_data():
    df = sample_df(high=[11] * 5, low=[9] * 5, close=[10] * 5)

    with pytest.raises(ValueError):
        calculate_atr_risk(df)
