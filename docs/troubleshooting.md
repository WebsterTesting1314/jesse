# Jesse 故障排除指南 🔧

本指南帮助您解决使用Jesse时可能遇到的常见问题。

## 目录

- [安装问题](#安装问题)
- [数据库问题](#数据库问题)
- [回测问题](#回测问题)
- [策略问题](#策略问题)
- [性能问题](#性能问题)
- [实盘交易问题](#实盘交易问题)
- [常见错误代码](#常见错误代码)

## 安装问题

### 问题: Python版本不兼容

**错误信息:**
```
ERROR: Python 3.9 is not supported. Jesse requires Python 3.10 or higher.
```

**解决方案:**
```bash
# 检查Python版本
python3 --version

# Ubuntu/Debian安装Python 3.10
sudo apt update
sudo apt install python3.10 python3.10-venv

# macOS使用Homebrew
brew install python@3.10

# 创建虚拟环境时指定Python版本
python3.10 -m venv venv
```

### 问题: TA-Lib安装失败

**错误信息:**
```
error: Microsoft Visual C++ 14.0 is required (Windows)
error: ta-lib/ta_libc.h: No such file or directory (Linux/macOS)
```

**解决方案:**

**Linux/macOS:**
```bash
# 安装系统依赖
sudo apt-get install build-essential wget

# 下载并编译TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install

# 安装Python包
pip install TA-Lib
```

**Windows:**
```bash
# 下载预编译的wheel文件
# 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
# 下载对应版本，例如: TA_Lib-0.4.24-cp310-cp310-win_amd64.whl

# 安装
pip install TA_Lib-0.4.24-cp310-cp310-win_amd64.whl
```

### 问题: 依赖包冲突

**错误信息:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**解决方案:**
```bash
# 清理并重新安装
pip cache purge
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt --force-reinstall

# 或使用conda
conda create -n jesse python=3.10
conda activate jesse
pip install -r requirements.txt
```

## 数据库问题

### 问题: PostgreSQL连接失败

**错误信息:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**解决方案:**

1. **检查PostgreSQL服务:**
```bash
# 检查服务状态
sudo systemctl status postgresql

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **检查配置文件:**
```bash
# 编辑pg_hba.conf
sudo nano /etc/postgresql/*/main/pg_hba.conf

# 确保有以下行
local   all   all                     md5
host    all   all   127.0.0.1/32      md5

# 重启PostgreSQL
sudo systemctl restart postgresql
```

3. **验证数据库设置:**
```bash
# 测试连接
psql -h localhost -U jesse_user -d jesse_db

# 重置密码
sudo -u postgres psql
ALTER USER jesse_user WITH PASSWORD 'new_password';
```

### 问题: Redis连接错误

**错误信息:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**解决方案:**
```bash
# 安装Redis
sudo apt-get install redis-server

# 启动Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 测试连接
redis-cli ping
# 应返回: PONG

# 检查配置
sudo nano /etc/redis/redis.conf
# 确保: bind 127.0.0.1
```

## 回测问题

### 问题: 没有历史数据

**错误信息:**
```
No candles found for BTC-USDT
```

**解决方案:**
```bash
# 导入历史数据
jesse import-candles Binance BTC-USDT 2023-01-01

# 查看可用数据
jesse candles BTC-USDT

# 批量导入多个交易对
jesse import-candles Binance BTC-USDT,ETH-USDT,BNB-USDT 2023-01-01
```

### 问题: 回测速度慢

**症状:** 回测一年数据需要超过10分钟

**解决方案:**

1. **优化策略代码:**
```python
# 使用缓存
@property
@cached
def slow_indicator(self):
    return ta.sma(self.candles, 200)

# 避免重复计算
def before(self):
    # 只计算一次
    self.indicators = {
        'sma': ta.sma(self.candles, 20),
        'rsi': ta.rsi(self.candles, 14)
    }
```

2. **使用更快的数据库:**
```bash
# 优化PostgreSQL
sudo -u postgres psql -d jesse_db
CREATE INDEX idx_candles_timestamp ON candles(timestamp);
CREATE INDEX idx_candles_symbol ON candles(symbol);
VACUUM ANALYZE;
```

3. **增加内存缓存:**
```python
# .env文件
REDIS_MAX_MEMORY=2gb
REDIS_MAX_MEMORY_POLICY=allkeys-lru
```

### 问题: 内存不足

**错误信息:**
```
MemoryError: Unable to allocate array
```

**解决方案:**
```bash
# 1. 减少数据加载量
jesse backtest 2023-01-01 2023-03-31  # 缩短时间范围

# 2. 优化策略内存使用
# 避免在策略中存储大量数据
self.history = []  # 不要这样做

# 3. 增加系统swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 策略问题

### 问题: 策略不触发交易

**症状:** 回测完成但没有任何交易

**调试步骤:**

1. **添加调试日志:**
```python
def should_long(self):
    signal = self.fast_ma > self.slow_ma
    self.log(f"Long signal: {signal}, Fast MA: {self.fast_ma}, Slow MA: {self.slow_ma}")
    return signal
```

2. **检查数据:**
```python
def before(self):
    if self.index < 100:  # 前100根K线
        print(f"Candle {self.index}: {self.time}, {self.close}")
```

3. **验证条件:**
```python
def should_long(self):
    # 确保有足够的历史数据
    if len(self.candles) < 50:
        return False
    
    # 添加更宽松的条件测试
    return True  # 临时总是返回True测试
```

### 问题: 订单被拒绝

**错误信息:**
```
Order rejected: Insufficient balance
```

**解决方案:**
```python
def go_long(self):
    # 检查余额
    max_position = self.balance * 0.95  # 留5%余额
    qty = utils.size_to_qty(max_position * 0.1, self.price)
    
    # 验证订单
    if qty * self.price > self.balance:
        self.log("余额不足，跳过交易")
        return
    
    # 确保满足最小订单要求
    min_qty = 0.001  # BTC最小订单
    if qty < min_qty:
        qty = min_qty
    
    self.buy = qty, self.price
```

### 问题: 指标计算错误

**错误信息:**
```
ValueError: Length of values does not match length of index
```

**解决方案:**
```python
def should_long(self):
    # 确保有足够数据
    required_candles = 200  # 最长指标周期
    if len(self.candles) < required_candles:
        return False
    
    # 安全计算指标
    try:
        sma = ta.sma(self.candles, 50)
        return sma > self.close
    except Exception as e:
        self.log(f"指标计算错误: {e}")
        return False
```

## 性能问题

### 问题: CPU使用率过高

**解决方案:**

1. **限制并行进程:**
```bash
# 设置环境变量
export JESSE_WORKERS=2  # 限制为2个进程

# 或在.env文件
WORKERS=2
```

2. **优化计算密集型代码:**
```python
# 使用NumPy向量化
# 不好的方式
result = []
for candle in self.candles:
    result.append(candle[2] * 2)

# 好的方式
result = self.candles[:, 2] * 2
```

### 问题: 数据库查询慢

**解决方案:**
```sql
-- 创建索引
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_orders_status ON orders(status);

-- 定期维护
VACUUM ANALYZE;
REINDEX DATABASE jesse_db;

-- 查看慢查询
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

## 实盘交易问题

### 问题: API密钥错误

**错误信息:**
```
Invalid API key/secret pair
```

**解决方案:**

1. **验证API权限:**
   - 确保API密钥有交易权限
   - 检查IP白名单设置
   - 验证API密钥没有过期

2. **正确配置.env:**
```bash
# .env文件
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_API_SECRET=your_actual_api_secret_here

# 注意：不要有多余的空格或引号
```

3. **测试连接:**
```python
# 测试脚本
from jesse.exchanges import Exchange

exchange = Exchange('Binance')
try:
    balance = exchange.get_balance()
    print(f"连接成功，余额: {balance}")
except Exception as e:
    print(f"连接失败: {e}")
```

### 问题: 订单延迟高

**症状:** 订单执行时间超过1秒

**解决方案:**

1. **使用更近的服务器:**
```bash
# 测试延迟
ping api.binance.com

# 考虑使用VPS
# AWS东京、新加坡等亚洲区域
```

2. **优化网络:**
```python
# 使用WebSocket而非REST API
# Jesse自动使用WebSocket进行实时数据
```

3. **减少API调用:**
```python
def before(self):
    # 缓存不常变动的数据
    if not hasattr(self, 'exchange_info'):
        self.exchange_info = self.get_exchange_info()
```

## 常见错误代码

### Jesse错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|---------|
| JESSE001 | 策略未找到 | 检查策略文件路径和类名 |
| JESSE002 | 数据库连接失败 | 检查PostgreSQL配置 |
| JESSE003 | 余额不足 | 减少仓位大小 |
| JESSE004 | 无效的时间框架 | 使用支持的时间框架 |
| JESSE005 | 指标计算错误 | 确保有足够的历史数据 |

### 交易所错误代码

| 错误代码 | 交易所 | 描述 | 解决方案 |
|---------|--------|------|---------|
| -1021 | Binance | 时间戳错误 | 同步系统时间 |
| -2010 | Binance | 余额不足 | 检查账户余额 |
| -1111 | Binance | 精度错误 | 调整价格/数量精度 |
| 10005 | OKX | 订单不存在 | 检查订单ID |
| 50004 | OKX | API冻结 | 等待解冻或联系客服 |

## 获取帮助

### 1. 启用详细日志

```bash
# .env文件
LOG_LEVEL=DEBUG
SAVE_LOGS=true

# 查看日志
tail -f storage/logs/jesse.log
```

### 2. 收集诊断信息

```bash
# 创建诊断报告
jesse diagnose > diagnosis.txt

# 包含的信息：
# - Jesse版本
# - Python版本
# - 依赖包版本
# - 系统信息
# - 配置检查
```

### 3. 社区支持

- 📝 [GitHub Issues](https://github.com/jesse-ai/jesse/issues) - 报告bug
- 💬 [Discord](https://discord.gg/jesse) - 实时帮助
- 📧 support@jesse.trade - 邮件支持

### 提问模板

```markdown
**问题描述:**
简要描述您遇到的问题

**错误信息:**
```
完整的错误信息
```

**重现步骤:**
1. 第一步
2. 第二步
3. ...

**环境信息:**
- Jesse版本: 
- Python版本:
- 操作系统:
- 相关配置:

**已尝试的解决方案:**
- 尝试1
- 尝试2
```

---

**记住：** 大多数问题都有解决方案。如果本指南没有解决您的问题，请不要犹豫寻求帮助！