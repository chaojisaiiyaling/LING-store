from __future__ import annotations

import pandas as pd


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".SZ", "").replace(".SH", "")


def lookup_stock_name(symbol: str) -> str | None:
    clean_symbol = normalize_symbol(symbol)
    if not clean_symbol:
        return None

    common_name = _lookup_common_name(clean_symbol)
    if common_name:
        return common_name

    name = _lookup_with_akshare(clean_symbol)
    if name:
        return name
    return None


def _lookup_with_akshare(symbol: str) -> str | None:
    try:
        import akshare as ak

        code_names = ak.stock_info_a_code_name()
    except Exception:
        return None

    if code_names.empty:
        return None

    columns = {str(col).lower(): col for col in code_names.columns}
    code_col = columns.get("code") or columns.get("代码")
    name_col = columns.get("name") or columns.get("名称")
    if not code_col or not name_col:
        return None

    normalized_codes = code_names[code_col].astype(str).str.zfill(6)
    matched = code_names.loc[normalized_codes == symbol]
    if matched.empty:
        return None

    name = matched.iloc[0][name_col]
    if pd.isna(name):
        return None
    return str(name)


def _lookup_common_name(symbol: str) -> str | None:
    common_names = {
        "000001": "平安银行",
        "000002": "万科A",
        "000063": "中兴通讯",
        "000333": "美的集团",
        "000651": "格力电器",
        "000858": "五粮液",
        "002415": "海康威视",
        "002594": "比亚迪",
        "300059": "东方财富",
        "300750": "宁德时代",
        "600000": "浦发银行",
        "600036": "招商银行",
        "600519": "贵州茅台",
        "600887": "伊利股份",
        "601318": "中国平安",
        "601398": "工商银行",
    }
    return common_names.get(symbol)
