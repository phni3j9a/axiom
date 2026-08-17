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


def main() -> None:
    parser = argparse.ArgumentParser(description="Package the Axiom Codex plugin.")
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()

    subprocess.run(
        ["python3", str(ROOT / "tools" / "validate_plugin.py")],
        check=True,
    )

    manifest = json.loads(
        (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    version = manifest["version"]
    args.output.mkdir(parents=True, exist_ok=True)
    archive = args.output / f"axiom-v{version}-plugin.zip"

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / "axiom"
        shutil.copytree(PLUGIN, stage)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    zf.write(path, path.relative_to(stage.parent))

    with zipfile.ZipFile(archive) as zf:
        bad = zf.testzip()
        if bad:
            raise RuntimeError(f"Corrupt archive member: {bad}")

    print(archive)


if __name__ == "__main__":
    main()
