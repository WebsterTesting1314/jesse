from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils
import numpy as np

class GridTrading(Strategy):
    """
    网格交易策略示例
    
    策略逻辑：
    1. 在价格区间内设置多个买卖网格
    2. 价格下跌时分批买入
    3. 价格上涨时分批卖出
    4. 适合震荡市场
    """
    
    def __init__(self):
        super().__init__()
        # 网格参数
        self.grid_levels = 10  # 网格数量
        self.grid_spacing = 0.01  # 网格间距 (1%)
        self.position_per_grid = 0.05  # 每个网格使用5%资金
        
        # 价格区间
        self.lookback_period = 100  # 历史回看周期
        self.range_multiplier = 1.2  # 区间扩展系数
        
        # 网格状态
        self.grid_orders = []
        self.filled_grids = {}
        
    def before(self):
        """初始化网格"""
        if len(self.candles) < self.lookback_period:
            return
        
        # 只在第一次或需要重置时初始化
        if not self.grid_orders or self.should_reset_grid():
            self.setup_grid()
    
    def setup_grid(self):
        """设置网格价格"""
        # 计算价格区间
        recent_prices = self.candles[-self.lookback_period:, 2]
        price_high = np.max(recent_prices) * self.range_multiplier
        price_low = np.min(recent_prices) / self.range_multiplier
        price_mid = (price_high + price_low) / 2
        
        # 清空现有网格
        self.grid_orders = []
        self.filled_grids = {}
        
        # 创建买入网格（当前价格以下）
        for i in range(self.grid_levels // 2):
            price = self.close * (1 - self.grid_spacing * (i + 1))
            if price > price_low:
                self.grid_orders.append({
                    'type': 'buy',
                    'price': price,
                    'qty': None,  # 将在下单时计算
                    'filled': False,
                    'level': i
                })
        
        # 创建卖出网格（当前价格以上）
        for i in range(self.grid_levels // 2):
            price = self.close * (1 + self.grid_spacing * (i + 1))
            if price < price_high:
                self.grid_orders.append({
                    'type': 'sell',
                    'price': price,
                    'qty': None,  # 将在下单时计算
                    'filled': False,
                    'level': i
                })
        
        self.log(f"网格初始化完成: {len(self.grid_orders)}个网格")
    
    def should_long(self) -> bool:
        """检查是否触发买入网格"""
        if not self.grid_orders:
            return False
        
        # 查找最近的未成交买入网格
        for grid in self.grid_orders:
            if grid['type'] == 'buy' and not grid['filled']:
                # 价格触及或低于网格价格
                if self.close <= grid['price']:
                    self.vars['current_grid'] = grid
                    return True
        
        return False
    
    def should_short(self) -> bool:
        """检查是否触发卖出网格"""
        if not self.grid_orders:
            return False
        
        # 只有持仓时才能卖出
        if not self.position or self.position.qty <= 0:
            return False
        
        # 查找最近的未成交卖出网格
        for grid in self.grid_orders:
            if grid['type'] == 'sell' and not grid['filled']:
                # 价格触及或高于网格价格
                if self.close >= grid['price']:
                    self.vars['current_grid'] = grid
                    return True
        
        return False
    
    def go_long(self):
        """执行网格买入"""
        grid = self.vars.get('current_grid')
        if not grid:
            return
        
        # 计算买入数量
        position_size = self.balance * self.position_per_grid
        qty = utils.size_to_qty(position_size, grid['price'])
        
        # 限价买入
        self.buy = qty, grid['price']
        
        # 标记网格
        grid['qty'] = qty
        grid['filled'] = True
        
        self.log(f"网格买入: 价格 {grid['price']:.2f}, 数量 {qty:.4f}")
    
    def go_short(self):
        """执行网格卖出"""
        grid = self.vars.get('current_grid')
        if not grid:
            return
        
        # 计算卖出数量（卖出部分持仓）
        sell_qty = min(self.position.qty * 0.2, self.position.qty)  # 每次卖出20%
        
        # 限价卖出
        self.sell = sell_qty, grid['price']
        
        # 标记网格
        grid['qty'] = sell_qty
        grid['filled'] = True
        
        self.log(f"网格卖出: 价格 {grid['price']:.2f}, 数量 {sell_qty:.4f}")
    
    def on_open_position(self, order):
        """开仓后不设置止损（网格策略特性）"""
        # 网格策略通常不使用止损
        # 而是通过网格平衡风险
        pass
    
    def update_position(self):
        """更新网格状态"""
        # 检查是否需要重置已成交的网格
        for grid in self.grid_orders:
            if grid['filled']:
                # 如果价格远离网格，可以重置
                distance = abs(self.close - grid['price']) / grid['price']
                if distance > self.grid_spacing * 3:
                    grid['filled'] = False
                    self.log(f"重置网格: {grid['type']} @ {grid['price']:.2f}")
    
    def should_reset_grid(self):
        """判断是否需要重置整个网格"""
        if not self.grid_orders:
            return True
        
        # 计算当前价格与网格中心的偏离
        grid_prices = [g['price'] for g in self.grid_orders]
        grid_center = np.mean(grid_prices)
        deviation = abs(self.close - grid_center) / grid_center
        
        # 如果偏离超过20%，重置网格
        return deviation > 0.2
    
    def should_cancel_entry(self):
        """不取消网格订单"""
        return False
    
    def filters(self):
        """过滤条件"""
        return [
            # 确保有足够的历史数据
            self.index >= self.lookback_period,
            
            # 避免极端行情
            ta.atr(self.candles, 14) < ta.sma(ta.atr(self.candles, 14), 50) * 2
        ]
    
    def on_stop_loss(self, order):
        """网格策略通常不使用止损"""
        pass
    
    def terminate(self):
        """策略结束统计"""
        total_grids = len(self.grid_orders)
        filled_grids = sum(1 for g in self.grid_orders if g['filled'])
        
        self.log(f"网格统计: {filled_grids}/{total_grids} 已成交")
        
        # 导出网格数据
        import json
        grid_data = {
            'total_grids': total_grids,
            'filled_grids': filled_grids,
            'grid_details': self.grid_orders
        }
        
        with open('logs/grid_trading_report.json', 'w') as f:
            json.dump(grid_data, f, indent=2)