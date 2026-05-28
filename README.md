# chiseled-application-template

Canonical framework-template for **Ubuntu Chiseled application-image** repositories: repos that build minimal, hardened OCI images with `chisel cut`, with opt-in supply-chain evidence (SBOM, build provenance, cosign signature).

[![CI](https://github.com/NWarila/chiseled-application-template/actions/workflows/ci.yaml/badge.svg)](https://github.com/NWarila/chiseled-application-template/actions/workflows/ci.yaml)
[![Security](https://github.com/NWarila/chiseled-application-template/actions/workflows/security.yaml/badge.svg)](https://github.com/NWarila/chiseled-application-template/actions/workflows/security.yaml)
[![Repo Hygiene](https://github.com/NWarila/chiseled-application-template/actions/workflows/repo-hygiene.yaml/badge.svg)](https://github.com/NWarila/chiseled-application-template/actions/workflows/repo-hygiene.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## What this produces, and why it is rigorous

This template builds container images from a **Chiseled** root filesystem: instead of starting from a full Ubuntu base image and removing packages, it starts from nothing and adds only the exact Ubuntu *package slices* an application needs. The build engine is Canonical's [`chisel`](https://github.com/canonical/chisel) (`chisel cut`), which carves Ubuntu slice definitions into a minimal rootfs that is then packaged as an OCI image.

The result is a deliberately small attack surface:

- **No shell, no package manager, no unused libraries** - only the slices the app declares.
- **Distroless and non-root by construction** - the runtime hardening checks fail the build if the image regresses.

Every build runs the runtime-hardening checks (below); with evidence enabled (`emit_evidence`, plus signing for the cosign signature), the build also emits **supply-chain evidence**, so the artifact is not just small but *provable*:

| Evidence | Tool | What it proves |
| --- | --- | --- |
| **SBOM** | [syft](https://github.com/anchore/syft) | Exactly which Ubuntu slices / files ship in the image. |
| **Build provenance / attestation** | [actions/attest-build-provenance](https://github.com/actions/attest-build-provenance) | The image was built by this workflow, from this commit, on a GitHub runner. |
| **Image signing** | [cosign](https://github.com/sigstore/cosign) | The image digest is cryptographically signed (keyless / OIDC). |
| **Runtime hardening checks** | in-workflow asserts | The image runs as non-root, ships no shell, and is distroless. |

Minimal image + SBOM + provenance + signature + hardening assertions = a supply-chain story a downstream consumer (or an auditor) can verify, not just trust.

## How a consumer uses it

Downstream application-image repos (for example `nwarila-platform/chiseled-hashicorp-vault`) own only their **app inputs** - which Ubuntu release, which slices, which application artifact, and the image name. They call this template's reusable build workflow by SHA and inherit the entire build + evidence pipeline:

```yaml
# .github/workflows/image.yaml in a consumer repo
jobs:
  build:
    permissions:
      contents: read
      id-token: write       # cosign keyless signing + provenance
      attestations: write   # build provenance attestation
      packages: write       # push image (when push: true)
    uses: NWarila/chiseled-application-template/.github/workflows/reusable-chiseled-image-build.yaml@<40-char-sha>
    with:
      ubuntu_release: "24.04"
      chisel_release: "ubuntu-24.04"
      slices: |
        ca-certificates_data
        libc6_libs
      app_artifact: dist/myapp
      entrypoint: /usr/bin/myapp
      image_name: ghcr.io/nwarila-platform/myapp
      push: true
      sign: true
```

The consumer surface (inputs + required caller workflows) is defined machine-readably in [`contract/chiseled-application-template-contract.yaml`](contract/chiseled-application-template-contract.yaml).

## Build engine and status

- **Build engine:** Canonical `chisel cut` (upstream `chisel` binary + Ubuntu slice definitions) -> minimal rootfs -> OCI image.
- **Status:** Shipped and validated in CI. The reusable build workflow performs a real `chisel cut`, assembles the OCI image with buildah, and emits the full v1 supply-chain evidence bundle (SBOM via syft, SLSA build-provenance attestation, cosign keyless signature) plus runtime-hardening checks (non-root, no shell, distroless). CI self-tests exercise the live pipeline end to end: `reference image self-test` (credential-free local build), `evidence self-test (build + push + sign)`, and `evidence self-test (verify + cleanup)`. See [`examples/hello/README.md`](examples/hello/README.md) for the credential-free reference build the template self-tests on every run.

## Documentation

- [`docs/README.md`](docs/README.md) - documentation map (Diataxis layout).
- [`docs/explanation/architecture.md`](docs/explanation/architecture.md) - the template boundary and the chisel build layer.
- [`docs/explanation/threat-model.md`](docs/explanation/threat-model.md) - STRIDE threat model for the chiseled image pattern.
- [`docs/decision-records/`](docs/decision-records/) - org, template, and repo ADRs.

## License

MIT - see [LICENSE](LICENSE).
