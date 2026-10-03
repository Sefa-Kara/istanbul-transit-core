#!/bin/bash
set -e

PORT="${PORT:-7860}"
BASE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=========================================================="
echo "🚀 Istanbul Transit Navigator - Container Bootstrap"
echo "=========================================================="
# Auto-download OTP shaded JAR if missing (zero-config boot)
mkdir -p "$BASE_DIR/bin"
if [ ! -f "$BASE_DIR/bin/otp-2.6.0-shaded.jar" ]; then
  echo "📥 OTP 2.6.0 shaded JAR not found locally. Downloading from official Maven Central..."
  curl -L -o "$BASE_DIR/bin/otp-2.6.0-shaded.jar" https://repo1.maven.org/maven2/org/opentripplanner/otp/2.6.0/otp-2.6.0-shaded.jar
  echo "✔ Download complete!"
fi

echo "Starting OpenTripPlanner 2.6 on port 8080..."
# Start OTP
java -Xmx4G -jar "$BASE_DIR/bin/otp-2.6.0-shaded.jar" --load "$BASE_DIR/data/router" &
OTP_PID=$!

echo "Waiting for OpenTripPlanner graph engine to be ready..."
for i in {1..30}; do
  if curl -s http://localhost:8080/ > /dev/null 2>&1; then
    echo "✔ OpenTripPlanner is healthy and listening on port 8080!"
    break
  fi
  sleep 1
done

echo "Starting Istanbul Transit API & Web Gateway on port $PORT..."
exec python3 -m uvicorn src.api.main:app --host 0.0.0.0 --port "$PORT"
