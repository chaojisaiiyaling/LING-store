from ashare_backtester.data.akshare_provider import AKShareDataProvider
from ashare_backtester.data.baostock_provider import BaoStockDataProvider
from ashare_backtester.data.base import DataProvider


DATA_SOURCE_OPTIONS = {
    "AKShare免费公开数据": {
        "provider": "akshare",
        "description": "默认接口，覆盖较广，不需要 Token。",
        "enabled": True,
    },
    "BaoStock免费公开数据": {
        "provider": "baostock",
        "description": "备用免费接口，不需要 Token，适合 AKShare 临时不可用时切换。",
        "enabled": True,
    },
    "Tushare需Token（预留）": {
        "provider": "tushare",
        "description": "需要单独申请 Token，当前版本暂未接入。",
        "enabled": False,
    },
}


def build_data_provider(source_name: str) -> DataProvider:
    option = DATA_SOURCE_OPTIONS[source_name]
    provider = option["provider"]
    if provider == "akshare":
        return AKShareDataProvider()
    if provider == "baostock":
        return BaoStockDataProvider()
    raise ValueError("该数据接口当前版本尚未接入，请先选择 AKShare 或 BaoStock。")
