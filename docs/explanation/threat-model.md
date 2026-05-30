# Threat Model

This template focuses on supply-chain and runtime-surface risks for custom
application images.

## Primary Risks

| Risk | Template Response |
| --- | --- |
| Mutable base image drift | Require downstream repos to pin the Ubuntu builder image by digest and build the Chiseled rootfs themselves. |
| Chisel definition drift | Require a pinned `canonical/chisel-releases` commit instead of an unreviewed branch name. |
| Tampered Chisel CLI | Require a Chisel release tarball checksum in the manifest and Dockerfile. |
| Tampered application artifact | Require per-platform application checksums and a verification mode. |
| Excess runtime tooling | Assert no shell, apt, curl, or wget in the final image. |
| Root runtime | Require a non-root runtime user. |
| Missing release evidence | Document SBOM, provenance, GitHub attestation, and Cosign signature expectations. |

## Out Of Scope

- Registry compromise response.
- Admission-controller policy.
- Application-level vulnerability management.
- Runtime sandbox configuration in Kubernetes or another orchestrator.
- Secrets handling inside applications.

Those belong in downstream image repos or deployment platforms.
