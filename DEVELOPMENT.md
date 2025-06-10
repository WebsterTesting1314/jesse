# 開發工作流指南

本文檔描述了 Jesse 項目的完整開發工作流程和最佳實踐。

## 🏗️ 分支策略

### 主要分支

- **`main`**: 生產就緒的穩定代碼
- **`develop`**: 開發分支，包含最新功能
- **`feature/*`**: 功能開發分支
- **`hotfix/*`**: 緊急修復分支
- **`release/*`**: 發布準備分支

### 分支命名規範

```
feature/core-add-new-indicator
feature/contracts-flash-loan-optimization
feature/defi-mev-cross-chain-arbitrage
fix/core-backtest-memory-leak
hotfix/security-api-key-exposure
release/v1.10.0
```

## 🔄 開發流程

### 1. 創建功能分支

```bash
# 從 develop 分支創建新功能分支
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name

# 或從 main 創建熱修復分支
git checkout main
git pull origin main
git checkout -b hotfix/critical-fix
```

### 2. 提交代碼

#### 提交信息格式

```
type(scope): description

[optional body]

[optional footer]
```

**類型 (type):**
- `feat`: 新功能
- `fix`: Bug修復
- `docs`: 文檔更改
- `style`: 代碼格式調整
- `refactor`: 代碼重構
- `test`: 測試相關
- `chore`: 構建/工具變更
- `perf`: 性能優化
- `ci`: CI配置變更

### 3. 推送和創建PR

```bash
git push origin feature/your-feature-name
# 然後在GitHub創建Pull Request
```

## 📋 代碼質量要求

- **測試覆蓋率 >80%**
- **通過所有CI檢查**
- **代碼審查通過**
- **遵循編碼標準**

---

*詳細信息請參考完整開發文檔*