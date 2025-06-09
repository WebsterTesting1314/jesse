# Jesse API 参考文档

## 目录

- [Strategy 类](#strategy-类)
- [技术指标](#技术指标)
- [工具函数](#工具函数)
- [数据结构](#数据结构)
- [事件回调](#事件回调)

## Strategy 类

### 基础属性

| 属性 | 类型 | 描述 |
|------|------|------|
| `self.candles` | np.ndarray | K线数据数组 [timestamp, open, close, high, low, volume] |
| `self.open` | float | 当前K线开盘价 |
| `self.close` | float | 当前K线收盘价 |
| `self.high` | float | 当前K线最高价 |
| `self.low` | float | 当前K线最低价 |
| `self.volume` | float | 当前K线成交量 |
| `self.time` | int | 当前时间戳（毫秒） |
| `self.index` | int | 当前K线索引 |

### 账户信息

| 属性 | 类型 | 描述 |
|------|------|------|
| `self.balance` | float | 可用余额 |
| `self.capital` | float | 总资产（包括持仓） |
| `self.equity` | float | 净值 |

### 仓位信息

| 属性 | 类型 | 描述 |
|------|------|------|
| `self.position` | Position | 当前仓位对象 |
| `self.position.qty` | float | 持仓数量 |
| `self.position.entry_price` | float | 开仓均价 |
| `self.position.value` | float | 持仓价值 |
| `self.position.pnl` | float | 未实现盈亏 |
| `self.position.pnl_percentage` | float | 未实现盈亏百分比 |
| `self.is_long` | bool | 是否持有多仓 |
| `self.is_short` | bool | 是否持有空仓 |
| `self.is_open` | bool | 是否有持仓 |
| `self.is_close` | bool | 是否无持仓 |

### 核心方法

#### should_long()
```python
def should_long(self) -> bool:
    """
    判断是否应该开多仓
    
    返回:
        bool: True表示应该开多仓
    """
```

#### should_short()
```python
def should_short(self) -> bool:
    """
    判断是否应该开空仓
    
    返回:
        bool: True表示应该开空仓
    """
```

#### go_long()
```python
def go_long(self):
    """
    执行开多仓操作
    设置 self.buy = qty, price
    """
```

#### go_short()
```python
def go_short(self):
    """
    执行开空仓操作
    设置 self.sell = qty, price
    """
```

### 订单管理

```python
# 买入订单
self.buy = qty, price  # 设置买入订单

# 卖出订单
self.sell = qty, price  # 设置卖出订单

# 止损订单
self.stop_loss = qty, price  # 设置止损

# 止盈订单
self.take_profit = qty, price  # 设置止盈

# 取消订单
self.cancel()  # 取消所有未成交订单
```

### 高级功能

#### 添加时间框架
```python
def __init__(self):
    super().__init__()
    self.add_timeframe('4h')  # 添加4小时时间框架
    self.add_timeframe('1d')  # 添加日线时间框架

def should_long(self):
    # 访问其他时间框架数据
    h4_candles = self.get_candles(self.symbol, '4h')
    d1_candles = self.get_candles(self.symbol, '1d')
```

#### 日志记录
```python
self.log("这是一条日志信息")  # 记录日志
self.log(f"价格: {self.price}, RSI: {rsi}", level='debug')
```

#### 变量存储
```python
# 使用 self.vars 字典存储临时变量
self.vars['signal_strength'] = 0.8
self.vars['entry_reason'] = "MA交叉"
```

## 技术指标

Jesse提供300+技术指标，使用方式：

```python
import jesse.indicators as ta
```

### 趋势指标

| 函数 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `ta.sma(candles, period)` | candles, period | float | 简单移动平均 |
| `ta.ema(candles, period)` | candles, period | float | 指数移动平均 |
| `ta.wma(candles, period)` | candles, period | float | 加权移动平均 |
| `ta.hma(candles, period)` | candles, period | float | Hull移动平均 |
| `ta.tema(candles, period)` | candles, period | float | 三重指数移动平均 |

### 动量指标

| 函数 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `ta.rsi(candles, period)` | candles, period=14 | float | 相对强弱指数 |
| `ta.stoch(candles, period)` | candles, period=14 | dict | 随机指标 |
| `ta.macd(candles, fast, slow, signal)` | candles, 12, 26, 9 | dict | MACD |
| `ta.adx(candles, period)` | candles, period=14 | float | 平均趋向指数 |
| `ta.cci(candles, period)` | candles, period=20 | float | 商品通道指数 |

### 波动率指标

| 函数 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `ta.atr(candles, period)` | candles, period=14 | float | 平均真实波幅 |
| `ta.bollinger_bands(candles, period, std)` | candles, 20, 2 | tuple | 布林带(上轨,中轨,下轨) |
| `ta.keltner(candles, period)` | candles, period=20 | tuple | 肯特纳通道 |
| `ta.donchian(candles, period)` | candles, period=20 | tuple | 唐奇安通道 |

### 成交量指标

| 函数 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `ta.obv(candles)` | candles | float | 能量潮 |
| `ta.mfi(candles, period)` | candles, period=14 | float | 资金流量指数 |
| `ta.vwap(candles)` | candles | float | 成交量加权平均价 |

### 使用示例

```python
# 单值返回
sma_value = ta.sma(self.candles, 20)
rsi_value = ta.rsi(self.candles, 14)

# 多值返回
upper, middle, lower = ta.bollinger_bands(self.candles, 20, 2)

# 字典返回
macd_result = ta.macd(self.candles)
macd_line = macd_result['macd']
signal_line = macd_result['signal']
histogram = macd_result['hist']
```

## 工具函数

### jesse.utils

| 函数 | 参数 | 返回值 | 描述 |
|------|------|--------|------|
| `size_to_qty(size, price)` | size, price | float | 将资金转换为数量 |
| `qty_to_size(qty, price)` | qty, price | float | 将数量转换为资金 |
| `risk_to_qty(risk, price, stop_price)` | risk, price, stop | float | 基于风险计算数量 |
| `round_price(price, precision)` | price, precision | float | 按精度四舍五入价格 |
| `round_qty(qty, precision)` | qty, precision | float | 按精度四舍五入数量 |

### 使用示例

```python
from jesse import utils

# 计算仓位大小
position_size = self.balance * 0.1  # 使用10%资金
qty = utils.size_to_qty(position_size, self.price)

# 基于风险计算仓位
risk_amount = 100  # 风险$100
stop_price = self.price * 0.98  # 2%止损
qty = utils.risk_to_qty(risk_amount, self.price, stop_price)

# 精度处理
qty = utils.round_qty(qty, 0.001)  # 保留3位小数
price = utils.round_price(price, 0.01)  # 保留2位小数
```

## 数据结构

### Candle 数组结构
```python
# self.candles 是一个 numpy 数组
# 每行代表一根K线，列定义如下：
# [0] timestamp - 时间戳（毫秒）
# [1] open     - 开盘价
# [2] close    - 收盘价
# [3] high     - 最高价
# [4] low      - 最低价
# [5] volume   - 成交量

# 访问示例
latest_candle = self.candles[-1]  # 最新K线
timestamp = latest_candle[0]
open_price = latest_candle[1]
close_price = latest_candle[2]

# 批量访问
closes = self.candles[:, 2]  # 所有收盘价
volumes = self.candles[:, 5]  # 所有成交量
```

### Position 对象
```python
class Position:
    qty: float           # 持仓数量
    entry_price: float   # 开仓均价
    current_price: float # 当前价格
    value: float         # 持仓价值
    pnl: float          # 未实现盈亏
    pnl_percentage: float # 盈亏百分比
    type: str           # 'long' 或 'short'
    opened_at: int      # 开仓时间戳
```

### Order 对象
```python
class Order:
    id: str              # 订单ID
    symbol: str          # 交易对
    side: str           # 'buy' 或 'sell'
    type: str           # 'MARKET' 或 'LIMIT'
    qty: float          # 数量
    price: float        # 价格
    status: str         # 状态
    created_at: int     # 创建时间
    executed_at: int    # 执行时间
```

## 事件回调

### 生命周期回调

```python
def before(self):
    """每根K线开始前调用"""
    pass

def after(self):
    """每根K线结束后调用"""
    pass

def before_terminate(self):
    """策略结束前调用"""
    pass

def terminate(self):
    """策略结束时调用"""
    pass
```

### 交易事件回调

```python
def on_open_position(self, order):
    """
    开仓成功后调用
    
    参数:
        order: Order对象，包含订单信息
    """
    pass

def on_close_position(self, order):
    """
    平仓成功后调用
    
    参数:
        order: Order对象，包含订单信息
    """
    pass

def on_stop_loss(self, order):
    """
    止损触发后调用
    
    参数:
        order: Order对象，包含订单信息
    """
    pass

def on_take_profit(self, order):
    """
    止盈触发后调用
    
    参数:
        order: Order对象，包含订单信息
    """
    pass

def on_cancel(self, order):
    """
    订单取消后调用
    
    参数:
        order: Order对象，包含订单信息
    """
    pass
```

### 自定义方法

```python
def filters(self):
    """
    定义过滤条件
    
    返回:
        list: 布尔条件列表，所有条件必须为True才能交易
    """
    return [
        self.index >= 50,  # 至少需要50根K线
        self.balance > 100,  # 余额大于100
    ]

def hyperparameters(self):
    """
    定义可优化参数
    
    返回:
        list: 参数定义列表
    """
    return [
        {'name': 'period', 'type': int, 'min': 10, 'max': 50, 'default': 20},
        {'name': 'multiplier', 'type': float, 'min': 0.5, 'max': 3.0, 'default': 1.5},
    ]

def update_position(self):
    """
    更新持仓（如移动止损）
    每根K线都会调用
    """
    pass

def should_cancel_entry(self):
    """
    判断是否应该取消未成交订单
    
    返回:
        bool: True表示取消订单
    """
    return False
```

## 完整示例

```python
from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class CompleteExample(Strategy):
    def __init__(self):
        super().__init__()
        self.fast_period = 10
        self.slow_period = 30
        
    def should_long(self):
        # 使用多个指标
        fast_ma = ta.sma(self.candles, self.fast_period)
        slow_ma = ta.sma(self.candles, self.slow_period)
        rsi = ta.rsi(self.candles, 14)
        
        # 组合条件
        return fast_ma > slow_ma and rsi < 70
    
    def go_long(self):
        # 计算仓位
        qty = utils.size_to_qty(self.balance * 0.1, self.price)
        
        # 下单
        self.buy = qty, self.price
        
        # 记录
        self.log(f"开多仓: {qty} @ {self.price}")
    
    def on_open_position(self, order):
        # 设置止损止盈
        self.stop_loss = self.position.qty, self.position.entry_price * 0.98
        self.take_profit = self.position.qty, self.position.entry_price * 1.05
    
    def update_position(self):
        # 移动止损
        if self.is_long and self.position.pnl_percentage > 2:
            self.stop_loss = self.position.qty, self.position.entry_price
```

---

**需要更详细的文档？** 访问 [完整文档](https://docs.jesse.trade)