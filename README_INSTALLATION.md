# Jesse Trading Bot - 源码安装与开发指南

## 🚀 快速概览

Jesse是一个高级的加密货币交易机器人框架，使用Python编写。本指南提供了经过实践验证的源码安装步骤，让您能够快速开始二次开发。

## 📋 系统要求

- **操作系统**: Ubuntu 20.04+ / Debian 11+ / macOS / Windows WSL2
- **Python**: 3.10 或更高版本
- **内存**: 至少 4GB RAM
- **存储**: 至少 10GB 可用空间

## 🛠️ 完整安装步骤

### 1. 安装系统依赖

```bash
# 更新系统包
sudo apt update && sudo apt upgrade -y

# 安装必要的系统依赖
sudo apt install -y postgresql postgresql-contrib redis-server build-essential wget git python3-dev python3-venv

# 安装TA-Lib (技术分析库)
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
cd ~
```

### 2. 克隆Jesse源码

```bash
# 克隆官方仓库
git clone https://github.com/jesse-ai/jesse.git
cd jesse
```

### 3. 设置Python虚拟环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/macOS
# 或者在Windows上:
# venv\Scripts\activate

# 升级pip
pip install --upgrade pip
```

### 4. 安装Python依赖

```bash
# 首先安装Cython和numpy（其他包的依赖）
pip install Cython numpy

# 安装所有依赖
pip install -r requirements.txt

# 以开发模式安装Jesse
pip install -e .
```

### 5. 配置PostgreSQL数据库

```bash
# 启动PostgreSQL服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库用户和数据库
sudo -u postgres psql << EOF
CREATE USER jesse_user WITH PASSWORD 'jessepwd123';
CREATE DATABASE jesse_db;
GRANT ALL PRIVILEGES ON DATABASE jesse_db TO jesse_user;
\q
EOF
```

### 6. 配置Redis

```bash
# 启动Redis服务
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 测试Redis连接
redis-cli ping
# 应该返回: PONG
```

### 7. 创建环境配置文件

在项目根目录复制 `.env.example` 为 `.env`：

```bash
cp .env.example .env
```

### 8. 验证安装

```bash
# 检查Jesse是否正确安装
python -c "import jesse; print(f'Jesse version: {jesse.__version__}')"

# 运行测试
pytest tests/

# 启动Jesse仪表板
jesse run
```

## 🔧 常见问题解决

### 1. TA-Lib安装失败

如果TA-Lib编译失败，尝试：

```bash
# 安装额外的依赖
sudo apt-get install -y libatlas-base-dev gfortran

# 或使用预编译版本
pip install TA-Lib --no-cache-dir
```

### 2. PostgreSQL连接错误

```bash
# 检查PostgreSQL服务状态
sudo systemctl status postgresql

# 检查认证方法
sudo nano /etc/postgresql/*/main/pg_hba.conf
# 确保有以下行：
# local   all   jesse_user   md5
# host    all   jesse_user   127.0.0.1/32   md5

# 重启PostgreSQL
sudo systemctl restart postgresql
```

### 3. 虚拟环境激活问题

```bash
# 如果虚拟环境无法激活，重新创建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
```

## 📁 项目结构

```
jesse/
├── jesse/              # 核心源码
│   ├── indicators/     # 技术指标
│   ├── strategies/     # 策略基类
│   ├── modes/         # 运行模式(回测/实盘)
│   └── services/      # 核心服务
├── tests/             # 测试套件
├── strategies/        # 您的自定义策略目录
├── storage/           # 数据存储
├── .env              # 环境配置
└── requirements.txt   # Python依赖
```

## 🚀 开始开发

### 创建您的第一个策略

1. 在项目根目录创建 `strategies` 文件夹：

```bash
mkdir -p strategies
```

2. 创建一个简单的策略文件 `strategies/MyFirstStrategy.py`：

```python
from jesse.strategies import Strategy
import jesse.indicators as ta

class MyFirstStrategy(Strategy):
    def should_long(self) -> bool:
        # 当快速MA穿越慢速MA时做多
        return ta.sma(self.candles, 10) > ta.sma(self.candles, 30)

    def should_short(self) -> bool:
        # 当快速MA低于慢速MA时做空
        return ta.sma(self.candles, 10) < ta.sma(self.candles, 30)

    def go_long(self):
        qty = self.capital / self.price
        self.buy = qty, self.price

    def go_short(self):
        qty = self.capital / self.price
        self.sell = qty, self.price

    def should_cancel_entry(self):
        return False

    def on_open_position(self, order):
        # 设置止损和止盈
        self.stop_loss = self.position.qty, self.price * 0.95
        self.take_profit = self.position.qty, self.price * 1.05
```

### 运行回测

```bash
# 使用Jesse CLI运行回测
jesse backtest 2023-01-01 2023-12-31 --debug
```

## 🔍 开发建议

1. **使用版本控制**: 始终使用Git跟踪您的策略更改
2. **编写测试**: 为您的策略编写单元测试
3. **优化参数**: 使用Jesse的优化功能找到最佳参数
4. **风险管理**: 始终实现适当的止损和仓位管理
5. **日志记录**: 使用Jesse的日志系统调试策略

## 📚 有用的资源

- [官方文档](https://docs.jesse.trade)
- [Discord社区](https://jesse.trade/discord)
- [YouTube教程](https://jesse.trade/youtube)
- [策略示例](https://github.com/jesse-ai/example-strategies)

## 🤝 贡献指南

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

## ⚠️ 免责声明

本软件仅供教育目的使用。请自行承担使用风险。作者和所有关联方对您的交易结果不承担任何责任。不要冒险投入您无法承受损失的资金。

---

**Happy Trading! 🚀**