import plotly.graph_objects as go
from plotly.subplots import make_subplots


def nav_chart(bars):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["strategy_nav"], name="策略净值"))
    fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["buy_hold_nav"], name="买入并持有"))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    return fig


def price_signal_chart(bars, trades):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["close"], name="收盘价"))
    if not trades.empty:
        buys = trades[trades["side"] == "BUY"]
        sells = trades[trades["side"] == "SELL"]
        fig.add_trace(go.Scatter(x=buys["trade_date"], y=buys["price"], mode="markers", name="买入", marker=dict(symbol="triangle-up", size=11)))
        fig.add_trace(go.Scatter(x=sells["trade_date"], y=sells["price"], mode="markers", name="卖出", marker=dict(symbol="triangle-down", size=11)))
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    return fig


def indicator_chart(bars, strategy_key):
    if strategy_key == "KDJ低位金叉":
        fig = go.Figure()
        for col in ["K", "D", "J"]:
            fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars[col], name=col))
    elif strategy_key == "MACD零轴上方金叉":
        fig = make_subplots(specs=[[{"secondary_y": False}]])
        fig.add_trace(go.Bar(x=bars["trade_date"], y=bars["MACD"], name="MACD柱"))
        fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["DIF"], name="DIF"))
        fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["DEA"], name="DEA"))
    elif strategy_key.startswith("BIAS20超跌反弹"):
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["close"], name="收盘价"), secondary_y=False)
        for col in ["MA5", "MA10", "MA20"]:
            fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars[col], name=col), secondary_y=False)
        fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["BIAS20"], name="BIAS20"), secondary_y=True)
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars["close"], name="收盘价"))
        for col in ["MA5", "MA10", "MA20"]:
            fig.add_trace(go.Scatter(x=bars["trade_date"], y=bars[col], name=col))
    fig.update_layout(height=360, margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h"))
    return fig
