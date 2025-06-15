# Zen MCP Server 診斷腳本
Write-Host "=== Zen MCP Server 診斷工具 ===" -ForegroundColor Cyan

# 1. 檢查 Docker Desktop
Write-Host "`n[1] 檢查 Docker Desktop..." -ForegroundColor Yellow
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if ($dockerProcess) {
    Write-Host "✓ Docker Desktop 正在運行" -ForegroundColor Green
} else {
    Write-Host "✗ Docker Desktop 未運行" -ForegroundColor Red
    Write-Host "  請啟動 Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# 2. 檢查 Docker 服務
Write-Host "`n[2] 檢查 Docker 服務..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
    if ($dockerVersion) {
        Write-Host "✓ Docker 版本: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "✗ Docker 命令無法執行" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "✗ Docker 未正確安裝" -ForegroundColor Red
    exit 1
}

# 3. 檢查容器狀態
Write-Host "`n[3] 檢查 zen-mcp-server 容器..." -ForegroundColor Yellow
$container = docker ps -a --filter "name=zen-mcp-server" --format "table {{.Names}}\t{{.Status}}" | Select-String "zen-mcp-server"
if ($container) {
    Write-Host "✓ 容器存在: $container" -ForegroundColor Green
    
    # 檢查是否運行中
    $running = docker ps --filter "name=zen-mcp-server" --format "{{.Names}}" | Select-String "zen-mcp-server"
    if (!$running) {
        Write-Host "  容器未運行，嘗試啟動..." -ForegroundColor Yellow
        docker start zen-mcp-server
    }
} else {
    Write-Host "✗ 容器不存在" -ForegroundColor Red
    Write-Host "  需要先構建並運行容器" -ForegroundColor Yellow
    
    # 檢查 docker-compose 文件
    if (Test-Path "zen-mcp-server\docker-compose.yml") {
        Write-Host "`n  找到 docker-compose.yml，嘗試啟動..." -ForegroundColor Cyan
        Set-Location zen-mcp-server
        docker-compose up -d
        Set-Location ..
    }
}

# 4. 測試服務
Write-Host "`n[4] 測試服務健康狀態..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✓ 服務正常運行" -ForegroundColor Green
        $health = $response.Content | ConvertFrom-Json
        Write-Host "  狀態: $($health.status)" -ForegroundColor Green
        Write-Host "  啟用的模型數: $($health.enabled_models)" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ 服務無法訪問" -ForegroundColor Red
    Write-Host "  錯誤: $_" -ForegroundColor Red
}

# 5. 檢查 API 密鑰
Write-Host "`n[5] 檢查 API 密鑰配置..." -ForegroundColor Yellow
if (Test-Path "zen-mcp-server\.env") {
    Write-Host "✓ .env 文件存在" -ForegroundColor Green
    
    # 檢查密鑰是否配置
    $envContent = Get-Content "zen-mcp-server\.env"
    $hasKeys = $false
    @("OPENAI_API_KEY", "GEMINI_API_KEY", "CLAUDE_API_KEY") | ForEach-Object {
        if ($envContent -match "$_=.+") {
            Write-Host "  ✓ $_ 已配置" -ForegroundColor Green
            $hasKeys = $true
        }
    }
    
    if (!$hasKeys) {
        Write-Host "  ⚠ 警告：沒有配置任何 API 密鑰" -ForegroundColor Yellow
    }
} else {
    Write-Host "✗ .env 文件不存在" -ForegroundColor Red
    Write-Host "  請在 zen-mcp-server 目錄創建 .env 文件" -ForegroundColor Yellow
}

# 6. 提供修復建議
Write-Host "`n=== 修復建議 ===" -ForegroundColor Cyan
Write-Host "1. 確保 Docker Desktop 已啟動並啟用 WSL 2 集成" -ForegroundColor White
Write-Host "2. 在 zen-mcp-server 目錄運行: docker-compose up -d" -ForegroundColor White
Write-Host "3. 重啟 Cursor 以載入 MCP 配置" -ForegroundColor White
Write-Host "4. 檢查 Cursor 的開發者工具 (Ctrl+Shift+I) 查看錯誤信息" -ForegroundColor White 