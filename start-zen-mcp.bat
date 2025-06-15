@echo off
echo === 啟動 Zen MCP Server ===
echo.

REM 檢查 Docker 是否運行
docker version >nul 2>&1
if errorlevel 1 (
    echo [錯誤] Docker 未運行！請先啟動 Docker Desktop
    pause
    exit /b 1
)

REM 進入目錄
cd zen-mcp-server

REM 檢查 .env 文件
if not exist .env (
    echo [警告] .env 文件不存在！
    echo 正在創建範例 .env 文件...
    (
        echo # 至少需要配置一個 API Key
        echo OPENAI_API_KEY=your_key_here
        echo GEMINI_API_KEY=your_key_here
        echo CLAUDE_API_KEY=your_key_here
        echo.
        echo SERVER_HOST=0.0.0.0
        echo SERVER_PORT=8000
    ) > .env
    echo.
    echo 請編輯 zen-mcp-server\.env 文件，添加您的 API 密鑰
    pause
)

REM 啟動容器
echo.
echo 正在啟動容器...
docker-compose up -d

REM 等待服務啟動
echo.
echo 等待服務啟動...
timeout /t 5 /nobreak >nul

REM 測試服務
echo.
echo 測試服務狀態...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo [警告] 服務可能尚未完全啟動
    echo 請稍後再試或檢查日誌: docker logs zen-mcp-server
) else (
    echo [成功] Zen MCP Server 已啟動！
    echo.
    echo 服務地址: http://localhost:8000
    echo 查看日誌: docker logs -f zen-mcp-server
)

cd ..
echo.
pause 