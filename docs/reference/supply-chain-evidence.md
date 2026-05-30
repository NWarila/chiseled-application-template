# Supply Chain Evidence

Downstream image repositories should publish evidence for the image digest, not
only for mutable tags. See [`docs/how-to/publish-image.md`](../how-to/publish-image.md)
for a drop-in workflow that produces every required evidence type below.

## Required Evidence

| Evidence | Expected Mechanism |
| --- | --- |
| SBOM | Docker BuildKit SBOM attestation, created with `--sbom=true` or `--attest type=sbom`. |
| Provenance | Docker BuildKit provenance attestation, preferably `--provenance=mode=max`. |
| Artifact attestation | GitHub `actions/attest` for the pushed image digest. BuildKit carries the SBOM attestation. |
| Signature | Cosign/Sigstore signature over the image digest. |
| Runtime hardening | Output from `tests/runtime-hardening.sh <image-ref>`. |

## Anchors

- Canonical Chisel publishes prebuilt CLI binaries and checksum files and uses
  `chisel cut --release ... --root ...` to build root filesystems:
  <https://documentation.ubuntu.com/chisel/latest/how-to/install-chisel/>
- `canonical/chisel-releases` is the official slice-definition source, with
  release branches such as `ubuntu-24.04` and `ubuntu-26.04`:
  <https://github.com/canonical/chisel-releases>
- Docker BuildKit creates provenance and SBOM attestations with `--provenance`
  and `--sbom`:
  <https://docs.docker.com/build/metadata/attestations/>
- Docker documents SBOM attestation generation and local validation:
  <https://docs.docker.com/build/metadata/attestations/sbom/>
- GitHub artifact attestations can establish provenance for binaries and
  container images:
  <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>
- Sigstore Cosign signs and verifies container images:
  <https://docs.sigstore.dev/quickstart/quickstart-cosign/>
- SLSA Build levels describe increasing provenance guarantees:
  <https://slsa.dev/spec/v1.0/levels>
- NIST SP 800-190 is the application container security guide:
  <https://csrc.nist.gov/pubs/sp/800/190/final>

## Review Notes

Docker's local `--load` exporter is for runtime testing only. It does not
preserve SBOM or provenance attestations in the local image store. Publish
jobs should use `--push` for registry-backed evidence, or a local/tar exporter
only when validating attestation JSON before publishing.

Build args are visible in provenance. Do not put secrets in build args. If a
derived image needs private fetch credentials, use BuildKit secrets and document
why the secret is needed in the downstream repository.
