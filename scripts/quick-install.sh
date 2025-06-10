#!/bin/bash

# Jesse Quick Installation Script
# This script automates the installation of Jesse trading framework

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}➜ $1${NC}"
}

check_command() {
    if command -v $1 &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# Header
echo "======================================"
echo "   Jesse Quick Installation Script    "
echo "======================================"
echo ""

# Check operating system
print_info "Checking operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DISTRO=$(lsb_release -si 2>/dev/null || echo "Unknown")
    print_success "Detected Linux ($DISTRO)"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_success "Detected macOS"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi

# Check Python version
print_info "Checking Python version..."
if check_command python3; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.10+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 not found"
    exit 1
fi

# Install system dependencies
print_info "Installing system dependencies..."
if [ "$OS" = "linux" ]; then
    # Update package list
    sudo apt-get update -qq
    
    # Install dependencies
    sudo apt-get install -y \
        postgresql postgresql-contrib \
        redis-server \
        build-essential \
        wget \
        git \
        python3-dev \
        python3-venv \
        libpq-dev
    
    print_success "System dependencies installed"
elif [ "$OS" = "macos" ]; then
    # Check if Homebrew is installed
    if ! check_command brew; then
        print_error "Homebrew not found. Please install from https://brew.sh"
        exit 1
    fi
    
    # Install dependencies
    brew install postgresql redis wget
    brew services start postgresql
    brew services start redis
    
    print_success "System dependencies installed"
fi

# Install TA-Lib
print_info "Installing TA-Lib..."
if [ ! -f "/usr/local/lib/libta_lib.a" ] && [ ! -f "/usr/lib/libta_lib.a" ]; then
    cd /tmp
    wget -q http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
    tar -xzf ta-lib-0.4.0-src.tar.gz
    cd ta-lib/
    ./configure --prefix=/usr/local
    make -j$(nproc)
    sudo make install
    cd ~
    print_success "TA-Lib installed"
else
    print_success "TA-Lib already installed"
fi

# Setup PostgreSQL
print_info "Setting up PostgreSQL..."
if [ "$OS" = "linux" ]; then
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# Check if database exists
DB_EXISTS=$(sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='jesse_db'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" != "1" ]; then
    print_info "Creating database and user..."
    sudo -u postgres psql <<EOF
CREATE USER jesse_user WITH PASSWORD 'jessepwd123';
CREATE DATABASE jesse_db;
GRANT ALL PRIVILEGES ON DATABASE jesse_db TO jesse_user;
EOF
    print_success "Database created"
else
    print_success "Database already exists"
fi

# Setup Redis
print_info "Starting Redis..."
if [ "$OS" = "linux" ]; then
    sudo systemctl start redis-server
    sudo systemctl enable redis-server
fi

# Test Redis connection
if redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is running"
else
    print_error "Redis is not running"
    exit 1
fi

# Create virtual environment
print_info "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
print_success "Pip upgraded"

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install Cython numpy > /dev/null 2>&1
print_success "Cython and numpy installed"

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    print_success "Requirements installed"
fi

# Install Jesse
print_info "Installing Jesse..."
pip install -e . > /dev/null 2>&1
print_success "Jesse installed"

# Create .env file if not exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_info "Copying .env.example to .env..."
        cp .env.example .env
        print_success ".env file created from .env.example"
    else
        print_error ".env.example not found. Please create one or see documentation."
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# Create necessary directories
print_info "Creating directories..."
mkdir -p strategies storage/logs storage/charts storage/genetics storage/temp
print_success "Directories created"

# Final checks
print_info "Running final checks..."

# Check if Jesse is installed
if python -c "import jesse" 2>/dev/null; then
    JESSE_VERSION=$(python -c "import jesse; print(jesse.__version__)" 2>/dev/null || echo "Unknown")
    print_success "Jesse $JESSE_VERSION installed successfully"
else
    print_error "Jesse installation failed"
    exit 1
fi

# Success message
echo ""
echo "======================================"
echo -e "${GREEN}✓ Installation completed successfully!${NC}"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Start Jesse: jesse run"
echo "3. Open browser: http://localhost:9000"
echo "4. Default password: JesseTrader2025"
echo ""
echo "For help, visit: https://docs.jesse.trade"
echo "Join Discord: https://discord.gg/jesse"
echo ""
echo "Happy Trading! 🚀"