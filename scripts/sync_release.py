"""Prepare an add-on update from a published Kinwall release; never commit or push."""

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


UPSTREAM = "https://github.com/JohnDuprey/kinwall"
VERSION = r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"


def image_ready(version):
    result = subprocess.run(
        ["docker", "buildx", "imagetools", "inspect", "--raw",
         f"ghcr.io/johnduprey/kinwall:{version}"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        print("Release image is unavailable; a later run will retry.")
        return False
    manifest = json.loads(result.stdout)
    platforms = {
        (entry.get("platform", {}).get("os"), entry.get("platform", {}).get("architecture"))
        for entry in manifest.get("manifests", [])
    }
    ready = {("linux", "amd64"), ("linux", "arm64")} <= platforms
    if not ready:
        print("Release image does not yet include both amd64 and arm64; a later run will retry.")
    return ready


def nested_notes(body):
    """Keep upstream headings inside this version, preserving fenced examples."""
    lines = []
    fence = None
    for line in (body or "").strip().splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            value = marker.group(1)
            if fence is None:
                fence = value
            elif value[0] == fence[0] and len(value) >= len(fence):
                fence = None
        elif fence is None:
            line = re.sub(r"^(#{1,6}) ", lambda m: "#" * min(len(m[1]) + 2, 6) + " ", line)
        lines.append(line)
    return "\n".join(lines)


def sync_release(root, release):
    if release.get("draft") or release.get("prerelease"):
        return None
    tag = release["tag_name"]
    if not re.fullmatch("v" + VERSION, tag):
        return None
    version = tag.removeprefix("v")
    config_path = root / "kinwall/config.yaml"
    changelog_path = root / "kinwall/CHANGELOG.md"
    config = config_path.read_text()
    current = re.search(r'^version: "(' + VERSION + r')"$', config, re.MULTILINE)
    if not current:
        raise ValueError("Expected one quoted stable version in kinwall/config.yaml")
    previous = current[1]
    if tuple(map(int, version.split("."))) <= tuple(map(int, previous.split("."))):
        return None
    if not image_ready(version):
        return None
    changelog = changelog_path.read_text()
    if not re.search(r"^## " + re.escape(version) + r"\s*$", changelog, re.MULTILINE):
        first_version = re.search(r"^## ", changelog, re.MULTILINE)
        if not first_version:
            raise ValueError("Expected version sections in kinwall/CHANGELOG.md")
        entry = (
            f"## {version}\n\nRuns Kinwall {version}.\n\n"
            f"[Release notes]({UPSTREAM}/releases/tag/{tag}) · "
            f"[All changes since {previous}]({UPSTREAM}/compare/v{previous}...{tag})\n\n"
        )
        notes = nested_notes(release.get("body"))
        if notes:
            entry += notes + "\n\n"
        changelog = changelog[:first_version.start()] + entry + changelog[first_version.start():]
    config = config[:current.start()] + f'version: "{version}"' + config[current.end():]
    config_path.write_text(config)
    changelog_path.write_text(changelog)
    return version


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("release", type=Path, help="JSON from GitHub's latest release endpoint")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    version = sync_release(args.root, json.loads(args.release.read_text()))
    output = f"changed={'true' if version else 'false'}\n"
    if version:
        output += f"version={version}\n"
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as stream:
            stream.write(output)
    print(output, end="")


if __name__ == "__main__":
    main()
