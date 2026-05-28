# Reference build: `hello`

A credential-free reference application the template self-tests on every CI run
against the live `chisel cut` build and evidence pipeline. It is intentionally
trivial: a tiny program that prints a line and exits, so the only moving part
under test is the **template's** build + evidence contract, not any real
application.

## What it exercises

The CI self-tests in
[`../../.github/workflows/ci.yaml`](../../.github/workflows/ci.yaml) feed these
inputs through the reusable build workflow
([`reusable-chiseled-image-build.yaml`](../../.github/workflows/reusable-chiseled-image-build.yaml))
and assert the produced image is:

- minimal - only the slices in [`inputs.yaml`](inputs.yaml) are present;
- non-root - runs as an unprivileged UID;
- distroless and shell-free - no `/bin/sh`, no package manager;
- accompanied by valid SBOM, provenance attestation, and a cosign signature.

## Files

| File | Role |
| --- | --- |
| [`hello.c`](hello.c) | Trivial source for the reference application. |
| [`inputs.yaml`](inputs.yaml) | The consumer input surface (slices, entrypoint, image name) the reference build feeds to the reusable workflow. |

## Building

The `reference image self-test` job in CI runs exactly this flow, and you can
reproduce it locally:

```sh
#   1. Compile a static binary:
#        cc -static -Os -o hello hello.c
#   2. Call the reusable build workflow with examples/hello/inputs.yaml, OR
#      locally:
#        chisel cut --release ubuntu-24.04 --root rootfs <slices from inputs.yaml>
#        # assemble OCI FROM scratch over rootfs/ + the hello binary
#   3. Assert SBOM + provenance + signature + hardening checks pass.
```

CI compiles `hello.c`, cuts the rootfs, assembles the OCI image, runs it, and
asserts the expected output plus the runtime-hardening invariants; the evidence
self-test additionally pushes, signs, and verifies SBOM + provenance + cosign.
