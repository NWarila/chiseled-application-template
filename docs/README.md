# Documentation

This repo follows the Diataxis documentation layout:

- `tutorials/` - learning-oriented walkthroughs (added as the build pipeline lands).
- `how-to/` - operational tasks for maintaining the template (added as needed).
- `reference/` - command surface and invariants (added as needed).
- `explanation/` - architecture and threat model for the chiseled image pattern.
- `decision-records/` - org, template, and repo ADRs.

The reusable build workflow lives at
[`../.github/workflows/reusable-chiseled-image-build.yaml`](../.github/workflows/reusable-chiseled-image-build.yaml),
and the credential-free reference build under [`../examples/`](../examples/).
