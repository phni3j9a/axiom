#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import stat
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
CORE_SKILL = PLUGIN / "skills" / "axiom"
DASHBOARD_SKILL = PLUGIN / "skills" / "axiom-dashboard"
DASHBOARD = PLUGIN / "dashboard"
WEB = DASHBOARD / "web"
EXPECTED_VERSION = "0.1.3"

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
    DASHBOARD_SKILL / "SKILL.md",
    DASHBOARD_SKILL / "agents" / "openai.yaml",
    DASHBOARD_SKILL / "references" / "setup.md",
    DASHBOARD / "Cargo.toml",
    DASHBOARD / "src" / "main.rs",
    DASHBOARD / "src" / "model.rs",
    DASHBOARD / "src" / "trace.rs",
    DASHBOARD / "src" / "git.rs",
    DASHBOARD / "launch" / "axiom-dashboard.sh",
    DASHBOARD / "launch" / "axiom-dashboard.ps1",
    WEB / "src" / "app.ts",
    WEB / "dist" / "index.html",
    WEB / "dist" / "app.js",
    WEB / "dist" / "styles.css",
    WEB / "dist" / "vendor" / "react.production.min.js",
    WEB / "dist" / "vendor" / "react-dom.production.min.js",
    WEB / "dist" / "vendor" / "REACT-LICENSE.txt",
]
for path in required_files:
    check(path.is_file(), f"required file exists: {path.relative_to(ROOT)}")

manifest = load_json(PLUGIN / ".codex-plugin" / "plugin.json")
compat = load_json(PLUGIN / "plugin.json")
marketplace = load_json(ROOT / ".agents" / "plugins" / "marketplace.json")

check(manifest.get("name") == "axiom", "Codex manifest name is axiom")
check(compat.get("name") == "axiom", "compatibility manifest name is axiom")
check(manifest.get("version") == compat.get("version"), "manifest versions match")
check(manifest.get("version") == EXPECTED_VERSION, f"manifest version is {EXPECTED_VERSION}")
check(
    bool(re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(manifest.get("version", "")))),
    "version is semantic",
)
check(manifest.get("skills") == "./skills/", "skills path is ./skills/")
check("dashboard" in manifest.get("keywords", []), "manifest advertises dashboard")
check("observability" in manifest.get("keywords", []), "manifest advertises observability")

author = manifest.get("author", {})
check(isinstance(author, dict) and bool(author.get("name")), "manifest author is present")

interface = manifest.get("interface", {})
check(isinstance(interface, dict), "manifest interface is an object")
check(interface.get("displayName") == "Axiom", "display name is Axiom")
check(len(str(interface.get("shortDescription", ""))) <= 30, "short description fits directory limit")
check(interface.get("category") == "Developer Tools", "category is Developer Tools")
check(
    isinstance(interface.get("defaultPrompt"), list) and len(interface.get("defaultPrompt", [])) <= 3,
    "defaultPrompt contains at most three prompts",
)
check(
    any("axiom-dashboard" in prompt for prompt in interface.get("defaultPrompt", [])),
    "manifest exposes an explicit dashboard prompt",
)
for prompt in interface.get("defaultPrompt", []):
    check(len(prompt) <= 128 and "\n" not in prompt, f"default prompt fits limit: {prompt[:32]}")

for field in ("logo", "composerIcon"):
    value = interface.get(field)
    check(isinstance(value, str) and value.startswith("./"), f"{field} uses a relative asset path")
    if isinstance(value, str) and value.startswith("./"):
        check((PLUGIN / value[2:]).is_file(), f"{field} asset exists")

plugins = marketplace.get("plugins", [])
check(marketplace.get("name") == "axiom-local", "marketplace name is axiom-local")
check(len(plugins) == 1 and plugins[0].get("name") == "axiom", "marketplace exposes axiom")
if plugins:
    check(
        plugins[0].get("source", {}).get("path") == "./plugins/axiom",
        "marketplace source points to ./plugins/axiom",
    )


def check_skill(skill: Path, name: str, implicit: bool) -> tuple[str, str]:
    skill_text = read(skill / "SKILL.md")
    frontmatter = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    check(frontmatter is not None, f"{name} SKILL.md has YAML frontmatter")
    if frontmatter:
        fm = frontmatter.group(1)
        check(re.search(rf"^name:\s*{re.escape(name)}\s*$", fm, re.MULTILINE) is not None, f"skill name is {name}")
        description_match = re.search(r"^description:\s*(.+)$", fm, re.MULTILINE)
        check(
            description_match is not None and len(description_match.group(1).strip()) <= 1024,
            f"{name} description is present and within limit",
        )
    openai_yaml = read(skill / "agents" / "openai.yaml")
    expected = "true" if implicit else "false"
    check(
        re.search(rf"allow_implicit_invocation:\s*{expected}", openai_yaml) is not None,
        f"{name} implicit invocation is explicitly {expected}",
    )
    check(
        re.search(r"products:\s*\n\s*-\s*CODEX", openai_yaml) is not None,
        f"{name} is scoped to CODEX",
    )
    return skill_text, openai_yaml


core_skill_text, _ = check_skill(CORE_SKILL, "axiom", True)
dashboard_skill_text, _ = check_skill(DASHBOARD_SKILL, "axiom-dashboard", False)

core_combined = "\n".join(
    p.read_text(encoding="utf-8")
    for p in [CORE_SKILL / "SKILL.md", *sorted((CORE_SKILL / "references").glob("*.md"))]
)
for required_text in (
    'gpt-5.6-luna',
    'reasoning_effort = "max"',
    'gpt-5.6-sol',
    'reasoning_effort = "xhigh"',
    'fork_turns = "none"',
    'same reviewer agent',
):
    check(required_text in core_combined, f"guidance contains {required_text}")

check("Never substitute Luna as the reviewer" in core_skill_text, "main skill forbids Luna reviewer")
check("Custom agents: do not install or depend on them" in core_skill_text, "main skill forbids custom-agent dependency")
check("reuse the same reviewer agent" in core_combined.lower(), "guidance requires same-reviewer re-review")
check("no fixed finding count" in core_combined.lower(), "guidance rejects a fixed finding-count cap")
check("no fixed review-round limit" in core_combined.lower(), "guidance rejects a fixed review-round cap")
check("prefer parallel luna" in core_combined.lower(), "guidance prefers proactive parallel Luna workers")
check(
    "spawn the independent luna workers before waiting" in core_combined.lower(),
    "guidance avoids accidental serial worker execution",
)
check("no fixed worker count" in core_combined.lower(), "guidance uses dependency-driven fleet sizing")
check("Maximum five findings" not in core_combined, "legacy maximum-five-findings rule is absent")
check("Default maximum: two review rounds" not in core_combined, "legacy two-round limit is absent")
check(not list((CORE_SKILL / "agents").glob("*.toml")), "no custom agent TOML is bundled")

for ref in ("delegation.md", "codex-0.147-subagents.md", "review.md", "context-management.md", "git.md"):
    check(f"references/{ref}" in core_skill_text, f"SKILL links {ref}")

for required in (
    "observation plane, not a control plane",
    "Do not modify the target repository",
    "Bind to localhost only",
    "Do not add hooks or background daemons",
    "Do not enable telemetry",
    "CODEX_ROLLOUT_TRACE_ROOT",
):
    check(required in dashboard_skill_text, f"dashboard skill preserves boundary: {required}")

cargo = {}
try:
    cargo = tomllib.loads(read(DASHBOARD / "Cargo.toml"))
except Exception as exc:
    errors.append(f"dashboard/Cargo.toml: invalid TOML: {exc}")
check(cargo.get("package", {}).get("name") == "axiom-dashboard", "Rust crate is axiom-dashboard")
check(cargo.get("package", {}).get("version") == "0.1.0", "Dashboard component version is 0.1.0")
for dependency in ("axum", "tokio", "serde", "serde_json", "clap"):
    check(dependency in cargo.get("dependencies", {}), f"Rust crate includes {dependency}")

main_rs = read(DASHBOARD / "src" / "main.rs")
trace_rs = read(DASHBOARD / "src" / "trace.rs")
git_rs = read(DASHBOARD / "src" / "git.rs")
for embedded in (
    '../web/dist/index.html',
    '../web/dist/app.js',
    '../web/dist/styles.css',
    '../web/dist/vendor/react.production.min.js',
    '../web/dist/vendor/react-dom.production.min.js',
):
    check(embedded in main_rs, f"Rust binary embeds {embedded}")
check("is_loopback" in main_rs and "--allow-remote" in main_rs, "server enforces loopback by default")
check("/api/state" in main_rs and "/api/events" in main_rs, "server exposes snapshot and SSE endpoints")
check("Command::new(\"git\")" in git_rs, "Git observer invokes the git executable")
for forbidden in ("git reset", "git checkout", "git clean", "git commit", "git add", "git restore"):
    check(forbidden not in git_rs.lower(), f"Git observer omits write command: {forbidden}")
check("STATE_NAME" in trace_rs and "TRACE_NAME" in trace_rs, "trace reader supports raw and reduced bundles")
check("canonicalize" in trace_rs and "starts_with" in trace_rs, "payload reads are constrained to bundle paths")
check("unknown" in trace_rs, "compliance reports unknown evidence")

index_html = read(WEB / "dist" / "index.html")
app_js = read(WEB / "dist" / "app.js")
styles = read(WEB / "dist" / "styles.css")
app_ts = read(WEB / "src" / "app.ts")
check("/vendor/react.production.min.js" in index_html, "web UI uses vendored React")
check("/api/state" in app_ts and "EventSource" in app_ts, "web UI consumes live local API")
check(len(app_js) > 1000 and len(styles) > 1000, "compiled web bundle is present")
for text, label in ((index_html, "index"), (app_js, "app"), (styles, "styles")):
    check("https://" not in text and "http://" not in text, f"web {label} has no remote runtime dependency")

launcher = DASHBOARD / "launch" / "axiom-dashboard.sh"
if launcher.exists():
    mode = launcher.stat().st_mode
    check(bool(mode & stat.S_IXUSR), "POSIX dashboard launcher is executable")
launcher_text = read(launcher)
check("cargo run" in launcher_text and "dashboard/bin" in launcher_text.replace("$DASHBOARD_DIR/", "dashboard/"), "launcher supports binary and Cargo fallback")

for svg_path in (PLUGIN / "assets").glob("*.svg"):
    try:
        svg_root = ET.parse(svg_path).getroot()
        check(svg_root.tag.endswith("svg"), f"{svg_path.name} has an svg root")
        check(
            bool(svg_root.attrib.get("viewBox") or (svg_root.attrib.get("width") and svg_root.attrib.get("height"))),
            f"{svg_path.name} declares dimensions",
        )
    except Exception as exc:
        errors.append(f"{svg_path.relative_to(ROOT)}: invalid SVG: {exc}")

ignored_dirs = {".git", "target", "node_modules", "dist", "__pycache__"}
text_suffixes = {".md", ".json", ".yaml", ".toml", ".py", ".yml", ".rs", ".ts", ".js", ".css", ".html", ".sh", ".ps1"}
for path in ROOT.rglob("*"):
    if any(part in ignored_dirs for part in path.parts):
        continue
    if path.is_file() and path.suffix.lower() in text_suffixes:
        text = read(path)
        placeholder_marker = "TODO" + "_PLACEHOLDER"
        check(placeholder_marker not in text, f"no placeholder in {path.relative_to(ROOT)}")

if errors:
    print("Axiom validation FAILED")
    for item in errors:
        print(f"  ERROR: {item}")
    print(f"\nPassed checks: {len(checks)}")
    sys.exit(1)

print(f"Axiom validation PASSED ({len(checks)} checks)")

