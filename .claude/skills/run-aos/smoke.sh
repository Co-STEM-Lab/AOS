#!/usr/bin/env bash
set -euo pipefail

# ─── AOS 网站构建与健康检查 ───────────────────────────────────────────────
# 用途：构建静态网站、启动本地预览、用 curl 验证关键页面可访问。
#
# 用法：
#   bash .claude/skills/run-aos/smoke.sh            # 构建 + 验证
#   bash .claude/skills/run-aos/smoke.sh --serve     # 构建 + 启动服务器（前台）
#   bash .claude/skills/run-aos/smoke.sh --no-serve  # 仅构建 + 文件检查（不启服务器）

cd "$(git rev-parse --show-toplevel 2>/dev/null)" || cd "$(dirname "$0")/../.."

source venv/bin/activate

BUILD_OUTPUT="website/public"
PORT="${PORT:-8765}"

echo "=== 1. 构建网站 ==="
python website/build.py
echo ""

# 关键页面列表
PAGES=(
  "index.html"
  "notes/index.html"
  "publications/index.html"
  "projects/index.html"
  "tools/index.html"
)

# 检查文件是否存在
echo "=== 2. 检查静态文件 ==="
MISSING=0
for page in "${PAGES[@]}"; do
  if [ -f "$BUILD_OUTPUT/$page" ]; then
    size=$(wc -c < "$BUILD_OUTPUT/$page")
    echo "  ✅ $page  ($size bytes)"
  else
    echo "  ❌ $page  — 缺失"
    MISSING=$((MISSING + 1))
  fi
done
echo ""

# 检查 notes 子页面
echo "  笔记页面:"
for note_dir in "$BUILD_OUTPUT/notes/"; do
  for d in "$note_dir"*/; do
    [ -d "$d" ] || continue
    note_name=$(basename "$d")
    if [ -f "${d}content.html" ]; then
      echo "      ✅ $note_name/content.html"
    else
      echo "      ⚠️  $note_name  (无 content.html)"
    fi
  done
done
echo ""

if [ "$MISSING" -gt 0 ]; then
  echo "❌ $MISSING 个关键页面缺失"
  exit 1
fi

# 如果只需要检查文件，可提前退出
if [ "${1:-}" = "--no-serve" ]; then
  echo "✅ 构建验证通过（未启动服务器）"
  exit 0
fi

# ─── 启动本地服务器并验证 HTTP 可用性 ────────────────────────────────────
echo "=== 3. 启动本地服务器 (port $PORT) ==="
cd "$BUILD_OUTPUT"
python -m http.server "$PORT" &
SERVER_PID=$!
cd - >/dev/null

# 等待服务器就绪
for i in $(seq 1 10); do
  if curl -s "http://127.0.0.1:$PORT/" >/dev/null 2>&1; then
    echo "  服务器就绪 (PID $SERVER_PID)"
    break
  fi
  if [ "$i" -eq 10 ]; then
    echo "❌ 服务器启动超时"
    kill "$SERVER_PID" 2>/dev/null
    exit 1
  fi
  sleep 0.5
done

echo ""

# 验证 HTTP 响应
echo "=== 4. HTTP 健康检查 ==="
HTTP_FAIL=0
for page in "${PAGES[@]}"; do
  url="http://127.0.0.1:$PORT/$page"
  http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
  if [ "$http_code" = "200" ]; then
    echo "  ✅ $page  → HTTP $http_code"
  else
    echo "  ❌ $page  → HTTP $http_code"
    HTTP_FAIL=$((HTTP_FAIL + 1))
  fi
done
echo ""

# 停止服务器
kill "$SERVER_PID" 2>/dev/null || true
wait "$SERVER_PID" 2>/dev/null || true

if [ "$HTTP_FAIL" -gt 0 ]; then
  echo "❌ $HTTP_FAIL 个页面 HTTP 检查失败"
  exit 1
fi

echo "✅ 全部通过！网站已构建并可正常服务。"
