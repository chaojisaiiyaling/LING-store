from __future__ import annotations

import pandas as pd

from ashare_backtester.data.base import DataProvider, normalize_ohlcv


class AKShareDataProvider(DataProvider):
    def get_daily(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            import akshare as ak
        except ImportError as exc:
            raise RuntimeError("未安装 AKShare，请先执行 pip install -r requirements.txt") from exc

        clean_symbol = symbol.strip().replace(".SZ", "").replace(".SH", "")
        raw = self._fetch_em(ak, clean_symbol, start_date, end_date)
        if raw is None:
            raw = self._fetch_sina(ak, clean_symbol, start_date, end_date)
        if raw is None:
            raise RuntimeError("AKShare 行情接口暂时不可用，请稍后重试或缩短日期区间。")
        if raw.empty:
            raise ValueError("未获取到历史行情，请检查股票代码和日期区间。")

        mapping = {
            "日期": "trade_date",
            "开盘": "open",
            "最高": "high",
            "最低": "low",
            "收盘": "close",
            "成交量": "volume",
            "成交额": "amount",
        }
        return normalize_ohlcv(raw.rename(columns=mapping))

    def _fetch_em(self, ak, symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        for _ in range(2):
            try:
                return ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", ""),
                    adjust="qfq",
                )
            except Exception:
                continue
        return None

    def _fetch_sina(self, ak, symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        prefix = "sh" if symbol.startswith(("6", "9")) else "sz"
        try:
            raw = ak.stock_zh_a_daily(
                symbol=f"{prefix}{symbol}",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq",
            )
        except Exception:
            return None
        return raw.rename(columns={"date": "日期", "open": "开盘", "high": "最高", "low": "最低", "close": "收盘", "volume": "成交量", "amount": "成交额"})
