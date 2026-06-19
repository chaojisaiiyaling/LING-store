def normalize_symbol(symbol: str) -> str:
    return symbol.strip().upper().replace(".SZ", "").replace(".SH", "")


def lookup_stock_name(symbol: str):
    clean_symbol = normalize_symbol(symbol)
    if not clean_symbol:
        return None
    return _lookup_common_name(clean_symbol)


def _lookup_common_name(symbol: str):
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
