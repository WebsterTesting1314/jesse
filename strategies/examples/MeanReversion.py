from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils
import numpy as np

class MeanReversion(Strategy):
    """
    均值回归策略示例
    
    策略逻辑：
    1. 使用布林带识别超买超卖
    2. RSI确认动量
    3. 成交量验证
    4. 适合震荡市场
    """
    
    def __init__(self):
        super().__init__()
        # 策略参数
        self.bb_period = 20
        self.bb_std = 2
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.volume_factor = 1.5
        
        # 风险参数
        self.position_size_pct = 0.1  # 使用10%资金
        self.stop_loss_pct = 0.03     # 3%止损
        self.take_profit_pct = 0.02   # 2%止盈
        
        # 状态跟踪
        self.entry_reason = ""
        
    @property
    def bb_upper(self):
        """布林带上轨"""
        return ta.bollinger_bands(self.candles, self.bb_period, self.bb_std)[0]
    
    @property
    def bb_middle(self):
        """布林带中轨"""
        return ta.bollinger_bands(self.candles, self.bb_period, self.bb_std)[1]
    
    @property
    def bb_lower(self):
        """布林带下轨"""
        return ta.bollinger_bands(self.candles, self.bb_period, self.bb_std)[2]
    
    @property
    def rsi(self):
        """相对强弱指数"""
        return ta.rsi(self.candles, self.rsi_period)
    
    @property
    def volume_sma(self):
        """成交量移动平均"""
        return ta.sma(self.candles[:, 5], 20)
    
    def should_long(self) -> bool:
        """买入信号：价格触及下轨且超卖"""
        # 确保有足够数据
        if len(self.candles) < max(self.bb_period, self.rsi_period) + 10:
            return False
        
        # 价格条件
        price_at_lower_band = self.close <= self.bb_lower * 1.005  # 允许0.5%误差
        
        # RSI超卖
        rsi_oversold = self.rsi < self.rsi_oversold
        
        # 成交量放大（确认卖压）
        volume_spike = self.volume > self.volume_sma * self.volume_factor
        
        # 不在强烈下跌趋势中
        not_strong_downtrend = self.close > ta.sma(self.candles, 50) * 0.95
        
        # 价格开始反弹
        price_bounce = self.close > self.low and self.close > self.candles[-2][2]
        
        signal = (price_at_lower_band and rsi_oversold and 
                 volume_spike and not_strong_downtrend and price_bounce)
        
        if signal:
            self.entry_reason = f"超卖回归: RSI={self.rsi:.1f}, 价格触及下轨"
        
        return signal
    
    def should_short(self) -> bool:
        """卖出信号：价格触及上轨且超买"""
        # 确保有足够数据
        if len(self.candles) < max(self.bb_period, self.rsi_period) + 10:
            return False
        
        # 价格条件
        price_at_upper_band = self.close >= self.bb_upper * 0.995  # 允许0.5%误差
        
        # RSI超买
        rsi_overbought = self.rsi > self.rsi_overbought
        
        # 成交量放大（确认买压）
        volume_spike = self.volume > self.volume_sma * self.volume_factor
        
        # 不在强烈上涨趋势中
        not_strong_uptrend = self.close < ta.sma(self.candles, 50) * 1.05
        
        # 价格开始回落
        price_pullback = self.close < self.high and self.close < self.candles[-2][2]
        
        signal = (price_at_upper_band and rsi_overbought and 
                 volume_spike and not_strong_uptrend and price_pullback)
        
        if signal:
            self.entry_reason = f"超买回归: RSI={self.rsi:.1f}, 价格触及上轨"
        
        return signal
    
    def go_long(self):
        """执行买入"""
        # 计算仓位
        position_size = self.balance * self.position_size_pct
        qty = utils.size_to_qty(position_size, self.price)
        
        # 市价买入（均值回归需要快速执行）
        self.buy = qty, self.price
        
        self.log(f"买入信号: {self.entry_reason}")
    
    def go_short(self):
        """执行卖出"""
        # 计算仓位
        position_size = self.balance * self.position_size_pct
        qty = utils.size_to_qty(position_size, self.price)
        
        # 市价卖出（均值回归需要快速执行）
        self.sell = qty, self.price
        
        self.log(f"卖出信号: {self.entry_reason}")
    
    def on_open_position(self, order):
        """设置止损止盈"""
        if self.is_long:
            # 多仓：止损在入场价下方，止盈在中轨
            self.stop_loss = self.position.qty, self.position.entry_price * (1 - self.stop_loss_pct)
            
            # 动态止盈：目标是布林带中轨
            target_price = min(self.bb_middle, self.position.entry_price * (1 + self.take_profit_pct))
            self.take_profit = self.position.qty, target_price
        else:
            # 空仓：止损在入场价上方，止盈在中轨
            self.stop_loss = self.position.qty, self.position.entry_price * (1 + self.stop_loss_pct)
            
            # 动态止盈：目标是布林带中轨
            target_price = max(self.bb_middle, self.position.entry_price * (1 - self.take_profit_pct))
            self.take_profit = self.position.qty, target_price
    
    def update_position(self):
        """更新止盈目标"""
        if not self.position:
            return
        
        # 更新止盈至布林带中轨
        if self.is_long:
            new_target = self.bb_middle
            if new_target > self.take_profit[1] and new_target < self.close:
                self.take_profit = self.position.qty, new_target
                self.log(f"更新止盈目标至中轨: {new_target:.2f}")
        else:
            new_target = self.bb_middle
            if new_target < self.take_profit[1] and new_target > self.close:
                self.take_profit = self.position.qty, new_target
                self.log(f"更新止盈目标至中轨: {new_target:.2f}")
        
        # 如果价格已经回归到中轨附近，考虑平仓
        distance_to_middle = abs(self.close - self.bb_middle) / self.bb_middle
        if distance_to_middle < 0.005:  # 0.5%以内
            if self.is_long:
                self.sell = self.position.qty, self.price
                self.log("价格回归中轨，平仓")
            else:
                self.buy = self.position.qty, self.price
                self.log("价格回归中轨，平仓")
    
    def should_cancel_entry(self):
        """取消订单条件"""
        # 如果价格快速反转，取消订单
        return False
    
    def filters(self):
        """过滤条件"""
        return [
            # 有足够的历史数据
            self.index >= 50,
            
            # 避免低波动率市场（布林带过窄）
            (self.bb_upper - self.bb_lower) / self.bb_middle > 0.02,
            
            # 避免单边趋势市场
            abs(ta.sma(self.candles, 20) - ta.sma(self.candles, 50)) / ta.sma(self.candles, 50) < 0.03
        ]
    
    def before(self):
        """计算市场状态"""
        if len(self.candles) < 50:
            return
        
        # 计算布林带宽度
        bb_width = (self.bb_upper - self.bb_lower) / self.bb_middle
        
        # 记录市场状态
        if bb_width < 0.02:
            self.vars['market_state'] = 'low_volatility'
        elif bb_width > 0.05:
            self.vars['market_state'] = 'high_volatility'
        else:
            self.vars['market_state'] = 'normal'
    
    def after(self):
        """记录策略状态"""
        if self.position and self.vars.get('market_state'):
            self.log(f"市场状态: {self.vars['market_state']}, 持仓盈亏: {self.position.pnl_percentage:.2f}%")
    
    def terminate(self):
        """策略结束统计"""
        # 统计不同市场状态下的表现
        self.log("均值回归策略执行完成")