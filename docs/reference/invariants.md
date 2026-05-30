# Invariants

The following invariants should remain true for this template and its derived
application image repositories.

| Invariant | Why It Matters |
| --- | --- |
| The final image uses `FROM scratch`. | Runtime contents are explicit copies, not inherited from a broad base. |
| The Ubuntu builder image is pinned by digest. | Builds do not silently follow mutable tags. |
| Chisel CLI downloads are checksum verified. | The tool that assembles the rootfs is authenticated by reviewed checksum. |
| `chisel-releases` is pinned by commit. | Slice definitions are reviewable and reproducible. |
| Application artifacts are selected per target architecture and verified before copy. | The final image is not assembled from the wrong platform or unchecked binaries. |
| Runtime user is non-root. | Default execution does not grant root inside the container. |
| Runtime image has no shell, apt, curl, or wget. | Post-compromise download and package-install paths are reduced. |
| SBOM, provenance, signature, and attestation evidence are published by digest. | Consumers can verify what was built and how. |
