# Jesse 快速开始指南 🚀

本指南将帮助您在5分钟内启动并运行Jesse，开始您的量化交易之旅。

## 目录

- [环境准备](#环境准备)
- [快速安装](#快速安装)
- [创建第一个策略](#创建第一个策略)
- [运行回测](#运行回测)
- [查看结果](#查看结果)
- [下一步](#下一步)

## 环境准备

### 最低要求

- 🖥️ **操作系统**: Ubuntu 20.04+ / macOS / Windows (WSL2)
- 🐍 **Python**: 3.10 或更高版本
- 💾 **内存**: 4GB RAM
- 💿 **存储**: 10GB 可用空间

### 检查环境

```bash
# 检查Python版本
python3 --version  # 应该显示 Python 3.10+

# 检查pip
pip3 --version
```

## 快速安装

### 方法1: 使用安装脚本（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/jesse-ai/jesse.git
cd jesse

# 2. 执行快速安装脚本
./scripts/quick-install.sh
```

### 方法2: 手动安装

```bash
# 1. 克隆项目
git clone https://github.com/jesse-ai/jesse.git
cd jesse

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -e .

# 4. 复制环境配置
cp .env.example .env
```

## 创建第一个策略

### 1. 创建策略文件

创建文件 `strategies/MyFirstStrategy.py`:

```python
from jesse.strategies import Strategy
import jesse.indicators as ta
from jesse import utils

class MyFirstStrategy(Strategy):
    """
    简单的移动平均线交叉策略
    """
    
    def should_long(self) -> bool:
        """当快速MA上穿慢速MA时买入"""
        fast_ma = ta.sma(self.candles, 10)
        slow_ma = ta.sma(self.candles, 30)
        
        # 检查交叉
        return fast_ma > slow_ma and fast_ma[-2] <= slow_ma[-2]
    
    def should_short(self) -> bool:
        """当快速MA下穿慢速MA时卖出"""
        fast_ma = ta.sma(self.candles, 10)
        slow_ma = ta.sma(self.candles, 30)
        
        # 检查交叉
        return fast_ma < slow_ma and fast_ma[-2] >= slow_ma[-2]
    
    def go_long(self):
        """执行买入操作"""
        # 使用账户余额的10%
        qty = utils.size_to_qty(self.balance * 0.1, self.price)
        self.buy = qty, self.price
    
    def go_short(self):
        """执行卖出操作"""
        # 使用账户余额的10%
        qty = utils.size_to_qty(self.balance * 0.1, self.price)
        self.sell = qty, self.price
    
    def on_open_position(self, order):
        """设置止损和止盈"""
        if self.is_long:
            self.stop_loss = self.position.qty, self.price * 0.98  # 2%止损
            self.take_profit = self.position.qty, self.price * 1.05  # 5%止盈
        else:
            self.stop_loss = self.position.qty, self.price * 1.02
            self.take_profit = self.position.qty, self.price * 0.95
```

### 2. 配置策略

编辑 `config.yml`:

```yaml
# 回测配置
backtest:
  start_date: 2023-01-01
  end_date: 2023-12-31
  
# 策略配置
strategies:
  - name: MyFirstStrategy
    exchange: Binance
    symbol: BTC-USDT
    timeframe: 1h
    capital: 10000  # 初始资金
```

## 运行回测

### 1. 启动Jesse

```bash
# 激活虚拟环境
source venv/bin/activate

# 启动Jesse
jesse run
```

### 2. 使用Web界面

打开浏览器访问: http://localhost:9000

![Jesse Dashboard](../assets/dashboard-preview.png)

### 3. 使用命令行

```bash
# 运行回测
jesse backtest 2023-01-01 2023-12-31

# 带调试信息
jesse backtest 2023-01-01 2023-12-31 --debug

# 指定配置文件
jesse backtest 2023-01-01 2023-12-31 --config config.yml
```

## 查看结果

### 回测报告

回测完成后，您会看到详细的报告：

```
============================== SUMMARY ==============================
Total Closed Trades:        45
Total Net Profit:           $2,847.13 (28.47%)
Starting Balance:           $10,000
Finishing Balance:          $12,847.13

Win Rate:                   55.56%
Ratio Avg Win/Loss:         1.82
Sharpe Ratio:               1.24
Calmar Ratio:               2.15
Max Drawdown:               -13.24%
Annual Return:              28.47%
Expectancy:                 $63.27

================== TRADES ===================
Total:                      45
Profitable:                 25 (55.56%)
Losing:                     20 (44.44%)
Avg Profit:                 $183.45
Avg Loss:                   -$100.82
```

### 性能图表

Jesse会自动生成多个图表：

- 📈 **权益曲线**: 显示账户余额变化
- 📊 **回撤图**: 显示最大回撤
- 📉 **交易分布**: 显示盈亏分布
- 📋 **月度收益**: 按月统计收益

## 实时模拟交易

### 1. 配置交易所API（可选）

编辑 `.env` 文件：

```bash
# Binance API (仅用于获取实时数据)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

### 2. 启动模拟交易

```bash
# 启动纸上交易
jesse paper-trade

# 查看实时日志
tail -f storage/logs/paper-trade.log
```

## 常用命令速查

| 命令 | 说明 |
|------|------|
| `jesse run` | 启动Web界面 |
| `jesse backtest` | 运行回测 |
| `jesse paper-trade` | 模拟交易 |
| `jesse import-candles` | 导入历史数据 |
| `jesse optimize` | 参数优化 |
| `jesse routes` | 查看策略路由 |

## 调试技巧

### 1. 使用日志

```python
def should_long(self):
    fast_ma = ta.sma(self.candles, 10)
    slow_ma = ta.sma(self.candles, 30)
    
    # 添加日志
    self.log(f"Fast MA: {fast_ma}, Slow MA: {slow_ma}")
    
    return fast_ma > slow_ma
```

### 2. 查看K线数据

```python
def before(self):
    # 打印最新K线
    print(f"时间: {self.time}")
    print(f"开盘: {self.open}")
    print(f"最高: {self.high}")
    print(f"最低: {self.low}")
    print(f"收盘: {self.close}")
    print(f"成交量: {self.volume}")
```

### 3. 使用断点

```python
def go_long(self):
    # 设置断点调试
    import pdb; pdb.set_trace()
    
    qty = utils.size_to_qty(self.balance * 0.1, self.price)
    self.buy = qty, self.price
```

## 常见问题

### Q: 如何获取历史数据？

```bash
# 从交易所导入数据
jesse import-candles Binance BTC-USDT 2023-01-01
```

### Q: 如何优化策略参数？

```bash
# 运行优化
jesse optimize MyFirstStrategy
```

### Q: 如何添加自定义指标？

```python
# 在策略中定义
def my_indicator(self, period=14):
    return ta.sma(self.candles, period) * 1.01
```

## 下一步

恭喜！您已经成功运行了第一个Jesse策略。接下来您可以：

### 📚 深入学习

1. **[策略开发指南](strategy-development.md)** - 学习高级策略开发技巧
2. **[指标使用指南](indicators-guide.md)** - 掌握300+技术指标
3. **[风险管理指南](risk-management.md)** - 学习专业的风险控制

### 🎯 实践项目

1. **优化现有策略** - 使用Jesse的优化功能提升策略性能
2. **开发新策略** - 尝试不同的交易逻辑
3. **多品种交易** - 同时交易多个加密货币

### 🤝 加入社区

- 💬 [Discord](https://discord.gg/jesse) - 获取实时帮助
- 📺 [YouTube](https://youtube.com/jessechannel) - 观看视频教程
- 📝 [论坛](https://forum.jesse.trade) - 分享策略和经验

## 有用的资源

### 官方资源
- 📖 [完整文档](https://docs.jesse.trade)
- 🔧 [API参考](api-reference.md)
- 🐛 [故障排除](troubleshooting.md)

### 策略示例
- [趋势跟踪策略](../strategies/examples/TrendFollowing.py)
- [网格交易策略](../strategies/examples/GridTrading.py)
- [套利策略](../strategies/examples/Arbitrage.py)

### 视频教程
- [5分钟快速入门](https://youtu.be/example1)
- [策略开发基础](https://youtu.be/example2)
- [高级优化技巧](https://youtu.be/example3)

---

**需要帮助？** 加入我们的[Discord社区](https://discord.gg/jesse)，获得实时支持！

**Happy Trading! 🚀**