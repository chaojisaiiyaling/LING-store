from datetime import date, timedelta

import streamlit as st

from ashare_backtester.config import (
    DEFAULT_BUY_COMMISSION_RATE,
    DEFAULT_INITIAL_CASH,
    DEFAULT_MIN_COMMISSION,
    DEFAULT_SELL_COMMISSION_RATE,
    DEFAULT_SLIPPAGE_RATE,
    DEFAULT_STAMP_TAX_RATE,
)
from ashare_backtester.data.akshare_provider import AKShareDataProvider
from ashare_backtester.engine.backtest_engine import BacktestEngine
from ashare_backtester.engine.broker import BrokerConfig
from ashare_backtester.reports.charts import indicator_chart, nav_chart, price_signal_chart
from ashare_backtester.strategies import KDJStrategy, MACDStrategy, MAStrategy


def _format_pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def _build_strategy(strategy_name: str):
    if strategy_name == "KDJ金叉死叉":
        period = st.number_input("KDJ周期", min_value=2, max_value=120, value=9, step=1, key="kdj_period")
        k_smooth = st.number_input("K平滑参数", min_value=1, max_value=30, value=3, step=1, key="kdj_k")
        d_smooth = st.number_input("D平滑参数", min_value=1, max_value=30, value=3, step=1, key="kdj_d")
        return KDJStrategy(period, k_smooth, d_smooth)
    if strategy_name == "MACD金叉死叉":
        fast = st.number_input("fast", min_value=2, max_value=120, value=12, step=1, key="macd_fast")
        slow = st.number_input("slow", min_value=3, max_value=240, value=26, step=1, key="macd_slow")
        signal = st.number_input("signal", min_value=2, max_value=120, value=9, step=1, key="macd_signal")
        if fast >= slow:
            st.warning("fast 应小于 slow。")
        return MACDStrategy(fast, slow, signal)
    mode = {
        "MA5上穿MA10": "ma5_ma10",
        "MA5上穿MA20": "ma5_ma20",
        "MA5/MA10/MA20多头排列": "bullish",
    }[strategy_name]
    return MAStrategy(mode)


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
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("凌氏资本时间空间交易系统")

    symbol = st.text_input("股票代码", value="000001", help="例如 000001、600519").strip()
    today = date.today()
    start_date = st.date_input("开始日期", value=today - timedelta(days=365 * 3))
    end_date = st.date_input("结束日期", value=today)
    initial_cash = st.number_input("初始资金", min_value=1000.0, value=DEFAULT_INITIAL_CASH, step=10000.0)
    strategy_name = st.selectbox(
        "策略选择",
        ["KDJ金叉死叉", "MACD金叉死叉", "MA5上穿MA10", "MA5上穿MA20", "MA5/MA10/MA20多头排列"],
    )

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

    try:
        with st.spinner("正在获取行情并回测..."):
            provider = AKShareDataProvider()
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

    metrics = result.metrics
    col1, col2 = st.columns(2, gap="small")
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
