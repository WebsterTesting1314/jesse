# Jesse Trading Bot 🚀

<div align="center">
  
  [![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791)](https://www.postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-6%2B-DC382D)](https://redis.io/)
  
  **专业的加密货币量化交易框架**
  
  [快速开始](#-快速开始) • [功能特性](#-核心功能) • [文档](#-文档) • [社区](#-社区支持)

</div>

---

## 📖 项目简介

Jesse是一个功能强大且易于使用的加密货币量化交易框架，专为专业交易者和开发者设计。它提供了完整的回测、优化和实盘交易功能，让您能够快速开发、测试和部署交易策略。

### 为什么选择Jesse？

- ✅ **简单易用** - 使用Python编写策略，语法简洁直观
- ✅ **功能完整** - 支持回测、优化、模拟交易和实盘交易
- ✅ **性能优异** - 高效的回测引擎，支持多核并行处理
- ✅ **社区活跃** - 丰富的文档和活跃的开发者社区

## 🎯 快速开始

### 系统要求

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- 4GB+ RAM
- Ubuntu/Debian/macOS/Windows(WSL2)

### 第一步：安装Jesse（5分钟）

```bash
# 1. 克隆项目
git clone https://github.com/jesse-ai/jesse.git
cd jesse

# 2. 运行快速安装脚本
./scripts/quick-install.sh

# 或者手动安装：
source venv/bin/activate  # 激活虚拟环境
pip install -e .          # 安装Jesse
```

### 第二步：启动Jesse（1分钟）

```bash
# 确保在虚拟环境中
source venv/bin/activate

# 启动Jesse Web界面
jesse run
```

🎉 打开浏览器访问 http://localhost:9000（默认密码：JesseTrader2025）

### 第三步：导入历史数据（5分钟）

```bash
# 导入比特币历史数据
jesse import-candles Binance BTC-USDT 2023-01-01

# 导入多个交易对
jesse import-candles Binance BTC-USDT,ETH-USDT 2023-01-01
```

### 第四步：运行第一个策略（3分钟）

**方法1：使用Web界面**
1. 访问 http://localhost:9000
2. 选择策略 → 设置时间范围 → 运行回测

**方法2：使用命令行**
```bash
jesse backtest 2023-01-01 2023-12-31 --debug
```

### 第五步：创建自己的策略（10分钟）

```python
# strategies/MyStrategy.py
from jesse.strategies import Strategy
import jesse.indicators as ta

class MyStrategy(Strategy):
    def should_long(self):
        # 买入条件：快速MA > 慢速MA
        return ta.sma(self.candles, 10) > ta.sma(self.candles, 30)
    
    def go_long(self):
        qty = self.capital * 0.1 / self.price  # 使用10%资金
        self.buy = qty, self.price
```

更多详细教程请查看 [快速开始指南](docs/quickstart.md)

## 💡 核心功能

<table>
<tr>
<td width="50%">

### 📊 强大的回测系统
- 毫秒级精度的回测引擎
- 支持多品种、多时间框架
- 详细的性能报告和图表
- 避免前瞻性偏差

</td>
<td width="50%">

### 🤖 智能优化工具
- 基于AI的参数优化
- 支持遗传算法和贝叶斯优化
- 防止过拟合的交叉验证
- 可视化优化结果

</td>
</tr>
<tr>
<td width="50%">

### 📈 实盘交易支持
- 支持主流交易所(币安、OKX等)
- 实时监控和通知
- 风险管理工具
- 支持现货和期货

</td>
<td width="50%">

### 🛠️ 丰富的技术指标
- 300+内置技术指标
- 支持自定义指标
- 指标可视化
- 高性能计算

</td>
</tr>
</table>

## 🏗️ 项目架构

```
jesse/
├── 📁 docs/                # 详细文档
│   ├── quickstart.md      # 快速开始指南
│   ├── architecture.md    # 架构说明
│   └── api-reference.md   # API参考
├── 📁 jesse/              # 核心代码
│   ├── indicators/        # 技术指标库
│   ├── strategies/        # 策略基类
│   ├── modes/            # 运行模式
│   └── services/         # 核心服务
├── 📁 strategies/         # 您的策略
├── 📁 storage/           # 数据存储
└── 📁 tests/             # 测试套件
```

## 📚 文档

### 新手入门
- 📘 [快速开始指南](docs/quickstart.md) - 5分钟上手Jesse
- 📗 [第一个策略](docs/first-strategy.md) - 创建您的第一个交易策略
- 📙 [视频教程](https://youtube.com/jessechannel) - 手把手视频教学

### 进阶学习
- 📕 [策略开发指南](docs/strategy-development.md) - 深入了解策略开发
- 📓 [性能优化](docs/optimization.md) - 提升策略性能
- 📔 [风险管理](docs/risk-management.md) - 专业的风险控制

### 开发者资源
- 🔧 [API参考](docs/api-reference.md) - 完整的API文档
- 🏗️ [架构设计](docs/architecture.md) - 系统架构详解
- 🐛 [故障排除](docs/troubleshooting.md) - 常见问题解决

## 💻 示例策略

### 1. 简单移动平均策略

```python
from jesse.strategies import Strategy
import jesse.indicators as ta

class SimpleMA(Strategy):
    def should_long(self):
        # 快速MA上穿慢速MA时做多
        return ta.sma(self.candles, 10) > ta.sma(self.candles, 30)
    
    def should_short(self):
        # 快速MA下穿慢速MA时做空
        return ta.sma(self.candles, 10) < ta.sma(self.candles, 30)
    
    def go_long(self):
        qty = self.capital * 0.1 / self.price  # 使用10%资金
        self.buy = qty, self.price
        self.stop_loss = qty, self.price * 0.98  # 2%止损
        self.take_profit = qty, self.price * 1.05  # 5%止盈
```

### 2. 更多示例策略

- 📈 [趋势跟踪策略](strategies/examples/TrendFollowing.py) - 使用ADX和移动平均线
- 🎯 [网格交易策略](strategies/examples/GridTrading.py) - 适合震荡市场
- 📊 [均值回归策略](strategies/examples/MeanReversion.py) - 使用布林带和RSI

## 🌟 成功案例

> "使用Jesse让我的交易策略开发效率提升了10倍！" - *专业量化交易员*

> "Jesse的回测系统非常准确，帮助我避免了很多陷阱。" - *加密基金经理*

## 🤝 社区支持

- 💬 [Discord社区](https://discord.gg/jesse) - 与其他交易者交流
- 🐦 [Twitter](https://twitter.com/jesse_ai) - 获取最新动态
- 📺 [YouTube频道](https://youtube.com/jessechannel) - 视频教程
- 📝 [博客](https://blog.jesse.trade) - 深度文章

## 🚀 学习路径

### 初学者路线（1-2天）
1. ✅ 完成上述快速开始步骤
2. ✅ 运行示例策略，理解回测报告
3. ✅ 修改策略参数，观察结果变化
4. ✅ 阅读[策略开发指南](docs/strategy-development.md)

### 进阶路线（1周）
1. 📖 掌握[技术指标](docs/api-reference.md#技术指标)使用
2. 💡 开发自定义策略
3. 🔧 使用参数优化功能
4. 📊 实现风险管理

### 专业路线（2-4周）
1. 🏗️ 深入[架构设计](docs/architecture.md)
2. 🚀 配置实盘交易
3. 🤖 集成机器学习模型
4. 📈 开发复杂策略组合

## 🎯 快速命令参考

```bash
# 基础命令
jesse run                    # 启动Web界面
jesse backtest              # 运行回测
jesse import-candles        # 导入数据
jesse optimize              # 参数优化

# 查看信息
jesse candles BTC-USDT      # 查看可用数据
jesse routes                # 查看策略配置
jesse stats                 # 查看统计信息

# 高级功能
jesse paper-trade           # 模拟交易
jesse live-trade           # 实盘交易
```

## 📊 性能展示

<div align="center">
  <img src="assets/performance-chart.png" alt="Performance Chart" width="80%">
  <p><em>Jesse策略回测结果示例</em></p>
</div>

## 🛡️ 安全与合规

- ✅ 开源透明，代码可审计
- ✅ 本地运行，数据安全
- ✅ 支持多种风险管理工具
- ✅ 遵循最佳安全实践

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 💡 实践建议

### 开发技巧
1. **从简单开始** - 先用示例策略熟悉系统
2. **重视回测** - 充分测试后再实盘
3. **风险管理** - 始终设置止损，控制仓位
4. **持续优化** - 记录表现，不断改进

### 常见陷阱
- ❌ 过度拟合历史数据
- ❌ 忽视交易成本和滑点
- ❌ 使用未来数据（前瞻性偏差）
- ❌ 风险管理不当

## ⚠️ 风险提示

加密货币交易存在高风险。请谨慎投资，只投入您能承受损失的资金。过去的表现不代表未来的结果。

---

<div align="center">
  
  **[🏠 官网](https://jesse.trade)** • **[📚 文档](https://docs.jesse.trade)** • **[💬 社区](https://discord.gg/jesse)**
  
  Made with ❤️ by Jesse Team
  
</div>