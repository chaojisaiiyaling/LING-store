import pandas as pd

from ashare_backtester.engine.suitability import evaluate_strategy_suitability


def sample_bars(close, buy_indices=None):
    buy_indices = buy_indices or []
    signals = [1 if i in buy_indices else 0 for i in range(len(close))]
    return pd.DataFrame(
        {
            "trade_date": pd.date_range("2026-01-01", periods=len(close), freq="D"),
            "open": close,
            "high": close,
            "low": close,
            "close": close,
            "volume": 1000,
            "amount": 10000,
            "signal": signals,
        }
    )


def test_trend_strategy_scores_strong_trend_higher_than_downtrend():
    uptrend = sample_bars([10 + i * 0.08 for i in range(90)], buy_indices=[20, 50])
    downtrend = sample_bars([20 - i * 0.08 for i in range(90)])

    up_score = evaluate_strategy_suitability(uptrend, "MA5/MA10/MA20多头排列")["score"]
    down_score = evaluate_strategy_suitability(downtrend, "MA5/MA10/MA20多头排列")["score"]

    assert up_score > down_score
    assert 0 <= up_score <= 100
    assert up_score < 95


def test_rebound_strategy_scores_oversold_recovery():
    close = [100] * 30 + [80, 78, 76, 79, 82, 84, 86, 88, 90, 92]
    result = evaluate_strategy_suitability(sample_bars(close, buy_indices=[34]), "BIAS20超跌反弹-标准")

    assert result["score"] >= 60
    assert "最低BIAS20" in result["details"][0]


def test_no_buy_signal_caps_score():
    close = [100] * 30 + [80, 78, 76, 79, 82, 84, 86, 88, 90, 92]
    result = evaluate_strategy_suitability(sample_bars(close), "BIAS20超跌反弹-标准")

    assert result["score"] <= 45


def test_suitability_handles_short_data():
    result = evaluate_strategy_suitability(sample_bars([10, 11, 12]), "MACD零轴上方金叉")

    assert result["score"] == 0
    assert result["level"] == "无法评分"
