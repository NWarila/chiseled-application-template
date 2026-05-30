# syntax=docker/dockerfile:1.7

# BuildKit SBOMs should include the build context as well as the builder stages
# that download and verify Chisel and application inputs, not only the final
# scratch image. BUILDKIT_SBOM_SCAN_CONTEXT is a global ARG; BUILDKIT_SBOM_SCAN_STAGE
# must be set as a per-stage ARG inside each stage that should be scanned (see
# https://docs.docker.com/build/metadata/attestations/sbom/#configure-sbom-scanners).
ARG BUILDKIT_SBOM_SCAN_CONTEXT=true

ARG UBUNTU_BUILDER_IMAGE

FROM ${UBUNTU_BUILDER_IMAGE} AS chisel-rootfs
ARG BUILDKIT_SBOM_SCAN_STAGE=true
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG TARGETARCH
ARG CHISEL_VERSION
# Chisel publishes per-architecture tarballs with different SHA384 digests.
# Provide one ARG per supported architecture; only the one matching TARGETARCH
# is required to be set for a given build invocation.
ARG CHISEL_SHA384_AMD64=""
ARG CHISEL_SHA384_ARM64=""
ARG CHISEL_RELEASE_REPOSITORY="https://github.com/canonical/chisel-releases.git"
ARG CHISEL_RELEASE_REF
ARG CHISEL_RELEASE_PATH="."
ARG CHISEL_SLICES

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl git tar; \
    rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    test -n "${CHISEL_VERSION}"; \
    case "${TARGETARCH}" in \
      amd64) expected_sha384="${CHISEL_SHA384_AMD64}" ;; \
      arm64) expected_sha384="${CHISEL_SHA384_ARM64}" ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    test -n "${expected_sha384}" || { echo "CHISEL_SHA384_$(echo "${TARGETARCH}" | tr a-z A-Z) must be set" >&2; exit 1; }; \
    chisel_asset="chisel_${CHISEL_VERSION}_linux_${TARGETARCH}.tar.gz"; \
    curl -fsSLo /tmp/chisel.tar.gz "https://github.com/canonical/chisel/releases/download/${CHISEL_VERSION}/${chisel_asset}"; \
    printf '%s  %s\n' "${expected_sha384}" "/tmp/chisel.tar.gz" | sha384sum -c -; \
    tar -xzf /tmp/chisel.tar.gz -C /usr/local/bin chisel; \
    chisel version

RUN set -eux; \
    test -n "${CHISEL_RELEASE_REF}"; \
    git init /tmp/chisel-release; \
    git -C /tmp/chisel-release remote add origin "${CHISEL_RELEASE_REPOSITORY}"; \
    git -C /tmp/chisel-release fetch --depth=1 origin "${CHISEL_RELEASE_REF}"; \
    git -C /tmp/chisel-release checkout --detach FETCH_HEAD

RUN set -eux; \
    test -n "${CHISEL_SLICES}"; \
    mkdir -p /rootfs; \
    chisel cut --release "/tmp/chisel-release/${CHISEL_RELEASE_PATH}" --root /rootfs ${CHISEL_SLICES}; \
    rm -rf /rootfs/var/cache/apt /rootfs/var/lib/apt /rootfs/var/log/apt

FROM ${UBUNTU_BUILDER_IMAGE} AS application
ARG BUILDKIT_SBOM_SCAN_STAGE=true
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ARG TARGETARCH
# Paths are relative to the Docker build context and must be allowed by
# .dockerignore. Only the file matching TARGETARCH is copied into the image.
ARG APP_BINARY_AMD64="dist/app-amd64"
ARG APP_BINARY_ARM64="dist/app-arm64"
ARG APP_SHA256_AMD64=""
ARG APP_SHA256_ARM64=""

WORKDIR /work
RUN --mount=type=bind,source=.,target=/context,readonly \
    set -eux; \
    case "${TARGETARCH}" in \
      amd64) app_binary="${APP_BINARY_AMD64}"; expected_sha256="${APP_SHA256_AMD64}" ;; \
      arm64) app_binary="${APP_BINARY_ARM64}"; expected_sha256="${APP_SHA256_ARM64}" ;; \
      *) echo "Unsupported TARGETARCH=${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    test -n "${app_binary}" || { echo "APP_BINARY_$(echo "${TARGETARCH}" | tr a-z A-Z) must be set" >&2; exit 1; }; \
    test -n "${expected_sha256}" || { echo "APP_SHA256_$(echo "${TARGETARCH}" | tr a-z A-Z) must be set" >&2; exit 1; }; \
    case "${app_binary}" in \
      /*|../*|*/../*|*/..|..) echo "Application binary path must be relative and stay inside the build context: ${app_binary}" >&2; exit 1 ;; \
    esac; \
    test -f "/context/${app_binary}" || { echo "Application binary not found in build context: ${app_binary}" >&2; exit 1; }; \
    cp "/context/${app_binary}" /work/app; \
    printf '%s  %s\n' "${expected_sha256}" "/work/app" | sha256sum -c -; \
    chmod 0555 /work/app

FROM scratch

ARG OCI_CREATED
ARG OCI_DESCRIPTION="Ubuntu Chiseled application image"
ARG OCI_REVISION
ARG OCI_SOURCE
ARG OCI_TITLE="chiseled-application"
ARG OCI_VERSION

LABEL org.opencontainers.image.created="${OCI_CREATED}" \
      org.opencontainers.image.description="${OCI_DESCRIPTION}" \
      org.opencontainers.image.revision="${OCI_REVISION}" \
      org.opencontainers.image.source="${OCI_SOURCE}" \
      org.opencontainers.image.title="${OCI_TITLE}" \
      org.opencontainers.image.version="${OCI_VERSION}"

COPY --from=chisel-rootfs /rootfs/ /
COPY --from=application /work/app /usr/local/bin/app

USER 65532:65532
ENTRYPOINT ["/usr/local/bin/app"]
