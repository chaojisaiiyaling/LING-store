from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ashare_backtester.engine.broker import BrokerConfig, buy_commission, calculate_lot_size, sell_costs
from ashare_backtester.engine.metrics import calculate_metrics
from ashare_backtester.strategies.base import Strategy


@dataclass
class BacktestResult:
    bars: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float]
    buy_hold_return: float
    strategy_name: str
    symbol: str


class BacktestEngine:
    def __init__(self, initial_cash: float = 100000.0, broker_config: BrokerConfig | None = None):
        self.initial_cash = float(initial_cash)
        self.broker_config = broker_config or BrokerConfig()

    def run(self, df: pd.DataFrame, strategy: Strategy, symbol: str = "") -> BacktestResult:
        if len(df) < 2:
            raise ValueError("回测至少需要两个交易日数据。")

        bars = strategy.generate_signals(df).copy().reset_index(drop=True)
        cash = self.initial_cash
        shares = 0
        trades: list[dict] = []
        equity_values: list[float] = []
        position_values: list[float] = []

        for i, row in bars.iterrows():
            if i > 0:
                prev_signal = int(bars.loc[i - 1, "signal"])
                if prev_signal == 1 and shares == 0:
                    execution_price = float(row["open"]) * (1 + self.broker_config.slippage_rate)
                    qty = calculate_lot_size(cash, float(row["open"]), self.broker_config)
                    gross = qty * execution_price
                    commission = buy_commission(gross, self.broker_config) if qty else 0.0
                    if qty > 0 and gross + commission <= cash:
                        cash -= gross + commission
                        shares += qty
                        trades.append(
                            {
                                "trade_date": row["trade_date"],
                                "side": "BUY",
                                "price": execution_price,
                                "shares": qty,
                                "amount": gross,
                                "commission": commission,
                                "stamp_tax": 0.0,
                                "signal_date": bars.loc[i - 1, "trade_date"],
                            }
                        )
                elif prev_signal == -1 and shares > 0:
                    execution_price = float(row["open"]) * (1 - self.broker_config.slippage_rate)
                    gross = shares * execution_price
                    commission, stamp_tax = sell_costs(gross, self.broker_config)
                    cash += gross - commission - stamp_tax
                    trades.append(
                        {
                            "trade_date": row["trade_date"],
                            "side": "SELL",
                            "price": execution_price,
                            "shares": shares,
                            "amount": gross,
                            "commission": commission,
                            "stamp_tax": stamp_tax,
                            "signal_date": bars.loc[i - 1, "trade_date"],
                        }
                    )
                    shares = 0

            position_value = shares * float(row["close"])
            position_values.append(position_value)
            equity_values.append(cash + position_value)

        bars["position_value"] = position_values
        bars["equity"] = equity_values
        bars["strategy_nav"] = bars["equity"] / self.initial_cash
        bars["buy_hold_nav"] = bars["close"] / bars["close"].iloc[0]

        trades_df = pd.DataFrame(
            trades,
            columns=["trade_date", "signal_date", "side", "price", "shares", "amount", "commission", "stamp_tax"],
        )
        metrics = calculate_metrics(bars["equity"], trades_df, self.initial_cash)
        buy_hold_return = float(bars["close"].iloc[-1] / bars["close"].iloc[0] - 1)
        return BacktestResult(bars, trades_df, metrics, buy_hold_return, strategy.name, symbol)
