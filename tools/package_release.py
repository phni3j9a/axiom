#!/usr/bin/env python3
"""Create deterministic-ish source and plugin ZIP archives using stdlib only."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"

EXCLUDED_DIRS = {".git", "__pycache__", "dist"}
EXCLUDED_NAMES = {".DS_Store"}


def iter_files(base: Path):
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(base)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if path.name in EXCLUDED_NAMES or path.suffix == ".pyc":
            continue
        yield path, rel


def write_zip(source: Path, destination: Path, prefix: str) -> None:
    with ZipFile(destination, "w", ZIP_DEFLATED) as zf:
        for path, rel in iter_files(source):
            zf.write(path, Path(prefix) / rel)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default=str(ROOT / "dist"))
    args = parser.parse_args()

    manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    version = manifest["version"]

    out = Path(args.output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)

    full_zip = out / f"axiom-v{version}-source.zip"
    plugin_zip = out / f"axiom-v{version}-plugin.zip"

    for p in (full_zip, plugin_zip):
        if p.exists():
            p.unlink()

    write_zip(ROOT, full_zip, f"axiom-v{version}-source")
    write_zip(PLUGIN, plugin_zip, "axiom")

    print(full_zip)
    print(plugin_zip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
