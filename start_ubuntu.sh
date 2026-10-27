#!/usr/bin/env bash
# Ubuntu 启动脚本：后端 FastAPI (8000) + 前端 Vite (5173)
# 使用前：chmod +x start_ubuntu.sh stop_ubuntu.sh
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.run"
BACKEND_PID="$PID_DIR/backend.pid"
FRONTEND_PID="$PID_DIR/frontend.pid"

mkdir -p "$LOG_DIR" "$PID_DIR"

if [ -x "$BACKEND_DIR/venv/bin/python" ]; then
  PYTHON="$BACKEND_DIR/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON="python3"
else
  PYTHON="python"
fi

echo "[1/2] 启动后端 API 服务 (http://localhost:8000)"
if [ -f "$BACKEND_PID" ] && kill -0 "$(cat "$BACKEND_PID")" 2>/dev/null; then
  echo "  后端已在运行 (PID $(cat "$BACKEND_PID"))，跳过"
else
  cd "$BACKEND_DIR"
  nohup "$PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
    > "$LOG_DIR/backend.log" 2>&1 &
  echo $! > "$BACKEND_PID"
  echo "  后端已启动 (PID $(cat "$BACKEND_PID"))，日志: logs/backend.log"
fi

echo "[2/2] 启动前端页面服务 (http://localhost:5173)"
if [ -f "$FRONTEND_PID" ] && kill -0 "$(cat "$FRONTEND_PID")" 2>/dev/null; then
  echo "  前端已在运行 (PID $(cat "$FRONTEND_PID"))，跳过"
else
  cd "$FRONTEND_DIR"
  nohup node node_modules/vite/bin/vite.js --port 5173 \
    > "$LOG_DIR/frontend.log" 2>&1 &
  echo $! > "$FRONTEND_PID"
  echo "  前端已启动 (PID $(cat "$FRONTEND_PID"))，日志: logs/frontend.log"
fi

echo "等待后端健康检查..."
for i in $(seq 1 15); do
  if curl -s -o /dev/null http://127.0.0.1:8000/health; then
    echo "  后端已就绪"
    break
  fi
  sleep 1
done

echo "启动完成：前端 http://localhost:5173，后端 http://localhost:8000"
echo "停止服务请运行：./stop_ubuntu.sh"
