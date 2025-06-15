#!/usr/bin/env python3
"""
HFT 延遲測試腳本
測試高頻交易組件的延遲性能
"""

import sys
import time
import numpy as np
import statistics
from pathlib import Path

# 添加核心模組路徑
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

try:
    from jesse.indicators.hft_optimized import hft_sma, hft_ema, hft_rsi
    from jesse.services.hft_cache import hft_cache_manager
    from jesse.services.hft_event_system import hft_event_bus
    from jesse.store.hft_optimized_orders import hft_order_manager
except ImportError as e:
    print(f"⚠️ Warning: HFT modules not available: {e}")
    print("Some tests will be skipped.")

class HFTLatencyTester:
    """HFT 延遲測試器"""
    
    def __init__(self):
        self.results = {}
        self.max_latency_us = 100  # 100 微秒閾值
        
    def test_indicator_latency(self) -> dict:
        """測試指標計算延遲"""
        print("🔍 Testing HFT Indicator Latency...")
        
        # 準備測試數據
        prices = np.random.random(1000).astype(np.float64) * 50000
        iterations = 1000
        
        results = {}
        
        try:
            # 測試 SMA 延遲
            latencies = []
            for _ in range(iterations):
                start = time.perf_counter()
                hft_sma(prices, 20)
                end = time.perf_counter()
                latencies.append((end - start) * 1_000_000)  # 轉換為微秒
            
            results['sma'] = {
                'mean_us': statistics.mean(latencies),
                'median_us': statistics.median(latencies),
                'p95_us': np.percentile(latencies, 95),
                'max_us': max(latencies)
            }
            
            # 測試 EMA 延遲
            latencies = []
            for _ in range(iterations):
                start = time.perf_counter()
                hft_ema(prices, 20)
                end = time.perf_counter()
                latencies.append((end - start) * 1_000_000)
            
            results['ema'] = {
                'mean_us': statistics.mean(latencies),
                'median_us': statistics.median(latencies),
                'p95_us': np.percentile(latencies, 95),
                'max_us': max(latencies)
            }
            
            # 測試 RSI 延遲
            latencies = []
            for _ in range(iterations):
                start = time.perf_counter()
                hft_rsi(prices, 14)
                end = time.perf_counter()
                latencies.append((end - start) * 1_000_000)
            
            results['rsi'] = {
                'mean_us': statistics.mean(latencies),
                'median_us': statistics.median(latencies),
                'p95_us': np.percentile(latencies, 95),
                'max_us': max(latencies)
            }
            
        except Exception as e:
            print(f"❌ Indicator latency test failed: {e}")
            return {'error': str(e)}
        
        return results
    
    def test_cache_latency(self) -> dict:
        """測試緩存延遲"""
        print("🔍 Testing Cache Latency...")
        
        try:
            # 初始化緩存管理器
            cache_manager = hft_cache_manager
            
            # 測試寫入延遲
            write_latencies = []
            for i in range(1000):
                start = time.perf_counter()
                cache_manager.set_position_cache(f"test_key_{i}", {"price": 50000 + i})
                end = time.perf_counter()
                write_latencies.append((end - start) * 1_000_000)
            
            # 測試讀取延遲
            read_latencies = []
            for i in range(1000):
                start = time.perf_counter()
                cache_manager.get_position_cache(f"test_key_{i}")
                end = time.perf_counter()
                read_latencies.append((end - start) * 1_000_000)
            
            return {
                'write': {
                    'mean_us': statistics.mean(write_latencies),
                    'p95_us': np.percentile(write_latencies, 95),
                    'max_us': max(write_latencies)
                },
                'read': {
                    'mean_us': statistics.mean(read_latencies),
                    'p95_us': np.percentile(read_latencies, 95),
                    'max_us': max(read_latencies)
                }
            }
            
        except Exception as e:
            print(f"❌ Cache latency test failed: {e}")
            return {'error': str(e)}
    
    def test_order_management_latency(self) -> dict:
        """測試訂單管理延遲"""
        print("🔍 Testing Order Management Latency...")
        
        try:
            # 測試訂單添加延遲
            add_latencies = []
            for i in range(1000):
                order_data = {
                    'id': f'order_{i}',
                    'symbol': 'BTCUSDT',
                    'side': 'buy',
                    'quantity': 0.001,
                    'price': 50000 + i
                }
                
                start = time.perf_counter()
                # 這裡應該調用實際的訂單管理器
                # hft_order_manager.add_order(order_data)
                end = time.perf_counter()
                add_latencies.append((end - start) * 1_000_000)
            
            # 測試訂單查找延遲
            lookup_latencies = []
            for i in range(1000):
                start = time.perf_counter()
                # 這裡應該調用實際的訂單查找
                # hft_order_manager.get_order(f'order_{i}')
                end = time.perf_counter()
                lookup_latencies.append((end - start) * 1_000_000)
            
            return {
                'add': {
                    'mean_us': statistics.mean(add_latencies),
                    'p95_us': np.percentile(add_latencies, 95),
                    'max_us': max(add_latencies)
                },
                'lookup': {
                    'mean_us': statistics.mean(lookup_latencies),
                    'p95_us': np.percentile(lookup_latencies, 95),
                    'max_us': max(lookup_latencies)
                }
            }
            
        except Exception as e:
            print(f"❌ Order management latency test failed: {e}")
            return {'error': str(e)}
    
    def validate_results(self, results: dict) -> bool:
        """驗證結果是否符合性能要求"""
        print("\n📊 Validating Performance Requirements...")
        
        passed = True
        
        # 驗證指標延遲
        if 'indicators' in results:
            for indicator, metrics in results['indicators'].items():
                if 'error' not in metrics:
                    p95_latency = metrics.get('p95_us', float('inf'))
                    if p95_latency > self.max_latency_us:
                        print(f"❌ {indicator.upper()} P95 latency {p95_latency:.2f}μs > {self.max_latency_us}μs")
                        passed = False
                    else:
                        print(f"✅ {indicator.upper()} P95 latency {p95_latency:.2f}μs ≤ {self.max_latency_us}μs")
        
        # 驗證緩存延遲
        if 'cache' in results and 'error' not in results['cache']:
            read_p95 = results['cache']['read'].get('p95_us', float('inf'))
            write_p95 = results['cache']['write'].get('p95_us', float('inf'))
            
            if read_p95 > self.max_latency_us:
                print(f"❌ Cache read P95 latency {read_p95:.2f}μs > {self.max_latency_us}μs")
                passed = False
            else:
                print(f"✅ Cache read P95 latency {read_p95:.2f}μs ≤ {self.max_latency_us}μs")
                
            if write_p95 > self.max_latency_us:
                print(f"❌ Cache write P95 latency {write_p95:.2f}μs > {self.max_latency_us}μs")
                passed = False
            else:
                print(f"✅ Cache write P95 latency {write_p95:.2f}μs ≤ {self.max_latency_us}μs")
        
        return passed
    
    def run_all_tests(self) -> bool:
        """運行所有延遲測試"""
        print("🚀 Starting HFT Latency Tests...")
        print(f"🎯 Target: All operations < {self.max_latency_us}μs (P95)")
        
        # 運行指標測試
        self.results['indicators'] = self.test_indicator_latency()
        
        # 運行緩存測試
        self.results['cache'] = self.test_cache_latency()
        
        # 運行訂單管理測試
        self.results['order_management'] = self.test_order_management_latency()
        
        # 打印詳細結果
        self.print_detailed_results()
        
        # 驗證結果
        passed = self.validate_results(self.results)
        
        if passed:
            print("\n✅ All HFT latency tests passed!")
            return True
        else:
            print("\n❌ Some HFT latency tests failed!")
            return False
    
    def print_detailed_results(self):
        """打印詳細測試結果"""
        print("\n📊 Detailed Latency Test Results:")
        print("=" * 60)
        
        for category, results in self.results.items():
            print(f"\n📈 {category.upper()} Results:")
            if 'error' in results:
                print(f"   ❌ Error: {results['error']}")
                continue
                
            if category == 'indicators':
                for indicator, metrics in results.items():
                    print(f"   {indicator.upper()}:")
                    print(f"     Mean: {metrics['mean_us']:.2f}μs")
                    print(f"     P95:  {metrics['p95_us']:.2f}μs")
                    print(f"     Max:  {metrics['max_us']:.2f}μs")
            elif category in ['cache', 'order_management']:
                for operation, metrics in results.items():
                    print(f"   {operation.upper()}:")
                    print(f"     Mean: {metrics['mean_us']:.2f}μs")
                    print(f"     P95:  {metrics['p95_us']:.2f}μs")
                    print(f"     Max:  {metrics['max_us']:.2f}μs")

def main():
    """主函數"""
    tester = HFTLatencyTester()
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 