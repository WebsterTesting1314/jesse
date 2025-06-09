from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils
import numpy as np

class TrendFollowing(Strategy):
    """
    趋势跟踪策略示例
    
    策略逻辑：
    1. 使用双均线系统识别趋势
    2. ADX确认趋势强度
    3. ATR动态止损
    4. 风险管理：每笔交易风险2%
    """
    
    def __init__(self):
        super().__init__()
        # 策略参数
        self.fast_period = 20
        self.slow_period = 50
        self.adx_period = 14
        self.adx_threshold = 25
        self.risk_per_trade = 0.02
        self.atr_multiplier = 2
        
    @property
    def fast_ema(self):
        """快速指数移动平均线"""
        return ta.ema(self.candles, self.fast_period)
    
    @property
    def slow_ema(self):
        """慢速指数移动平均线"""
        return ta.ema(self.candles, self.slow_period)
    
    @property
    def adx(self):
        """平均趋向指数"""
        return ta.adx(self.candles, self.adx_period)
    
    @property
    def atr(self):
        """平均真实波幅"""
        return ta.atr(self.candles, 14)
    
    def should_long(self) -> bool:
        """买入信号"""
        # 确保有足够的历史数据
        if len(self.candles) < self.slow_period + 10:
            return False
        
        # 趋势条件
        trend_up = self.fast_ema > self.slow_ema
        
        # 趋势强度
        strong_trend = self.adx > self.adx_threshold
        
        # 突破确认
        price_above_ema = self.close > self.fast_ema
        
        # 避免追高
        not_overbought = (self.close - self.slow_ema) / self.slow_ema < 0.05
        
        return trend_up and strong_trend and price_above_ema and not_overbought
    
    def should_short(self) -> bool:
        """卖出信号"""
        # 确保有足够的历史数据
        if len(self.candles) < self.slow_period + 10:
            return False
        
        # 趋势条件
        trend_down = self.fast_ema < self.slow_ema
        
        # 趋势强度
        strong_trend = self.adx > self.adx_threshold
        
        # 突破确认
        price_below_ema = self.close < self.fast_ema
        
        # 避免追低
        not_oversold = (self.slow_ema - self.close) / self.slow_ema < 0.05
        
        return trend_down and strong_trend and price_below_ema and not_oversold
    
    def go_long(self):
        """执行买入"""
        # 计算仓位大小（基于风险）
        stop_distance = self.atr * self.atr_multiplier
        position_size = self.calculate_position_size(stop_distance)
        
        # 下单
        qty = utils.size_to_qty(position_size, self.price)
        self.buy = qty, self.price
        
        # 记录入场原因
        self.vars['entry_reason'] = f"Trend Up: EMA{self.fast_period} > EMA{self.slow_period}, ADX: {self.adx:.2f}"
    
    def go_short(self):
        """执行卖出"""
        # 计算仓位大小（基于风险）
        stop_distance = self.atr * self.atr_multiplier
        position_size = self.calculate_position_size(stop_distance)
        
        # 下单
        qty = utils.size_to_qty(position_size, self.price)
        self.sell = qty, self.price
        
        # 记录入场原因
        self.vars['entry_reason'] = f"Trend Down: EMA{self.fast_period} < EMA{self.slow_period}, ADX: {self.adx:.2f}"
    
    def on_open_position(self, order):
        """开仓后设置止损止盈"""
        stop_distance = self.atr * self.atr_multiplier
        
        if self.is_long:
            # 多仓止损止盈
            self.stop_loss = self.position.qty, self.position.entry_price - stop_distance
            self.take_profit = self.position.qty, self.position.entry_price + (stop_distance * 3)  # 3:1盈亏比
        else:
            # 空仓止损止盈
            self.stop_loss = self.position.qty, self.position.entry_price + stop_distance
            self.take_profit = self.position.qty, self.position.entry_price - (stop_distance * 3)
        
        self.log(f"开仓: {self.vars['entry_reason']}")
    
    def update_position(self):
        """更新仓位（移动止损）"""
        if not self.position:
            return
        
        # 计算新的止损位
        stop_distance = self.atr * self.atr_multiplier
        
        if self.is_long:
            new_stop = self.close - stop_distance
            # 只向上移动止损
            if new_stop > self.stop_loss[1]:
                self.stop_loss = self.position.qty, new_stop
                self.log(f"移动止损至: {new_stop:.2f}")
        else:
            new_stop = self.close + stop_distance
            # 只向下移动止损
            if new_stop < self.stop_loss[1]:
                self.stop_loss = self.position.qty, new_stop
                self.log(f"移动止损至: {new_stop:.2f}")
    
    def should_cancel_entry(self):
        """取消未成交订单"""
        # 如果价格偏离过多，取消订单
        if self.buy and abs(self.price - self.buy[1]) / self.buy[1] > 0.01:
            return True
        if self.sell and abs(self.price - self.sell[1]) / self.sell[1] > 0.01:
            return True
        return False
    
    def calculate_position_size(self, stop_distance):
        """基于风险计算仓位大小"""
        risk_amount = self.balance * self.risk_per_trade
        position_size = risk_amount / stop_distance
        
        # 限制最大仓位
        max_position = self.balance * 0.3  # 最多使用30%资金
        position_size = min(position_size, max_position)
        
        return position_size
    
    def terminate(self):
        """策略结束时的清理工作"""
        if hasattr(self, 'trades_log'):
            # 导出交易记录
            import json
            with open('logs/trend_following_trades.json', 'w') as f:
                json.dump(self.trades_log, f, indent=2)