#!/bin/bash

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🛑 İstanbul Transit Navigator servisleri durduruluyor..."

# 1. Stop FastAPI on port 8000
API_PID=$(lsof -ti :8000 2>/dev/null || true)
if [ -n "$API_PID" ]; then
  kill -9 $API_PID 2>/dev/null || true
  echo "✔ Web Sunucusu (PID $API_PID) durduruldu."
fi

# 2. Stop OTP on port 8080
bash "$BASE_DIR/bin/stop_otp.sh" > /dev/null 2>&1 || true
OTP_PID=$(lsof -ti :8080 2>/dev/null || true)
if [ -n "$OTP_PID" ]; then
  kill -9 $OTP_PID 2>/dev/null || true
fi
echo "✔ OTP Çekirdek Motoru durduruldu."

echo ""
echo "=================================================================="
echo "✨ Tüm servisler başarıyla kapatıldı. Sıfır arka plan tüketimi!"
echo "=================================================================="
