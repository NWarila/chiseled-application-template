#!/usr/bin/env python3
"""Local verification entrypoint for the chiseled application template."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"

DOC_DIRS = [
    "docs/decision-records/org",
    "docs/decision-records/template",
    "docs/decision-records/repo",
    "docs/explanation",
    "docs/how-to",
    "docs/reference",
    "docs/tutorials",
]

ADR_HEADINGS = [
    "## TL;DR",
    "## Context and Problem Statement",
    "## Decision Drivers",
    "## Considered Options",
    "## Decision Outcome",
    "## Pros and Cons of the Options",
    "## Confirmation",
    "## Consequences",
    "## Assumptions",
    "## Supersedes",
    "## Superseded by",
    "## Implementing PRs",
    "## Related ADRs",
    "## Compliance Notes",
]

# Org ADRs every consumer must mirror (ADR-0001..0005); all five are required
# here. Byte-identity against the org source is enforced separately by drift-gate.
EXPECTED_ORG_ADRS = {"0001", "0002", "0003", "0004", "0005"}


class VerifyError(Exception):
    """Raised when a verification target fails."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerifyError(message)


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def _load_tool(module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, TOOLS_DIR / f"{module_name}.py")
    if spec is None or spec.loader is None:
        raise VerifyError(f"unable to load tools/{module_name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def check_docs_layout() -> None:
    for directory in DOC_DIRS:
        require((ROOT / directory).is_dir(), f"missing docs directory: {directory}")

    require((ROOT / "docs/README.md").is_file(), "missing docs/README.md")
    require((ROOT / "docs/decision-records/README.md").is_file(), "missing ADR index")
    for document in (
        "docs/how-to/derive-image-repo.md",
        "docs/how-to/build-image.md",
        "docs/how-to/publish-image.md",
        "docs/reference/governance.md",
        "docs/reference/quality-gates.md",
        "docs/reference/supply-chain-evidence.md",
    ):
        require((ROOT / document).is_file(), f"missing required documentation: {document}")

    org_adrs = sorted((ROOT / "docs/decision-records/org").glob("[0-9][0-9][0-9][0-9]-*.md"))
    present_org_adrs = {adr.name[:4] for adr in org_adrs}
    missing_org_adrs = sorted(EXPECTED_ORG_ADRS - present_org_adrs)
    require(
        not missing_org_adrs,
        "missing mirrored org ADRs under docs/decision-records/org: "
        + ", ".join(missing_org_adrs),
    )

    for adr in (ROOT / "docs/decision-records/template").glob("[0-9][0-9][0-9][0-9]-*.md"):
        text = adr.read_text(encoding="utf-8")
        missing = [heading for heading in ADR_HEADINGS if heading not in text]
        require(not missing, f"{adr.relative_to(ROOT)} missing ADR headings: {', '.join(missing)}")


def check_manifest() -> None:
    # The committed example manifest carries real, working pins so the
    # template builds end-to-end; validate it in strict mode so any future
    # regression that reintroduces REPLACE_WITH_* markers is caught here.
    run([sys.executable, "tools/check_image_manifest.py", "examples/image-manifest.json"])

    # Downstream repositories still need template mode while they fill in
    # their own pins. Exercise it in-process against a synthetic manifest so
    # the permissive path is regression-tested without committing a second
    # fixture.
    validator = _load_tool("check_image_manifest")
    manifest = json.loads((ROOT / "examples/image-manifest.json").read_text(encoding="utf-8"))
    manifest["chisel"]["release"]["commit"] = "REPLACE_WITH_CHISEL_RELEASES_COMMIT"
    validator.validate_manifest(manifest, template=True)


def check_dockerfile_contract() -> None:
    dockerfile = ROOT / "containers/Dockerfile"
    require(dockerfile.is_file(), "missing containers/Dockerfile")
    text = dockerfile.read_text(encoding="utf-8")

    required_markers = [
        "FROM scratch",
        "chisel cut",
        "CHISEL_RELEASE_REF",
        "CHISEL_SLICES",
        "CHISEL_SHA384_AMD64",
        "CHISEL_SHA384_ARM64",
        "APP_BINARY_AMD64",
        "APP_BINARY_ARM64",
        "APP_SHA256_AMD64",
        "APP_SHA256_ARM64",
        "RUN --mount=type=bind,source=.,target=/context,readonly",
        "cp \"/context/${app_binary}\" /work/app",
        "sha384sum -c -",
        "sha256sum -c -",
        "USER 65532:65532",
        "ENTRYPOINT [\"/usr/local/bin/app\"]",
        "BUILDKIT_SBOM_SCAN_CONTEXT=true",
    ]
    missing = [marker for marker in required_markers if marker not in text]
    require(not missing, f"Dockerfile missing contract markers: {', '.join(missing)}")
    require("SECRET" not in text.upper(), "Dockerfile must not define secret build args")
    # The single-string CHISEL_SHA384 pattern was removed because it cannot
    # match per-arch Chisel tarballs; guard against accidental reintroduction.
    require(
        "ARG CHISEL_SHA384\n" not in text and "ARG CHISEL_SHA384=" not in text,
        "Dockerfile must not define a single-arch ARG CHISEL_SHA384; use per-arch ARG CHISEL_SHA384_<ARCH>",
    )
    require(
        "ARG APP_SHA256\n" not in text and "ARG APP_SHA256=" not in text,
        "Dockerfile must not define a single-arch ARG APP_SHA256; use per-arch ARG APP_SHA256_<ARCH>",
    )
    require(
        "COPY ${APP_BINARY}" not in text,
        "Dockerfile must not COPY a single app binary; select the per-arch artifact in the application stage",
    )

    dockerignore = ROOT / ".dockerignore"
    require(dockerignore.is_file(), "missing .dockerignore")
    dockerignore_text = dockerignore.read_text(encoding="utf-8")
    for marker in ["*", "!dist/", "!dist/**"]:
        require(marker in dockerignore_text.splitlines(), f".dockerignore missing build-context marker: {marker}")

    # BUILDKIT_SBOM_SCAN_STAGE is a per-stage ARG. It must appear inside both
    # the chisel-rootfs and application builder stages with value true.
    builder_stages = ("chisel-rootfs", "application")
    for stage in builder_stages:
        marker = f"FROM ${{UBUNTU_BUILDER_IMAGE}} AS {stage}"
        require(marker in text, f"Dockerfile missing builder stage '{stage}'")
        stage_body = text.split(marker, 1)[1].split("\nFROM ", 1)[0]
        require(
            "ARG BUILDKIT_SBOM_SCAN_STAGE=true" in stage_body,
            f"stage '{stage}' must declare ARG BUILDKIT_SBOM_SCAN_STAGE=true so BuildKit scans it",
        )


def check_runtime_script() -> None:
    script = ROOT / "tests/runtime-hardening.sh"
    require(script.is_file(), "missing tests/runtime-hardening.sh")
    text = script.read_text(encoding="utf-8")
    for path in ["/bin/sh", "/usr/bin/apt", "/usr/bin/curl", "/usr/bin/wget"]:
        require(path in text, f"runtime hardening script does not assert absence of {path}")


# Build args that the Dockerfile reads from the build runtime (date, git, CI
# context) rather than from the reviewed manifest. The generator is not
# expected to emit these; they are populated by the downstream release
# workflow.
RUNTIME_ONLY_ARGS = {
    "BUILDKIT_SBOM_SCAN_CONTEXT",
    "BUILDKIT_SBOM_SCAN_STAGE",
    "TARGETARCH",
    "OCI_CREATED",
    "OCI_DESCRIPTION",
    "OCI_REVISION",
    "OCI_SOURCE",
    "OCI_VERSION",
}


GO_IMAGE_PIN = re.compile(r"golang:[A-Za-z0-9._-]+@sha256:[a-f0-9]{64}")


def check_build_tool_pins() -> None:
    required_files = [
        "Makefile",
        "tools/build_app.sh",
        ".github/workflows/reusable-chisel-image-build.yaml",
    ]
    for relative_path in required_files:
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        require(
            GO_IMAGE_PIN.search(text) is not None,
            f"{relative_path} must pin the example Go builder image as tag@sha256",
        )

    renovate = (ROOT / ".github/renovate.json5").read_text(encoding="utf-8")
    for marker in [
        "depName=(?<depName>[^\\\\s]+)",
        "currentDigest",
        "GO_IMAGE",
        "\"matchDatasources\": [\"docker\"]",
        "\"matchDepNames\": [\"golang\"]",
    ]:
        require(marker in renovate, f"Renovate config missing Go image pin marker: {marker}")


def check_build_args_generator() -> None:
    generator = _load_tool("generate_build_args")
    manifest_path = ROOT / "examples/image-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Template mode mirrors how downstream repositories will exercise the
    # generator on the starter manifest before they supply real pins.
    invocation = generator.build_invocation(manifest)
    build_args = invocation["build_args"]
    platforms = invocation["platforms"]

    require(platforms == manifest["image"]["platforms"], "generator must echo image.platforms verbatim")

    expected_keys = {
        "UBUNTU_BUILDER_IMAGE",
        "CHISEL_VERSION",
        "CHISEL_RELEASE_REPOSITORY",
        "CHISEL_RELEASE_REF",
        "CHISEL_RELEASE_PATH",
        "CHISEL_SLICES",
        "OCI_TITLE",
    }
    for platform in platforms:
        arch = platform.split("/", 1)[1].upper()
        expected_keys.update({f"CHISEL_SHA384_{arch}", f"APP_BINARY_{arch}", f"APP_SHA256_{arch}"})
    missing = sorted(expected_keys - set(build_args))
    require(not missing, f"generator missing build args: {', '.join(missing)}")

    # Every Dockerfile ARG that is not runtime-only must have a manifest-derived
    # value. This catches the case where a new ARG is added to the Dockerfile
    # without a corresponding manifest source, or vice versa.
    dockerfile_args = set(re.findall(r"^\s*ARG\s+([A-Z][A-Z0-9_]*)", (ROOT / "containers/Dockerfile").read_text(encoding="utf-8"), re.MULTILINE))
    expected_from_dockerfile = dockerfile_args - RUNTIME_ONLY_ARGS
    missing_from_generator = sorted(expected_from_dockerfile - set(build_args))
    require(
        not missing_from_generator,
        f"Dockerfile defines ARGs the generator does not emit: {', '.join(missing_from_generator)} (add to manifest or RUNTIME_ONLY_ARGS)",
    )
    unknown_from_generator = sorted(set(build_args) - dockerfile_args)
    require(
        not unknown_from_generator,
        f"generator emits build args the Dockerfile does not declare: {', '.join(unknown_from_generator)}",
    )

    # JSON form must round-trip the same structure.
    rendered_json = generator.render_json(invocation)
    decoded = json.loads(rendered_json)
    require(decoded == invocation, "json renderer must round-trip the invocation structure")

    # docker-buildx form pairs each flag with its value on adjacent lines so
    # that `mapfile -t` consumers can pass them as separate arguments to
    # docker buildx build.
    rendered = generator.render_docker_buildx(invocation).splitlines()
    require(rendered[0] == "--platform", "docker-buildx output must lead with --platform")
    require(rendered[1] == ",".join(platforms), "docker-buildx --platform value must follow on the next line")
    flag_value_pairs = rendered[2:]
    require(len(flag_value_pairs) % 2 == 0, "docker-buildx --build-arg flags and values must be paired")
    for index in range(0, len(flag_value_pairs), 2):
        require(flag_value_pairs[index] == "--build-arg", f"expected --build-arg at line {index + 3}")
        pair = flag_value_pairs[index + 1]
        require("=" in pair, f"build arg pair at line {index + 4} must be KEY=VALUE")


def check_local_build_helper() -> None:
    helper = ROOT / "tools/build_image.sh"
    require(helper.is_file(), "missing tools/build_image.sh")
    text = helper.read_text(encoding="utf-8")
    require("--load" in text, "local image helper must load the image for runtime tests")
    require("--provenance=false" in text, "local image helper must disable BuildKit provenance")
    forbidden_markers = ["--provenance=mode=max", "--sbom=true", "--attest"]
    present = [marker for marker in forbidden_markers if marker in text]
    require(
        not present,
        "local image helper must not pretend to emit release attestations: " + ", ".join(present),
    )


def check_stale_placeholders() -> None:
    tokens = ["TO" + "DO", "FIX" + "ME", "CHANGE" + "ME", r"YOUR_[A-Z0-9_]+"]
    pattern = re.compile(r"\b(" + "|".join(tokens) + r")\b")
    ignored_parts = {".git"}
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if any(part in ignored_parts for part in path.parts):
            continue
        if not path.is_file() or path.suffix.lower() not in {".md", ".py", ".sh", ".json", ".json5", ".yaml"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_no, line in enumerate(text.splitlines(), start=1):
            if pattern.search(line):
                findings.append(f"{path.relative_to(ROOT)}:{line_no}: {line.strip()}")
    require(not findings, "stale placeholders found:\n" + "\n".join(findings))


# Universal quality-gate caller workflows use reusable workflows hosted in
# NWarila/.github and pinned by 40-char SHA.
ORG_REUSABLE_CALLER_WORKFLOWS = {
    "codeql.yaml": "reusable-codeql.yaml",
    "scorecard.yaml": "reusable-scorecard.yaml",
    "security.yaml": "reusable-iac-security.yaml",
    "auto-merge.yaml": "reusable-auto-merge.yaml",
}

REUSABLE_USES_PATTERN = re.compile(
    r"uses:\s+NWarila/\.github/\.github/workflows/(?P<reusable>reusable-[a-z0-9-]+\.yaml)@(?P<sha>[0-9a-f]{40})\b"
)


def check_security_workflows() -> None:
    workflows_dir = ROOT / ".github/workflows"
    require(workflows_dir.is_dir(), "missing .github/workflows directory")

    for filename, reusable in ORG_REUSABLE_CALLER_WORKFLOWS.items():
        path = workflows_dir / filename
        require(path.is_file(), f"missing universal quality-gate caller: .github/workflows/{filename}")
        text = path.read_text(encoding="utf-8")
        match = REUSABLE_USES_PATTERN.search(text)
        require(
            match is not None,
            f".github/workflows/{filename} must call NWarila/.github/.github/workflows/<reusable>@<40-char-sha>",
        )
        assert match is not None  # for type-checkers
        require(
            match.group("reusable") == reusable,
            f".github/workflows/{filename} must call {reusable} (found {match.group('reusable')})",
        )

    # The chiseled-application-template carries Python (under tools/) and Go
    # (under app/) source the default CodeQL languages list ("actions") would
    # not analyze. Require those languages to be present in the codeql caller
    # so the override is not silently reverted to template default.
    codeql_text = (workflows_dir / "codeql.yaml").read_text(encoding="utf-8")
    require(
        "languages:" in codeql_text,
        ".github/workflows/codeql.yaml must override the default languages input",
    )
    for language in ("actions", "python", "go"):
        require(
            f'"{language}"' in codeql_text,
            f".github/workflows/codeql.yaml must include {language!r} in the languages list",
        )


# Template-specific reusable workflows. The build + SHA-verify + runtime-
# hardening pipeline is exposed as a reusable workflow so downstream image
# repositories can call the same contract instead of copy-pasting the steps;
# ci.yaml exercises it as the template's own self-test. This keeps the
# template-specific logic referenced from the template, while truly universal
# scans (codeql/scorecard/security) live in NWarila/.github.
def check_template_reusables() -> None:
    workflows_dir = ROOT / ".github/workflows"
    reusable = workflows_dir / "reusable-chisel-image-build.yaml"
    require(
        reusable.is_file(),
        "missing template reusable: .github/workflows/reusable-chisel-image-build.yaml",
    )
    text = reusable.read_text(encoding="utf-8")

    require(
        "workflow_call:" in text,
        "reusable-chisel-image-build.yaml must be a workflow_call reusable",
    )
    for inp in ("manifest_path:", "image_tag:", "platform:", "go_image:"):
        require(inp in text, f"reusable-chisel-image-build.yaml must declare input {inp!r}")
    for step in (
        "tools/build_app.sh",
        "tools/verify_app_shas.py",
        "tools/build_image.sh",
        "tests/runtime-hardening.sh",
    ):
        require(step in text, f"reusable-chisel-image-build.yaml must run {step}")

    ci_text = (workflows_dir / "ci.yaml").read_text(encoding="utf-8")
    require(
        "uses: ./.github/workflows/reusable-chisel-image-build.yaml" in ci_text,
        "ci.yaml must exercise the template reusable via "
        "uses: ./.github/workflows/reusable-chisel-image-build.yaml",
    )


MARKDOWN_LINK = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")


def check_markdown_links() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*.md"):
        if ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            for match in MARKDOWN_LINK.finditer(line):
                target = match.group(1).strip()
                if not target or target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                target = target.split("#", 1)[0].strip().strip("<>")
                if not target:
                    continue
                candidate = (path.parent / unquote(target)).resolve()
                try:
                    candidate.relative_to(ROOT)
                except ValueError:
                    findings.append(f"{path.relative_to(ROOT)}:{line_no}: link escapes repo: {target}")
                    continue
                if not candidate.exists():
                    findings.append(f"{path.relative_to(ROOT)}:{line_no}: missing link target: {target}")
    require(not findings, "broken local markdown links found:\n" + "\n".join(findings))


TARGETS = {
    "docs-layout": check_docs_layout,
    "manifest": check_manifest,
    "dockerfile-contract": check_dockerfile_contract,
    "runtime-script": check_runtime_script,
    "build-tool-pins": check_build_tool_pins,
    "build-args": check_build_args_generator,
    "local-build-helper": check_local_build_helper,
    "security-workflows": check_security_workflows,
    "template-reusables": check_template_reusables,
    "stale-placeholders": check_stale_placeholders,
    "markdown-links": check_markdown_links,
}

GROUPS = {
    "ci": [
        "docs-layout",
        "manifest",
        "dockerfile-contract",
        "runtime-script",
        "build-tool-pins",
        "build-args",
        "local-build-helper",
        "security-workflows",
        "template-reusables",
        "stale-placeholders",
        "markdown-links",
    ],
    "verify": [
        "docs-layout",
        "manifest",
        "dockerfile-contract",
        "runtime-script",
        "build-tool-pins",
        "build-args",
        "local-build-helper",
        "security-workflows",
        "template-reusables",
        "stale-placeholders",
        "markdown-links",
    ],
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=sorted(set(TARGETS) | set(GROUPS)))
    args = parser.parse_args()

    selected = GROUPS.get(args.target, [args.target])
    try:
        for target in selected:
            TARGETS[target]()
            print(f"{target}: ok")
    except (VerifyError, subprocess.CalledProcessError) as exc:
        print(f"verify failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
