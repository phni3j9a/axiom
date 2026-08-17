#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
SKILL = PLUGIN / "skills" / "axiom"

errors: list[str] = []
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        checks.append(message)
    else:
        errors.append(message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}
    check(isinstance(data, dict), f"{path.relative_to(ROOT)} is a JSON object")
    return data


required = [
    ROOT / ".agents" / "plugins" / "marketplace.json",
    PLUGIN / ".codex-plugin" / "plugin.json",
    PLUGIN / "plugin.json",
    SKILL / "SKILL.md",
    SKILL / "agents" / "openai.yaml",
    SKILL / "references" / "delegation.md",
    SKILL / "references" / "codex-0.147-subagents.md",
    SKILL / "references" / "review.md",
    SKILL / "references" / "context-management.md",
    SKILL / "references" / "git.md",
    PLUGIN / "assets" / "axiom-logo.svg",
    PLUGIN / "assets" / "axiom-composer.svg",
]

for path in required:
    check(path.is_file(), f"required file exists: {path.relative_to(ROOT)}")

manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
compat = load_json(PLUGIN / "plugin.json")
marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")

check(manifest.get("name") == "axiom", "Codex manifest name is axiom")
check(compat.get("name") == "axiom", "compatibility manifest name is axiom")
check(manifest.get("version") == compat.get("version"), "manifest versions match")

check(manifest.get("version") == "0.1.2", "manifest version is 0.1.2")
check(bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(manifest.get("version", "")))),
      "version is semantic")
check(manifest.get("skills") == "./skills/", "skills path is ./skills/")

author = manifest.get("author", {})
check(isinstance(author, dict) and bool(author.get("name")), "manifest author is present")

interface = manifest.get("interface", {})
check(isinstance(interface, dict), "manifest interface is an object")
check(interface.get("displayName") == "Axiom", "display name is Axiom")
check(len(str(interface.get("shortDescription", ""))) <= 30, "short description fits directory limit")
check(interface.get("category") == "Developer Tools", "category is Developer Tools")
check(isinstance(interface.get("defaultPrompt"), list) and len(interface.get("defaultPrompt", [])) <= 3,
      "defaultPrompt contains at most three prompts")
for prompt in interface.get("defaultPrompt", []):
    check(len(prompt) <= 128 and "\n" not in prompt, f"default prompt fits limit: {prompt[:32]}")

for field in ("logo", "composerIcon"):
    value = interface.get(field)
    check(isinstance(value, str) and value.startswith("./"), f"{field} uses a relative asset path")
    if isinstance(value, str):
        asset = PLUGIN / value[2:]
        check(asset.is_file(), f"{field} asset exists")

plugins = marketplace.get("plugins", [])
check(marketplace.get("name") == "axiom-local", "marketplace name is axiom-local")
check(len(plugins) == 1 and plugins[0].get("name") == "axiom", "marketplace exposes axiom")
if plugins:
    check(plugins[0].get("source", {}).get("path") == "./plugins/axiom",
          "marketplace source points to ./plugins/axiom")

skill_text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
check(frontmatter is not None, "SKILL.md has YAML frontmatter")
if frontmatter:
    fm = frontmatter.group(1)
    check(re.search(r"^name:\s*axiom\s*$", fm, re.MULTILINE) is not None,
          "skill name is axiom")
    description_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
    check(description_match is not None and len(description_match.group(1).strip()) <= 1024,
          "skill description is present and within limit")

openai_yaml = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
check(re.search(r"allow_implicit_invocation:\s*true", openai_yaml) is not None,
      "implicit invocation is explicitly enabled")
check(re.search(r"products:\s*\n\s*-\s*CODEX", openai_yaml) is not None,
      "skill is scoped to CODEX")

combined = "\n".join(
    p.read_text(encoding="utf-8")
    for p in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
)
for required_text in (
    'gpt-5.6-luna',
    'reasoning_effort = "max"',
    'gpt-5.6-sol',
    'reasoning_effort = "xhigh"',
    'fork_turns = "none"',
    'Finding Freeze',
):
    check(required_text in combined, f"guidance contains {required_text}")

check("Never substitute Luna as the reviewer" in skill_text,
      "main skill forbids Luna reviewer")
check("Custom agents: do not install or depend on them" in skill_text,
      "main skill forbids custom-agent dependency")
check("same reviewer" in combined.lower(),
      "guidance requires same-reviewer continuity for re-review")
check("no arbitrary finding-count or round-count cap" in combined.lower() or
      "no arbitrary finding-count limit and no arbitrary review-round limit" in combined.lower(),
      "guidance rejects arbitrary review caps")
for forbidden_review_rule in (
    "Maximum five findings",
    "Default maximum: two review rounds",
    "VERDICT: SHIP | FIX_FIRST | RETHINK",
    "[CRITICAL|MAJOR]",
):
    check(forbidden_review_rule not in combined, f"removed rigid review schema/cap: {forbidden_review_rule}")

for forbidden_workflow_text in (
    "## Default decision process",
    "Every delegated task must be self-contained",
    "workers do not commit",
    "send a follow-up only when",
):
    check(forbidden_workflow_text not in combined, f"removed rigid workflow rule: {forbidden_workflow_text}")

check("## Three kinds of guidance" in skill_text, "main skill distinguishes constraints/defaults/heuristics")
config_text = (PLUGIN / "config" / "codex-0.147.example.toml").read_text(encoding="utf-8")
check("default_wait_timeout_ms = 3600000" in config_text, "v0.147 default wait timeout is configured to 60 minutes")
check("max_wait_timeout_ms = 3600000" in config_text, "v0.147 max wait timeout is configured to 60 minutes")
check("wait_agent(timeout_ms = 3600000)" in combined, "guidance explicitly uses a 60-minute wait_agent timeout")
check(not list((SKILL / "agents").glob("*.toml")),
      "no custom agent TOML is bundled")

for ref in (
    "delegation.md",
    "codex-0.147-subagents.md",
    "review.md",
    "context-management.md",
    "git.md",
):
    check(f"references/{ref}" in skill_text, f"SKILL links {ref}")

for svg_path in (PLUGIN / "assets").glob("*.svg"):
    try:
        root = ET.parse(svg_path).getroot()
        check(root.tag.endswith("svg"), f"{svg_path.name} has an svg root")
        check(bool(root.attrib.get("viewBox") or (root.attrib.get("width") and root.attrib.get("height"))),
              f"{svg_path.name} declares dimensions")
    except Exception as exc:
        errors.append(f"{svg_path.relative_to(ROOT)}: invalid SVG: {exc}")

for path in ROOT.rglob("*"):
    if path.is_file() and path.suffix.lower() in {".md", ".json", ".yaml", ".toml", ".py", ".yml"}:
        text = path.read_text(encoding="utf-8")
        placeholder_marker = "TODO" + "_PLACEHOLDER"
        check(placeholder_marker not in text, f"no placeholder in {path.relative_to(ROOT)}")

if errors:
    print("Axiom validation FAILED")
    for item in errors:
        print(f"  ERROR: {item}")
    print(f"\nPassed checks: {len(checks)}")
    sys.exit(1)

print(f"Axiom validation PASSED ({len(checks)} checks)")
