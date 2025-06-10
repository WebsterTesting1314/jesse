# Jesse 交易機器人 🚀

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

### 第一步：安裝 Jesse（5分鐘）

```bash
# 1. 複製專案
git clone https://github.com/jesse-ai/jesse.git
cd jesse

# 2. 執行快速安裝腳本
./scripts/quick-install.sh

# 或者手動安裝：
source venv/bin/activate  # 啟動虛擬環境
pip install -e .          # 安裝 Jesse
# 3. 複製環境配置
cp .env.example .env
```

### 第二步：啟動 Jesse（1分鐘）

```bash
# 確保在虛擬環境中
source venv/bin/activate

# 啟動 Jesse Web 介面
jesse run
```

🎉 開啟瀏覽器存取 http://localhost:9000（預設密碼：JesseTrader2025）

### 第三步：匯入歷史資料（5分鐘）

```bash
# 匯入比特幣歷史資料
jesse import-candles Binance BTC-USDT 2023-01-01

# 匯入多個交易對
jesse import-candles Binance BTC-USDT,ETH-USDT 2023-01-01
```

### 第四步：執行第一個策略（3分鐘）

**方法1：使用 Web 介面**
1. 存取 http://localhost:9000
2. 選擇策略 → 設定時間範圍 → 執行回測

**方法2：使用命令列**
```bash
jesse backtest 2023-01-01 2023-12-31 --debug
```

### 第五步：建立自己的策略（10分鐘）

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

### 📊 強大的回測系統
- 毫秒級精度的回測引擎
- 支援多品種、多時間框架
- 詳細的效能報告和圖表
- 避免前瞻性偏差

### 🤖 智慧優化工具
- 基於 AI 的參數優化
- 支援遺傳演算法和貝葉斯優化
- 防止過度擬合的交叉驗證
- 視覺化優化結果

### 📈 實盤交易支援
- 支援主流交易所（幣安、OKX 等）
- 即時監控和通知
- 風險管理工具
- 支援現貨和期貨

### 🛠️ 豐富的技術指標
- 300+ 內建技術指標
- 支援自訂指標
- 指標視覺化
- 高效能運算

## 🏗️ 專案架構

```
jesse/
├── 📁 docs/                # 詳細文檔
│   ├── quickstart.md      # 快速開始指南
│   ├── architecture.md    # 架構說明
│   └── api-reference.md   # API 參考
├── 📁 jesse/              # 核心程式碼
│   ├── indicators/        # 技術指標庫
│   ├── strategies/        # 策略基底類別
│   ├── modes/            # 執行模式
│   └── services/         # 核心服務
├── 📁 strategies/         # 您的策略
├── 📁 storage/           # 資料儲存
└── 📁 tests/             # 測試套件
```

## 📚 文檔

### 新手入門
- 📘 [快速開始指南](docs/quickstart.md) - 5分鐘上手 Jesse
- 📗 [第一個策略](docs/first-strategy.md) - 建立您的第一個交易策略
- 📙 [影片教學](https://youtube.com/jessechannel) - 手把手影片教學

### 進階學習
- 📕 [策略開發指南](docs/strategy-development.md) - 深入了解策略開發
- 📓 [效能優化](docs/optimization.md) - 提升策略效能
- 📔 [風險管理](docs/risk-management.md) - 專業的風險控制

### 開發者資源
- 🔧 [API 參考](docs/api-reference.md) - 完整的 API 文檔
- 🏗️ [架構設計](docs/architecture.md) - 系統架構詳解
- 🐛 [故障排除](docs/troubleshooting.md) - 常見問題解決

## 💻 範例策略

### 1. 簡單移動平均策略

```python
from jesse.strategies import Strategy
import jesse.indicators as ta

class SimpleMA(Strategy):
    def should_long(self):
        # 快速 MA 上穿慢速 MA 時做多
        return ta.sma(self.candles, 10) > ta.sma(self.candles, 30)
    
    def should_short(self):
        # 快速 MA 下穿慢速 MA 時做空
        return ta.sma(self.candles, 10) < ta.sma(self.candles, 30)
    
    def go_long(self):
        qty = self.capital * 0.1 / self.price  # 使用 10% 資金
        self.buy = qty, self.price
        self.stop_loss = qty, self.price * 0.98  # 2% 停損
        self.take_profit = qty, self.price * 1.05  # 5% 停利
```

### 2. 更多範例策略

- 📈 [趨勢跟蹤策略](strategies/examples/TrendFollowing.py) - 使用 ADX 和移動平均線
- 🎯 [網格交易策略](strategies/examples/GridTrading.py) - 適合震盪市場
- 📊 [均值回歸策略](strategies/examples/MeanReversion.py) - 使用布林通道和 RSI

## 🌟 成功案例

> "使用 Jesse 讓我的交易策略開發效率提升了 10 倍！" - *專業量化交易員*

> "Jesse 的回測系統非常準確，幫助我避免了很多陷阱。" - *加密基金經理*

## 🤝 社群支援

- 💬 [Discord 社群](https://discord.gg/jesse) - 與其他交易者交流
- 🐦 [Twitter](https://twitter.com/jesse_ai) - 獲取最新動態
- 📺 [YouTube 頻道](https://youtube.com/jessechannel) - 影片教學
- 📝 [部落格](https://blog.jesse.trade) - 深度文章

## 🚀 學習路徑

### 初學者路線（1-2天）
1. ✅ 完成上述快速開始步驟
2. ✅ 執行範例策略，理解回測報告
3. ✅ 修改策略參數，觀察結果變化
4. ✅ 閱讀[策略開發指南](docs/strategy-development.md)

### 進階路線（1週）
1. 📖 掌握[技術指標](docs/api-reference.md#技術指標)使用
2. 💡 開發自訂策略
3. 🔧 使用參數優化功能
4. 📊 實現風險管理

### 專業路線（2-4週）
1. 🏗️ 深入[架構設計](docs/architecture.md)
2. 🚀 配置實盤交易
3. 🤖 整合機器學習模型
4. 📈 開發複雜策略組合

## 🎯 快速命令參考

```bash
# 基礎命令
jesse run                    # 啟動 Web 介面
jesse backtest              # 執行回測
jesse import-candles        # 匯入資料
jesse optimize              # 參數優化

# 查看資訊
jesse candles BTC-USDT      # 查看可用資料
jesse routes                # 查看策略配置
jesse stats                 # 查看統計資訊

# 進階功能
jesse paper-trade           # 模擬交易
jesse live-trade           # 實盤交易
```

## 🛡️ 安全與合規

- ✅ 開源透明，程式碼可審計
- ✅ 本地執行，資料安全
- ✅ 支援多種風險管理工具
- ✅ 遵循最佳安全實務

## 📝 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 檔案

## 💡 實務建議

### 開發技巧
1. **從簡單開始** - 先用範例策略熟悉系統
2. **重視回測** - 充分測試後再實盤
3. **風險管理** - 始終設定停損，控制倉位
4. **持續優化** - 記錄表現，不斷改進

### 常見陷阱
- ❌ 過度擬合歷史資料
- ❌ 忽視交易成本和滑點
- ❌ 使用未來資料（前瞻性偏差）
- ❌ 風險管理不當

## ⚠️ 風險提示

加密貨幣交易存在高風險。請謹慎投資，只投入您能承受損失的資金。過去的表現不代表未來的結果。

---

<div align="center">
  
  **[🏠 官網](https://jesse.trade)** • **[📚 文檔](https://docs.jesse.trade)** • **[💬 社群](https://discord.gg/jesse)**
  
  Made with ❤️ by Jesse Team
  
</div>
