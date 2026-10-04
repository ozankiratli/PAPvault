#!/usr/bin/env bash
#
# Build PAPvault and serve it, so the page can be looked at before anything is
# released.
#
# Usage: dev/scripts/start-server.sh           build, serve, print the address
#        dev/scripts/start-server.sh --stop    stop the server this script started
#        dev/scripts/start-server.sh --lan     serve to the local network as well
#
# Opening dist/index.html straight from disk is the offline file, and it behaves a
# little differently: a file has no origin, so a browser offers it no directory
# handle and treats it as insecure. What the website serves is this, over http, which
# is why reviewing a release means serving it rather than double-clicking it.
#
# The port is 8765 and the address is 127.0.0.1 unless --lan is given, which binds
# every interface so a phone on the same network can reach it. The process id is kept
# in dev/scripts/.server.pid, and --stop kills that one process and nothing else: a
# server started by hand, or anybody else's, is not this script's to touch.

set -euo pipefail

PORT=8765
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"
PID_FILE="dev/scripts/.server.pid"

running() {
    [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

if [ "${1-}" = "--stop" ]; then
    if running; then
        kill "$(cat "$PID_FILE")"
        echo "stopped the server on port $PORT (pid $(cat "$PID_FILE"))"
        rm -f "$PID_FILE"
    else
        echo "no server of this script's is running"
        rm -f "$PID_FILE"
    fi
    exit 0
fi

BIND="127.0.0.1"
WHERE="http://127.0.0.1:$PORT/"
if [ "${1-}" = "--lan" ]; then
    BIND="0.0.0.0"
    ADDRESS="$(ip -4 -o addr show scope global 2>/dev/null | awk 'NR==1 {sub(/\/.*/, "", $4); print $4}')"
    WHERE="http://${ADDRESS:-127.0.0.1}:$PORT/"
fi

if running; then
    echo "a server of this script's is already on port $PORT (pid $(cat "$PID_FILE"))"
    echo "stop it with: $0 --stop"
    exit 1
fi

# Somebody else's server, which this script will not touch.
if command -v ss >/dev/null && ss -ltn 2>/dev/null | grep -q ":$PORT "; then
    echo "ERROR: something else is already listening on port $PORT" >&2
    echo "       it was not started here, so it is not stopped here either" >&2
    exit 1
fi

python3 build.py

python3 -m http.server "$PORT" --bind "$BIND" --directory dist > /dev/null 2>&1 &
echo $! > "$PID_FILE"
sleep 1

if ! running; then
    rm -f "$PID_FILE"
    echo "ERROR: the server did not start" >&2
    exit 1
fi

echo
echo "serving dist/ at $WHERE  (pid $(cat "$PID_FILE"))"
echo "stop it with: $0 --stop"
