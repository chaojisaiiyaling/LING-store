from dataclasses import dataclass


@dataclass
class BrokerConfig:
    buy_commission_rate: float = 0.0003
    sell_commission_rate: float = 0.0003
    min_commission: float = 5.0
    stamp_tax_rate: float = 0.001
    slippage_rate: float = 0.0005


def buy_commission(amount: float, config: BrokerConfig) -> float:
    return max(amount * config.buy_commission_rate, config.min_commission)


def sell_costs(amount: float, config: BrokerConfig) -> tuple[float, float]:
    commission = max(amount * config.sell_commission_rate, config.min_commission)
    stamp_tax = amount * config.stamp_tax_rate
    return commission, stamp_tax


def calculate_lot_size(cash: float, open_price: float, config: BrokerConfig, invest_ratio: float = 0.95) -> int:
    if cash <= 0 or open_price <= 0:
        return 0
    execution_price = open_price * (1 + config.slippage_rate)
    spendable = cash * invest_ratio
    shares = int(spendable / (execution_price * (1 + config.buy_commission_rate)) // 100 * 100)
    while shares > 0:
        gross = shares * execution_price
        if gross + buy_commission(gross, config) <= spendable:
            return shares
        shares -= 100
    return 0
