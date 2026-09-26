#!/bin/zsh
# Doppelklick startet das Looper-Display. Kein Node.js noetig -- diese Datei
# ist bereits das komplette Programm. Das Terminalfenster minimiert sich
# danach von selbst, ein Browser-Tab mit der Anzeige oeffnet automatisch.
# Beendet sich der Server -- per Ctrl+C, "Looper-Display beenden.command"
# oder dem "Server beenden"-Button in der Anzeige selbst -- schliesst sich
# auch das Terminalfenster gleich mit.
#
# Beim allerersten Mal fragt macOS einmalig, ob "osascript" das Terminal
# steuern darf: fuer Minimieren und automatisches Schliessen noetig. Ohne
# diese Erlaubnis laeuft die App trotzdem ganz normal, nur bleibt das
# Fenster dann offen und muss von Hand geschlossen werden.
cd "$(dirname "$0")"
APP="Programm (nicht anfassen)/looper-display"

# Nach dem Herunterladen und Entpacken markiert macOS jede einzelne
# Binaerdatei als "aus dem Internet" (Quarantaene) -- das betrifft nicht
# nur looper-display selbst, sondern auch die MIDI-Bibliothek in
# node_modules, und macOS "vergisst" diese Markierung nach einem erlaubten
# Start nicht zuverlaessig von selbst. Deshalb raeumt dieses Skript sie bei
# jedem Start aktiv weg -- auch bei sich selbst, damit auch die einmalige
# Sicherheitsbestaetigung fuer diese Datei nicht wiederkehrt. Betrifft nur
# eigene Dateien, braucht daher keine Admin-Rechte.
xattr -cr "Programm (nicht anfassen)" 2>/dev/null
xattr -d com.apple.quarantine "$0" 2>/dev/null

if [ ! -x "$APP" ]; then
  echo "$APP fehlt oder ist nicht ausfuehrbar. Liegt diese Datei im selben Ordner wie \"Programm (nicht anfassen)\"?"
  read -k 1 "?Taste druecken zum Schliessen"
  exit 1
fi

PORT=${HTTP_PORT:-8080}
MYTTY=$(tty)

close_window() {
  osascript <<APPLESCRIPT 2>/dev/null
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if tty of t is "$MYTTY" then close w
    end repeat
  end repeat
end tell
APPLESCRIPT
}
trap close_window EXIT

osascript <<APPLESCRIPT 2>/dev/null &
tell application "Terminal"
  repeat with w in windows
    repeat with t in tabs of w
      if tty of t is "$MYTTY" then set miniaturized of w to true
    end repeat
  end repeat
end tell
APPLESCRIPT

( for i in $(seq 1 100); do
    curl -s -o /dev/null "http://localhost:$PORT" && { open "http://localhost:$PORT"; break; }
    sleep 0.2
  done ) &

"./$APP"
