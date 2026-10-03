#!/bin/bash
set -e

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

mkdir -p "$BASE_DIR/logs"

echo ""
echo "=================================================================="
echo "🚀 İSTANBUL TRANSIT NAVIGATOR (Moovit & Google Maps Alternatifi)"
echo "=================================================================="
echo "Sistem başlatılıyor..."

# 1. Start OpenTripPlanner if not already running
OTP_PID=$(lsof -ti :8080 2>/dev/null || true)
if [ -n "$OTP_PID" ]; then
  echo "✔ OTP Motoru zaten çalışıyor (PID $OTP_PID)."
else
  echo "⏳ OTP Rota Motoru başlatılıyor (Port 8080)..."
  bash "$BASE_DIR/bin/start_otp.sh" > /dev/null 2>&1
  echo "✔ OTP Motoru aktif edildi."
fi

# 2. Start FastAPI Server if not already running
API_PID=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$API_PID" ]; then
  echo "✔ Web Sunucusu zaten çalışıyor (PID $API_PID)."
else
  echo "⏳ Web Arayüzü ve API Ağ Geçidi başlatılıyor (Port 8000)..."
  nohup python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 > "$BASE_DIR/logs/api.log" 2>&1 &
  NEW_API_PID=$!
  sleep 1
  echo "✔ Web Sunucusu aktif edildi (PID $NEW_API_PID)."
fi

# 3. Health Check
echo "🔍 Servisler doğrulanıyor..."
READY=0
for i in {1..15}; do
  if curl -s http://localhost:8000/api/hubs > /dev/null 2>&1; then
    READY=1
    break
  fi
  sleep 0.8
done

if [ $READY -eq 1 ]; then
  echo ""
  echo "=================================================================="
  echo "✅ SİSTEM BAŞARIYLA HAZIR HALE GETİRİLDİ!"
  echo "🌐 Arayüz Adresi : http://localhost:8000"
  echo "⚙️  Çekirdek Motor: http://localhost:8080"
  echo "🛑 Durdurmak için : ./stop.sh"
  echo "=================================================================="
  echo ""
  
  # Auto open browser on macOS
  if which open > /dev/null 2>&1; then
    echo "🌍 Tarayıcıda açılıyor: http://localhost:8000"
    open "http://localhost:8000"
  fi
else
  echo "❌ Sistem başlatılırken bir gecikme oluştu. Logları kontrol edin: $BASE_DIR/logs/api.log"
fi
