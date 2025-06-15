# MCP 工具安裝與設定指南

## 已安裝的 MCP 工具

1. **Task Master MCP** ✅
   - 功能：任務分解、PRD 轉任務、進度追蹤
   - 已在 `.cursor/mcp.json` 中配置

2. **GitHub MCP** ✅
   - 功能：直接操作 repo、Issue、PR、分支等
   - 需要設定：`GITHUB_PERSONAL_ACCESS_TOKEN`

3. **Zapier MCP** ✅
   - 功能：整合 6000+ SaaS 工具與自動化流程
   - 需要設定：`ZAPIER_API_KEY`

4. **Docker MCP** ✅
   - 功能：在隔離容器中安全執行任意語言腳本
   - 需求：確保 Docker Desktop 已安裝並運行

5. **Vectorize MCP** ✅
   - 功能：連接企業知識庫、PDF、文件，支援向量檢索
   - 需要設定：`VECTORIZE_API_KEY`

6. **Brave Search MCP** ✅
   - 功能：私有化網頁/本地搜尋
   - 需要設定：`BRAVE_API_KEY`

## 設定步驟

### 1. 獲取 API 密鑰

- **GitHub Personal Access Token**
  1. 前往 https://github.com/settings/tokens
  2. 點擊 "Generate new token (classic)"
  3. 選擇需要的權限（repo, workflow, admin:org 等）
  4. 複製生成的 token

- **Zapier API Key**
  1. 登入 https://zapier.com
  2. 前往 https://zapier.com/app/settings/integrations
  3. 找到 "AI Actions" 並點擊 "Manage"
  4. 複製 API Key

- **Brave Search API Key**
  1. 前往 https://brave.com/search/api/
  2. 註冊並創建 API Key
  3. 複製生成的 key

- **Vectorize API Key**
  1. 前往 Vectorize 服務提供商網站
  2. 註冊並獲取 API Key

### 2. 設定環境變數

#### 方法一：在 Cursor 設定中直接添加
1. 開啟 Cursor 設定（Ctrl+,）
2. 搜尋 "MCP"
3. 在環境變數區域添加以下內容：
   ```
   GITHUB_PERSONAL_ACCESS_TOKEN=你的_github_token
   ZAPIER_API_KEY=你的_zapier_key
   VECTORIZE_API_KEY=你的_vectorize_key
   BRAVE_API_KEY=你的_brave_key
   ```

#### 方法二：創建 .env 檔案
1. 在專案根目錄創建 `.env` 檔案
2. 添加以下內容：
   ```env
   # Task Master AI API Keys
   ANTHROPIC_API_KEY=your_anthropic_api_key_here
   PERPLEXITY_API_KEY=your_perplexity_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   GOOGLE_API_KEY=your_google_api_key_here
   MISTRAL_API_KEY=your_mistral_api_key_here
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   XAI_API_KEY=your_xai_api_key_here
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here

   # GitHub MCP
   GITHUB_PERSONAL_ACCESS_TOKEN=your_github_pat_here

   # Zapier MCP
   ZAPIER_API_KEY=your_zapier_api_key_here

   # Vectorize MCP
   VECTORIZE_API_KEY=your_vectorize_api_key_here

   # Brave Search MCP
   BRAVE_API_KEY=your_brave_api_key_here
   ```

### 3. 重啟 Cursor

完成設定後，需要重啟 Cursor 以載入新的 MCP 配置。

### 4. Docker MCP 特別注意事項

Docker MCP 需要確保：
1. Docker Desktop 已安裝並運行
2. 用戶有執行 Docker 命令的權限
3. 首次使用時會自動下載 `mcp/server-docker` 映像

## 使用範例

### Task Master
- 初始化專案：使用 `initialize_project` 工具
- 解析 PRD：使用 `parse_prd` 工具
- 查看任務：使用 `get_tasks` 工具

### GitHub MCP
- 創建 Issue
- 提交 PR
- 管理分支

### Zapier MCP
- 觸發自動化流程
- 整合各種 SaaS 服務

### Docker MCP
- 在隔離環境中執行代碼
- 測試不同語言的腳本

### Vectorize MCP
- 搜尋知識庫
- 查詢 PDF 文件

### Brave Search MCP
- 搜尋網頁內容
- 查找技術文檔

## 疑難排解

1. 如果 MCP 工具無法載入，檢查：
   - API 密鑰是否正確設定
   - Cursor 是否已重啟
   - 網路連接是否正常

2. Docker MCP 問題：
   - 確保 Docker Desktop 正在運行
   - 檢查 Docker 命令是否可用：`docker --version`

3. 權限問題：
   - GitHub token 需要適當的權限範圍
   - Zapier API key 需要啟用 AI Actions 