# Jesse 策略开发完全指南

## 目录

1. [策略基础](#策略基础)
2. [核心概念](#核心概念)
3. [策略生命周期](#策略生命周期)
4. [数据访问](#数据访问)
5. [订单管理](#订单管理)
6. [风险管理](#风险管理)
7. [高级技巧](#高级技巧)
8. [最佳实践](#最佳实践)

## 策略基础

### 策略类结构

每个Jesse策略都继承自`Strategy`基类：

```python
from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__()
        # 初始化策略参数
        self.stop_loss_pct = 0.02  # 2%止损
        self.take_profit_pct = 0.05  # 5%止盈
```

### 必须实现的方法

```python
class MyStrategy(Strategy):
    def should_long(self) -> bool:
        """判断是否应该开多仓"""
        return False
    
    def should_short(self) -> bool:
        """判断是否应该开空仓"""
        return False
    
    def go_long(self):
        """执行开多仓操作"""
        pass
    
    def go_short(self):
        """执行开空仓操作"""
        pass
    
    def should_cancel_entry(self) -> bool:
        """判断是否应该取消未成交订单"""
        return False
```

## 核心概念

### 1. K线数据结构

```python
# self.candles 数组结构
# [
#   [timestamp, open, close, high, low, volume],
#   ...
# ]

# 访问最新K线
current_candle = self.candles[-1]
timestamp = current_candle[0]
open_price = current_candle[1]
close_price = current_candle[2]
high_price = current_candle[3]
low_price = current_candle[4]
volume = current_candle[5]

# 便捷属性
self.open    # 当前开盘价
self.close   # 当前收盘价
self.high    # 当前最高价
self.low     # 当前最低价
self.volume  # 当前成交量
self.time    # 当前时间戳
```

### 2. 账户信息

```python
# 账户余额
self.balance          # 可用余额
self.capital          # 总资产（包括持仓）

# 仓位信息
self.position         # 当前仓位对象
self.position.qty     # 持仓数量
self.position.value   # 持仓价值
self.position.pnl     # 未实现盈亏
self.position.pnl_percentage  # 盈亏百分比

# 仓位状态
self.is_long          # 是否持有多仓
self.is_short         # 是否持有空仓
self.is_open          # 是否有开仓
self.is_close         # 是否已平仓
```

### 3. 多时间框架

```python
def __init__(self):
    super().__init__()
    # 定义额外的时间框架
    self.add_timeframe('4h')  # 添加4小时K线
    self.add_timeframe('1d')  # 添加日线

def should_long(self):
    # 访问不同时间框架的数据
    m5_close = self.candles[-1][2]  # 5分钟收盘价
    h4_close = self.get_candles('BTC-USDT', '4h')[-1][2]  # 4小时收盘价
    d1_close = self.get_candles('BTC-USDT', '1d')[-1][2]  # 日线收盘价
    
    # 多时间框架策略逻辑
    return m5_close > h4_close > d1_close
```

## 策略生命周期

### 执行流程

```python
class MyStrategy(Strategy):
    def before(self):
        """每根K线开始前调用"""
        # 更新指标、检查市场状态等
        self.sma_fast = ta.sma(self.candles, 10)
        self.sma_slow = ta.sma(self.candles, 30)
    
    def after(self):
        """每根K线结束后调用"""
        # 记录日志、更新统计等
        if self.position:
            self.log(f"持仓盈亏: {self.position.pnl}")
    
    def on_open_position(self, order):
        """开仓后调用"""
        self.log(f"开仓成功: {order}")
        # 设置止损止盈
        self.stop_loss = self.position.qty, self.price * 0.98
        self.take_profit = self.position.qty, self.price * 1.05
    
    def on_close_position(self, order):
        """平仓后调用"""
        self.log(f"平仓完成: {order}")
        self.log(f"交易盈亏: {order.pnl}")
    
    def on_stop_loss(self, order):
        """止损触发后调用"""
        self.log(f"止损触发: {order}")
    
    def on_take_profit(self, order):
        """止盈触发后调用"""
        self.log(f"止盈触发: {order}")
```

### 事件顺序

```
1. before() → 准备阶段
2. should_long/short() → 信号判断
3. go_long/short() → 下单执行
4. on_open_position() → 开仓回调
5. 持仓管理... 
6. on_close_position() → 平仓回调
7. after() → 清理阶段
```

## 数据访问

### 1. 技术指标

```python
import jesse.indicators as ta

def should_long(self):
    # 移动平均线
    sma = ta.sma(self.candles, period=20)
    ema = ta.ema(self.candles, period=20)
    
    # 动量指标
    rsi = ta.rsi(self.candles, period=14)
    macd = ta.macd(self.candles, fast=12, slow=26, signal=9)
    
    # 波动率指标
    atr = ta.atr(self.candles, period=14)
    bb_upper, bb_middle, bb_lower = ta.bollinger_bands(self.candles)
    
    # 成交量指标
    obv = ta.obv(self.candles)
    mfi = ta.mfi(self.candles, period=14)
    
    # 组合条件
    return sma > ema and rsi < 70 and self.close > bb_middle
```

### 2. 自定义指标

```python
def custom_indicator(self, period=14):
    """创建自定义指标"""
    closes = self.candles[:, 2]  # 收盘价数组
    
    # 计算自定义逻辑
    avg = np.mean(closes[-period:])
    std = np.std(closes[-period:])
    
    return (closes[-1] - avg) / std  # Z-score

def should_long(self):
    z_score = self.custom_indicator(20)
    return z_score > 2  # 价格偏离2个标准差
```

### 3. 缓存优化

```python
@property
@cached  # 使用缓存装饰器
def slow_sma(self):
    """缓存计算结果，避免重复计算"""
    return ta.sma(self.candles, 200)

def should_long(self):
    # slow_sma只会计算一次
    return self.close > self.slow_sma
```

## 订单管理

### 1. 基础订单

```python
def go_long(self):
    # 市价单
    qty = utils.size_to_qty(self.balance * 0.1, self.price)
    self.buy = qty, self.price
    
    # 限价单
    limit_price = self.price * 0.99  # 低于市价1%
    self.buy = qty, limit_price
    
    # 止损单
    self.stop_loss = qty, self.price * 0.98
    
    # 止盈单
    self.take_profit = qty, self.price * 1.05
```

### 2. 高级订单管理

```python
def go_long(self):
    # 分批建仓
    total_qty = utils.size_to_qty(self.balance * 0.3, self.price)
    
    # 第一批：市价买入1/3
    self.buy = total_qty / 3, self.price
    
    # 第二批：限价买入1/3
    self.limit_orders.append({
        'qty': total_qty / 3,
        'price': self.price * 0.99
    })
    
    # 第三批：更低价格买入1/3
    self.limit_orders.append({
        'qty': total_qty / 3,
        'price': self.price * 0.98
    })

def update_position(self):
    """动态调整仓位"""
    if self.is_long and self.position.pnl_percentage > 2:
        # 盈利2%时加仓
        additional_qty = self.position.qty * 0.5
        self.buy = additional_qty, self.price
        
        # 更新止损
        self.stop_loss = self.position.qty, self.position.entry_price
```

### 3. 订单验证

```python
def validate_order(self, qty, price):
    """验证订单是否合法"""
    # 检查最小订单量
    min_qty = self.exchange.min_order_qty(self.symbol)
    if qty < min_qty:
        return False
    
    # 检查账户余额
    required_balance = qty * price
    if required_balance > self.balance:
        return False
    
    # 检查价格精度
    price_precision = self.exchange.price_precision(self.symbol)
    if not self.is_valid_price(price, price_precision):
        return False
    
    return True
```

## 风险管理

### 1. 仓位管理

```python
def calculate_position_size(self, risk_per_trade=0.02):
    """凯利公式计算仓位"""
    # 计算历史胜率和盈亏比
    win_rate = self.winning_trades / self.total_trades
    avg_win = self.average_winning_trade
    avg_loss = abs(self.average_losing_trade)
    
    # 凯利公式
    kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    
    # 限制最大仓位
    position_pct = min(kelly_pct * 0.25, risk_per_trade)
    
    return self.balance * position_pct

def go_long(self):
    position_size = self.calculate_position_size()
    qty = utils.size_to_qty(position_size, self.price)
    self.buy = qty, self.price
```

### 2. 动态止损

```python
def update_position(self):
    """移动止损"""
    if not self.is_long:
        return
    
    # ATR移动止损
    atr = ta.atr(self.candles, 14)
    atr_multiplier = 2
    new_stop = self.close - (atr * atr_multiplier)
    
    # 只向上移动止损
    if new_stop > self.stop_loss[1]:
        self.stop_loss = self.position.qty, new_stop
        self.log(f"止损更新至: {new_stop}")
    
    # 保本止损
    if self.position.pnl_percentage > 5:
        breakeven = self.position.entry_price * 1.001  # 覆盖手续费
        if self.stop_loss[1] < breakeven:
            self.stop_loss = self.position.qty, breakeven
            self.log("设置保本止损")
```

### 3. 最大回撤控制

```python
def before(self):
    # 计算当前回撤
    self.current_drawdown = self.calculate_drawdown()
    
    # 如果回撤超过阈值，停止交易
    if self.current_drawdown > 0.15:  # 15%最大回撤
        self.stop_trading = True
        self.log("回撤过大，暂停交易")

def should_long(self):
    if hasattr(self, 'stop_trading') and self.stop_trading:
        return False
    
    # 正常策略逻辑...
    return self.signal_long()
```

## 高级技巧

### 1. 机器学习集成

```python
import joblib
from sklearn.ensemble import RandomForestClassifier

class MLStrategy(Strategy):
    def __init__(self):
        super().__init__()
        # 加载预训练模型
        self.model = joblib.load('models/rf_model.pkl')
        self.lookback = 20
    
    def prepare_features(self):
        """准备特征数据"""
        features = []
        
        # 价格特征
        returns = np.diff(self.candles[-self.lookback:, 2]) / self.candles[-self.lookback:-1, 2]
        features.extend(returns)
        
        # 技术指标特征
        rsi = ta.rsi(self.candles, 14)
        features.append(rsi)
        
        macd = ta.macd(self.candles)
        features.append(macd['macd'])
        features.append(macd['signal'])
        
        # 成交量特征
        volume_sma = ta.sma(self.candles[:, 5], 20)
        features.append(self.volume / volume_sma)
        
        return np.array(features).reshape(1, -1)
    
    def should_long(self):
        if len(self.candles) < self.lookback + 1:
            return False
        
        features = self.prepare_features()
        prediction = self.model.predict_proba(features)[0]
        
        # 如果上涨概率大于60%
        return prediction[1] > 0.6
```

### 2. 多策略组合

```python
class PortfolioStrategy(Strategy):
    def __init__(self):
        super().__init__()
        # 子策略权重
        self.strategy_weights = {
            'trend': 0.4,
            'mean_reversion': 0.3,
            'momentum': 0.3
        }
    
    def trend_signal(self):
        """趋势跟踪信号"""
        ema50 = ta.ema(self.candles, 50)
        ema200 = ta.ema(self.candles, 200)
        return 1 if ema50 > ema200 else -1
    
    def mean_reversion_signal(self):
        """均值回归信号"""
        bb_upper, bb_middle, bb_lower = ta.bollinger_bands(self.candles)
        if self.close < bb_lower:
            return 1  # 超卖
        elif self.close > bb_upper:
            return -1  # 超买
        return 0
    
    def momentum_signal(self):
        """动量信号"""
        rsi = ta.rsi(self.candles, 14)
        if rsi < 30:
            return 1
        elif rsi > 70:
            return -1
        return 0
    
    def should_long(self):
        # 综合多个策略信号
        total_signal = (
            self.strategy_weights['trend'] * self.trend_signal() +
            self.strategy_weights['mean_reversion'] * self.mean_reversion_signal() +
            self.strategy_weights['momentum'] * self.momentum_signal()
        )
        
        return total_signal > 0.5
```

### 3. 市场状态识别

```python
class AdaptiveStrategy(Strategy):
    def identify_market_regime(self):
        """识别市场状态"""
        # 计算波动率
        atr = ta.atr(self.candles, 14)
        avg_atr = ta.sma(atr, 50)
        
        # 计算趋势强度
        adx = ta.adx(self.candles, 14)
        
        # 判断市场状态
        if adx > 25 and atr > avg_atr * 1.5:
            return 'trending_volatile'
        elif adx > 25 and atr <= avg_atr * 1.5:
            return 'trending_calm'
        elif adx <= 25 and atr > avg_atr * 1.5:
            return 'ranging_volatile'
        else:
            return 'ranging_calm'
    
    def should_long(self):
        regime = self.identify_market_regime()
        
        # 根据市场状态使用不同策略
        if regime == 'trending_volatile':
            # 趋势跟踪
            return self.trend_following_signal()
        elif regime == 'ranging_calm':
            # 均值回归
            return self.mean_reversion_signal()
        else:
            # 混合策略
            return self.hybrid_signal()
```

## 最佳实践

### 1. 代码组织

```python
# strategies/base.py
class BaseStrategy(Strategy):
    """基础策略类，包含通用功能"""
    
    def calculate_position_size(self):
        """通用仓位计算"""
        pass
    
    def set_risk_parameters(self):
        """风险参数设置"""
        pass

# strategies/trend_following.py
from .base import BaseStrategy

class TrendFollowing(BaseStrategy):
    """继承基础策略"""
    def should_long(self):
        # 具体策略逻辑
        pass
```

### 2. 参数优化

```python
class OptimizableStrategy(Strategy):
    def hyperparameters(self):
        """定义可优化参数"""
        return [
            {'name': 'fast_period', 'type': int, 'min': 5, 'max': 50, 'default': 10},
            {'name': 'slow_period', 'type': int, 'min': 20, 'max': 200, 'default': 30},
            {'name': 'rsi_period', 'type': int, 'min': 7, 'max': 21, 'default': 14},
            {'name': 'stop_loss', 'type': float, 'min': 0.01, 'max': 0.05, 'default': 0.02},
        ]
    
    def should_long(self):
        # 使用超参数
        fast_ma = ta.sma(self.candles, self.hp['fast_period'])
        slow_ma = ta.sma(self.candles, self.hp['slow_period'])
        rsi = ta.rsi(self.candles, self.hp['rsi_period'])
        
        return fast_ma > slow_ma and rsi < 70
```

### 3. 日志和监控

```python
class MonitoredStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.trade_log = []
    
    def on_open_position(self, order):
        # 记录交易信息
        trade_info = {
            'time': self.time,
            'type': 'long' if self.is_long else 'short',
            'price': order.price,
            'qty': order.qty,
            'reason': self.entry_reason
        }
        self.trade_log.append(trade_info)
        
        # 发送通知
        self.notify(f"开仓: {trade_info}")
    
    def terminate(self):
        """策略结束时导出日志"""
        import json
        with open('logs/trades.json', 'w') as f:
            json.dump(self.trade_log, f, indent=2)
```

## 调试技巧

### 1. 使用调试模式

```bash
# 启用调试输出
jesse backtest 2023-01-01 2023-12-31 --debug
```

### 2. 策略内调试

```python
def should_long(self):
    # 打印关键变量
    self.log(f"Price: {self.price}, SMA: {self.sma}")
    
    # 条件断点
    if self.price > 50000:
        import pdb; pdb.set_trace()
    
    # 保存调试数据
    self.debug_data.append({
        'time': self.time,
        'price': self.price,
        'indicators': self.get_indicators()
    })
```

### 3. 可视化调试

```python
def terminate(self):
    """策略结束后生成调试图表"""
    import matplotlib.pyplot as plt
    
    # 绘制价格和指标
    plt.figure(figsize=(12, 6))
    plt.plot(self.prices, label='Price')
    plt.plot(self.sma_values, label='SMA')
    plt.scatter(self.buy_signals, self.buy_prices, color='green', marker='^')
    plt.scatter(self.sell_signals, self.sell_prices, color='red', marker='v')
    plt.legend()
    plt.savefig('debug/strategy_signals.png')
```

## 总结

成功的策略开发需要：

1. ✅ **扎实的基础** - 理解Jesse的核心概念
2. ✅ **严格的风控** - 始终把风险管理放在首位  
3. ✅ **持续优化** - 不断测试和改进策略
4. ✅ **代码质量** - 保持代码清晰、可维护
5. ✅ **数据验证** - 确保数据质量和策略逻辑

---

**下一步：**
- 📚 阅读[API参考文档](api-reference.md)了解所有可用接口
- 🔧 查看[示例策略](../strategies/examples/)获得灵感
- 💬 加入[Discord社区](https://discord.gg/jesse)交流经验