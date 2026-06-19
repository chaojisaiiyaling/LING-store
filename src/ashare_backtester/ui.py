from datetime import date

import streamlit as st

from ashare_backtester.config import (
    DEFAULT_BUY_COMMISSION_RATE,
    DEFAULT_INITIAL_CASH,
    DEFAULT_MIN_COMMISSION,
    DEFAULT_SELL_COMMISSION_RATE,
    DEFAULT_SLIPPAGE_RATE,
    DEFAULT_STAMP_TAX_RATE,
)
from ashare_backtester.data import DATA_SOURCE_OPTIONS, build_data_provider
from ashare_backtester.engine.backtest_engine import BacktestEngine
from ashare_backtester.engine.broker import BrokerConfig
from ashare_backtester.reports.charts import indicator_chart, nav_chart, price_signal_chart
from ashare_backtester.strategies import KDJStrategy, MACDStrategy, MAStrategy


STRATEGY_DESCRIPTIONS = {
    "KDJ低位金叉": {
        "buy": "K线上穿D线，且K值小于30",
        "sell": "K线下穿D线，或K值大于80",
    },
    "MACD零轴上方金叉": {
        "buy": "DIF上穿DEA，且DIF大于0，DEA大于0",
        "sell": "DIF下穿DEA",
    },
    "MA5/MA10短线金叉": {
        "buy": "MA5上穿MA10",
        "sell": "MA5下穿MA10",
    },
    "MA5/MA20趋势突破": {
        "buy": "MA5上穿MA20",
        "sell": "MA5下穿MA20",
    },
    "MA5/MA10/MA20多头排列": {
        "buy": "MA5 > MA10 > MA20，且收盘价大于MA5",
        "sell": "收盘价跌破MA20，或MA5下穿MA10",
    },
    "BIAS20超跌反弹-保守": {
        "buy": "最近3个交易日内，BIAS20曾经小于-5；今日收盘价重新站上MA5；今日收盘价高于昨日收盘价",
        "sell": "BIAS20大于5；或收盘价跌破MA10；或持仓超过10个交易日",
        "scene": "短线超跌反弹，快进快出。",
        "risk": "卖出较快，可能错过后续大反弹。",
    },
    "BIAS20超跌反弹-标准": {
        "buy": "最近3个交易日内，BIAS20曾经小于-5；今日收盘价重新站上MA5；今日收盘价高于昨日收盘价",
        "sell": "BIAS20大于8；或收盘价跌破MA10；或持仓超过15个交易日；或持仓收益率达到12%后，从最高收益回撤超过5%",
        "scene": "普通超跌反弹，平衡交易次数和收益空间。",
        "risk": "震荡下跌行情中可能出现反复假反弹。",
    },
    "BIAS20超跌反弹-激进": {
        "buy": "最近5个交易日内，BIAS20曾经小于-8；今日收盘价重新站上MA5；今日收盘价高于昨日收盘价",
        "sell": "BIAS20大于10；或收盘价跌破MA20；或持仓超过20个交易日；或持仓收益率达到15%后，从最高收益回撤超过6%",
        "scene": "深度超跌后的反弹修复。",
        "risk": "买入信号较少，且如果趋势继续下跌，回撤可能较大。",
    },
}


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_money(value: float) -> str:
    return f"¥{value:,.2f}"


def _build_strategy(strategy_name: str):
    if strategy_name == "KDJ低位金叉":
        period = st.number_input("KDJ周期", min_value=2, max_value=120, value=9, step=1, key="kdj_period")
        k_smooth = st.number_input("K平滑参数", min_value=1, max_value=30, value=3, step=1, key="kdj_k")
        d_smooth = st.number_input("D平滑参数", min_value=1, max_value=30, value=3, step=1, key="kdj_d")
        return KDJStrategy(period, k_smooth, d_smooth)
    if strategy_name == "MACD零轴上方金叉":
        fast = st.number_input("fast", min_value=2, max_value=120, value=12, step=1, key="macd_fast")
        slow = st.number_input("slow", min_value=3, max_value=240, value=26, step=1, key="macd_slow")
        signal = st.number_input("signal", min_value=2, max_value=120, value=9, step=1, key="macd_signal")
        if fast >= slow:
            st.warning("fast 应小于 slow。")
        return MACDStrategy(fast, slow, signal)
    mode = {
        "MA5/MA10短线金叉": "ma5_ma10",
        "MA5/MA20趋势突破": "ma5_ma20",
        "MA5/MA10/MA20多头排列": "bullish",
        "BIAS20超跌反弹-保守": "bias_conservative",
        "BIAS20超跌反弹-标准": "bias_standard",
        "BIAS20超跌反弹-激进": "bias_aggressive",
    }[strategy_name]
    return MAStrategy(mode)


def _show_strategy_description(strategy_name: str) -> None:
    description = STRATEGY_DESCRIPTIONS[strategy_name]
    st.markdown(
        f"""
        <div class="strategy-note">
          <div><strong>买入条件：</strong>{description["buy"]}</div>
          <div><strong>卖出条件：</strong>{description["sell"]}</div>
          <div><strong>适用场景：</strong>{description.get("scene", "按固定技术条件执行。")}</div>
          <div><strong>风险提示：</strong>{description.get("risk", "技术指标可能出现假信号，请结合风险控制。")}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title="凌氏资本时间空间交易系统", page_icon="📈", layout="centered")
    st.markdown(
        """
        <style>
        .stButton > button {
            min-height: 3rem;
            border-radius: 8px;
            font-weight: 700;
        }
        [data-testid="stMetric"] {
            background: #f8fafc;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 0.75rem;
        }
        [data-testid="stMetricLabel"] {
            font-size: 0.86rem;
        }
        .strategy-note {
            border: 1px solid #d1d5db;
            background: #f9fafb;
            border-radius: 8px;
            padding: 0.8rem 0.9rem;
            line-height: 1.7;
            margin: 0.2rem 0 1rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("凌氏资本时间空间交易系统")

    symbol = st.text_input("股票代码", value="000001", help="例如 000001、600519").strip()
    data_source = st.selectbox("数据接口", list(DATA_SOURCE_OPTIONS.keys()))
    selected_source = DATA_SOURCE_OPTIONS[data_source]
    st.caption(selected_source["description"])
    today = date.today()
    start_date = st.date_input("开始日期", value=date(2026, 1, 1))
    end_date = st.date_input("结束日期", value=today)
    initial_cash = st.number_input("初始资金", min_value=1000.0, value=DEFAULT_INITIAL_CASH, step=10000.0)
    strategy_name = st.selectbox(
        "策略选择",
        list(STRATEGY_DESCRIPTIONS.keys()),
    )

    st.subheader("策略说明")
    _show_strategy_description(strategy_name)

    st.subheader("策略参数")
    strategy = _build_strategy(strategy_name)

    with st.expander("高级设置", expanded=False):
        buy_commission_rate = st.number_input("买入佣金率", min_value=0.0, value=DEFAULT_BUY_COMMISSION_RATE, format="%.6f")
        sell_commission_rate = st.number_input("卖出佣金率", min_value=0.0, value=DEFAULT_SELL_COMMISSION_RATE, format="%.6f")
        min_commission = st.number_input("最低佣金", min_value=0.0, value=DEFAULT_MIN_COMMISSION, step=1.0)
        stamp_tax_rate = st.number_input("印花税", min_value=0.0, value=DEFAULT_STAMP_TAX_RATE, format="%.6f")
        slippage_rate = st.number_input("滑点", min_value=0.0, value=DEFAULT_SLIPPAGE_RATE, format="%.6f")
        use_risk_control = st.checkbox("启用止损/止盈", value=False)
        stop_loss_pct = 0.0
        take_profit_pct = 0.0
        if use_risk_control:
            stop_loss_pct = st.number_input("止损比例", min_value=0.0, max_value=0.8, value=0.08, step=0.01, format="%.2f")
            take_profit_pct = st.number_input("止盈比例", min_value=0.0, max_value=3.0, value=0.20, step=0.01, format="%.2f")

    run = st.button("开始回测", use_container_width=True, type="primary")
    if not run:
        return

    if start_date >= end_date:
        st.error("开始日期必须早于结束日期。")
        return
    if not selected_source["enabled"]:
        st.error("该数据接口当前版本尚未接入，请先选择 AKShare 或 BaoStock。")
        return

    try:
        with st.spinner("正在获取行情并回测..."):
            provider = build_data_provider(data_source)
            data = provider.get_daily(symbol, start_date.isoformat(), end_date.isoformat())
            config = BrokerConfig(buy_commission_rate, sell_commission_rate, min_commission, stamp_tax_rate, slippage_rate)
            result = BacktestEngine(
                initial_cash,
                config,
                stop_loss_pct=stop_loss_pct if use_risk_control and stop_loss_pct > 0 else None,
                take_profit_pct=take_profit_pct if use_risk_control and take_profit_pct > 0 else None,
            ).run(data, strategy, symbol=symbol)
    except Exception as exc:
        st.error(str(exc))
        return

    st.success("回测完成")
    st.markdown(f"**{symbol}** ｜ {start_date.isoformat()} 至 {end_date.isoformat()} ｜ {result.strategy_name}")
    if not (result.bars["signal"] == 1).any():
        st.info("当前策略参数下未触发买入信号，可尝试选择更保守版本或延长回测周期。")

    metrics = result.metrics
    final_equity = float(result.bars["equity"].iloc[-1])
    profit_loss = final_equity - float(initial_cash)

    col1, col2 = st.columns(2, gap="small")
    col1.metric("初始资金", _format_money(initial_cash))
    col2.metric("期末总资产", _format_money(final_equity), delta=_format_money(profit_loss))
    col1.metric("总收益率", _format_pct(metrics["total_return"]))
    col2.metric("年化收益率", _format_pct(metrics["annual_return"]))
    col1.metric("最大回撤", _format_pct(metrics["max_drawdown"]))
    col2.metric("夏普比率", f"{metrics['sharpe']:.2f}")
    col1.metric("胜率", _format_pct(metrics["win_rate"]))
    col2.metric("交易次数", str(metrics["trade_count"]))
    st.metric("买入并持有收益率", _format_pct(result.buy_hold_return))

    tab_nav, tab_price, tab_indicator, tab_trades = st.tabs(["净值", "买卖点", "指标", "交易"])
    with tab_nav:
        st.plotly_chart(nav_chart(result.bars), use_container_width=True)
    with tab_price:
        st.plotly_chart(price_signal_chart(result.bars, result.trades), use_container_width=True)
    with tab_indicator:
        st.plotly_chart(indicator_chart(result.bars, strategy_name), use_container_width=True)

    with tab_trades:
        if result.trades.empty:
            st.info("本次回测没有产生已成交交易。")
        else:
            st.dataframe(result.trades, use_container_width=True, hide_index=True)
