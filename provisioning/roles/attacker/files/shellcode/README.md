
- Edit the command string in `shellcode_32.py` (keep the `*` marker in the
  same column), then run `./shellcode_32.py` to write `codefile_32`
  (the raw shellcode bytes).

- `run-shellcode` is a **Set-UID-root** runner (provided, built at sandbox
  creation): it reads your `codefile_32` and executes it as root.

- So the whole flow is:  `./shellcode_32.py && ./run-shellcode`

(`call_shellcode.c` is the source `run-shellcode` was compiled from, kept here
for reference.)
