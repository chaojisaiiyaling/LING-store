from __future__ import annotations

import pandas as pd


TREND_STRATEGIES = {"MACD零轴上方金叉", "MA5/MA20趋势突破", "MA5/MA10/MA20多头排列"}
SHORT_SWING_STRATEGIES = {"KDJ低位金叉", "MA5/MA10短线金叉"}
REBOUND_STRATEGIES = {"BIAS20超跌反弹-保守", "BIAS20超跌反弹-标准", "BIAS20超跌反弹-激进"}


def _clip_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def _level(score: int) -> str:
    if score >= 80:
        return "较适合"
    if score >= 60:
        return "可以观察"
    if score >= 40:
        return "谨慎使用"
    return "不太适合"


def _ma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=max(2, window // 2)).mean()


def _score_range(value: float, good_low: float, good_high: float, soft_low: float, soft_high: float, points: int) -> float:
    if good_low <= value <= good_high:
        return points
    if soft_low <= value < good_low:
        return points * (value - soft_low) / (good_low - soft_low)
    if good_high < value <= soft_high:
        return points * (soft_high - value) / (soft_high - good_high)
    return 0.0


def _apply_signal_cap(score: float, buy_signals: int) -> float:
    if buy_signals == 0:
        return min(score, 45)
    if buy_signals <= 1:
        return min(score, 75)
    return score


def evaluate_strategy_suitability(bars: pd.DataFrame, strategy_name: str) -> dict[str, object]:
    if bars.empty or "close" not in bars.columns:
        return {
            "score": 0,
            "level": "无法评分",
            "summary": "行情数据不足，无法判断策略适配度。",
            "details": [],
        }

    close = pd.to_numeric(bars["close"], errors="coerce").dropna()
    if len(close) < 20:
        return {
            "score": 0,
            "level": "无法评分",
            "summary": "回测交易日太少，建议延长回测周期后再看评分。",
            "details": [],
        }

    ma20 = _ma(close, 20)
    ma60 = _ma(close, 60)
    daily_returns = close.pct_change().dropna()
    total_return = float(close.iloc[-1] / close.iloc[0] - 1)
    max_drawdown = float((close / close.cummax() - 1).min())
    volatility = float(daily_returns.std(ddof=0)) if not daily_returns.empty else 0.0
    above_ma20_ratio = float((close > ma20).mean())
    above_ma60_ratio = float((close > ma60).mean()) if ma60.notna().any() else above_ma20_ratio
    ma20_slope = float(ma20.iloc[-1] / ma20.dropna().iloc[0] - 1) if ma20.dropna().size >= 2 else 0.0
    ma60_ready = bool(pd.notna(ma60.iloc[-1]))
    ma_alignment = bool(ma60_ready and close.iloc[-1] > ma20.iloc[-1] > ma60.iloc[-1])
    bias20 = (close - ma20) / ma20 * 100
    min_bias20 = float(bias20.min()) if bias20.notna().any() else 0.0
    last_above_ma5 = bool(close.iloc[-1] > _ma(close, 5).iloc[-1])
    buy_signals = int((bars["signal"] == 1).sum()) if "signal" in bars.columns else 0

    if strategy_name in TREND_STRATEGIES:
        score = 20
        score += 18 if total_return > 0.05 else 9 if total_return > 0 else 0
        score += 20 if ma20_slope > 0.08 else 12 if ma20_slope > 0.02 else 4 if ma20_slope > 0 else 0
        score += 18 if above_ma60_ratio > 0.70 else 12 if above_ma60_ratio > 0.55 else 4 if above_ma60_ratio > 0.40 else 0
        score += 12 if ma_alignment else 0
        score += 10 if max_drawdown > -0.15 else 5 if max_drawdown > -0.25 else 0
        score += _score_range(volatility, 0.006, 0.035, 0.002, 0.060, 8)
        score = _apply_signal_cap(score, buy_signals)
        details = [
            f"区间涨跌幅 {total_return * 100:.2f}%",
            f"MA20趋势 {'向上' if ma20_slope > 0 else '偏弱'}",
            f"收盘价在MA60上方占比 {above_ma60_ratio * 100:.0f}%",
            f"买入信号 {buy_signals} 次",
        ]
        summary = "这类策略更适合趋势清楚、均线向上的股票。"
    elif strategy_name in SHORT_SWING_STRATEGIES:
        score = 22
        score += _score_range(total_return, -0.10, 0.35, -0.30, 0.70, 18)
        score += _score_range(volatility, 0.012, 0.040, 0.004, 0.070, 22)
        score += 16 if above_ma20_ratio > 0.55 else 10 if above_ma20_ratio > 0.40 else 4 if above_ma20_ratio > 0.25 else 0
        score += 12 if max_drawdown > -0.18 else 6 if max_drawdown > -0.32 else 0
        score += 10 if buy_signals >= 2 else 4 if buy_signals == 1 else 0
        details = [
            f"区间涨跌幅 {total_return * 100:.2f}%",
            f"日波动水平 {volatility * 100:.2f}%",
            f"收盘价在MA20上方占比 {above_ma20_ratio * 100:.0f}%",
            f"买入信号 {buy_signals} 次",
        ]
        summary = "这类策略更适合有波动、有反弹，但不是单边阴跌的股票。"
    elif strategy_name in REBOUND_STRATEGIES:
        score = 18
        score += 24 if min_bias20 <= -8 else 18 if min_bias20 <= -5 else 6 if min_bias20 <= -3 else 0
        score += 14 if last_above_ma5 else 0
        score += _score_range(volatility, 0.015, 0.055, 0.006, 0.090, 18)
        score += 12 if max_drawdown > -0.25 else 6 if max_drawdown > -0.45 else 0
        score += 10 if total_return > -0.15 else 4 if total_return > -0.35 else 0
        score += 8 if buy_signals >= 1 else 0
        score = _apply_signal_cap(score, buy_signals)
        details = [
            f"最低BIAS20 {min_bias20:.2f}",
            f"当前收盘价{'站上' if last_above_ma5 else '未站上'}MA5",
            f"最大回撤 {max_drawdown * 100:.2f}%",
            f"买入信号 {buy_signals} 次",
        ]
        summary = "这类策略更适合短期超跌后开始修复、但没有持续崩坏的股票。"
    else:
        score = 50
        details = ["当前策略暂无专门适配模型。"]
        summary = "可结合回测收益、最大回撤和买入并持有对比观察。"

    final_score = _clip_score(score)
    return {
        "score": final_score,
        "level": _level(final_score),
        "summary": summary,
        "details": details,
    }
