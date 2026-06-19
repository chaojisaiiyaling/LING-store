from ashare_backtester.data.stock_info import lookup_stock_name, normalize_symbol


def test_normalize_symbol_removes_market_suffix():
    assert normalize_symbol("000001.SZ") == "000001"
    assert normalize_symbol("600519.sh") == "600519"


def test_lookup_stock_name_uses_common_fallback():
    assert lookup_stock_name("000001") == "平安银行"
    assert lookup_stock_name("600519.SH") == "贵州茅台"
