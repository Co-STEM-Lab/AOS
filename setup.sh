#!/usr/bin/env bash
# AOS 一键初始化 —— 从克隆到构建网站 + 安装 Codex 技能
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
python3 -m pip install -r requirements.txt -q
echo "   ✅ 完成"

# 安装 Codex 技能（项目级）
echo -e "\n🧩 安装 Codex AI 技能..."
CODEX_SKILLS="${CODEX_HOME:-$HOME/.codex}/skills"
if [ -d "$CODEX_SKILLS" ]; then
    for skill_dir in .claude/skills/*; do
        name=$(basename "$skill_dir"); dir_name="${name%.md}"
        if [ -f "$skill_dir" ] && [ "${skill_dir##*.}" = "md" ]; then
            # 平铺 .md 文件 → 创建 skills/<dir_name>/SKILL.md
            dest="$CODEX_SKILLS/$dir_name"
            mkdir -p "$dest"
            cp "$skill_dir" "$dest/SKILL.md"
            echo "   ✅ $name"
        elif [ -d "$skill_dir" ]; then
            # 子目录技能 → 复制到目标（先删除旧版）
            dest="$CODEX_SKILLS/$name"
            rm -rf "$dest"
            cp -r "$skill_dir" "$dest"
            rm -rf "$dest/__pycache__"
            echo "   ✅ $name"
        fi
    done
    echo "   技能已安装到: $CODEX_SKILLS"
else
    echo "   ⚠️  Codex 技能目录不存在 ($CODEX_SKILLS)，跳过"
fi

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
