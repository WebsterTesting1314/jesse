# Jesse Trading Bot 🚀

<div align="center">
  
  [![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
  [![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13%2B-336791)](https://www.postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-6%2B-DC382D)](https://redis.io/)
  
  **專業的加密貨幣量化交易框架**

[快速開始](#-快速開始) • [功能特性](#-核心功能) • [文檔](#-文檔) • [社群](#-社群支援)

</div>

---

## 📖 專案簡介

Jesse 是一個功能強大且易於使用的加密貨幣量化交易框架，專為專業交易者和開發者設計。它提供了完整的回測、優化和實盤交易功能，讓您能夠快速開發、測試和部署交易策略。

### 為什麼選擇 Jesse？

- ✅ **簡單易用** - 使用 Python 編寫策略，語法簡潔直觀
- ✅ **功能完整** - 支援回測、優化、模擬交易和實盤交易
- ✅ **效能優異** - 高效的回測引擎，支援多核心並行處理
- ✅ **社群活躍** - 豐富的文檔和活躍的開發者社群

## 🎯 快速開始

### 系統需求

- Python 3.10+
- PostgreSQL 13+
- Redis 6+
- 4GB+ RAM
- Ubuntu/Debian/macOS/Windows(WSL2)

### 第一步：安裝 Jesse（5 分鐘）

```bash
# 1. 複製專案
git clone https://github.com/jesse-ai/jesse.git
cd jesse

# 2. 執行快速安裝腳本
./scripts/quick-install.sh

# 或者手動安裝：
source venv/bin/activate  # 啟動虛擬環境
pip install -e .          # 安裝 Jesse
cp .env.example .env      # 複製環境配置檔案
```

### 第二步：啟動 Jesse（1 分鐘）

```bash
# 確保在虛擬環境中
source venv/bin/activate

# 啟動 Jesse Web 介面
jesse run
```

🎉 開啟瀏覽器存取 http://localhost:9000（預設密碼：JesseTrader2025）

### 第三步：匯入歷史資料（5 分鐘）

```bash
# 匯入比特幣歷史資料
jesse import-candles Binance BTC-USDT 2023-01-01

# 匯入多個交易對
jesse import-candles Binance BTC-USDT,ETH-USDT 2023-01-01
```

### 第四步：執行第一個策略（3 分鐘）

**方法 1：使用 Web 介面**

1. 存取 http://localhost:9000
2. 選擇策略 → 設定時間範圍 → 執行回測

**方法 2：使用命令列**

```bash
jesse backtest 2023-01-01 2023-12-31 --debug
```

### 第五步：建立自己的策略（10 分鐘）

```python
# strategies/MyStrategy.py
from jesse.strategies import Strategy
import jesse.indicators as ta

class MyStrategy(Strategy):
    def should_long(self):
        # 買入條件：快速 MA > 慢速 MA
        return ta.sma(self.candles, 10) > ta.sma(self.candles, 30)

    def go_long(self):
        qty = self.capital * 0.1 / self.price  # 使用 10% 資金
        self.buy = qty, self.price
```

更多詳細教學請查看 [快速開始指南](docs/quickstart.md)

## 💡 核心功能

<table>
<tr>
<td width="50%">

### 📊 強大的回測系統

- 毫秒級精度的回測引擎
- 支援多品種、多時間框架
- 詳細的效能報告和圖表
- 避免前瞻性偏差

</td>
<td width="50%">

### 🤖 智慧優化工具

- 基於 AI 的參數優化
- 支援遺傳演算法和貝葉斯優化
- 防止過度擬合的交叉驗證
- 視覺化優化結果

</td>
</tr>
<tr>
<td width="50%">

### 📈 實盤交易支援

- 支援主流交易所（幣安、OKX 等）
- 即時監控和通知
- 風險管理工具
- 支援現貨和期貨

</td>
<td width="50%">

### 🛠️ 豐富的技術指標

- 300+ 內建技術指標
- 支援自訂指標
- 指標視覺化
- 高效能運算

</td>
</tr>
</table>

## 🏗️ 项目架构

```
jesse/
├── 📁 core/               # Jesse 核心框架
│   ├── jesse/            # 核心代码
│   ├── strategies/       # 策略基类
│   ├── tests/           # 测试套件
│   └── requirements.txt  # 依赖管理
├── 📁 jesse-defi-mev/    # DeFi MEV 扩展
│   ├── connectors/       # DeFi 连接器
│   ├── strategies/       # DeFi 策略
│   └── pyproject.toml   # Poetry 配置
├── 📁 docs/              # 详细文档
└── 📁 config/            # 配置文件
```

## 📚 文档

### 新手入门

- 📘 [快速开始指南](docs/quickstart.md) - 5 分钟上手 Jesse
- 📗 [第一个策略](docs/first-strategy.md) - 创建您的第一个交易策略
- 📙 [视频教程](https://youtube.com/jessechannel) - 手把手视频教学

### 进阶学习

- 📕 [策略开发指南](docs/strategy-development.md) - 深入了解策略开发
- 📓 [性能优化](docs/optimization.md) - 提升策略性能
- 📔 [风险管理](docs/risk-management.md) - 专业的风险控制

### 开发者资源

- 🔧 [API 参考](docs/api-reference.md) - 完整的 API 文档
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

- 📈 [趋势跟踪策略](strategies/examples/TrendFollowing.py) - 使用 ADX 和移动平均线
- 🎯 [网格交易策略](strategies/examples/GridTrading.py) - 适合震荡市场
- 📊 [均值回归策略](strategies/examples/MeanReversion.py) - 使用布林带和 RSI

## 🌟 成功案例

> "使用 Jesse 让我的交易策略开发效率提升了 10 倍！" - _专业量化交易员_

> "Jesse 的回测系统非常准确，帮助我避免了很多陷阱。" - _加密基金经理_

## 🤝 社区支持

- 💬 [Discord 社区](https://discord.gg/jesse) - 与其他交易者交流
- 🐦 [Twitter](https://twitter.com/jesse_ai) - 获取最新动态
- 📺 [YouTube 频道](https://youtube.com/jessechannel) - 视频教程
- 📝 [博客](https://blog.jesse.trade) - 深度文章

## 🚀 学习路径

### 初学者路线（1-2 天）

1. ✅ 完成上述快速开始步骤
2. ✅ 运行示例策略，理解回测报告
3. ✅ 修改策略参数，观察结果变化
4. ✅ 阅读[策略开发指南](docs/strategy-development.md)

### 进阶路线（1 周）

1. 📖 掌握[技术指标](docs/api-reference.md#技术指标)使用
2. 💡 开发自定义策略
3. 🔧 使用参数优化功能
4. 📊 实现风险管理

### 专业路线（2-4 周）

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
