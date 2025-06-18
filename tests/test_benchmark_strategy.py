import pytest

pytest.importorskip("jesse")

from strategies.DeFiArbitrageStrategy import DeFiArbitrageStrategy
from jesse.services.web3_client import ChainId


def test_benchmark_get_rpc_url(benchmark):
    strategy = DeFiArbitrageStrategy()
    # benchmark the RPC URL retrieval method
    benchmark(lambda: strategy._get_rpc_url(ChainId.ETHEREUM))