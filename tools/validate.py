#!/usr/bin/env python3
"""Validate the Axiom source tree with Python stdlib only."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
SKILL = PLUGIN / "skills" / "axiom"


class ValidationError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ValidationError(message)


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"missing JSON file: {path.relative_to(ROOT)}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def parse_frontmatter(text: str) -> dict[str, str]:
    require(text.startswith("---\n"), "SKILL.md must start with YAML frontmatter")
    try:
        _, front, _body = text.split("---", 2)
    except ValueError:
        fail("SKILL.md frontmatter is not closed")
    values: dict[str, str] = {}
    for raw in front.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def validate_manifest() -> None:
    manifest_path = PLUGIN / ".codex-plugin" / "plugin.json"
    manifest = read_json(manifest_path)
    for key in ("name", "version", "description", "skills"):
        require(manifest.get(key), f"plugin.json missing required project field: {key}")
    require(manifest["name"] == "axiom", "plugin name must be axiom")
    require(re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]) is not None,
            "plugin version must be simple semver")
    require(manifest["skills"].startswith("./"), "skills path must start with ./")
    skills_path = (PLUGIN / manifest["skills"]).resolve()
    require(skills_path.is_dir(), "manifest skills path does not resolve to a directory")
    require(PLUGIN.resolve() in skills_path.parents or skills_path == PLUGIN.resolve(),
            "manifest skills path escapes plugin root")

    interface = manifest.get("interface") or {}
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        require(interface.get(key), f"plugin interface missing: {key}")
    require(isinstance(interface.get("defaultPrompt"), list) and interface["defaultPrompt"],
            "plugin interface.defaultPrompt must be a non-empty list")

    plugin_dot_dir_files = {p.name for p in (PLUGIN / ".codex-plugin").iterdir() if p.is_file()}
    require(plugin_dot_dir_files == {"plugin.json"},
            ".codex-plugin must contain only plugin.json")


def validate_marketplace() -> None:
    marketplace_path = ROOT / ".agents" / "plugins" / "marketplace.json"
    market = read_json(marketplace_path)
    require(market.get("name") == "axiom-local", "unexpected marketplace name")
    plugins = market.get("plugins")
    require(isinstance(plugins, list) and len(plugins) == 1, "marketplace must list exactly Axiom")
    entry = plugins[0]
    require(entry.get("name") == "axiom", "marketplace plugin name mismatch")
    source = entry.get("source") or {}
    require(source.get("source") == "local", "marketplace source must be local")
    path = source.get("path")
    require(isinstance(path, str) and path.startswith("./"), "marketplace path must start with ./")
    resolved = (ROOT / path).resolve()
    require(resolved == PLUGIN.resolve(), "marketplace path does not point to plugins/axiom")


def validate_skill() -> None:
    skill_path = SKILL / "SKILL.md"
    text = skill_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    require(fm.get("name") == "axiom", "SKILL.md name must be axiom")
    require(bool(fm.get("description")), "SKILL.md description is required")
    require("non-trivial" in fm["description"].lower(),
            "skill trigger must be scoped away from trivial edits")

    required_phrases = [
        "gpt-5.6-luna",
        "reasoning_effort: max",
        "gpt-5.6-sol",
        "reasoning_effort: xhigh",
        "fork_turns: none",
        "Finding Freeze",
        "ACCEPT / DEFER / REJECT",
        "Do not force one task = one commit",
    ]
    combined = "\n".join(
        p.read_text(encoding="utf-8")
        for p in [skill_path, *sorted((SKILL / "references").glob("*.md"))]
    )
    for phrase in required_phrases:
        require(phrase in combined, f"missing semantic contract phrase: {phrase}")

    yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
    require("allow_implicit_invocation: true" in yaml,
            "Axiom must allow implicit invocation")
    require("default_prompt:" in yaml, "openai.yaml must provide default_prompt")


def validate_clean_rewrite() -> None:
    all_files = [p for p in PLUGIN.rglob("*") if p.is_file()]
    custom_toml = [p for p in all_files if p.suffix == ".toml"]
    require(not custom_toml, "custom agent TOML profiles are forbidden in Axiom")
    require(not (PLUGIN / "hooks").exists(), "hooks directory must not exist")
    require(not (PLUGIN / ".mcp.json").exists(), "Axiom should not bundle an MCP server")

    skill_dirs = sorted(p.parent for p in (PLUGIN / "skills").glob("*/SKILL.md"))
    require(len(skill_dirs) == 1 and skill_dirs[0].name == "axiom",
            "Axiom must expose exactly one primary skill")

    forbidden_legacy_paths = [
        "using-axiom", "doctor", "spec", "plan", "run", "gate", "finish",
    ]
    for name in forbidden_legacy_paths:
        require(not (PLUGIN / "skills" / name).exists(), f"legacy phase skill must not exist: {name}")


def main() -> int:
    try:
        validate_manifest()
        validate_marketplace()
        validate_skill()
        validate_clean_rewrite()
    except (ValidationError, OSError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print("OK: Axiom contract validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
