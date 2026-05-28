# Threat Model

This is a STRIDE-style threat model for
`NWarila/chiseled-application-template` and, by extension, the chiseled
application-image pattern this template demonstrates. It exists to make the
security posture of derivative image repos legible: a real image built from this
template inherits these trust boundaries and adds whatever its application and
publish target introduce.

## Scope

What this document covers:

- The template repository's own threats: supply chain, CI compromise,
  contributor account compromise, and dependency drift.
- Threats inherent to the chiseled image pattern: slice-definition tampering,
  unreviewed build-tool changes, image-signing gaps, and evidence confusion.
- Threats consumers should account for when they supply a real application
  artifact and push to a registry.

What this document does not cover:

- Threats specific to a particular application's runtime behavior. Consumers own
  those addenda.
- Registry and deployment-platform hardening. The template proves image
  provenance; where the image runs is out of scope here.

## Trust Boundaries

1. **Author to Repository.** Authors commit workflows, contract rules, and
   docs. Trust depends on GitHub account security, review discipline, and branch
   protection.
2. **Repository to CI runner.** CI checks out the repo onto GitHub-hosted
   runners. Trust depends on runner-image integrity and Actions permissions.
3. **CI runner to build-tool sources.** The build installs a pinned `chisel`
   binary and fetches Ubuntu slice definitions. Trust depends on upstream
   release integrity and checksum-verified, exact pins.
4. **Build to application artifact.** Consumers layer an application artifact on
   the chiseled rootfs. Trust depends on review and provenance of that artifact.
5. **Image to registry / verifier.** A pushed image is signed and attested.
   Trust depends on cosign keyless signing (Fulcio/Rekor) and attestation
   verification by downstream consumers.

## Threats By Category

### Spoofing

- **Spoofed GitHub Action dependency.** A workflow uses a tag or branch that
  later moves. Mitigation: every `uses:` is pinned to a full 40-character SHA;
  the org `repo_hygiene` policy (run via `repo-hygiene.yaml`) enforces this, and
  Renovate keeps pins current.
- **Spoofed chisel binary or slice definitions.** A malicious build tool or
  tampered slice set is accepted silently. Mitigation: `chisel` is pinned to an
  exact release and its tarball is checksum-verified (sha384) before install,
  and the slice-definition release channel is pinned via the `chisel_release`
  input.

### Tampering

- **Slice-definition tampering broadens the image.** An unreviewed slice change
  adds a shell or package manager. Mitigation: slices are declared in reviewed
  consumer inputs, and runtime-hardening checks fail the build if the image
  regresses to non-distroless or root.
- **Workflow tampering through privileged PR events.** `pull_request_target`
  could execute PR-controlled content with a write token. Mitigation: only
  `auto-merge.yaml` uses `pull_request_target`, and the org repo-hygiene policy
  rejects unsafe PR-content reads in that path.

### Repudiation

- **An author denies a release-affecting change.** Mitigation: Git history, PR
  review, workflow runs, and release-please changelog entries provide durable
  attribution.
- **A consumer denies which inputs built an image.** Mitigation: build
  provenance attestation binds the image digest to the workflow, commit, and
  runner; the SBOM records the exact image contents.

### Information Disclosure

- **Secrets leak through build logs or layers.** A real application build may
  use registry credentials or signing identities. Mitigation: the reference
  build is credential-free; consumers keep secrets in GitHub secrets/OIDC, and
  the deny-all `.gitignore` tracks only allowlisted files so build output and
  caches stay untracked.

### Denial Of Service

- **Build-tool release source unavailable.** CI fails during chisel install or
  cut. Mitigation: exact, checksum-verified pins make the failure explicit and
  reviewable rather than silent.

### Elevation Of Privilege

- **Image runs as root.** A container running as root widens blast radius if the
  app is exploited. Mitigation: the runtime-hardening check fails the build
  unless the effective user is non-root.
- **Workflow token over-permission.** A job that only validates should not write
  contents, packages, or attestations. Mitigation: jobs default to
  `contents: read`; write and `id-token`/`attestations` permissions are scoped
  to the build/release surfaces that need them, gated by `push`/`sign` inputs.

## What A Consumer Adds

A real chiseled image consumer inherits this threat model and adds, at minimum:

- Provenance and review of its own application artifact.
- Registry credential handling and least-privilege push permissions.
- Signature and attestation *verification* at deploy time.
- Incident response for a compromised image or revoked signing identity.
