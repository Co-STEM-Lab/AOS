#!/usr/bin/env bash
# 论文管理仓库初始化 + 网站构建
set -euo pipefail

echo "============================================"
echo "  AOS — 初始化与构建"
echo "============================================"

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 需要 Python 3.10+，请先安装"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
python3 -m pip install -r requirements.txt -q
echo "   ✅ 完成"

# 构建网站
echo ""
echo "🌐 构建学术网站..."
python3 website/build.py
echo "   ✅ 完成"

echo ""
echo "============================================"
echo "  完成！预览命令："
echo "  cd website/public && python3 -m http.server 8000"
echo "============================================"
