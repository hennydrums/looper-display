#!/bin/zsh
# Beendet ein laufendes Looper-Display, auch wenn das Startfenster schon zu ist.
PORT=${HTTP_PORT:-8080}
PID=$(lsof -ti TCP:$PORT -sTCP:LISTEN 2>/dev/null)
if [ -z "$PID" ]; then
  echo "Kein Looper-Display auf Port $PORT aktiv -- offenbar schon beendet."
else
  kill "$PID" && echo "Looper-Display (Prozess $PID) beendet."
fi
read -k 1 "?Taste druecken zum Schliessen"
