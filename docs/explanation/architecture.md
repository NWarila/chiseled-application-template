# Architecture

`chiseled-application-template` is the canonical framework-template for Ubuntu
Chiseled application-image repositories. It separates the repo-quality
boilerplate from the application-specific image build so consumer repos can supply only
their app inputs while inheriting the same build, evidence, security, and
documentation posture.

## Template Boundary

The template owns:

- The reusable image build workflow,
  [`reusable-chiseled-image-build.yaml`](../../.github/workflows/reusable-chiseled-image-build.yaml),
  which cuts a minimal rootfs with `chisel cut`, assembles an OCI image, and
  emits supply-chain evidence.
- The supply-chain evidence pipeline: SBOM (syft), build provenance
  attestation, image signing (cosign), and runtime-hardening checks.
- The consumer contract,
  [`contract/chiseled-application-template-contract.yaml`](../../contract/chiseled-application-template-contract.yaml),
  defining the consumer input surface and required caller workflows.
- A template-tier `baseline-manifest.json` that tells consumers which
  repo-hygiene files should stay byte-identical.
- The universal security, drift-gate, repo-hygiene, and release surface every
  derivative repo inherits.
- A credential-free reference application under [`../../examples/`](../../examples/)
  used to self-test the template.

It does not own a real application. Consumers (for example
`nwarila-platform/chiseled-hashicorp-vault`) own the Ubuntu/chisel release they
target, the slice list, the application artifact, the entrypoint, and the image
name.

## The Chisel Build Layer

The build engine is Canonical's [`chisel`](https://github.com/canonical/chisel)
(`chisel cut`). Rather than starting from a full Ubuntu base image and removing
packages, the build starts from nothing and adds only the exact Ubuntu *package
slices* the application declares:

1. Install a pinned `chisel` binary.
2. `chisel cut --release <chisel_release> --root rootfs <slices>` carves the
   requested slices into a minimal root filesystem.
3. Assemble an OCI image `FROM scratch` over that rootfs (buildah preferred,
   or `docker build` from scratch), layering the application artifact and
   setting a non-root user and entrypoint.

The smaller the slice set, the smaller the attack surface. No shell, no package
manager, and no unused libraries ship unless a slice explicitly provides them.

## Evidence Layer

Every build emits four pieces of evidence so the image is provable, not just
small:

- **SBOM** (syft) - the exact contents of the image.
- **Build provenance** (actions/attest-build-provenance) - that this workflow,
  from this commit, on a GitHub runner, produced this digest.
- **Signature** (cosign, keyless/OIDC) - a cryptographic signature over the
  image digest.
- **Runtime-hardening checks** - in-workflow assertions that fail the build if
  the image regresses to root, ships a shell, or stops being distroless.

## Status

The build engine and evidence pipeline are fully implemented and validated in
CI. `reusable-chiseled-image-build.yaml` performs a checksum-verified pinned
`chisel cut`, assembles the OCI image with buildah, and emits the SBOM,
build-provenance attestation, and cosign signature alongside the runtime-
hardening checks. The CI self-tests (`reference image self-test` and the
`evidence self-test` build/verify jobs) exercise the live pipeline end to end on
every run.

## External Dependencies

- [`NWarila/.github`](https://github.com/NWarila/.github) provides org-baseline
  ADR masters mirrored under `docs/decision-records/org/` and the reusable
  security, repo-hygiene, auto-merge, and release-please workflows.
- `chisel` and Ubuntu slice definitions, syft, cosign, and the GitHub
  attestation actions form the build and evidence toolchain.
- Renovate owns reviewed updates for GitHub Actions and the SHA-pinned reusable
  and drift-gate baseline refs.
