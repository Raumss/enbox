#!/bin/bash
# Enbox 停止脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.enbox.pid"

if [ ! -f "$PID_FILE" ]; then
  # 尝试通过端口查找
  PID=$(lsof -ti:8000 2>/dev/null)
  if [ -n "$PID" ]; then
    echo "🔍 未找到 PID 文件，但检测到端口 8000 被占用 (PID: $PID)"
    kill "$PID" 2>/dev/null
    sleep 1
    echo "✅ Enbox 已停止"
    exit 0
  fi
  echo "ℹ️  Enbox 未在运行"
  exit 0
fi

PID=$(cat "$PID_FILE")

if kill -0 "$PID" 2>/dev/null; then
  echo "🛑 正在停止 Enbox (PID: $PID)..."
  kill "$PID" 2>/dev/null
  # 等待进程退出
  for i in $(seq 1 10); do
    if ! kill -0 "$PID" 2>/dev/null; then
      break
    fi
    sleep 0.5
  done
  # 如果还没退出，强制终止
  if kill -0 "$PID" 2>/dev/null; then
    kill -9 "$PID" 2>/dev/null
  fi
  echo "✅ Enbox 已停止"
else
  echo "ℹ️  Enbox 未在运行 (PID $PID 不存在)"
fi

rm -f "$PID_FILE"
