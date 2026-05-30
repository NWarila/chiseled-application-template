# Architecture Decision Records

This directory holds the Architecture Decision Records (ADRs) governing this
template. Per [org ADR-0001](org/0001-use-architecture-decision-records.md),
ADRs are organized into three scopes:

- `org/` - byte-identical mirrors of org-baseline ADRs from `NWarila/.github`.
- `template/` - decisions owned by this chiseled application image template.
- `repo/` - repository-specific ADRs for this repository only.

## Template ADRs

No template-scoped ADRs exist yet. The Ubuntu Chiseled direction is an accepted
portfolio constraint for this repository, so it is documented in the README and
reference material rather than justified with a template ADR.

## Org ADRs

The `org/` scope is mirrored from `NWarila/.github`.

| ADR | Status | Decision |
| --- | --- | --- |
| [ADR-0001](org/0001-use-architecture-decision-records.md) | Accepted | Use ADRs to document design rationale. |
| [ADR-0002](org/0002-adopt-diataxis-documentation-framework.md) | Accepted | Use Diataxis for non-ADR documentation. |
| [ADR-0003](org/0003-use-deny-all-gitignore-strategy.md) | Accepted | Use deny-all `.gitignore` allowlists. |
| [ADR-0004](org/0004-use-renovate-for-dependency-updates.md) | Accepted | Use Renovate for dependency updates. |
| [ADR-0005](org/0005-pin-terraform-and-provider-versions-exactly.md) | Accepted | Pin Terraform and provider versions exactly. |

The `.gitkeep` placeholder in `repo/` keeps the directory skeleton complete
until this repository has a repo-specific ADR.
