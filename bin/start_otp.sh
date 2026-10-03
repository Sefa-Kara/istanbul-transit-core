#!/bin/bash
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR"

PID=$(lsof -ti :8080)
if [ -n "$PID" ]; then
  echo "OTP is already running on PID $PID"
  exit 0
fi

echo "Starting OpenTripPlanner 2.6 in background..."
nohup java -Xmx4G -jar "$BASE_DIR/bin/otp-2.6.0-shaded.jar" --load "$BASE_DIR/data/router" > "$LOG_DIR/otp.log" 2>&1 &
NEW_PID=$!
echo "Started with PID $NEW_PID. Waiting for port 8080 to listen..."

for i in {1..20}; do
  if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "OpenTripPlanner is online and ready on http://localhost:8080!"
    exit 0
  fi
  sleep 1
done

echo "Warning: OTP process started but port 8080 not responding yet. Check $LOG_DIR/otp.log"
