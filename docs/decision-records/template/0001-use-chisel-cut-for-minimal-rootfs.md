# ADR-template/0001: Use Canonical chisel cut for the Minimal Rootfs

| Field          | Value                                   |
| -------------- | --------------------------------------- |
| Status         | Accepted                                |
| Date           | 2026-05-28                              |
| Authors        | Nick Warila (@NWarila)                  |
| Decision-maker | Nick Warila (sole portfolio maintainer) |
| Consulted      | Existing framework-template scaffold ADRs. |
| Informed       | Derivative chiseled application-image repositories. |
| Reversibility  | Medium                                  |
| Review-by      | N/A (Accepted)                          |

## TL;DR

Chiseled application-image repositories derived from this template build their
root filesystem with Canonical's `chisel cut` (the upstream `chisel` binary plus
Ubuntu slice definitions), then package that rootfs as an OCI image. They do not
start from a full base image and remove packages.

## Context and Problem Statement

A minimal, hardened application image needs a deliberately small, auditable set
of files. Two strategies exist: start from a full Ubuntu base and strip it down,
or start from nothing and add only the exact package *slices* an application
needs. The strip-down approach is hard to audit (you must prove the absence of
things) and tends to leave a shell and package manager behind. The additive
approach makes the image contents an explicit, reviewable input.

`chisel` is Canonical's first-party tool for the additive approach: it cuts
Ubuntu slice definitions into a rootfs containing only the requested slices.
Because it is upstream and Ubuntu-aligned, the slice definitions track the same
packages and CVEs as Ubuntu itself.

## Decision Drivers

1. Minimal, auditable attack surface (no shell, no package manager by default).
2. Image contents are an explicit, reviewable input, not an emergent leftover.
3. First-party Ubuntu alignment for slice definitions and security updates.
4. A consumer surface a downstream repo can own with just a slice list.
5. Reproducible, pin-able build tooling.

## Considered Options

1. Canonical `chisel cut` over Ubuntu slice definitions.
2. Full Ubuntu base image with package removal.
3. A third-party distroless base (e.g. an external distroless project).
4. Hand-rolled `FROM scratch` with manually copied libraries.

## Decision Outcome

Chosen option: **Option 1, `chisel cut` over Ubuntu slice definitions.**

The reusable build workflow installs a pinned `chisel`, runs
`chisel cut --release <chisel_release> --root rootfs <slices>`, and packages the
result as an OCI image. Consumers supply the slice list and app inputs.

## Pros and Cons of the Options

### Option 1: chisel cut over Ubuntu slice definitions

- Good, because image contents are an explicit allowlist of slices.
- Good, because it is first-party and Ubuntu-aligned.
- Bad, because consumers must learn the slice model.

### Option 2: Full base image with package removal

- Good, because it is familiar.
- Bad, because absence is hard to prove and leftovers are common.

### Option 3: Third-party distroless base

- Good, because images are small out of the box.
- Bad, because contents and update cadence are controlled by a third party.

### Option 4: Hand-rolled FROM scratch

- Good, because it is maximally minimal.
- Bad, because dependency resolution is manual, fragile, and unauditable.

## Confirmation

1. `reusable-chiseled-image-build.yaml` installs a checksum-verified pinned
   `chisel` and cuts the rootfs with `chisel cut`; the CI self-tests exercise
   this on every run.
2. The slice list is a consumer-supplied input, not hard-coded.
3. Runtime-hardening checks confirm the resulting image is distroless and
   shell-free.

## Consequences

### Positive

- Smaller, more auditable images.
- Image contents reviewable as an explicit slice list.

### Negative

- Consumers must determine the slice set their app needs.

### Neutral

- Non-Ubuntu base requirements would need a different template.

## Assumptions

1. Target applications can run on an Ubuntu-derived rootfs.
2. Required Ubuntu slices exist or can be defined.
3. `chisel` remains addressable and pinnable by release.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

- The initial repository structure established the reusable build workflow
  shape.
- The `chisel cut` build engine (checksum-pinned `chisel` install + cut +
  buildah OCI assembly + runtime-hardening checks) was then implemented and is
  validated by the CI self-tests.

## Related ADRs

- [Template ADR-template/0002](0002-emit-supply-chain-evidence-on-every-build.md)
- [Org ADR-0003](../org/0003-use-deny-all-gitignore-strategy.md)

## Compliance Notes

- The working `chisel cut` build and checksum-verified `chisel` pin land in
  follow-up iterate PRs.
