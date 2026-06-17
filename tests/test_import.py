def test_app_imports_main():
    from ashare_backtester.ui import main

    assert callable(main)
