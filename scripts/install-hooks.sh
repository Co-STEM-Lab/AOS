#!/usr/bin/env bash
# 安装 AOS pre-commit hook（硬守卫）

set -e

HOOKS_DIR="$(git rev-parse --git-dir)/hooks"
PRE_COMMIT="$HOOKS_DIR/pre-commit"

cat > "$PRE_COMMIT" << 'HOOKEOF'
#!/usr/bin/env bash
# AOS Guardian Layer 1: 硬守卫
# 在每次 commit 前运行不变式校验，HARD 违规 = 拒绝提交

set -e

# 激活 venv（如果存在）
if [ -f venv/bin/activate ]; then
    source venv/bin/activate
fi

echo "🔍 AOS Guardian: 不变式校验中..."

# 运行检查
python scripts/check_invariants.py --json > /tmp/aos-check-result.json 2>&1
EXIT_CODE=$?

if [ $EXIT_CODE -eq 1 ]; then
    echo ""
    echo "❌ 发现 HARD 违规，提交被拒绝："
    echo ""
    python -c "
import json
with open('/tmp/aos-check-result.json') as f:
    data = json.load(f)
for v in data.get('hard_violations', []):
    print(f\"  📄 {v['file']}\")
    print(f\"     {v['message']}\")
    print(f\"     → {v.get('fix', '手动修复')}\")
    print()
"
    echo "💡 修复方法："
    echo "   1. 根据上述提示修复违规项"
    echo "   2. 运行 python scripts/check_invariants.py 验证"
    echo "   3. 重新 commit"
    echo ""
    echo "   ⚠️  紧急情况可跳过检查: SKIP_AOS_GUARDIAN=1 git commit ..."
    exit 1
elif [ $EXIT_CODE -eq 2 ]; then
    echo "🟡 仅有 SOFT 警告，允许提交。"
    echo "   建议后续处理: python scripts/check_invariants.py"
    exit 0
else
    echo "✅ 不变式校验通过。"
    exit 0
fi
HOOKEOF

chmod +x "$PRE_COMMIT"
echo "✅ AOS Guardian pre-commit hook 已安装到 $PRE_COMMIT"
