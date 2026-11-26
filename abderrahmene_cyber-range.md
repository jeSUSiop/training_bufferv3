# CLAUDE.md — CyberRangeCZ training sandbox (context for building a new exercise)

This file describes how a **CyberRangeCZ Platform** (formerly KYPO CRP) training sandbox is
structured, using this buffer-overflow lab as the worked example. Drop it into a fresh chat to
generate a **new** exercise on the same platform. It captures the file layout, the required
schemas, and the non-obvious platform rules (learned the hard way — see "Gotchas").

> Audience: a Claude session (or developer) that will author a new CyberRangeCZ training from
> scratch. It assumes no prior knowledge of the platform.

---

## 1. What a CyberRangeCZ training is

A training = **two independent artifacts** that the platform combines:

1. **Sandbox definition** — a git repo describing the VMs, network, and provisioning. This is
   what builds the student's environment. Key files: `topology.yml`, `variables.yml`,
   `provisioning/`.
2. **Training definition** — `training.json`: the levels, instructions, flags, hints, scoring.
   Imported separately in the platform UI and *pointed at* a pool built from the sandbox.

The two are linked only by **answer variable names** (see Gotcha #1). Keep them in one repo for
sanity, but understand they are uploaded/imported through different UI flows.

Deployment flow in the UI: import sandbox definition → build a **pool** (N sandboxes) → import
`training.json` → create a **training instance** against that pool. For per-student flags you
must tick **"Generate variant sandboxes"** when creating the pool/instance.

Docs: https://docs.platform.cyberrange.cz/

---

## 2. Repository layout (this lab)

```
topology.yml                 # VMs, routers, networks, IP mappings
variables.yml                # APG per-sandbox variables (variant answers) — repo ROOT
training.json                # the training definition (levels/flags/hints)
game_design.md               # narrative + per-task design notes
README.md                    # human overview + topology table
provisioning/
  requirements.yml           # external community Ansible roles to pull (galaxy-style)
  playbook.yml               # top-level playbook: maps hosts -> roles
  host_vars/attacker.yml     # per-host ansible vars (e.g. ansible_python_interpreter)
  roles/
    attacker/
      tasks/main.yml         # provisions the student box + plants flag_task1
      files/shellcode/       # call_shellcode.c, shellcode_32.py, README
      files/attack-code/     # exploit.py (skeleton), brute-force.sh
    server/
      tasks/main.yml         # builds+runs vulnerable Docker containers, plants flag_level1/2/3
      handlers/main.yml
      files/Labsetup/        # the SEED lab: server-code/, bof-containers/, docker-compose.yml
```

Community roles (`user-access`, `chrony`, `sandbox-logging`) are pulled from
github.com/cyberrangecz via `requirements.yml`; don't vendor them.

---

## 3. `topology.yml` schema

```yaml
name: training-buffer-overflow          # sandbox definition name

hosts:                                   # the VMs students interact with
  - name: attacker
    base_box:
      image: seed                        # OpenStack image name (must exist in the cloud)
      mgmt_user: ubuntu                  # the account the platform SSHes in as to provision
    flavor: m1.medium                    # OpenStack flavor (must exist)
  - name: server
    base_box: { image: seed, mgmt_user: ubuntu }
    flavor: m1.medium

routers:                                 # gateway(s) between the lab net and the WAN
  - name: router
    base_box: { image: debian-12-x86_64, mgmt_user: debian }
    flavor: m1.small

wan:                                     # uplink network (internet access for the sandbox)
  name: internet-connection
  cidr: 100.100.100.0/24

networks:
  - name: seed-switch
    cidr: 10.1.26.0/24
    accessible_by_user: True             # True => students can Open GUI / SSH into hosts on it

net_mappings:                            # host -> network -> static IP
  - { host: attacker, network: seed-switch, ip: 10.1.26.23 }
  - { host: server,   network: seed-switch, ip: 10.1.26.9 }

router_mappings:
  - { router: router, network: seed-switch, ip: 10.1.26.1 }

groups: []
```

Rules:
- `image`, `flavor`, and `mgmt_user` must match what the OpenStack backend actually provides.
  A wrong flavor or image name fails the sandbox build immediately. `mgmt_user` must be an
  account that already exists in the image.
- At least one network with `accessible_by_user: True` so students can reach their box.
- The router + `wan` give hosts outbound internet (needed here for `docker build` / image pulls).

---

## 4. `variables.yml` — per-sandbox variant answers (APG)

Lives at the **repo root**, next to `topology.yml`. Declares variables whose value the platform's
**APG (Automatic Problem Generator)** randomizes per sandbox (i.e. per student). Each becomes a
plain Ansible variable injected into provisioning (reference as `{{ name }}`).

```yaml
flag_task1:
  type: password        # mandatory
  length: 16            # optional
flag_level1: { type: password, length: 16 }
flag_level2: { type: password, length: 16 }
flag_level3: { type: password, length: 16 }
```

Supported `type` values and their optional attributes:
| type       | attributes                         | notes                                   |
|------------|------------------------------------|-----------------------------------------|
| `password` | `length` (default none)            | random characters — best for flags      |
| `username` | `length` (default 8)               | random username                         |
| `port`     | `min` (def 35000), `max` (def min+4000), `prohibited: []` | random port |
| `text`     | —                                  | random *sentence* — not for exact-match flags |

`min`/`max`/`prohibited` also exist for IP-style ranges. Use `password` for CTF-style flags.

---

## 5. `training.json` — the training definition

Top-level keys: `title`, `description`, `prerequisites`, `outcomes`, `state`,
`show_stepper_bar`, `levels[]`, `estimated_duration`, **`variant_sandboxes`**.

- Set `"variant_sandboxes": true` whenever any level uses a variant answer.

Level types (`level_type`):
- **`INFO_LEVEL`** — read-only intro. Keys: `title`, `level_type`, `order`,
  `estimated_duration`, `minimal_possible_solve_time`, `content` (markdown).
- **`ACCESS_LEVEL`** — "log in to prove access". Keys add `passkey` (static answer, e.g.
  `start`), `cloud_content`, `local_content` (markdown shown for cloud vs local sandboxes).
- **`TRAINING_LEVEL`** — a task with a flag. Key fields:
  ```jsonc
  {
    "title": "...",
    "level_type": "TRAINING_LEVEL",
    "order": 2,
    "estimated_duration": 15,
    "minimal_possible_solve_time": 5,
    "answer": null,                       // null when using a variant answer
    "answer_variable_name": "flag_level1",// MUST match a key in variables.yml
    "variant_answers": true,              // true => per-sandbox answer
    "content": "markdown task text",
    "solution": "full walkthrough",
    "solution_penalized": true,
    "hints": [ { "title": "...", "content": "...", "hint_penalty": 10, "order": 0 } ],
    "incorrect_answer_limit": 10,
    "max_score": 100,
    "reference_solution": "...",
    "mitre_techniques": [],
    "expected_commands": [],
    "commands_required": false
  }
  ```
  For a **static** flag instead: set `"answer": "THEFLAG"`, `"answer_variable_name": null`,
  `"variant_answers": false`.

---

## 6. Provisioning conventions

- `playbook.yml` maps host groups to roles. Hosts named in `topology.yml` become Ansible groups.
  Community roles: `user-access` (creates the student login — here `user`/`Password123` with
  sudo), `chrony` (time sync), `sandbox-logging` (central syslog; leave as-is).
- Custom roles put shipped files under `roles/<role>/files/` and copy them with the `copy` module.
- **Flags must be the APG-injected value**, planted by provisioning. Do NOT self-generate flags
  (no `set_fact` + `lookup('password')`): the platform checks the student's answer against the
  APG value, so a self-generated flag will never match. Plant `{{ flag_level1 }}` etc. directly.
  Example (server role):
  ```yaml
  - name: Plant the Level 1 flag inside its container (root only)
    command: >
      docker exec server-1-10.9.0.5
      bash -c "echo {{ flag_level1 }} > /root/flag && chmod 600 /root/flag"
  ```

---

## 7. What THIS lab does (the worked example)

SEED "Buffer Overflow Attack Lab (Server Version)". Student works from **attacker**
(`10.1.26.23`, SEED Ubuntu, has gcc/python3/nc/gdb) against **server** (`10.1.26.9`) which runs
three vulnerable 32-bit services as root in Docker:

| Level | Port | ASLR | Leaks | Technique | Flag var |
|-------|------|------|-------|-----------|----------|
| Task 1 | — (local Set-UID on attacker) | n/a | — | setuid shellcode reads root-only `/opt/flag` | `flag_task1` |
| Task 2 / L1 | 9090 | off (`setarch -R`) | ebp + buffer | fixed-address overflow | `flag_level1` |
| Task 3 / L2 | 9091 | off | buffer only | size-independent address spray | `flag_level2` |
| Task 4 / L3 | 9092 | **on** | ebp + buffer | brute-force fixed `ret` (~2¹⁹ entropy) | `flag_level3` |

- `stack.c` (`strcpy` into `char buffer[BUF_SIZE]`) is the vuln; `server.c` forks per connection
  and `dup2`s the socket to stdin/stdout/stderr, so shellcode output (`cat /root/flag`) returns
  on the same TCP connection — no reverse shell strictly needed.
- The server reads **all 517 bytes of stdin first** (`fread`), then prints the leak. A short
  probe (`echo hello`) only shows the leak if the client sends EOF — use `nc -q 0`.
- ASLR is host-global; L1/L2 opt out with `setarch -R` in `docker-compose.yml`, L3 keeps it on.

---

## 8. Gotchas (things that broke, and the fix) — READ BEFORE AUTHORING

1. **Variant answers need `variables.yml` + `variant_sandboxes: true`.** Error
   *"Variable names [...] aren't present in the sandbox definition"* at instance creation = you
   referenced `answer_variable_name` in `training.json` but never declared it in `variables.yml`.
   Also enable "Generate variant sandboxes" in the UI. Plant the injected `{{ var }}`, never a
   self-generated value.
2. **`setarch -R` in Docker needs seccomp off.** `setarch -R` calls
   `personality(ADDR_NO_RANDOMIZE)`, which Docker's default seccomp profile blocks → container
   exits instantly. Add `security_opt: [seccomp:unconfined]` to any container that uses it.
   `docker-compose up -d` returns success even when a container then dies, so add a post-start
   "is it running?" check that dumps `docker logs` on failure.
3. **Short probes hang.** Programs that `fread` a fixed size before printing will block on a
   short input unless the client half-closes. Tell students to use `nc -q 0` (netcat-traditional)
   or `nc -N` (openbsd). The real exploit (full-size payload) doesn't need it.
4. **`mgmt_user` is image-specific and intentional here (`ubuntu` on the `seed` image).** Don't
   "fix" it without checking the image's real default account.
5. **Flavors/images must exist in the target cloud** or the build fails — verify with
   `openstack flavor list` / `openstack image show <name>`.
6. **Keep docs in sync.** `README.md`, `topology.pdf`, `game_design.md` are generated/hand-written
   from `topology.yml`; update them when you change the topology.

---

## 9. How to author a NEW exercise on this platform

1. **Design** the scenario and levels (narrative, what each flag proves, difficulty curve). Put
   it in `game_design.md`.
2. **`topology.yml`**: choose hosts/images/flavors/IPs. Keep one user-accessible network + a
   router/WAN if you need internet in the sandbox.
3. **`variables.yml`**: declare one variable per per-student flag (`type: password`).
4. **`provisioning/`**: write roles that build the vulnerable/target setup and **plant the
   injected flag variables**. Reuse community roles via `requirements.yml`.
5. **`training.json`**: INFO + ACCESS + one TRAINING_LEVEL per task; set
   `answer_variable_name` to match `variables.yml`, `variant_answers: true`, and top-level
   `variant_sandboxes: true`.
6. **Test what you can locally** (Docker build/run, exploit reachability) before relying on the
   cloud redeploy, which is the only real test of Ansible+APG.
7. Watch every item in §8.

---

## 10. Local testing notes (Windows host used here)

- No Ansible/OpenStack locally; the platform redeploy is the only real test of provisioning+APG.
- Docker Desktop **is** available — the container/exploit mechanics can be tested by hand:
  build `Labsetup` in `ubuntu:20.04` (needs `gcc-multilib` for `-m32`), run `docker compose`
  on a user-defined network, then drive exploits from a `python:3-slim` container on that net.
  `setarch -R` and Set-UID/`su` tests need `--security-opt seccomp=unconfined`.
- Files use CRLF line endings; YAML/JSON parsers accept it.
