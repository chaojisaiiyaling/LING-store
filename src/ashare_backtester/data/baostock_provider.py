from __future__ import annotations

import pandas as pd

from ashare_backtester.data.base import DataProvider, normalize_ohlcv


class BaoStockDataProvider(DataProvider):
    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            import baostock as bs
        except ImportError as exc:
            raise RuntimeError("未安装 BaoStock，请先执行 pip install -r requirements.txt") from exc

        code = self._format_symbol(symbol)
        login = bs.login()
        if login.error_code != "0":
            raise RuntimeError(f"BaoStock 登录失败: {login.error_msg}")

        try:
            fields = "date,open,high,low,close,volume,amount"
            query = bs.query_history_k_data_plus(
                code,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="2",
            )
            if query.error_code != "0":
                raise RuntimeError(f"BaoStock 行情接口错误: {query.error_msg}")

            rows = []
            while query.next():
                rows.append(query.get_row_data())
            raw = pd.DataFrame(rows, columns=query.fields)
        finally:
            bs.logout()

        if raw.empty:
            raise ValueError("未获取到历史行情，请检查股票代码、日期区间或切换数据接口。")

        mapping = {
            "date": "trade_date",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume",
            "amount": "amount",
        }
        return normalize_ohlcv(raw.rename(columns=mapping))

    def _format_symbol(self, symbol: str) -> str:
        clean_symbol = symbol.strip().lower().replace(".sz", "").replace(".sh", "")
        if clean_symbol.startswith(("6", "9")):
            return f"sh.{clean_symbol}"
        return f"sz.{clean_symbol}"
