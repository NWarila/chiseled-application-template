#!/usr/bin/env python3
"""Validate the chiseled application image manifest contract."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


HEX40 = re.compile(r"^[a-f0-9]{40}$")
HEX64 = re.compile(r"^[a-f0-9]{64}$")
HEX96 = re.compile(r"^[a-f0-9]{96}$")
PLATFORM = re.compile(r"^linux/(amd64|arm64)$")
SLICE = re.compile(r"^[a-z0-9.+-]+_[a-z0-9.+-]+$")
UBUNTU_SERIES = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
VERSION = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")

FORBIDDEN_BASELINE = {
    "/bin/sh",
    "/bin/bash",
    "/usr/bin/apt",
    "/usr/bin/apt-get",
    "/usr/bin/curl",
    "/usr/bin/wget",
}

EVIDENCE_BASELINE = {
    "buildkit-sbom",
    "buildkit-provenance",
    "github-artifact-attestation",
    "cosign-signature",
    "runtime-hardening",
}

VERIFICATION_TYPES = {
    "checksum",
    "checksum-signature",
    "sigstore-bundle",
    "pgp-signature",
    "none",
}


class ManifestError(Exception):
    """Raised when the manifest violates the local contract."""


def has_placeholder(value: Any) -> bool:
    if isinstance(value, str):
        return "REPLACE_WITH_" in value or value.startswith("<") or value == "TBD"
    if isinstance(value, list):
        return any(has_placeholder(item) for item in value)
    if isinstance(value, dict):
        return any(has_placeholder(item) for item in value.values())
    return False


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def require_keys(obj: dict[str, Any], keys: set[str], path: str) -> None:
    missing = sorted(keys - set(obj))
    require(not missing, f"{path} missing required keys: {', '.join(missing)}")


def require_relative_context_path(value: Any, path: str) -> None:
    require(isinstance(value, str) and value, f"{path} must be a non-empty string")
    require("\\" not in value, f"{path} must use POSIX '/' separators")
    parsed = PurePosixPath(value)
    require(not parsed.is_absolute(), f"{path} must be relative to the Docker build context")
    require(".." not in parsed.parts, f"{path} must not traverse outside the Docker build context")
    require(not value.endswith("/"), f"{path} must name a file, not a directory")
    require(parsed.name, f"{path} must name a file, not a directory")


def match_or_placeholder(pattern: re.Pattern[str], value: str, template: bool, message: str) -> None:
    if template and has_placeholder(value):
        return
    require(bool(pattern.match(value)), message)


def validate_manifest(manifest: dict[str, Any], *, template: bool) -> None:
    require(manifest.get("schema_version") == "1.0", "schema_version must be 1.0")
    require_keys(
        manifest,
        {"image", "builder", "chisel", "application", "runtime", "evidence"},
        "manifest",
    )

    if not template:
        require(not has_placeholder(manifest), "real manifests must not contain replacement markers")

    image = manifest["image"]
    require_keys(image, {"name", "ubuntu_series", "platforms"}, "image")
    require(isinstance(image["name"], str) and image["name"], "image.name must be non-empty")
    require(bool(UBUNTU_SERIES.match(image["ubuntu_series"])), "image.ubuntu_series must look like 24.04")
    require(isinstance(image["platforms"], list) and image["platforms"], "image.platforms must be non-empty")
    seen_platforms = set()
    for platform in image["platforms"]:
        require(isinstance(platform, str), f"unsupported image platform: {platform}")
        require(bool(PLATFORM.match(platform)), f"unsupported image platform: {platform}")
        require(platform not in seen_platforms, f"duplicate image platform: {platform}")
        seen_platforms.add(platform)

    builder = manifest["builder"]
    require_keys(builder, {"image"}, "builder")
    if template and has_placeholder(builder["image"]):
        require("@sha256:" in builder["image"], "builder.image must show digest pinning")
    else:
        require(
            "@sha256:" in builder["image"] and bool(HEX64.match(builder["image"].rsplit("@sha256:", 1)[1])),
            "builder.image must be pinned by sha256 digest",
        )

    chisel = manifest["chisel"]
    require_keys(chisel, {"cli", "release", "slices"}, "chisel")
    require_keys(chisel["cli"], {"version", "sha384"}, "chisel.cli")
    match_or_placeholder(VERSION, chisel["cli"]["version"], template, "chisel.cli.version must be vX.Y.Z")
    sha384_map = chisel["cli"]["sha384"]
    require(
        isinstance(sha384_map, dict) and sha384_map,
        "chisel.cli.sha384 must be a non-empty object keyed by architecture",
    )
    supported_arches = {"amd64", "arm64"}
    unknown_arches = set(sha384_map) - supported_arches
    require(not unknown_arches, f"chisel.cli.sha384 has unsupported arches: {', '.join(sorted(unknown_arches))}")
    for arch, digest in sha384_map.items():
        match_or_placeholder(HEX96, digest, template, f"chisel.cli.sha384.{arch} must be 96 hex chars")
    image_arches = {platform.split("/", 1)[1] for platform in manifest["image"]["platforms"]}
    require(
        image_arches <= set(sha384_map),
        f"chisel.cli.sha384 missing entries for: {', '.join(sorted(image_arches - set(sha384_map)))}",
    )
    require_keys(chisel["release"], {"repository", "commit", "path"}, "chisel.release")
    require(
        chisel["release"]["repository"] == "https://github.com/canonical/chisel-releases.git",
        "chisel.release.repository must be canonical/chisel-releases",
    )
    match_or_placeholder(HEX40, chisel["release"]["commit"], template, "chisel.release.commit must be a git SHA")
    require(chisel["release"]["path"], "chisel.release.path must be non-empty")
    require(isinstance(chisel["slices"], list) and chisel["slices"], "chisel.slices must be non-empty")
    for slice_name in chisel["slices"]:
        require(bool(SLICE.match(slice_name)), f"invalid Chisel slice name: {slice_name}")

    application = manifest["application"]
    require_keys(application, {"source", "binary_path", "artifacts", "verification"}, "application")
    require(
        application["source"] in {"go-binary", "vendor-release-binary", "static-binary", "other"},
        "application.source has unsupported value",
    )
    require(application["binary_path"].startswith("/"), "application.binary_path must be absolute")
    require(isinstance(application["artifacts"], list) and application["artifacts"], "application.artifacts must be non-empty")
    artifact_platforms = set()
    for artifact in application["artifacts"]:
        require_keys(artifact, {"platform", "path", "sha256"}, "application.artifacts[]")
        require(bool(PLATFORM.match(artifact["platform"])), f"unsupported artifact platform: {artifact['platform']}")
        require(artifact["platform"] not in artifact_platforms, f"duplicate application artifact platform: {artifact['platform']}")
        require_relative_context_path(artifact["path"], "application.artifacts[].path")
        match_or_placeholder(HEX64, artifact["sha256"], template, "artifact sha256 must be 64 hex chars")
        artifact_platforms.add(artifact["platform"])
    require(set(image["platforms"]) <= artifact_platforms, "every image platform needs an application artifact")

    verification = application["verification"]
    require_keys(verification, {"type"}, "application.verification")
    require(verification["type"] in VERIFICATION_TYPES, "application.verification.type is unsupported")
    if verification["type"] in {"checksum-signature", "pgp-signature"}:
        require("signature_url" in verification, "signature verification requires signature_url")
    if verification["type"] == "sigstore-bundle":
        require(
            "certificate_identity" in verification and "certificate_oidc_issuer" in verification,
            "sigstore-bundle verification requires certificate identity and issuer",
        )

    runtime = manifest["runtime"]
    require_keys(runtime, {"user", "entrypoint", "forbidden_executables"}, "runtime")
    require(runtime["user"] not in {"", "0", "0:0", "root"}, "runtime.user must be non-root")
    require(isinstance(runtime["entrypoint"], list) and runtime["entrypoint"], "runtime.entrypoint must be non-empty")
    require(runtime["entrypoint"][0].startswith("/"), "runtime.entrypoint[0] must be absolute")
    forbidden = set(runtime["forbidden_executables"])
    require(FORBIDDEN_BASELINE <= forbidden, "runtime.forbidden_executables missing baseline tools")

    evidence = manifest["evidence"]
    require_keys(evidence, {"required"}, "evidence")
    required_evidence = set(evidence["required"])
    require(EVIDENCE_BASELINE <= required_evidence, "evidence.required missing baseline evidence types")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--template",
        action="store_true",
        help="allow explicit REPLACE_WITH_* markers in the starter manifest",
    )
    args = parser.parse_args()

    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        validate_manifest(manifest, template=args.template)
    except (OSError, json.JSONDecodeError, ManifestError) as exc:
        print(f"manifest check failed: {exc}", file=sys.stderr)
        return 1

    print(f"manifest check passed: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
