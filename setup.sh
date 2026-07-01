#!/usr/bin/env bash
# 论文管理仓库初始化
set -euo pipefail

echo "============================================"
echo "  Papers — 初始化"
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

echo ""
echo "============================================"
echo "  完成！"
echo "============================================"
