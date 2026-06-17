import math

import pandas as pd

from ashare_backtester.config import TRADING_DAYS_PER_YEAR


def calculate_metrics(equity: pd.Series, trades: pd.DataFrame, initial_cash: float) -> dict[str, float]:
    if equity.empty:
        return {}
    daily_returns = equity.pct_change().fillna(0)
    total_return = equity.iloc[-1] / initial_cash - 1
    years = max(len(equity) / TRADING_DAYS_PER_YEAR, 1 / TRADING_DAYS_PER_YEAR)
    annual_return = (1 + total_return) ** (1 / years) - 1 if total_return > -1 else -1
    drawdown = equity / equity.cummax() - 1
    sharpe = 0.0
    if daily_returns.std(ddof=0) > 0:
        sharpe = daily_returns.mean() / daily_returns.std(ddof=0) * math.sqrt(TRADING_DAYS_PER_YEAR)

    wins = []
    buy_amount = None
    for _, row in trades.iterrows():
        if row["side"] == "BUY":
            buy_amount = row["amount"] + row["commission"]
        elif row["side"] == "SELL" and buy_amount:
            sell_net = row["amount"] - row["commission"] - row["stamp_tax"]
            wins.append(sell_net > buy_amount)
            buy_amount = None

    sell_count = int((trades["side"] == "SELL").sum()) if not trades.empty else 0
    win_rate = sum(wins) / len(wins) if wins else 0.0
    return {
        "total_return": float(total_return),
        "annual_return": float(annual_return),
        "max_drawdown": float(drawdown.min()),
        "sharpe": float(sharpe),
        "win_rate": float(win_rate),
        "trade_count": sell_count,
    }
