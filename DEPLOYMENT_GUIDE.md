# Jesse HFT 部署指南

## 部署架構概覽

```
┌─────────────────────────────────────────────────────────────────┐
│                     Jesse HFT 部署架構                          │
├─────────────────────────────────────────────────────────────────┤
│  Load Balancer (HAProxy/Nginx)                                 │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ HFT Node 1  │  │ HFT Node 2  │  │ HFT Node 3  │              │
│  │             │  │             │  │             │              │
│  │ - Strategy  │  │ - Strategy  │  │ - Strategy  │              │
│  │ - Cache     │  │ - Cache     │  │ - Cache     │              │
│  │ - Events    │  │ - Events    │  │ - Events    │              │
│  │ - Risk Mgmt │  │ - Risk Mgmt │  │ - Risk Mgmt │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Redis       │  │ PostgreSQL  │  │ Monitoring  │              │
│  │ Cluster     │  │ Cluster     │  │ Stack       │              │
│  │             │  │             │  │             │              │
│  │ - Cache     │  │ - Orders    │  │ - Grafana   │              │
│  │ - PubSub    │  │ - Positions │  │ - Prometheus│              │
│  │ - Sessions  │  │ - Trades    │  │ - AlertMgr  │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 部署前檢查清單

### 硬體要求

#### 最低要求 (開發/測試)
- **CPU**: 4 核心 (支持 AVX2)
- **內存**: 8GB RAM
- **存儲**: 100GB SSD
- **網絡**: 1Gbps 連接

#### 推薦配置 (生產環境)
- **CPU**: 16+ 核心 (Intel Xeon/AMD EPYC)
- **內存**: 64GB+ ECC RAM
- **存儲**: 1TB+ NVMe SSD (RAID 1)
- **網絡**: 10Gbps+ 低延遲連接 (<5ms 到交易所)

#### 高性能配置 (企業級)
- **CPU**: 32+ 核心，3.5GHz+ 基頻
- **內存**: 128GB+ DDR4-3200 ECC
- **存儲**: 2TB+ NVMe SSD (RAID 10)
- **網絡**: 25Gbps+ 專線，<1ms 延遲
- **其他**: 專用交易服務器機房，接近交易所

### 軟體要求

```bash
# 操作系統
Ubuntu 22.04 LTS (推薦)
CentOS 8+ / RHEL 8+
Debian 11+

# Python 環境
Python 3.10.x 或 3.11.x
pip 23.0+
virtualenv

# 數據庫
PostgreSQL 14+ 
Redis 7.0+

# 監控工具
Prometheus 2.40+
Grafana 9.0+
AlertManager 0.25+

# 負載均衡
HAProxy 2.6+ / Nginx 1.22+

# 容器化 (可選)
Docker 24.0+
Docker Compose 2.20+
Kubernetes 1.28+ (企業級)
```

### 網絡要求

```bash
# 防火牆配置
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 8000/tcp    # Jesse API
sudo ufw allow 6379/tcp    # Redis (內部)
sudo ufw allow 5432/tcp    # PostgreSQL (內部)
sudo ufw allow 9090/tcp    # Prometheus (內部)
sudo ufw allow 3000/tcp    # Grafana (內部)

# 時間同步
sudo systemctl enable ntp
sudo systemctl start ntp

# 時區設置
sudo timedatectl set-timezone UTC
```

## 🏗️ 部署步驟

### Step 1: 環境準備

#### 1.1 創建部署用戶

```bash
# 創建 jesse 用戶
sudo useradd -m -s /bin/bash jesse
sudo usermod -aG sudo jesse

# 切換到 jesse 用戶
sudo su - jesse

# 生成 SSH 密鑰 (用於 Git)
ssh-keygen -t rsa -b 4096 -C "jesse@production"
```

#### 1.2 系統優化

```bash
# CPU 性能調優
echo 'performance' | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# 網絡調優
sudo tee -a /etc/sysctl.conf << EOF
# 網絡性能優化
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.core.rmem_default = 65536
net.core.wmem_default = 65536
net.ipv4.tcp_rmem = 4096 65536 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_congestion_control = bbr

# 文件描述符限制
fs.file-max = 2097152
fs.nr_open = 2097152

# 內存優化
vm.swappiness = 1
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5
EOF

sudo sysctl -p

# 用戶限制
sudo tee -a /etc/security/limits.conf << EOF
jesse soft nofile 1048576
jesse hard nofile 1048576
jesse soft nproc 65536
jesse hard nproc 65536
EOF
```

#### 1.3 安裝系統依賴

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝編譯工具和依賴
sudo apt install -y \
    build-essential \
    gcc-11 \
    g++-11 \
    cmake \
    git \
    curl \
    wget \
    htop \
    iotop \
    nethogs \
    tmux \
    screen \
    vim \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    postgresql-client-14 \
    redis-tools \
    nginx \
    certbot \
    python3-certbot-nginx

# 設置 Python 別名
echo "alias python=python3.10" >> ~/.bashrc
echo "alias pip=pip3" >> ~/.bashrc
source ~/.bashrc
```

### Step 2: 數據庫安裝

#### 2.1 PostgreSQL 安裝

```bash
# 安裝 PostgreSQL
sudo apt install -y postgresql-14 postgresql-client-14 postgresql-contrib-14

# 啟動服務
sudo systemctl enable postgresql
sudo systemctl start postgresql

# 創建數據庫和用戶
sudo -u postgres psql << EOF
CREATE USER jesse WITH PASSWORD 'your_secure_password';
CREATE DATABASE jesse OWNER jesse;
GRANT ALL PRIVILEGES ON DATABASE jesse TO jesse;
\q
EOF

# 配置 PostgreSQL
sudo tee -a /etc/postgresql/14/main/postgresql.conf << EOF
# 性能調優
shared_buffers = 2GB
effective_cache_size = 8GB
maintenance_work_mem = 512MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 64MB
min_wal_size = 1GB
max_wal_size = 4GB
EOF

# 重啟 PostgreSQL
sudo systemctl restart postgresql
```

#### 2.2 Redis 安裝

```bash
# 安裝 Redis
sudo apt install -y redis-server

# 配置 Redis
sudo tee /etc/redis/redis.conf << EOF
# 基本配置
bind 127.0.0.1
port 6379
timeout 300
tcp-keepalive 60

# 內存配置
maxmemory 4gb
maxmemory-policy allkeys-lru

# 持久化配置
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir /var/lib/redis

# 日誌配置
loglevel notice
logfile /var/log/redis/redis-server.log

# 性能優化
tcp-backlog 511
databases 16
EOF

# 啟動 Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 3: Jesse HFT 部署

#### 3.1 代碼部署

```bash
# 創建項目目錄
mkdir -p /home/jesse/trading
cd /home/jesse/trading

# 克隆代碼
git clone <your-jesse-hft-repo> jesse-hft
cd jesse-hft

# 創建虛擬環境
python3.10 -m venv venv
source venv/bin/activate

# 升級 pip
pip install --upgrade pip setuptools wheel

# 安裝依賴
cd core
pip install -r requirements.txt

# 安裝額外 HFT 依賴
pip install numba==0.58.1 \
            psutil==5.9.6 \
            asyncio-mqtt==0.13.0 \
            aioredis==2.0.1 \
            asyncpg==0.29.0 \
            uvloop==0.19.0 \
            orjson==3.9.10 \
            cython==3.0.6
```

#### 3.2 配置文件

```bash
# 創建配置目錄
mkdir -p /home/jesse/trading/config

# 生產環境配置
tee /home/jesse/trading/config/config.py << 'EOF'
import os
from pathlib import Path

# 基本配置
DEBUG = False
ENVIRONMENT = 'production'
SECRET_KEY = os.environ.get('JESSE_SECRET_KEY', 'your-very-secure-secret-key')

# 數據庫配置
DATABASES = {
    'default': {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 5432)),
        'username': os.environ.get('DB_USER', 'jesse'),
        'password': os.environ.get('DB_PASSWORD'),
        'name': os.environ.get('DB_NAME', 'jesse'),
        'pool_size': 20,
        'max_overflow': 0
    }
}

# Redis 配置
REDIS = {
    'host': os.environ.get('REDIS_HOST', 'localhost'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': int(os.environ.get('REDIS_DB', 0)),
    'password': os.environ.get('REDIS_PASSWORD'),
    'max_connections': 100
}

# HFT 優化配置
HFT_ENABLED = True
HFT_CACHE_TTL_MS = {
    'position': 50,
    'order': 20,
    'market_data': 1
}

HFT_PERFORMANCE_TARGETS = {
    'max_latency_us': 100,
    'min_throughput': 10000,
    'cache_hit_ratio': 0.95,
    'max_memory_mb': 8000
}

HFT_RISK_LIMITS = {
    'max_position_value': 1000000,
    'max_daily_loss': 50000,
    'max_drawdown': 0.15,
    'emergency_stop_triggers': 3
}

# 日誌配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            'format': '{"level": "%(levelname)s", "time": "%(asctime)s", "module": "%(module)s", "message": "%(message)s"}',
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/jesse/trading/logs/jesse.log',
            'maxBytes': 100*1024*1024,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/jesse/trading/logs/error.log',
            'maxBytes': 100*1024*1024,
            'backupCount': 5,
            'formatter': 'json',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        }
    },
    'root': {
        'handlers': ['file', 'error_file', 'console'],
        'level': 'INFO',
    }
}

# API 配置
API_CONFIG = {
    'host': '0.0.0.0',
    'port': 8000,
    'workers': 4,
    'max_requests': 10000,
    'max_requests_jitter': 1000,
    'keepalive': 2,
    'timeout': 30
}

# 監控配置
MONITORING = {
    'enabled': True,
    'prometheus_port': 9090,
    'metrics_interval': 1,
    'alert_webhook': os.environ.get('ALERT_WEBHOOK_URL')
}
EOF

# 創建環境變量文件
tee /home/jesse/trading/.env << 'EOF'
# 數據庫憑證
DB_PASSWORD=your_secure_db_password
REDIS_PASSWORD=your_secure_redis_password

# API 密鑰
JESSE_SECRET_KEY=your_very_secure_secret_key_minimum_32_characters_long

# 交易所 API 憑證 (加密存儲)
BINANCE_API_KEY=encrypted:your_encrypted_api_key
BINANCE_SECRET_KEY=encrypted:your_encrypted_secret_key

# 監控和警報
ALERT_WEBHOOK_URL=https://hooks.slack.com/your/webhook/url
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# 其他配置
LOG_LEVEL=INFO
MAX_WORKERS=4
ENVIRONMENT=production
EOF

# 設置權限
chmod 600 /home/jesse/trading/.env
```

#### 3.3 服務配置

```bash
# 創建 systemd 服務文件
sudo tee /etc/systemd/system/jesse-hft.service << 'EOF'
[Unit]
Description=Jesse HFT Trading System
After=network.target postgresql.service redis-server.service
Wants=postgresql.service redis-server.service

[Service]
Type=forking
User=jesse
Group=jesse
WorkingDirectory=/home/jesse/trading/jesse-hft/core
Environment=PATH=/home/jesse/trading/jesse-hft/venv/bin
EnvironmentFile=/home/jesse/trading/.env
ExecStartPre=/bin/sleep 10
ExecStart=/home/jesse/trading/jesse-hft/venv/bin/python -m jesse run --production
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

# 安全設置
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/home/jesse/trading
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes

# 資源限制
LimitNOFILE=1048576
LimitNPROC=65536
MemoryMax=8G
CPUQuota=80%

[Install]
WantedBy=multi-user.target
EOF

# 創建日誌目錄
mkdir -p /home/jesse/trading/logs
chown jesse:jesse /home/jesse/trading/logs

# 啟用服務
sudo systemctl daemon-reload
sudo systemctl enable jesse-hft.service
```

### Step 4: 監控系統部署

#### 4.1 Prometheus 安裝

```bash
# 下載 Prometheus
cd /tmp
wget https://github.com/prometheus/prometheus/releases/download/v2.40.7/prometheus-2.40.7.linux-amd64.tar.gz
tar xzf prometheus-2.40.7.linux-amd64.tar.gz

# 安裝 Prometheus
sudo mkdir -p /opt/prometheus
sudo cp prometheus-2.40.7.linux-amd64/* /opt/prometheus/
sudo chown -R jesse:jesse /opt/prometheus

# 配置 Prometheus
sudo mkdir -p /etc/prometheus
sudo tee /etc/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 1s
  evaluation_interval: 1s

rule_files:
  - "alert_rules.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

scrape_configs:
  - job_name: 'jesse-hft'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 1s
    metrics_path: /metrics

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:9121']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
EOF

# 創建告警規則
sudo tee /etc/prometheus/alert_rules.yml << 'EOF'
groups:
  - name: jesse-hft-alerts
    rules:
      - alert: HighLatency
        expr: jesse_latency_p95_microseconds > 1000
        for: 5s
        labels:
          severity: critical
        annotations:
          summary: "HFT system latency too high"
          description: "P95 latency is {{ $value }}μs, exceeding 1ms threshold"

      - alert: LowCacheHitRatio
        expr: jesse_cache_hit_ratio < 0.9
        for: 30s
        labels:
          severity: warning
        annotations:
          summary: "Cache hit ratio too low"
          description: "Cache hit ratio is {{ $value }}, below 90% threshold"

      - alert: HighErrorRate
        expr: jesse_error_rate > 0.01
        for: 10s
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }}, exceeding 1% threshold"

      - alert: SystemDown
        expr: up{job="jesse-hft"} == 0
        for: 5s
        labels:
          severity: critical
        annotations:
          summary: "Jesse HFT system is down"
          description: "Jesse HFT system has been down for more than 5 seconds"
EOF

# 創建 Prometheus 服務
sudo tee /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
After=network.target

[Service]
Type=simple
User=jesse
Group=jesse
ExecStart=/opt/prometheus/prometheus \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/home/jesse/trading/prometheus \
  --web.console.templates=/opt/prometheus/consoles \
  --web.console.libraries=/opt/prometheus/console_libraries \
  --web.listen-address=0.0.0.0:9090 \
  --web.enable-lifecycle \
  --storage.tsdb.retention.time=30d
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 創建數據目錄
mkdir -p /home/jesse/trading/prometheus
sudo systemctl daemon-reload
sudo systemctl enable prometheus
```

#### 4.2 Grafana 安裝

```bash
# 添加 Grafana APT 倉庫
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
echo "deb https://packages.grafana.com/oss/deb stable main" | sudo tee -a /etc/apt/sources.list.d/grafana.list

# 安裝 Grafana
sudo apt update
sudo apt install -y grafana

# 配置 Grafana
sudo tee /etc/grafana/grafana.ini << 'EOF'
[server]
http_port = 3000
domain = localhost

[database]
type = postgres
host = localhost:5432
name = grafana
user = jesse
password = your_secure_db_password

[security]
admin_user = admin
admin_password = your_grafana_password
secret_key = your_grafana_secret_key

[users]
allow_sign_up = false

[auth.anonymous]
enabled = false

[dashboards]
default_home_dashboard_path = /var/lib/grafana/dashboards/jesse-hft-overview.json
EOF

# 創建 Grafana 數據庫
sudo -u postgres psql << EOF
CREATE DATABASE grafana OWNER jesse;
\q
EOF

# 啟用 Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server
```

### Step 5: 負載均衡和反向代理

#### 5.1 Nginx 配置

```bash
# 移除默認站點
sudo rm /etc/nginx/sites-enabled/default

# 創建 Jesse HFT 站點配置
sudo tee /etc/nginx/sites-available/jesse-hft << 'EOF'
upstream jesse_backend {
    least_conn;
    server 127.0.0.1:8000 max_fails=3 fail_timeout=30s;
    server 127.0.0.1:8001 max_fails=3 fail_timeout=30s backup;
}

# API 端點
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 安全頭
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";
    
    # 壓縮
    gzip on;
    gzip_types text/plain application/json application/javascript text/css;
    
    # API 代理
    location /api/ {
        proxy_pass http://jesse_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超時設置
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 30s;
        
        # 緩衝設置
        proxy_buffering off;
        proxy_request_buffering off;
    }
    
    # 靜態文件
    location /static/ {
        alias /home/jesse/trading/jesse-hft/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 健康檢查
    location /health {
        access_log off;
        proxy_pass http://jesse_backend/health;
    }
    
    # 限制訪問
    location /admin/ {
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        allow 192.168.0.0/16;
        deny all;
        
        proxy_pass http://jesse_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# 監控端點 (內部訪問)
server {
    listen 127.0.0.1:8080;
    server_name localhost;
    
    # Grafana 代理
    location /grafana/ {
        proxy_pass http://127.0.0.1:3000/;
        proxy_set_header Host $host;
    }
    
    # Prometheus 代理
    location /prometheus/ {
        proxy_pass http://127.0.0.1:9090/;
        proxy_set_header Host $host;
    }
    
    # 系統狀態
    location /status {
        stub_status on;
        access_log off;
    }
}
EOF

# 啟用站點
sudo ln -s /etc/nginx/sites-available/jesse-hft /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx
```

#### 5.2 SSL 證書

```bash
# 獲取 Let's Encrypt 證書
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 設置自動續期
sudo crontab -e
# 添加以下行：
# 0 12 * * * /usr/bin/certbot renew --quiet
```

### Step 6: 安全配置

#### 6.1 防火牆設置

```bash
# 配置 UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing

# 允許必要端口
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS

# 限制 SSH 訪問
sudo ufw limit 22/tcp

# 啟用防火牆
sudo ufw --force enable
```

#### 6.2 SSH 安全配置

```bash
# 配置 SSH
sudo tee -a /etc/ssh/sshd_config << 'EOF'
# 安全設置
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
MaxStartups 3:30:10
ClientAliveInterval 300
ClientAliveCountMax 2

# 限制用戶
AllowUsers jesse

# 禁用不安全功能
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
EOF

sudo systemctl restart ssh
```

#### 6.3 文件權限

```bash
# 設置嚴格權限
sudo chmod 750 /home/jesse
sudo chmod 755 /home/jesse/trading
sudo chmod 750 /home/jesse/trading/jesse-hft
sudo chmod 600 /home/jesse/trading/.env
sudo chmod 600 /home/jesse/trading/config/config.py
sudo chmod 755 /home/jesse/trading/logs

# 設置 SELinux (如適用)
# sudo setsebool -P httpd_can_network_connect on
```

### Step 7: 部署驗證

#### 7.1 服務啟動

```bash
# 啟動所有服務
sudo systemctl start postgresql redis-server prometheus grafana-server nginx

# 等待數據庫準備
sleep 10

# 啟動 Jesse HFT
sudo systemctl start jesse-hft

# 檢查服務狀態
sudo systemctl status jesse-hft prometheus grafana-server nginx
```

#### 7.2 系統驗證

```bash
# 創建驗證腳本
tee /home/jesse/trading/verify_deployment.py << 'EOF'
#!/usr/bin/env python3
"""
Jesse HFT 部署驗證腳本
"""
import asyncio
import aiohttp
import aioredis
import asyncpg
import time
import json
from urllib.parse import urljoin

class DeploymentVerifier:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.results = {}
    
    async def verify_database(self):
        """驗證數據庫連接"""
        try:
            conn = await asyncpg.connect(
                host='localhost',
                port=5432,
                user='jesse',
                password='your_secure_db_password',
                database='jesse'
            )
            
            # 測試查詢
            result = await conn.fetchval('SELECT 1')
            await conn.close()
            
            self.results['database'] = {
                'status': 'OK' if result == 1 else 'FAIL',
                'message': 'Database connection successful'
            }
        except Exception as e:
            self.results['database'] = {
                'status': 'FAIL',
                'message': f'Database connection failed: {str(e)}'
            }
    
    async def verify_redis(self):
        """驗證 Redis 連接"""
        try:
            redis = aioredis.from_url("redis://localhost")
            await redis.ping()
            await redis.close()
            
            self.results['redis'] = {
                'status': 'OK',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            self.results['redis'] = {
                'status': 'FAIL',
                'message': f'Redis connection failed: {str(e)}'
            }
    
    async def verify_api(self):
        """驗證 API 端點"""
        try:
            async with aiohttp.ClientSession() as session:
                # 健康檢查
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.results['api_health'] = {
                            'status': 'OK',
                            'message': 'API health check passed',
                            'data': data
                        }
                    else:
                        self.results['api_health'] = {
                            'status': 'FAIL',
                            'message': f'API health check failed: HTTP {resp.status}'
                        }
                
                # 系統狀態
                async with session.get(f"{self.base_url}/api/system/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        self.results['api_status'] = {
                            'status': 'OK',
                            'message': 'System status API working',
                            'data': data
                        }
                    else:
                        self.results['api_status'] = {
                            'status': 'WARN',
                            'message': f'System status API error: HTTP {resp.status}'
                        }
        
        except Exception as e:
            self.results['api_health'] = {
                'status': 'FAIL',
                'message': f'API verification failed: {str(e)}'
            }
    
    async def verify_hft_components(self):
        """驗證 HFT 組件"""
        try:
            # 導入 HFT 組件
            import sys
            sys.path.append('/home/jesse/trading/jesse-hft/core')
            
            from jesse.indicators.hft_optimized import hft_sma
            from jesse.services.hft_cache import hft_cache_manager
            from jesse.services.hft_performance_monitor import hft_performance_monitor
            
            import numpy as np
            
            # 測試指標計算
            prices = np.random.random(1000)
            start_time = time.time_ns()
            result = hft_sma(prices, 20)
            end_time = time.time_ns()
            
            latency_us = (end_time - start_time) / 1000
            
            self.results['hft_indicators'] = {
                'status': 'OK' if latency_us < 1000 else 'WARN',
                'message': f'HFT indicators working, latency: {latency_us:.1f}μs',
                'latency_us': latency_us
            }
            
            # 測試緩存系統
            cache_stats = hft_cache_manager.get_all_stats()
            self.results['hft_cache'] = {
                'status': 'OK',
                'message': 'HFT cache system working',
                'stats': cache_stats
            }
            
            # 測試性能監控
            summary = hft_performance_monitor.get_performance_summary()
            self.results['hft_monitoring'] = {
                'status': 'OK',
                'message': 'HFT performance monitoring working',
                'summary': summary
            }
            
        except Exception as e:
            self.results['hft_components'] = {
                'status': 'FAIL',
                'message': f'HFT components verification failed: {str(e)}'
            }
    
    async def verify_monitoring(self):
        """驗證監控系統"""
        try:
            async with aiohttp.ClientSession() as session:
                # Prometheus
                async with session.get("http://localhost:9090/-/healthy") as resp:
                    self.results['prometheus'] = {
                        'status': 'OK' if resp.status == 200 else 'FAIL',
                        'message': f'Prometheus health: HTTP {resp.status}'
                    }
                
                # Grafana
                async with session.get("http://localhost:3000/api/health") as resp:
                    self.results['grafana'] = {
                        'status': 'OK' if resp.status == 200 else 'FAIL',
                        'message': f'Grafana health: HTTP {resp.status}'
                    }
        
        except Exception as e:
            self.results['monitoring'] = {
                'status': 'FAIL',
                'message': f'Monitoring verification failed: {str(e)}'
            }
    
    async def run_all_verifications(self):
        """運行所有驗證"""
        print("🔍 開始部署驗證...")
        
        await self.verify_database()
        await self.verify_redis()
        await self.verify_api()
        await self.verify_hft_components()
        await self.verify_monitoring()
        
        # 生成報告
        self.generate_report()
    
    def generate_report(self):
        """生成驗證報告"""
        print("\n" + "="*80)
        print("📊 Jesse HFT 部署驗證報告")
        print("="*80)
        
        total_checks = len(self.results)
        passed_checks = sum(1 for r in self.results.values() if r['status'] == 'OK')
        
        for component, result in self.results.items():
            status_icon = {
                'OK': '✅',
                'WARN': '⚠️',
                'FAIL': '❌'
            }.get(result['status'], '❓')
            
            print(f"{status_icon} {component.upper()}: {result['message']}")
            
            if 'data' in result and result['data']:
                print(f"   數據: {json.dumps(result['data'], indent=6)}")
        
        print("\n" + "-"*80)
        print(f"📈 總體結果: {passed_checks}/{total_checks} 檢查通過")
        
        if passed_checks == total_checks:
            print("🎉 所有檢查通過！Jesse HFT 系統部署成功。")
            return True
        else:
            print("⚠️  部分檢查失敗，請檢查上述錯誤訊息。")
            return False

async def main():
    verifier = DeploymentVerifier()
    success = await verifier.run_all_verifications()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
EOF

# 運行驗證
cd /home/jesse/trading
source jesse-hft/venv/bin/activate
python verify_deployment.py
```

#### 7.3 性能測試

```bash
# 運行性能基準測試
cd /home/jesse/trading/jesse-hft/core
python -m jesse.services.hft_benchmark

# 檢查系統資源
htop
iotop
nethogs

# 檢查服務日誌
sudo journalctl -u jesse-hft -f
tail -f /home/jesse/trading/logs/jesse.log
```

## 🔄 部署後維護

### 日常監控

```bash
# 創建監控腳本
tee /home/jesse/trading/monitor.sh << 'EOF'
#!/bin/bash
# Jesse HFT 系統監控腳本

echo "Jesse HFT 系統狀態檢查 - $(date)"
echo "=================================="

# 檢查服務狀態
echo "服務狀態:"
systemctl is-active jesse-hft && echo "✅ Jesse HFT: 運行中" || echo "❌ Jesse HFT: 停止"
systemctl is-active postgresql && echo "✅ PostgreSQL: 運行中" || echo "❌ PostgreSQL: 停止"
systemctl is-active redis-server && echo "✅ Redis: 運行中" || echo "❌ Redis: 停止"
systemctl is-active prometheus && echo "✅ Prometheus: 運行中" || echo "❌ Prometheus: 停止"
systemctl is-active grafana-server && echo "✅ Grafana: 運行中" || echo "❌ Grafana: 停止"
systemctl is-active nginx && echo "✅ Nginx: 運行中" || echo "❌ Nginx: 停止"

echo -e "\n系統資源:"
echo "CPU 使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "內存使用率: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "磁盤使用率: $(df -h / | awk 'NR==2{print $5}')"

echo -e "\n網絡連接:"
echo "活躍連接數: $(netstat -an | grep ESTABLISHED | wc -l)"

echo -e "\n最近錯誤 (最後10行):"
tail -10 /home/jesse/trading/logs/error.log 2>/dev/null || echo "無錯誤日誌"

echo -e "\n=================================="
EOF

chmod +x /home/jesse/trading/monitor.sh

# 設置定時監控
crontab -e
# 添加: */5 * * * * /home/jesse/trading/monitor.sh >> /home/jesse/trading/logs/monitor.log 2>&1
```

### 備份策略

```bash
# 創建備份腳本
tee /home/jesse/trading/backup.sh << 'EOF'
#!/bin/bash
# Jesse HFT 系統備份腳本

BACKUP_DIR="/home/jesse/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${DATE}"

mkdir -p "${BACKUP_PATH}"

echo "開始備份 Jesse HFT 系統 - $(date)"

# 備份數據庫
echo "備份 PostgreSQL..."
pg_dump -h localhost -U jesse jesse > "${BACKUP_PATH}/database.sql"

# 備份 Redis
echo "備份 Redis..."
redis-cli --rdb "${BACKUP_PATH}/redis_dump.rdb"

# 備份配置文件
echo "備份配置文件..."
cp -r /home/jesse/trading/config "${BACKUP_PATH}/"
cp /home/jesse/trading/.env "${BACKUP_PATH}/"

# 備份日誌
echo "備份日誌文件..."
cp -r /home/jesse/trading/logs "${BACKUP_PATH}/"

# 壓縮備份
echo "壓縮備份文件..."
cd "${BACKUP_DIR}"
tar -czf "${DATE}.tar.gz" "${DATE}"
rm -rf "${DATE}"

# 清理舊備份 (保留30天)
find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +30 -delete

echo "備份完成: ${BACKUP_DIR}/${DATE}.tar.gz"
EOF

chmod +x /home/jesse/trading/backup.sh

# 設置每日備份
crontab -e
# 添加: 0 2 * * * /home/jesse/trading/backup.sh >> /home/jesse/trading/logs/backup.log 2>&1
```

### 日誌輪轉

```bash
# 配置 logrotate
sudo tee /etc/logrotate.d/jesse-hft << 'EOF'
/home/jesse/trading/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 jesse jesse
    postrotate
        /bin/kill -HUP $(cat /var/run/jesse-hft.pid 2>/dev/null) 2>/dev/null || true
    endscript
}
EOF
```

## 🔧 故障排除

### 常見問題

1. **服務啟動失敗**
```bash
# 檢查詳細錯誤
sudo journalctl -u jesse-hft -n 50

# 檢查端口占用
sudo netstat -tlnp | grep :8000

# 檢查權限
ls -la /home/jesse/trading/
```

2. **數據庫連接問題**
```bash
# 測試數據庫連接
psql -h localhost -U jesse -d jesse

# 檢查 PostgreSQL 狀態
sudo systemctl status postgresql
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

3. **Redis 連接問題**
```bash
# 測試 Redis 連接
redis-cli ping

# 檢查 Redis 狀態
sudo systemctl status redis-server
sudo tail -f /var/log/redis/redis-server.log
```

4. **性能問題**
```bash
# 檢查系統負載
htop
iotop -a

# 檢查網絡延遲
ping exchange-api-endpoint.com

# 運行性能測試
python /home/jesse/trading/jesse-hft/core/jesse/services/hft_benchmark.py
```

### 緊急恢復

```bash
# 創建緊急恢復腳本
tee /home/jesse/trading/emergency_recovery.sh << 'EOF'
#!/bin/bash
# Jesse HFT 緊急恢復腳本

echo "🚨 Jesse HFT 緊急恢復程序啟動"

# 停止所有服務
echo "停止服務..."
sudo systemctl stop jesse-hft nginx

# 檢查並修復文件權限
echo "修復權限..."
sudo chown -R jesse:jesse /home/jesse/trading/
sudo chmod 600 /home/jesse/trading/.env

# 清理緩存和臨時文件
echo "清理緩存..."
rm -rf /home/jesse/trading/jesse-hft/core/jesse/__pycache__/
redis-cli FLUSHALL

# 重新啟動基礎服務
echo "重啟基礎服務..."
sudo systemctl restart postgresql redis-server

# 等待服務準備
sleep 10

# 重新啟動 Jesse HFT
echo "重啟 Jesse HFT..."
sudo systemctl start jesse-hft

# 重新啟動 Nginx
sudo systemctl start nginx

# 檢查狀態
echo "檢查服務狀態..."
systemctl is-active jesse-hft && echo "✅ Jesse HFT 已恢復" || echo "❌ Jesse HFT 恢復失敗"

echo "🎯 緊急恢復程序完成"
EOF

chmod +x /home/jesse/trading/emergency_recovery.sh
```

---

此部署指南提供了從開發到生產環境的完整部署流程。按照步驟執行可確保 Jesse HFT 系統穩定、安全、高性能運行。