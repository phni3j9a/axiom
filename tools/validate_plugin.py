#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
CORE_SKILL = PLUGIN / "skills" / "axiom"
REMOVED_DASHBOARD_PATHS = (
    PLUGIN / "dashboard",
    PLUGIN / "skills" / "axiom-dashboard",
)
CONFIG_EXAMPLE = PLUGIN / "config" / "codex-0.147.example.toml"
TRACE_EVALS = ROOT / "docs" / "TRACE_EVALS.md"
ROLLOUT_AUDIT = CORE_SKILL / "scripts" / "audit_rollout.py"
HIDE_SPAWN_AGENT_METADATA_ASSIGNMENT = re.compile(
    r'''(?mx)
    ^[ \t]*
    (?:(?:["']?features["']?)[ \t]*\.[ \t]*
       (?:["']?multi_agent_v2["']?)[ \t]*\.[ \t]*)?
    (?:["']?hide_spawn_agent_metadata["']?)[ \t]*=
    '''
)
EXPECTED_CONFIG_VALUES = {
    "enabled": True,
    "expose_spawn_agent_model_overrides": True,
    "wait_agent_enabled": True,
    "default_wait_timeout_ms": 3_600_000,
    "max_wait_timeout_ms": 3_600_000,
}
EXPECTED_VERSION = "0.1.8"
FORBIDDEN_MANIFEST_TERMS = (
    "dashboard",
    "axiom-dashboard",
    "observability",
    "rollout-trace",
)

errors: list[str] = []
checks: list[str] = []


def check(condition: bool, message: str) -> None:
    if condition:
        checks.append(message)
    else:
        errors.append(message)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: invalid JSON: {exc}")
        return {}


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        errors.append(f"{path.relative_to(ROOT)}: could not read: {exc}")
        return ""


required_files = [
    PLUGIN / ".codex-plugin" / "plugin.json",
    PLUGIN / "plugin.json",
    CORE_SKILL / "SKILL.md",
    CORE_SKILL / "agents" / "openai.yaml",
    CORE_SKILL / "references" / "delegation.md",
    CORE_SKILL / "references" / "codex-0.147-subagents.md",
    CORE_SKILL / "references" / "review.md",
    CORE_SKILL / "references" / "context-management.md",
    CORE_SKILL / "references" / "git.md",
    CONFIG_EXAMPLE,
    TRACE_EVALS,
    ROLLOUT_AUDIT,
]
for path in required_files:
    check(path.is_file(), f"required file exists: {path.relative_to(ROOT)}")

for path in REMOVED_DASHBOARD_PATHS:
    check(not path.exists(), f"removed path remains absent: {path.relative_to(ROOT)}")

check(not list(PLUGIN.rglob("Cargo.toml")), "plugin contains no Cargo manifest")
check(not list(PLUGIN.rglob("Cargo.lock")), "plugin contains no Cargo lockfile")
check(not list(PLUGIN.rglob("package.json")), "plugin contains no Node package manifest")
check(not list(PLUGIN.rglob("tsconfig*.json")), "plugin contains no TypeScript configuration")
check(not list(PLUGIN.rglob("*.rs")), "plugin contains no Rust source")
check(not list(PLUGIN.rglob("*.ts")), "plugin contains no TypeScript source")
check(not list(PLUGIN.rglob("*.tsx")), "plugin contains no TSX source")

manifest_path = PLUGIN / ".codex-plugin" / "plugin.json"
compat_path = PLUGIN / "plugin.json"
manifest = load_json(manifest_path)
compat = load_json(compat_path)
marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")

check(manifest.get("name") == "axiom", "Codex manifest name is axiom")
check(compat.get("name") == "axiom", "compatibility manifest name is axiom")
check(manifest.get("version") == compat.get("version"), "manifest versions match")
check(manifest.get("version") == EXPECTED_VERSION, f"manifest version is {EXPECTED_VERSION}")
check(
    bool(
        re.fullmatch(
            r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?",
            str(manifest.get("version", "")),
        )
    ),
    "version is semantic",
)
check(manifest.get("skills") == "./skills/", "skills path is ./skills/")

for path, data in ((manifest_path, manifest), (compat_path, compat)):
    serialized = json.dumps(data, ensure_ascii=False).lower()
    for term in FORBIDDEN_MANIFEST_TERMS:
        check(
            term not in serialized,
            f"{path.relative_to(ROOT)} omits removed metadata: {term}",
        )

author = manifest.get("author", {})
check(isinstance(author, dict) and bool(author.get("name")), "manifest author is present")

interface = manifest.get("interface", {})
check(isinstance(interface, dict), "manifest interface is an object")
check(interface.get("displayName") == "Axiom", "display name is Axiom")
check(
    len(str(interface.get("shortDescription", ""))) <= 30,
    "short description fits directory limit",
)
check(interface.get("category") == "Developer Tools", "category is Developer Tools")
prompts = interface.get("defaultPrompt", [])
check(
    isinstance(prompts, list) and len(prompts) <= 3,
    "defaultPrompt contains at most three prompts",
)
if not isinstance(prompts, list):
    prompts = []
for prompt in prompts:
    check(
        isinstance(prompt, str) and len(prompt) <= 128 and "\n" not in prompt,
        f"default prompt fits limit: {str(prompt)[:32]}",
    )

for field in ("logo", "composerIcon"):
    value = interface.get(field)
    check(
        isinstance(value, str) and value.startswith("./"),
        f"{field} uses a relative asset path",
    )
    if isinstance(value, str) and value.startswith("./"):
        check((PLUGIN / value[2:]).is_file(), f"{field} asset exists")

plugins = marketplace.get("plugins", [])
check(marketplace.get("name") == "axiom-local", "marketplace name is axiom-local")
check(
    len(plugins) == 1 and plugins[0].get("name") == "axiom",
    "marketplace exposes axiom",
)
if plugins:
    check(
        plugins[0].get("source", {}).get("path") == "./plugins/axiom",
        "marketplace source points to ./plugins/axiom",
    )


def check_skill(skill: Path, name: str, implicit: bool) -> str:
    skill_text = read(skill / "SKILL.md")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    check(frontmatter is not None, f"{name} SKILL.md has YAML frontmatter")
    if frontmatter:
        fm = frontmatter.group(1)
        check(
            re.search(rf"^name:\s*{re.escape(name)}\s*$", fm, re.MULTILINE)
            is not None,
            f"skill name is {name}",
        )
        description_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        check(
            description_match is not None
            and len(description_match.group(1).strip()) <= 1024,
            f"{name} description is present and within limit",
        )
    openai_yaml = read(skill / "agents" / "openai.yaml")
    expected = "true" if implicit else "false"
    check(
        re.search(rf"allow_implicit_invocation:\s*{expected}", openai_yaml)
        is not None,
        f"{name} implicit invocation is explicitly {expected}",
    )
    check(
        re.search(r"^\s*products:\s*$", openai_yaml, re.MULTILINE) is None,
        f"{name} omits unsupported policy.products",
    )
    return skill_text


core_skill_text = check_skill(CORE_SKILL, "axiom", True)

guidance_paths = sorted(
    {
        ROOT / "README.md",
        ROOT / "DESIGN.md",
        ROOT / "CHANGELOG.md",
        *PLUGIN.glob("*.md"),
        *PLUGIN.glob("config/*.toml"),
        *CORE_SKILL.rglob("*.md"),
    }
)
for path in guidance_paths:
    check(
        HIDE_SPAWN_AGENT_METADATA_ASSIGNMENT.search(read(path)) is None,
        f"{path.relative_to(ROOT)} has no active hide_spawn_agent_metadata assignment",
    )

config_data: dict = {}
if CONFIG_EXAMPLE.is_file():
    config_text = read(CONFIG_EXAMPLE)
    try:
        config_data = tomllib.loads(config_text)
    except tomllib.TOMLDecodeError as exc:
        errors.append(f"{CONFIG_EXAMPLE.relative_to(ROOT)}: invalid TOML: {exc}")

features = config_data.get("features", {})
multi_agent_v2 = features.get("multi_agent_v2", {}) if isinstance(features, dict) else {}
check(
    isinstance(multi_agent_v2, dict),
    "codex-0.147 config has a features.multi_agent_v2 table",
)
for key, expected in EXPECTED_CONFIG_VALUES.items():
    actual = multi_agent_v2.get(key) if isinstance(multi_agent_v2, dict) else None
    check(
        type(actual) is type(expected) and actual == expected,
        f"codex-0.147 config sets {key}={str(expected).lower()}",
    )
check(
    isinstance(multi_agent_v2, dict)
    and "hide_spawn_agent_metadata" not in multi_agent_v2,
    "codex-0.147 config omits hide_spawn_agent_metadata",
)

core_combined = "\n".join(
    path.read_text(encoding="utf-8")
    for path in [
        CORE_SKILL / "SKILL.md",
        *sorted((CORE_SKILL / "references").glob("*.md")),
    ]
)
for required_text in (
    "gpt-5.6-luna",
    'reasoning_effort = "max"',
    "gpt-5.6-sol",
    'reasoning_effort = "xhigh"',
    'fork_turns = "none"',
    "same reviewer agent",
    "requested `spawn_agent` args",
    "`turn_context` model/effort",
    "`task_complete` event",
    "Never rely on a child's self-report alone",
    "not an automatic reset rule",
    "does not set the user's risk tolerance",
    "one child turn returned",
    "Polling cadence remains task-specific",
    "context-cost heuristic, not an ownership rule",
):
    check(required_text in core_combined, f"guidance contains {required_text}")

trace_eval_text = read(TRACE_EVALS)
check(
    "diagnostic, not gates" in trace_eval_text,
    "trace evals are advisory rather than orchestration gates",
)
check(
    "no single count" in trace_eval_text,
    "trace evals avoid fixed metric verdicts",
)

check(
    "Never substitute Luna as the reviewer" in core_skill_text,
    "main skill forbids Luna reviewer",
)
check(
    "Design worker: `gpt-5.6-sol` / `max`" in core_skill_text,
    "main skill routes design-sensitive work to Sol MAX",
)
check(
    "Do not route work to Sol merely because it touches frontend files"
    in core_combined,
    "frontend file ownership alone does not trigger Sol routing",
)
check(
    "never reuse a design worker as the independent reviewer" in core_combined.lower(),
    "design worker remains separate from independent reviewer",
)
check(
    "Custom agents: do not install or depend on them" in core_skill_text,
    "main skill forbids custom-agent dependency",
)
check(
    "reuse the same reviewer agent" in core_combined.lower(),
    "guidance requires same-reviewer re-review",
)
check(
    "no fixed finding count" in core_combined.lower(),
    "guidance rejects a fixed finding-count cap",
)
check(
    "no fixed review-round limit" in core_combined.lower(),
    "guidance rejects a fixed review-round cap",
)
check(
    "prefer parallel luna" in core_combined.lower(),
    "guidance prefers proactive parallel Luna workers",
)
check(
    "spawn the independent luna workers before waiting" in core_combined.lower(),
    "guidance avoids accidental serial worker execution",
)
check(
    "no fixed worker count" in core_combined.lower(),
    "guidance uses dependency-driven fleet sizing",
)
check(
    "main context is expensive; luna compute is almost free"
    in core_combined.lower(),
    "guidance preserves the v0.1.4 Luna economics principle",
)
check(
    "do not avoid a useful luna spawn" in core_combined.lower(),
    "guidance does not conserve Luna usage at Main-context expense",
)
check(
    "luna's token cost by itself is not a reason to stay in main"
    in core_combined.lower(),
    "delegation economics are explicit",
)
check(
    "Maximum five findings" not in core_combined,
    "legacy maximum-five-findings rule is absent",
)
check(
    "Default maximum: two review rounds" not in core_combined,
    "legacy two-round limit is absent",
)
check(
    not list((CORE_SKILL / "agents").glob("*.toml")),
    "no custom agent TOML is bundled",
)

for ref in (
    "delegation.md",
    "codex-0.147-subagents.md",
    "review.md",
    "context-management.md",
    "git.md",
):
    check(f"references/{ref}" in core_skill_text, f"SKILL links {ref}")

for svg_path in (PLUGIN / "assets").glob("*.svg"):
    try:
        svg_root = ET.parse(svg_path).getroot()
        check(svg_root.tag.endswith("svg"), f"{svg_path.name} has an svg root")
        check(
            bool(
                svg_root.attrib.get("viewBox")
                or (
                    svg_root.attrib.get("width")
                    and svg_root.attrib.get("height")
                )
            ),
            f"{svg_path.name} declares dimensions",
        )
    except Exception as exc:
        errors.append(f"{svg_path.relative_to(ROOT)}: invalid SVG: {exc}")

ignored_dirs = {".git", "target", "node_modules", "dist", "__pycache__"}
text_suffixes = {
    ".md",
    ".json",
    ".yaml",
    ".toml",
    ".py",
    ".yml",
    ".sh",
    ".ps1",
}
for path in ROOT.rglob("*"):
    if any(part in ignored_dirs for part in path.parts):
        continue
    if path.is_file() and path.suffix.lower() in text_suffixes:
        text = read(path)
        placeholder_marker = "TODO" + "_PLACEHOLDER"
        check(
            placeholder_marker not in text,
            f"no placeholder in {path.relative_to(ROOT)}",
        )

if errors:
    print("Axiom validation FAILED")
    for item in errors:
        print(f"  ERROR: {item}")
    print(f"\nPassed checks: {len(checks)}")
    sys.exit(1)

print(f"Axiom validation PASSED ({len(checks)} checks)")
