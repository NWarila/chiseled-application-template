# chiseled-application-template

Reference template for application OCI image repositories that build minimal
Ubuntu Chiseled runtime images from pinned Canonical Chisel inputs. It ships
as a fully working example: a tiny Go binary, real pinned upstream digests, a
manifest-driven build pipeline, and runtime hardening assertions that all run
end-to-end in CI.

The template is intentionally not application-specific. The example application
is deliberately useless so the focus stays on the supply-chain shape.

## Prerequisites

The contract checks need only Python; the image lifecycle needs Docker:

- Python 3.12+
- Bash, for the build and runtime hardening scripts
- Docker Buildx, when building the image or rebuilding the example binary

## Quickstart

Run the contract checks (no Docker required):

```sh
python tools/verify.py ci
```

Build the example image end-to-end (Docker required):

```sh
make image
```

`make image` builds the example Go binary in a digest-pinned `golang` container,
verifies the resulting SHA256 against the committed manifest, generates the
docker buildx flags from the manifest, builds the Chiseled image for
`linux/amd64`, and runs the runtime hardening assertions against it.

To derive a real image repository, start with the full derivation flow in
[`docs/how-to/derive-image-repo.md`](docs/how-to/derive-image-repo.md). The
first edits are:

1. `examples/image-manifest.json`, or the downstream repo's real manifest path.
2. `containers/Dockerfile`, especially the application artifact stage.
3. Replace `app/` with the real application source or point the manifest at a
   vendor release binary.
4. `README.md` and repo-specific docs.
5. `docs/decision-records/repo/` for local decisions.
6. The release workflow that will publish, attest, and sign the real image.

## Template Shape

| Path | Role |
| --- | --- |
| [`contracts/image-manifest.schema.json`](contracts/image-manifest.schema.json) | Human-reviewable image manifest schema. |
| [`examples/image-manifest.json`](examples/image-manifest.json) | Working manifest with real pinned upstream values. |
| [`app/`](app/) | Example useless Go application that the template builds and ships. |
| [`containers/Dockerfile`](containers/Dockerfile) | Multi-stage Chisel pattern: pinned Ubuntu builder, verified Chisel CLI, pinned `chisel-releases` commit, scratch final image. |
| [`.dockerignore`](.dockerignore) | Deny-all build-context baseline that only allows reviewed application artifacts by default. |
| [`tests/runtime-hardening.sh`](tests/runtime-hardening.sh) | Runtime assertion script for no shell, package manager, curl, or wget. |
| [`tools/verify.py`](tools/verify.py) | Local and CI contract checks. |
| [`tools/generate_build_args.py`](tools/generate_build_args.py) | Render docker buildx flags from a reviewed manifest. |
| [`tools/build_app.sh`](tools/build_app.sh) | Deterministically rebuild the example application binaries. |
| [`tools/build_image.sh`](tools/build_image.sh) | Build the image from a manifest plus the rendered build args. |
| [`tools/verify_app_shas.py`](tools/verify_app_shas.py) | Verify built application binaries match the manifest's SHA256 values. |
| [`docs/`](docs/) | Diataxis documentation plus derivation, publishing, governance, and org/template/repo ADR scopes. |
| [`.github/workflows/`](.github/workflows/) | `ci.yaml` runs the contract checks and calls the image-build reusable; `codeql.yaml`, `scorecard.yaml`, `security.yaml`, and `repo-hygiene.yaml` call the canonical reusable workflows in `NWarila/.github` for CodeQL, OpenSSF Scorecard, Trivy + Gitleaks + zizmor, and org repo hygiene. |
| [`.github/workflows/reusable-chisel-image-build.yaml`](.github/workflows/reusable-chisel-image-build.yaml) | Template-specific reusable: build app binaries → verify SHA256 → build Chiseled image → run runtime hardening. Downstream repos call it (`uses: NWarila/chiseled-application-template/.github/workflows/reusable-chisel-image-build.yaml@<sha>`) instead of copying the pipeline. |

## What This Is, And What It Is Not

| | This repo | A downstream image repo |
| --- | --- | --- |
| Defines the Chiseled image contract | Yes | Yes |
| Builds a working image end-to-end | Yes, an intentionally useless example | Yes, the real application |
| Pins Chisel inputs | Real pins for the example | Real pins for the application |
| Publishes SBOM, provenance, signatures, and attestations | Documents the required path and release workflow shape | Implements the full publish path |
| Contains Vault-specific logic | No | Only if the downstream image is Vault |

The template does not provide a shared mutable base image. Derived repositories
build their own root filesystem directly from pinned Chisel inputs so review can
trace the builder image, Chisel CLI release, `chisel-releases` commit, slices,
application artifact, and runtime policy in one place.

## Normalized Repo Interface

| Command | Purpose |
| --- | --- |
| `make verify` | Run the local CI-equivalent contract checks. |
| `make build-args` | Render docker buildx flags from the manifest. |
| `make app-build` | Rebuild the example Go binaries deterministically. |
| `make app-verify` | Check built binaries' SHA256 against the manifest. |
| `make image-build` | Build the OCI image for `linux/amd64`. |
| `make image-test` | Run runtime hardening assertions against the built image. |
| `make image` | Run the full app -> image -> hardening pipeline. |

## Build Evidence Expectations

Downstream image repositories should publish images by digest and attach:

- BuildKit provenance with `--provenance=mode=max`.
- BuildKit SBOM attestations with `--sbom=true`.
- A GitHub artifact attestation for the pushed image digest. BuildKit carries
  the SBOM attestation.
- Cosign/Sigstore signatures on the image digest.
- Runtime hardening evidence from `tests/runtime-hardening.sh`.

The template's CI loads the example image locally for runtime testing and
explicitly disables local provenance so the test path is not confused with
release evidence. BuildKit SBOM, BuildKit provenance, signing, and GitHub
artifact attestations are downstream release concerns once a real registry
destination is chosen. The detailed expectations live in
[`docs/reference/supply-chain-evidence.md`](docs/reference/supply-chain-evidence.md),
and [`docs/how-to/publish-image.md`](docs/how-to/publish-image.md) carries a
publish workflow skeleton that wires build + push, Cosign keyless signing,
GitHub artifact attestation upload, and runtime hardening against the pushed
digest around the existing manifest-driven pipeline.

## License

MIT - see [LICENSE](LICENSE).
