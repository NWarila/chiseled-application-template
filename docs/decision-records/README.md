# Architecture Decision Records

This directory holds the Architecture Decision Records (ADRs) governing this
chiseled application-image framework-template. Per
[org ADR-0001](org/0001-use-architecture-decision-records.md), ADRs are
organized into three scopes:

- `org/` - byte-identical mirrors of org-baseline ADRs from
  [`NWarila/.github`](https://github.com/NWarila/.github). These apply to every
  repo in the org regardless of stack.
- `template/` - chiseled-application-template ADRs owned by this repository.
  Derivative consumers inherit these decisions.
- `repo/` - repository-specific ADRs for this repository only. This scope is
  currently empty.

`chiseled-application-template` is itself a type-template: it owns the canonical
chiseled image build contract, the supply-chain evidence pipeline, the reusable
build workflow, and framework-tier decisions that derivative chiseled
application-image repositories inherit.

## Template ADRs

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-template/0001](template/0001-use-chisel-cut-for-minimal-rootfs.md) | Accepted | Build the minimal rootfs with Canonical `chisel cut` over Ubuntu slice definitions. |
| [ADR-template/0002](template/0002-emit-supply-chain-evidence-on-every-build.md) | Accepted | Emit SBOM, provenance, signing, and runtime-hardening evidence on every build. |

## Org ADRs

The `org/` scope is mirrored from `NWarila/.github` and enforced by the org
drift gate.

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-0001](org/0001-use-architecture-decision-records.md) | Accepted | Use ADRs to document design rationale. |
| [ADR-0002](org/0002-adopt-diataxis-documentation-framework.md) | Accepted | Use Diátaxis for non-ADR documentation. |
| [ADR-0003](org/0003-use-deny-all-gitignore-strategy.md) | Accepted | Use deny-all `.gitignore` allowlists. |
| [ADR-0004](org/0004-use-renovate-for-dependency-updates.md) | Accepted | Use Renovate for dependency updates. |
| [ADR-0005](org/0005-pin-terraform-and-provider-versions-exactly.md) | Accepted | Pin Terraform and provider versions exactly. |

The `.gitkeep` placeholder in `repo/` keeps the directory skeleton complete
until this repository has a repo-specific ADR.
