#!/usr/bin/env bash
# AOS 一键初始化 —— 从克隆到构建网站
set -euo pipefail

echo "============================================"
echo "  AOS — 初始化"
echo "============================================"
echo ""

# 检查 Python
if ! command -v python3 &>/dev/null; then
    echo "❌ 需要 Python 3.10+，请先安装"
    exit 1
fi

# 安装依赖
echo "📦 安装依赖..."
pip3 install -r requirements.txt -q
echo "   ✅ 完成"

# 运行系统检查
echo -e "\n🔍 运行系统检查..."
python scripts/check_invariants.py --json 2>&1 | python3 -c "
import sys, json
d = json.load(sys.stdin)
if d['summary']['pass']:
    print('   ✅ 全部不变式通过')
else:
    print(f'   ⚠️  存在 {d[\"summary\"][\"hard\"]} 个 HARD 违规')
    sys.exit(1)
"

# 构建网站
echo -e "\n🌐 构建个人学术网站..."
python website/build.py 2>&1 | tail -1

echo ""
echo "============================================"
echo "  完成！"
echo "============================================"
echo ""
echo "预览网站:  cd website/public && python -m http.server 8000"
echo "自动重建:  python website/build.py --watch"
echo ""
