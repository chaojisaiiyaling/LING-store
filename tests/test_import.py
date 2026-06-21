def test_app_imports_main():
    from ashare_backtester.ui import main

    assert callable(main)


def test_strategy_comparison_builds_all_strategies():
    from ashare_backtester.ui import _all_strategy_names, _build_strategy_with_defaults

    strategies = [_build_strategy_with_defaults(strategy_name) for strategy_name in _all_strategy_names()]
    assert len(strategies) == len(_all_strategy_names())
    assert all(hasattr(strategy, "generate_signals") for strategy in strategies)
