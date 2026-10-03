#!/bin/bash
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

echo "=== İstanbul Bağımsız Toplu Taşıma Sistemi Başlatılıyor ==="

# 1. Start OTP if not running
bash "$BASE_DIR/bin/start_otp.sh"

# 2. Check if FastAPI is already running on port 8000
API_PID=$(lsof -ti :8000)
if [ -n "$API_PID" ]; then
  echo "FastAPI Gateway is already running on PID $API_PID"
else
  echo "Starting FastAPI Gateway on http://localhost:8000..."
  cd "$BASE_DIR"
  nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/api.log" 2>&1 &
  NEW_API_PID=$!
  echo "FastAPI started with PID $NEW_API_PID."
fi

# Wait for API to respond
for i in {1..10}; do
  if curl -s http://localhost:8000/api/hubs > /dev/null 2>&1; then
    echo ""
    echo "================================================================="
    echo "✅ SİSTEM BAŞARIYLA AKTİF EDİLDİ!"
    echo "🌐 Arayüz Adresi : http://localhost:8000"
    echo "⚙️ Çekirdek Motor: http://localhost:8080"
    echo "================================================================="
    exit 0
  fi
  sleep 1
done

echo "FastAPI başlatıldı. Logları kontrol edin: $LOG_DIR/api.log"
