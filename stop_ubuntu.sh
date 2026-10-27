#!/usr/bin/env bash
# Ubuntu 停止脚本：按 .run/ 中的 PID 停止后端与前端服务
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$ROOT_DIR/.run"

for name in backend frontend; do
  pidfile="$PID_DIR/$name.pid"
  if [ ! -f "$pidfile" ]; then
    echo "$name 未在运行（无 PID 文件）"
    continue
  fi

  pid=$(cat "$pidfile")
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "$name 未在运行（PID $pid 已不存在）"
    rm -f "$pidfile"
    continue
  fi

  echo "停止 $name (PID $pid)"
  kill "$pid" 2>/dev/null || true
  for i in $(seq 1 10); do
    if ! kill -0 "$pid" 2>/dev/null; then
      break
    fi
    sleep 1
  done

  if kill -0 "$pid" 2>/dev/null; then
    echo "  $name 未正常退出，强制结束"
    kill -9 "$pid" 2>/dev/null || true
  fi
  rm -f "$pidfile"
done

echo "全部服务已停止"
