#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
EXCLUDED_DIRS = {".git", "target", "node_modules", "__pycache__", ".pytest_cache"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
SUPPORTED_BINARY_NAMES = {
    "darwin-aarch64": "axiom-dashboard",
    "darwin-x86_64": "axiom-dashboard",
    "linux-x86_64": "axiom-dashboard",
    "linux-aarch64": "axiom-dashboard",
    "windows-x86_64": "axiom-dashboard.exe",
}
RELEASE_REQUIRED_PLATFORMS = {
    "darwin-aarch64",
    "darwin-x86_64",
    "linux-x86_64",
    "windows-x86_64",
}



def ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    # Exclude generated repository output only at the repository root.
    # Dashboard web/dist is a committed runtime asset and must be packaged.
    root_output = bool(rel.parts) and rel.parts[0] == "dist"
    return (
        root_output
        or any(part in EXCLUDED_DIRS for part in rel.parts)
        or path.suffix in EXCLUDED_SUFFIXES
    )


def copy_tree(source: Path, destination: Path) -> None:
    for path in source.rglob("*"):
        if ignored(path):
            continue
        relative = path.relative_to(source)
        target = destination / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        elif path.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def overlay_binaries(stage_plugin: Path, binary_root: Path) -> set[str]:
    found: set[str] = set()
    target_root = stage_plugin / "dashboard" / "bin"
    for platform, filename in SUPPORTED_BINARY_NAMES.items():
        candidates = [
            binary_root / platform / filename,
            binary_root / filename if binary_root.name == platform else binary_root / "__missing__",
        ]
        source = next((path for path in candidates if path.is_file()), None)
        if source is None:
            continue
        destination = target_root / platform / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if not filename.endswith(".exe"):
            destination.chmod(destination.stat().st_mode | 0o755)
        found.add(platform)
    return found


def write_zip(source_parent: Path, source_name: str, archive: Path) -> None:
    source = source_parent / source_name
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_parent))
    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"Corrupt archive member: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Package Axiom Plugin and source archives.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--dashboard-binaries",
        type=Path,
        help="Directory containing <platform>/axiom-dashboard[.exe] overlays.",
    )
    parser.add_argument(
        "--require-dashboard-binaries",
        action="store_true",
        help="Fail when no prebuilt Dashboard binary was overlaid.",
    )
    args = parser.parse_args()

    subprocess.run(["python3", str(ROOT / "tools" / "validate_plugin.py")], check=True)

    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    plugin_archive = output / f"axiom-v{version}-plugin.zip"
    source_archive = output / f"axiom-codex-plugin-v{version}-source.zip"

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        plugin_stage = temp / "plugin" / "axiom"
        copy_tree(PLUGIN, plugin_stage)
        binary_platforms: set[str] = set()
        if args.dashboard_binaries:
            binary_platforms = overlay_binaries(
                plugin_stage, args.dashboard_binaries.resolve()
            )
        if args.require_dashboard_binaries:
            missing = sorted(RELEASE_REQUIRED_PLATFORMS - binary_platforms)
            if missing:
                raise RuntimeError(
                    "Missing required Dashboard binaries: " + ", ".join(missing)
                )
        write_zip(plugin_stage.parent, plugin_stage.name, plugin_archive)

        source_stage = temp / "source" / "axiom-codex-plugin"
        copy_tree(ROOT, source_stage)
        write_zip(source_stage.parent, source_stage.name, source_archive)

    print(plugin_archive)
    print(source_archive)
    if args.dashboard_binaries:
        print(
            "Dashboard binaries overlaid: "
            + ", ".join(sorted(binary_platforms))
        )


if __name__ == "__main__":
    main()
