# Runtime Hardening

The runtime baseline is intentionally small and inspectable.

## Required Assertions

`tests/runtime-hardening.sh <image-ref>` checks that:

- The image config uses a non-root user.
- The entrypoint targets `/usr/local/bin/app`.
- `/bin/sh` and `/bin/bash` are absent.
- `apt`, `apt-get`, `curl`, and `wget` are absent.
- Apt cache, state, and log trees are absent.

The script inspects the exported root filesystem, so it does not require the
application to start or accept a health-check flag.

## Downstream Extensions

Derived repositories should add application-specific assertions, such as:

- Expected ports.
- Read-only filesystem compatibility.
- Required CA certificate files.
- Absence of unexpected interpreters or package managers introduced by extra
  Chisel slices.
