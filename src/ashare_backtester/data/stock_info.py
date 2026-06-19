from __future__ import annotations

import pandas as pd


def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".SZ", "").replace(".SH", "")


def lookup_stock_name(symbol: str, allow_remote: bool = False) -> str | None:
    clean_symbol = normalize_symbol(symbol)
    if not clean_symbol:
        return None
    if allow_remote:
        remote_name = _lookup_single_with_akshare(clean_symbol)
        if remote_name:
            return remote_name
    common_name = _lookup_common_name(clean_symbol)
    if common_name:
        return common_name
    return None


def _lookup_single_with_akshare(symbol: str) -> str | None:
    try:
        import akshare as ak

        info = ak.stock_individual_info_em(symbol=symbol)
    except Exception:
        return None

    if info.empty:
        return None

    columns = {str(col).lower(): col for col in info.columns}
    item_col = columns.get("item") or columns.get("项目")
    value_col = columns.get("value") or columns.get("值")
    if item_col and value_col:
        item_values = info[item_col].astype(str)
        matched = info.loc[item_values.isin(["股票简称", "股票名称", "名称"])]
        if not matched.empty:
            name = matched.iloc[0][value_col]
            if not pd.isna(name):
                return str(name)

    name = _extract_name_from_flat_info(info)
    if pd.isna(name):
        return None
    return str(name)


def _extract_name_from_flat_info(info: pd.DataFrame):
    for col in info.columns:
        col_name = str(col)
        if col_name in {"股票简称", "股票名称", "名称", "name"}:
            value = info.iloc[0][col]
            if not pd.isna(value):
                return value
    return None


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
