#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: tests/runtime-hardening.sh <image-ref>

Inspect a built downstream image for the template's runtime hardening baseline:
non-root user, no shell, no apt, no curl, and no wget in the exported rootfs.
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

image_ref="${1:-}"
if [[ -z "${image_ref}" ]]; then
  usage >&2
  exit 2
fi

command -v docker >/dev/null 2>&1 || {
  echo "docker is required for runtime hardening assertions" >&2
  exit 2
}

tmp_dir="$(mktemp -d)"
container_id=""
cleanup() {
  if [[ -n "${container_id}" ]]; then
    docker rm "${container_id}" >/dev/null 2>&1 || true
  fi
  rm -rf "${tmp_dir}"
}
trap cleanup EXIT

container_id="$(docker create "${image_ref}")"
docker export "${container_id}" -o "${tmp_dir}/rootfs.tar"
tar -tf "${tmp_dir}/rootfs.tar" | sed 's#^\./##' > "${tmp_dir}/files.txt"

assert_absent_file() {
  local path="${1#/}"
  if grep -Fxq "${path}" "${tmp_dir}/files.txt"; then
    echo "forbidden runtime file exists: /${path}" >&2
    exit 1
  fi
}

assert_absent_tree() {
  local path="${1#/}"
  if grep -Eq "^${path}(/|$)" "${tmp_dir}/files.txt"; then
    echo "forbidden runtime tree exists: /${path}" >&2
    exit 1
  fi
}

for executable in \
  /bin/sh \
  /bin/bash \
  /usr/bin/apt \
  /usr/bin/apt-get \
  /usr/bin/curl \
  /usr/bin/wget
do
  assert_absent_file "${executable}"
done

for directory in \
  /var/cache/apt \
  /var/lib/apt \
  /var/log/apt
do
  assert_absent_tree "${directory}"
done

runtime_user="$(docker image inspect --format '{{.Config.User}}' "${image_ref}")"
case "${runtime_user}" in
  ""|"0"|"0:0"|"root")
    echo "image must run as a non-root numeric or named user; got '${runtime_user}'" >&2
    exit 1
    ;;
esac

entrypoint="$(docker image inspect --format '{{json .Config.Entrypoint}}' "${image_ref}")"
if [[ "${entrypoint}" == "null" || "${entrypoint}" != *"/usr/local/bin/app"* ]]; then
  echo "image entrypoint should target the application binary; got ${entrypoint}" >&2
  exit 1
fi

echo "runtime hardening checks passed for ${image_ref}"
