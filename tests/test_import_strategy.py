import pytest

pytest.importorskip("jesse")

def test_import_defi_arbitrage_strategy():
    from strategies.DeFiArbitrageStrategy import DeFiArbitrageStrategy
    # Ensure the class can be instantiated and has expected attributes
    strategy = DeFiArbitrageStrategy()
    assert hasattr(strategy, 'before')
    assert hasattr(strategy, '_initialize_services')