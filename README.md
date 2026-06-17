# 中国A股简易回测系统

`ashare_backtester` 是一个面向 Streamlit Cloud 部署的中国 A 股日线回测 MVP。第一版只提供固定策略，不做自由策略组合器、不做实盘交易、不连接券商账户。

## 功能

- 使用 AKShare 获取 A 股历史日线数据
- 支持 KDJ 金叉死叉、MACD 金叉死叉、均线策略
- T 日收盘确认信号，T+1 交易日开盘成交
- 买入使用可用资金 95%，买入数量按 100 股整数倍
- 支持买入佣金、卖出佣金、最低佣金、卖出印花税和滑点
- 展示收益指标、净值曲线、价格买卖点、指标图和交易记录
- 单列 Streamlit 页面，适合手机和微信浏览器访问

## 本地启动

```bash
cd ashare_backtester
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -c "from ashare_backtester.ui import main; print('import ok')"
pytest
streamlit run app.py
```

浏览器打开 Streamlit 显示的网址即可使用。

## 策略说明

### KDJ金叉死叉

- K 线上穿 D 线买入
- K 线下穿 D 线卖出
- 默认参数：周期 9，K 平滑 3，D 平滑 3

### MACD金叉死叉

- DIF 上穿 DEA 买入
- DIF 下穿 DEA 卖出
- 默认参数：fast 12，slow 26，signal 9

### 均线策略

- MA5 上穿 MA10 买入，MA5 下穿 MA10 卖出
- MA5 上穿 MA20 买入，MA5 下穿 MA20 卖出
- MA5 > MA10 > MA20 多头排列买入，多头排列破坏卖出

## 项目结构

```text
app.py
src/ashare_backtester/
  data/
  indicators/
  strategies/
  engine/
  reports/
  ui.py
tests/
```

## 注意

本项目仅用于学习和研究，不构成投资建议。回测结果不代表未来收益。
