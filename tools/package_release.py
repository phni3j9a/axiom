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


def ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    # Exclude generated repository output only at the repository root.
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


def write_zip(source_parent: Path, source_name: str, archive: Path) -> None:
    source = source_parent / source_name
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as zf:
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
    args = parser.parse_args()

    subprocess.run(["python3", str(ROOT / "tools" / "validate_plugin.py")], check=True)

    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    version = manifest["version"]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    plugin_archive = output / f"axiom-v{version}-plugin.zip"
    source_archive = output / f"axiom-codex-plugin-v{version}-source.zip"

    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        plugin_stage = temp / "plugin" / "axiom"
        copy_tree(PLUGIN, plugin_stage)
        write_zip(plugin_stage.parent, plugin_stage.name, plugin_archive)

        source_stage = temp / "source" / "axiom-codex-plugin"
        copy_tree(ROOT, source_stage)
        write_zip(source_stage.parent, source_stage.name, source_archive)

    print(plugin_archive)
    print(source_archive)


if __name__ == "__main__":
    main()
