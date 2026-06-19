import pytest

from ashare_backtester.data import DATA_SOURCE_OPTIONS, build_data_provider
from ashare_backtester.data.akshare_provider import AKShareDataProvider
from ashare_backtester.data.baostock_provider import BaoStockDataProvider


def test_data_source_options_include_free_providers():
    assert DATA_SOURCE_OPTIONS["AKShare免费公开数据"]["enabled"]
    assert DATA_SOURCE_OPTIONS["BaoStock免费公开数据"]["enabled"]
    assert not DATA_SOURCE_OPTIONS["Tushare需Token（预留）"]["enabled"]


def test_build_data_provider_returns_selected_provider():
    assert isinstance(build_data_provider("AKShare免费公开数据"), AKShareDataProvider)
    assert isinstance(build_data_provider("BaoStock免费公开数据"), BaoStockDataProvider)


def test_build_data_provider_rejects_reserved_tushare():
    with pytest.raises(ValueError):
        build_data_provider("Tushare需Token（预留）")
