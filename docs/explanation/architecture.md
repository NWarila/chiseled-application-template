# Architecture

`chiseled-application-template` is the reference template for one-application
Ubuntu Chiseled image repositories. It owns the reusable contract and ships a
working example image so the contract is exercised end-to-end on every change.

## Template Boundary

The template owns:

- A manifest shape that records builder, Chisel, application, runtime, and
  evidence inputs.
- A manifest-to-build-args generator so the manifest is the single review
  surface for buildx invocations.
- A Dockerfile pattern for building a scratch final image from a Chisel-cut
  root filesystem.
- A deliberately useless example Go application under `app/`, built
  deterministically inside a pinned `golang` container, that proves the full
  pipeline works on every CI run.
- Runtime hardening assertions that the example image and downstream images
  must pass.
- Documentation for expected SBOM, provenance, signature, and attestation
  evidence.
- A CI workflow that builds the example image and runs the hardening checks
  against it on every push and pull request.

It does not own:

- A shared mutable base image.
- Application-specific upstream verification rules.
- Registry publication, promotion, or environment approval policy.
- Cosign signing and GitHub artifact attestation upload (those bind to a
  publish destination the template does not own).

## Build Flow

The expected downstream build has three layers:

1. **Input review.** The image manifest records the Ubuntu builder digest,
   Chisel CLI checksum, `chisel-releases` commit, slice list, application
   artifact checksums, runtime policy, and required evidence.
2. **Root filesystem construction.** The Dockerfile verifies Chisel, checks out
   the pinned release definitions, and runs `chisel cut` into `/rootfs`.
3. **Runtime assembly.** The final image starts from `scratch`, copies the
   rootfs and verified application binary, runs as `65532:65532`, and exposes
   only the application entrypoint.

## External Dependencies

- Canonical Chisel CLI and `canonical/chisel-releases`.
- Docker BuildKit and Buildx for SBOM and provenance attestations.
- GitHub Actions for CI and artifact attestations in downstream repositories.
- Sigstore Cosign for image signatures.
