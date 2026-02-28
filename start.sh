#!/bin/bash
# Enbox 启动脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$SCRIPT_DIR/.venv"
PID_FILE="$SCRIPT_DIR/.enbox.pid"
LOG_FILE="$SCRIPT_DIR/enbox.log"

# 检查虚拟环境
if [ ! -d "$VENV" ]; then
  echo "⚠️  虚拟环境不存在，正在创建..."
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"
fi

# 如果已经在运行，先停止
if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "⚠️  Enbox 已在运行 (PID: $OLD_PID)，正在重启..."
    kill "$OLD_PID" 2>/dev/null
    sleep 1
  fi
  rm -f "$PID_FILE"
fi

# 启动服务
echo "🚀 启动 Enbox..."
cd "$SCRIPT_DIR"
nohup "$VENV/bin/python" main.py > "$LOG_FILE" 2>&1 &
PID=$!
echo "$PID" > "$PID_FILE"

sleep 1
if kill -0 "$PID" 2>/dev/null; then
  echo "✅ Enbox 已启动"
  echo "   PID:  $PID"
  echo "   地址: http://localhost:8000"
  echo "   日志: $LOG_FILE"
else
  echo "❌ 启动失败，请查看日志: $LOG_FILE"
  rm -f "$PID_FILE"
  exit 1
fi
