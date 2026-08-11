#!/usr/bin/env bash
# Xjoy 一键启动脚本
# 同时启动 FastAPI 后端 (port 8000) 和 Next.js 前端 (port 3000)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "============================================"
echo "  📖 Xjoy — AI-Powered KJV Bible"
echo "============================================"
echo ""

# 加载 nvm（如果存在）
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

# 优先使用 Node.js 20（Next.js 14 兼容性最佳）
if command -v nvm &>/dev/null; then
    if nvm ls 20 &>/dev/null; then
        nvm use 20 &>/dev/null || true
    fi
fi

# 检查 Python 虚拟环境
if [ ! -f "$ROOT/packages/api/venv/bin/activate" ]; then
    echo "❌ 未找到 Python 虚拟环境，请先运行: cd packages/api && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 启动后端
echo "🔧 启动 FastAPI 后端 (port 8000)..."
cd "$ROOT"
source "$ROOT/packages/api/venv/bin/activate"
PYTHONPATH="$ROOT/packages/api" python -m uvicorn xjoy.api:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# 启动前端
echo "🔧 启动 Next.js 前端 (port 3000)..."
cd "$ROOT/packages/app"
NODE_ENV=development npx next dev --port 3000 &
FRONTEND_PID=$!

echo ""
echo "✅ 服务已启动:"
echo "   前端: http://localhost:3000"
echo "   后端: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，清理子进程
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "✅ 服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待任意子进程结束
wait
