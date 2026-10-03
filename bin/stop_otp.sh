#!/bin/bash
PID=$(lsof -ti :8080)
if [ -n "$PID" ]; then
  echo "Stopping OTP (PID $PID)..."
  kill "$PID"
  echo "OTP stopped."
else
  echo "OTP is not running on port 8080."
fi
