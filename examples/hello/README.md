# Reference build: `hello`

A credential-free reference application the template self-tests once the
`chisel cut` build and evidence pipeline are wired. It is intentionally trivial:
a tiny program that prints a line and exits, so the only moving part under test
is the **template's** build + evidence contract, not any real application.

## What it exercises

When wired (see `# TODO(iterate)` below and in
[`../../.github/workflows/ci.yaml`](../../.github/workflows/ci.yaml)), this
example feeds the reusable build workflow
([`reusable-chiseled-image-build.yaml`](../../.github/workflows/reusable-chiseled-image-build.yaml))
and asserts the produced image is:

- minimal - only the slices in [`inputs.yaml`](inputs.yaml) are present;
- non-root - runs as an unprivileged UID;
- distroless and shell-free - no `/bin/sh`, no package manager;
- accompanied by valid SBOM, provenance attestation, and a cosign signature.

## Files

| File | Role |
| --- | --- |
| [`hello.c`](hello.c) | Trivial source for the reference application. |
| [`inputs.yaml`](inputs.yaml) | The consumer input surface (slices, entrypoint, image name) the reference build feeds to the reusable workflow. |

## Building (deferred)

```sh
# TODO(iterate): wire the real build. Sketch:
#   1. Compile a static binary:
#        cc -static -Os -o hello hello.c
#   2. Call the reusable build workflow with examples/hello/inputs.yaml, OR
#      locally:
#        chisel cut --release ubuntu-24.04 --root rootfs <slices from inputs.yaml>
#        # assemble OCI FROM scratch over rootfs/ + the hello binary
#   3. Assert SBOM + provenance + signature + hardening checks pass.
```

Until the build is wired, this directory documents the intended self-test and
keeps the reference inputs reviewable.
