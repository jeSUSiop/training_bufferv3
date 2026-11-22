# Buffer Overflow Attack Lab (Server Version)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-orange.svg)](https://creativecommons.org/licenses/by/4.0/)

Hands-on buffer-overflow attack lab for the [CyberRangeCZ Platform](https://docs.platform.cyberrange.cz/).
The player acts as a penetration tester who must exploit two vulnerable **network servers** running
as **root**, inject shellcode, and obtain a **root reverse shell** on each. Based on the
[SEED Labs](https://seedsecuritylabs.org/) *Buffer Overflow Attack Lab (Server Version)*.

## Scenario

A target server (`10.1.26.9`) exposes two TCP services, each wrapping a C program that contains a
classic **stack buffer-overflow** and runs with root privilege. Working from the **attacker** box
(`10.1.26.23`, a SEED Ubuntu machine with `gcc`, `python3`, `netcat`, `gdb` and the lab files in
`~/shellcode` and `~/attack-code`), the player crafts a payload, overwrites the saved return address,
runs shellcode, and reads `/root/flag` on each target.

| Target  | Address           | What it leaks                       |
|---------|-------------------|-------------------------------------|
| Level 1 | `10.1.26.9:9090`  | frame pointer (ebp) **and** buffer address (ASLR off) |
| Level 2 | `10.1.26.9:9091`  | **only** the buffer address, size unknown (ASLR off) |
| Level 3 | `10.1.26.9:9092`  | same as Level 1 but **ASLR on** (Task 4 brute-force target) |

## Game Levels Summary

| # | Level | Goal | Flag |
|---|-------|------|------|
| 0 | Introduction | Read the scenario, rules and topology | — |
| 1 | Get Access | Log in to the **attacker** machine (Open GUI or SSH) | `start` |
| 2 | Task 1 – Shellcode & Set-UID | Edit `shellcode_32.py` to run `cat /opt/flag`, execute it via the Set-UID-root runner | contents of `/opt/flag` (per sandbox) |
| 3 | Task 2 – Level 1 attack (32-bit) | Use leaked ebp + buffer addr, build `exploit.py`, get a root reverse shell on `:9090` | contents of `/root/flag` |
| 4 | Task 3 – Level 2 attack (buffer size unknown) | Spray the return address to make one size-independent payload, root shell on `:9091` | contents of `/root/flag` |
| 5 | Task 4 – Defeating Address Randomization | Brute-force the ASLR-enabled Level 3 container (`:9092`) with the Task 2 payload | contents of `/root/flag` |

> **Note:** levels follow the SEED lab (Task 1, 2, 3) plus a brute-force-ASLR task relabelled
> Task 4; the remaining SEED tasks are not part of this training.

## Learning Outcomes

- Understand how a stack buffer overflow overwrites the saved return address.
- Build a payload (NOP sled + shellcode + return address) and exploit a remote service.
- Obtain a root reverse shell on a vulnerable server.
- Explain how ASLR mitigates buffer-overflow attacks.

**Prerequisites:** basic Linux command line · basic C and stack layout · basic networking (TCP, netcat).
**Estimated duration:** ~65 minutes.

## Topology

See [topology.pdf](topology.pdf) for a diagram. Defined in [topology.yml](topology.yml).

| Host | IP | Image | Flavor | Role |
|------|----|-------|--------|------|
| attacker | `10.1.26.23` | seed | m1.medium | the player's box (log in here) |
| server | `10.1.26.9` | seed | m1.medium | runs the vulnerable services `:9090` / `:9091` / `:9092` |
| router | `10.1.26.1` | debian-12-x86_64 | standard.small | gateway between the lab network and the WAN |

- **lab-switch** network: `10.1.26.0/24`
- **WAN** (`internet-connection`): `100.100.100.0/24`

## Repository Layout

```
training.json                 # the training definition (levels, flags, hints) loaded by the platform
game_design.md                # narrative + per-task design of the lab
topology.yml / topology.pdf   # network topology
Buffer_Overflow_*.pdf         # original SEED lab writeups (Server & Setuid)
provisioning/
  playbook.yml                # top-level Ansible playbook
  roles/
    attacker/                 # provisions the SEED attacker box + ~/shellcode and ~/attack-code
    server/                   # builds & runs the vulnerable services (Docker: server.c / stack.c)
```

The vulnerable programs and the attacker tooling live under
`provisioning/roles/server/files/Labsetup/` and `provisioning/roles/attacker/files/`.

## License

This repository uses a dual licensing approach:

* The code (Ansible provisioning and custom code) is licensed under the terms of the
  [MIT License](https://opensource.org/license/mit).
* The game design is licensed under a
  [Creative Commons Attribution 4.0 International License (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

**Attribution:** the lab is based on the SEED Labs *Buffer Overflow Attack Lab (Server Version)*
by Wenliang Du (Syracuse University), [seedsecuritylabs.org](https://seedsecuritylabs.org/).
See [ATTRIBUTION.txt](ATTRIBUTION.txt).
