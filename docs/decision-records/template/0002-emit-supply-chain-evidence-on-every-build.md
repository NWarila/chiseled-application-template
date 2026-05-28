# ADR-template/0002: Emit SBOM, Provenance, Signing, and Hardening Evidence on Every Build

| Field          | Value                                   |
| -------------- | --------------------------------------- |
| Status         | Accepted                                |
| Date           | 2026-05-28                              |
| Authors        | Nick Warila (@NWarila)                  |
| Decision-maker | Nick Warila (sole portfolio maintainer) |
| Consulted      | Supply-chain evidence direction for the fleet. |
| Informed       | Derivative chiseled application-image repositories. |
| Reversibility  | Medium                                  |
| Review-by      | N/A (Accepted)                          |

## TL;DR

Every image build produced by this template emits four pieces of supply-chain
evidence: an SBOM, a build provenance attestation, a cosign signature, and
runtime-hardening checks. The build fails if the hardening checks fail. This is
the template's v1 evidence contract.

## Context and Problem Statement

A minimal image is necessary but not sufficient. A consumer or auditor should be
able to *verify* what shipped, that it came from this pipeline, that it has not
been tampered with, and that it is actually hardened - not merely trust that it
is. Leaving evidence optional per-consumer would let images diverge in rigor and
would undermine the template's value proposition.

## Decision Drivers

1. Verifiability: contents, origin, integrity, and hardening are all provable.
2. Uniformity: every image in the fleet carries the same evidence.
3. Fail-closed hardening: a regression to root/shell/non-distroless blocks the
   build rather than shipping silently.
4. Standard, interoperable tooling (SPDX SBOM, in-toto attestation, cosign).

## Considered Options

1. Emit all four (SBOM + provenance + signing + hardening) on every build.
2. Emit a subset (e.g. SBOM only) and leave the rest opt-in.
3. Make all evidence opt-in per consumer.

## Decision Outcome

Chosen option: **Option 1, emit all four on every build.**

The reusable build workflow generates an SBOM with syft, attests build
provenance with actions/attest-build-provenance, signs the pushed image digest
with cosign (keyless/OIDC), and runs runtime-hardening assertions that fail the
build on regression. Signing applies to pushed images; the other three apply to
every build.

## Pros and Cons of the Options

### Option 1: Emit all four on every build

- Good, because every image is uniformly provable.
- Good, because hardening fails closed.
- Bad, because the pipeline is heavier than a bare image build.

### Option 2: Emit a subset

- Good, because it is lighter.
- Bad, because evidence rigor diverges across consumers.

### Option 3: All opt-in

- Good, because consumers choose their own cost.
- Bad, because it abandons the template's central guarantee.

## Confirmation

1. `reusable-chiseled-image-build.yaml` implements the SBOM, provenance,
   signing, and hardening steps, each keyed off the registry manifest digest of
   the built image; the CI evidence self-test verifies SBOM + provenance +
   cosign end to end.
2. Hardening checks fail the build on a non-root/shell/non-distroless
   regression.
3. The SBOM and provenance attestation are emitted for the pushed image digest
   (gated on `emit_evidence`), and cosign signing runs when the image is pushed
   and `sign` is set.

## Consequences

### Positive

- Uniform, verifiable supply-chain story across the fleet.

### Negative

- Builds are heavier and require `id-token`/`attestations` permissions.

### Neutral

- Tools (syft, cosign, attestation actions) can be swapped behind the same
  evidence contract via a future ADR.

## Assumptions

1. Consumers can grant `id-token: write` and `attestations: write` to the build.
2. Keyless cosign signing via Fulcio/Rekor is acceptable for the fleet.
3. SPDX/in-toto formats remain the interoperable baseline.

## Supersedes

None.

## Superseded by

None (current).

## Implementing PRs

- The initial repository structure established the evidence-step shape for all
  four evidence types.
- Each evidence step (SBOM, build-provenance attestation, cosign signature,
  runtime-hardening checks) was then wired to the real built-image digest and is
  verified by the CI evidence self-test.

## Related ADRs

- [Template ADR-template/0001](0001-use-chisel-cut-for-minimal-rootfs.md)

## Compliance Notes

- Full evidence wiring (SBOM, provenance, signing, hardening) lands across
  follow-up iterate PRs.
