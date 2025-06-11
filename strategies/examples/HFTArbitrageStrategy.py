"""
High-Frequency Trading Arbitrage Strategy
Demonstrates the use of all HFT optimizations for ultra-low latency trading

This strategy:
1. Uses Numba-optimized indicators for sub-millisecond calculations
2. Implements event-driven architecture for real-time processing
3. Utilizes optimized caching for position and order management
4. Monitors cross-exchange arbitrage opportunities
5. Executes trades with minimal latency
"""

import asyncio
import time
import numpy as np
from typing import Dict, List, Optional, Tuple

from jesse.strategies import Strategy
from jesse.services.hft_cache import CachedStrategy, hft_cache_manager
from jesse.services.hft_event_system import (
    EventHandler, EventType, Event, hft_event_bus,
    publish_price_update, publish_arbitrage_opportunity
)
from jesse.indicators.hft_optimized import (
    hft_sma, hft_ema, hft_rsi, hft_correlation,
    get_memory_pool, hft_batch_indicators
)
from jesse.store.hft_optimized_orders import (
    hft_orders_state, add_order_fast, get_active_orders_fast
)
import jesse.helpers as jh
import jesse.services.selectors as selectors
from jesse.enums import sides, order_types


class HFTArbitrageStrategy(Strategy, CachedStrategy, EventHandler):
    """
    Ultra-low latency arbitrage strategy using all HFT optimizations
    """
    
    def __init__(self):
        Strategy.__init__(self)
        CachedStrategy.__init__(self)
        EventHandler.__init__(self, "HFTArbitrageStrategy", max_latency_us=100)
        
        # Performance optimization setup
        self.memory_pool = get_memory_pool()
        self.indicator_cache = {}
        self.price_cache = {}
        self.last_calculation_time = 0
        
        # Arbitrage parameters
        self.min_profit_bps = 10  # Minimum 10 basis points profit
        self.max_position_size = 0.1  # Max 10% of capital per position
        self.correlation_threshold = 0.7  # Minimum correlation for pairs
        
        # Performance tracking
        self.execution_times = []
        self.arbitrage_opportunities = 0
        self.successful_trades = 0
        
        # Subscribe to events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self):
        """Subscribe to relevant events for real-time processing"""
        hft_event_bus.subscribe(EventType.TICK_UPDATE, self)
        hft_event_bus.subscribe(EventType.ARBITRAGE_OPPORTUNITY, self)
        hft_event_bus.subscribe(EventType.ORDER_FILLED, self)
        hft_event_bus.subscribe(EventType.RISK_LIMIT_BREACH, self)
    
    # ========================================================================
    # Core Strategy Logic (HFT-Optimized)
    # ========================================================================
    
    def should_long(self) -> bool:
        """
        HFT-optimized long entry logic using cached calculations
        """
        start_time = time.time_ns()
        
        try:
            # Use cached position for ultra-fast access
            if self.position.qty != 0:
                return False
            
            # Get cached prices for multiple timeframes
            prices = self._get_cached_prices()
            if prices is None:
                return False
            
            # Use batch indicator calculation for efficiency
            indicators = self._calculate_indicators_batch(prices)
            
            # Multi-factor entry signal
            sma_signal = indicators['fast_sma'] > indicators['slow_sma']
            rsi_signal = indicators['rsi'] < 30  # Oversold
            correlation_signal = self._check_correlation_signals()
            
            # Arbitrage opportunity check
            arbitrage_signal = self._check_arbitrage_opportunity()
            
            result = sma_signal and rsi_signal and (correlation_signal or arbitrage_signal)
            
            # Track execution time
            execution_time = (time.time_ns() - start_time) / 1000  # microseconds
            self.execution_times.append(execution_time)
            
            # Keep only last 1000 measurements
            if len(self.execution_times) > 1000:
                self.execution_times = self.execution_times[-1000:]
            
            return result
            
        except Exception as e:
            jh.log_error(f"Error in should_long: {e}")
            return False
    
    def should_short(self) -> bool:
        """
        HFT-optimized short entry logic
        """
        start_time = time.time_ns()
        
        try:
            if self.position.qty != 0:
                return False
            
            prices = self._get_cached_prices()
            if prices is None:
                return False
            
            indicators = self._calculate_indicators_batch(prices)
            
            # Multi-factor short signal
            sma_signal = indicators['fast_sma'] < indicators['slow_sma']
            rsi_signal = indicators['rsi'] > 70  # Overbought
            correlation_signal = self._check_correlation_signals(short=True)
            arbitrage_signal = self._check_arbitrage_opportunity(short=True)
            
            result = sma_signal and rsi_signal and (correlation_signal or arbitrage_signal)
            
            execution_time = (time.time_ns() - start_time) / 1000
            self.execution_times.append(execution_time)
            
            return result
            
        except Exception as e:
            jh.log_error(f"Error in should_short: {e}")
            return False
    
    def go_long(self):
        """
        Execute long position with HFT optimizations
        """
        try:
            # Calculate position size with risk management
            position_size = self._calculate_optimal_position_size()
            
            # Use market order for immediate execution in HFT
            self.buy = position_size, self.price
            
            # Set tight stop-loss and take-profit for HFT
            self.stop_loss = position_size, self.price * 0.995  # 0.5% stop loss
            self.take_profit = position_size, self.price * 1.01  # 1% take profit
            
            # Log trade for analysis
            jh.log_info(f"HFT Long entry: {position_size} @ {self.price}")
            
        except Exception as e:
            jh.log_error(f"Error in go_long: {e}")
    
    def go_short(self):
        """
        Execute short position with HFT optimizations
        """
        try:
            position_size = self._calculate_optimal_position_size()
            
            self.sell = position_size, self.price
            self.stop_loss = position_size, self.price * 1.005  # 0.5% stop loss
            self.take_profit = position_size, self.price * 0.99  # 1% take profit
            
            jh.log_info(f"HFT Short entry: {position_size} @ {self.price}")
            
        except Exception as e:
            jh.log_error(f"Error in go_short: {e}")
    
    # ========================================================================
    # HFT-Optimized Helper Methods
    # ========================================================================
    
    def _get_cached_prices(self) -> Optional[np.ndarray]:
        """
        Get prices with intelligent caching
        """
        current_time = time.time()
        cache_key = f"prices_{self.exchange}_{self.symbol}"
        
        # Check cache (1ms TTL for HFT)
        if (cache_key in self.price_cache and 
            current_time - self.price_cache[cache_key]['timestamp'] < 0.001):
            return self.price_cache[cache_key]['data']
        
        # Cache miss - calculate new
        if len(self.candles) < 50:
            return None
        
        prices = self.candles[:, 2].astype(np.float64)  # Close prices
        
        self.price_cache[cache_key] = {
            'data': prices,
            'timestamp': current_time
        }
        
        return prices
    
    def _calculate_indicators_batch(self, prices: np.ndarray) -> Dict:
        """
        Calculate multiple indicators in batch for efficiency
        """
        cache_key = f"indicators_{len(prices)}"
        current_time = time.time()
        
        # Check cache (10ms TTL for indicators)
        if (cache_key in self.indicator_cache and 
            current_time - self.indicator_cache[cache_key]['timestamp'] < 0.01):
            return self.indicator_cache[cache_key]['data']
        
        # Calculate indicators using HFT-optimized functions
        fast_sma = hft_sma(prices, 10)
        slow_sma = hft_sma(prices, 30)
        rsi = hft_rsi(prices, 14)
        ema_12 = hft_ema(prices, 12)
        ema_26 = hft_ema(prices, 26)
        
        indicators = {
            'fast_sma': fast_sma[-1],
            'slow_sma': slow_sma[-1],
            'rsi': rsi[-1],
            'ema_12': ema_12[-1],
            'ema_26': ema_26[-1],
            'trend': 1 if fast_sma[-1] > slow_sma[-1] else -1
        }
        
        # Cache result
        self.indicator_cache[cache_key] = {
            'data': indicators,
            'timestamp': current_time
        }
        
        return indicators
    
    def _check_correlation_signals(self, short: bool = False) -> bool:
        """
        Check correlation with other symbols for signal confirmation
        """
        try:
            # Get correlated symbols (would be configured in real implementation)
            correlated_symbols = ['ETHUSDT'] if self.symbol == 'BTCUSDT' else ['BTCUSDT']
            
            for corr_symbol in correlated_symbols:
                # Get correlation from market data cache
                correlation = self._get_symbol_correlation(corr_symbol)
                
                if correlation and abs(correlation) > self.correlation_threshold:
                    # Check if correlated symbol supports our signal
                    corr_trend = self._get_symbol_trend(corr_symbol)
                    
                    if short:
                        return correlation > 0 and corr_trend < 0
                    else:
                        return correlation > 0 and corr_trend > 0
            
            return False
            
        except Exception as e:
            jh.log_error(f"Error in correlation check: {e}")
            return False
    
    def _check_arbitrage_opportunity(self, short: bool = False) -> bool:
        """
        Check for arbitrage opportunities across exchanges
        """
        try:
            # This would check prices across multiple exchanges
            # For demo, we'll simulate a simple spread check
            
            # Get current spread
            spread_bps = self._calculate_current_spread()
            
            if spread_bps > self.min_profit_bps:
                self.arbitrage_opportunities += 1
                
                # Publish arbitrage opportunity event
                asyncio.create_task(publish_arbitrage_opportunity(
                    buy_exchange=self.exchange,
                    sell_exchange='alternate_exchange',  # Would be real exchange
                    symbol=self.symbol,
                    profit_bps=spread_bps
                ))
                
                return True
            
            return False
            
        except Exception as e:
            jh.log_error(f"Error in arbitrage check: {e}")
            return False
    
    def _calculate_optimal_position_size(self) -> float:
        """
        Calculate optimal position size with risk management
        """
        try:
            # Use cached position for fast access
            available_capital = self.capital * self.max_position_size
            
            # Adjust for volatility (using cached ATR)
            volatility_adjustment = self._get_volatility_adjustment()
            
            # Calculate position size
            position_value = available_capital * volatility_adjustment
            position_size = position_value / self.price
            
            return round(position_size, 6)
            
        except Exception as e:
            jh.log_error(f"Error calculating position size: {e}")
            return 0.01  # Fallback to small size
    
    # ========================================================================
    # Event Handlers
    # ========================================================================
    
    async def handle(self, event: Event) -> None:
        """
        Handle real-time events with ultra-low latency
        """
        try:
            if event.event_type == EventType.TICK_UPDATE:
                await self._handle_tick_update(event)
            elif event.event_type == EventType.ARBITRAGE_OPPORTUNITY:
                await self._handle_arbitrage_opportunity(event)
            elif event.event_type == EventType.ORDER_FILLED:
                await self._handle_order_filled(event)
            elif event.event_type == EventType.RISK_LIMIT_BREACH:
                await self._handle_risk_breach(event)
                
        except Exception as e:
            jh.log_error(f"Error handling event {event.event_type}: {e}")
    
    async def _handle_tick_update(self, event: Event) -> None:
        """
        Handle real-time price updates
        """
        if event.exchange == self.exchange and event.symbol == self.symbol:
            price = event.data.get('price')
            if price:
                # Update price cache
                hft_cache_manager.market_data_cache.update_price(
                    self.exchange, self.symbol, price
                )
                
                # Check for immediate trading opportunities
                if self._should_execute_immediate_trade(price):
                    await self._execute_immediate_trade(price)
    
    async def _handle_arbitrage_opportunity(self, event: Event) -> None:
        """
        Handle arbitrage opportunities
        """
        profit_bps = event.data.get('profit_bps', 0)
        
        if (profit_bps > self.min_profit_bps and 
            event.exchange == self.exchange and 
            event.symbol == self.symbol):
            
            # Execute arbitrage if position is available
            if self.position.qty == 0:
                await self._execute_arbitrage_trade(event)
    
    async def _handle_order_filled(self, event: Event) -> None:
        """
        Handle order fill events
        """
        order_id = event.data.get('order_id')
        if order_id:
            # Update statistics
            self.successful_trades += 1
            
            # Invalidate position cache
            self.invalidate_position_cache()
            
            jh.log_info(f"Order filled: {order_id}")
    
    async def _handle_risk_breach(self, event: Event) -> None:
        """
        Handle risk management events
        """
        jh.log_error(f"Risk breach detected: {event.data}")
        
        # Emergency position closure
        if self.position.qty != 0:
            # Close position immediately
            if self.position.qty > 0:
                self.sell = abs(self.position.qty), self.price
            else:
                self.buy = abs(self.position.qty), self.price
    
    # ========================================================================
    # Performance Monitoring
    # ========================================================================
    
    def get_performance_stats(self) -> Dict:
        """
        Get strategy performance statistics
        """
        if not self.execution_times:
            return {}
        
        return {
            'avg_execution_time_us': np.mean(self.execution_times),
            'max_execution_time_us': np.max(self.execution_times),
            'p95_execution_time_us': np.percentile(self.execution_times, 95),
            'arbitrage_opportunities': self.arbitrage_opportunities,
            'successful_trades': self.successful_trades,
            'execution_count': len(self.execution_times)
        }
    
    def should_cancel_entry(self) -> bool:
        """
        HFT strategies rarely cancel entries due to speed requirements
        """
        return False
    
    # ========================================================================
    # Helper Methods (Placeholder implementations)
    # ========================================================================
    
    def _get_symbol_correlation(self, symbol: str) -> Optional[float]:
        """Get correlation with another symbol"""
        # Placeholder - would implement real correlation calculation
        return 0.8
    
    def _get_symbol_trend(self, symbol: str) -> int:
        """Get trend direction for symbol"""
        # Placeholder - would implement real trend calculation
        return 1
    
    def _calculate_current_spread(self) -> int:
        """Calculate current spread in basis points"""
        # Placeholder - would implement real spread calculation
        return 15
    
    def _get_volatility_adjustment(self) -> float:
        """Get volatility adjustment factor"""
        # Placeholder - would implement real volatility calculation
        return 1.0
    
    def _should_execute_immediate_trade(self, price: float) -> bool:
        """Check if immediate trade should be executed"""
        # Placeholder - would implement real immediate trade logic
        return False
    
    async def _execute_immediate_trade(self, price: float) -> None:
        """Execute immediate trade"""
        # Placeholder - would implement real immediate trade execution
        pass
    
    async def _execute_arbitrage_trade(self, event: Event) -> None:
        """Execute arbitrage trade"""
        # Placeholder - would implement real arbitrage execution
        pass


# ========================================================================
# Strategy Registration and Configuration
# ========================================================================

def initialize_hft_strategy():
    """
    Initialize HFT strategy with all optimizations
    """
    async def setup():
        # Start HFT event bus
        await hft_event_bus.start()
        
        # Warm up caches
        hft_cache_manager.warm_up_caches(
            exchanges=['Binance'],
            symbols=['BTCUSDT', 'ETHUSDT']
        )
        
        jh.log_info("HFT Strategy initialized with all optimizations")
    
    # Run setup
    asyncio.run(setup())


# Strategy configuration
def hyperparameters():
    """
    Define hyperparameters for optimization
    """
    return [
        {'name': 'min_profit_bps', 'type': int, 'min': 5, 'max': 50, 'default': 10},
        {'name': 'max_position_size', 'type': float, 'min': 0.05, 'max': 0.2, 'default': 0.1},
        {'name': 'correlation_threshold', 'type': float, 'min': 0.5, 'max': 0.9, 'default': 0.7},
    ]


if __name__ == "__main__":
    # Test strategy performance
    strategy = HFTArbitrageStrategy()
    
    # Run performance test
    print("HFT Strategy Performance Test")
    print("=" * 40)
    
    # Simulate some calculations
    import time
    test_prices = np.random.random(1000) * 100
    
    start_time = time.time_ns()
    for _ in range(100):
        strategy._calculate_indicators_batch(test_prices)
    end_time = time.time_ns()
    
    avg_time_us = (end_time - start_time) / 100 / 1000  # microseconds
    print(f"Average indicator calculation time: {avg_time_us:.2f} μs")
    
    # Print cache stats
    stats = hft_cache_manager.get_all_stats()
    print(f"Cache performance: {stats}")