from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


ATR_EXPLANATION = (
    "ATR不是预测上涨或下跌的指标，而是衡量股票最近正常波动幅度的指标。"
    "ATR越大，说明股票波动越大，止损和止盈距离应该适当放宽。"
    "ATR越小，说明股票波动越小，止损和止盈距离可以适当收紧。"
)


@dataclass(frozen=True)
class ATRRiskResult:
    close: float
    atr14: float
    atr_pct: float
    volatility_level: str
    conservative_stop: float
    standard_stop: float
    loose_stop: float
    short_take_profit: float
    standard_take_profit: float
    trend_take_profit: float
    trailing_stop_formula: str
    trailing_stop_example: str
    explanation: str


def calculate_true_range(df: pd.DataFrame) -> pd.Series:
    required = {"high", "low", "close"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"ATR测算缺少必要字段: {', '.join(sorted(missing))}")

    high = pd.to_numeric(df["high"], errors="coerce")
    low = pd.to_numeric(df["low"], errors="coerce")
    close = pd.to_numeric(df["close"], errors="coerce")
    previous_close = close.shift(1)
    ranges = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    )
    return ranges.max(axis=1)


def volatility_level(atr_pct: float) -> str:
    if atr_pct < 2:
        return "低波动"
    if atr_pct < 4:
        return "中等波动"
    if atr_pct < 6:
        return "高波动"
    return "极高波动"


def calculate_atr_risk(df: pd.DataFrame, period: int = 14) -> ATRRiskResult:
    if len(df) < period:
        raise ValueError(f"ATR{period}测算至少需要{period}个交易日数据，请延长回测区间。")

    clean = df.copy().dropna(subset=["high", "low", "close"]).reset_index(drop=True)
    if len(clean) < period:
        raise ValueError(f"ATR{period}测算有效行情不足，请检查数据源或延长回测区间。")

    tr = calculate_true_range(clean)
    atr = float(tr.tail(period).mean())
    close = float(clean["close"].iloc[-1])
    if close <= 0:
        raise ValueError("当前收盘价异常，无法进行ATR测算。")

    atr_pct = atr / close * 100
    trailing_example_high = close + 4 * atr
    trailing_example = trailing_example_high - 2 * atr

    return ATRRiskResult(
        close=close,
        atr14=atr,
        atr_pct=atr_pct,
        volatility_level=volatility_level(atr_pct),
        conservative_stop=close - 1 * atr,
        standard_stop=close - 2 * atr,
        loose_stop=close - 3 * atr,
        short_take_profit=close + 2 * atr,
        standard_take_profit=close + 4 * atr,
        trend_take_profit=close + 6 * atr,
        trailing_stop_formula="移动止盈价 = 持仓后最高价 - 2 * ATR14",
        trailing_stop_example=f"例如持仓后最高价达到{trailing_example_high:.2f}，移动止盈价约为{trailing_example:.2f}。",
        explanation=ATR_EXPLANATION,
    )
