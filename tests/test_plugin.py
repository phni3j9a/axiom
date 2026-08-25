from __future__ import annotations

import json
import re
import subprocess
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
CORE_SKILL = PLUGIN / "skills" / "axiom"


class AxiomPluginTests(unittest.TestCase):
    def test_validator(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "validate_plugin.py")],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_and_marketplace_identity_and_version(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        compat = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["name"], "axiom")
        self.assertEqual(manifest["version"], "0.1.8")
        self.assertEqual(compat["name"], "axiom")
        self.assertEqual(compat["version"], "0.1.8")
        self.assertEqual(marketplace["plugins"][0]["name"], "axiom")

    def test_codex_0147_hotfix_config_and_docs(self) -> None:
        unsafe_assignment = re.compile(
            r'''(?mx)
            ^[ \t]*
            (?:(?:["']?features["']?)[ \t]*\.[ \t]*
               (?:["']?multi_agent_v2["']?)[ \t]*\.[ \t]*)?
            (?:["']?hide_spawn_agent_metadata["']?)[ \t]*=
            '''
        )
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
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(
                unsafe_assignment.search(text),
                f"unsafe assignment remains in {path.relative_to(ROOT)}",
            )

        for unsafe in (
            "hide_spawn_agent_metadata = false",
            '"hide_spawn_agent_metadata" = false',
            "features.multi_agent_v2.hide_spawn_agent_metadata = false",
            '"features"."multi_agent_v2"."hide_spawn_agent_metadata" = false',
        ):
            with self.subTest(unsafe=unsafe):
                self.assertIsNotNone(unsafe_assignment.search(unsafe))
        for safe in (
            "# hide_spawn_agent_metadata = false",
            "Delete `hide_spawn_agent_metadata = false` when upgrading.",
        ):
            with self.subTest(safe=safe):
                self.assertIsNone(unsafe_assignment.search(safe))

        config = tomllib.loads(
            (PLUGIN / "config" / "codex-0.147.example.toml").read_text(
                encoding="utf-8"
            )
        )
        values = config["features"]["multi_agent_v2"]
        self.assertIs(values["enabled"], True)
        self.assertIs(values["expose_spawn_agent_model_overrides"], True)
        self.assertIs(values["wait_agent_enabled"], True)
        self.assertIs(type(values["default_wait_timeout_ms"]), int)
        self.assertEqual(values["default_wait_timeout_ms"], 3_600_000)
        self.assertIs(type(values["max_wait_timeout_ms"]), int)
        self.assertEqual(values["max_wait_timeout_ms"], 3_600_000)
        self.assertNotIn("hide_spawn_agent_metadata", values)

    def test_core_is_proactive(self) -> None:
        core = (CORE_SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", core)

    def test_removed_runtime_is_absent(self) -> None:
        self.assertFalse((PLUGIN / "dashboard").exists())
        self.assertFalse((PLUGIN / "skills" / "axiom-dashboard").exists())
        self.assertFalse((ROOT / "VALIDATION_REPORT.md").exists())
        self.assertEqual(list(PLUGIN.rglob("Cargo.toml")), [])
        self.assertEqual(list(PLUGIN.rglob("package.json")), [])
        self.assertEqual(list(PLUGIN.rglob("*.rs")), [])
        self.assertEqual(list(PLUGIN.rglob("*.ts")), [])

    def test_manifests_do_not_advertise_removed_runtime(self) -> None:
        for path in (
            PLUGIN / ".codex-plugin" / "plugin.json",
            PLUGIN / "plugin.json",
        ):
            text = path.read_text(encoding="utf-8").lower()
            for term in (
                "dashboard",
                "axiom-dashboard",
                "observability",
                "rollout-trace",
            ):
                self.assertNotIn(term, text)

    def test_direct_spawn_roles(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [
                CORE_SKILL / "SKILL.md",
                *sorted((CORE_SKILL / "references").glob("*.md")),
            ]
        )
        self.assertIn('model = "gpt-5.6-luna"', text)
        self.assertIn('reasoning_effort = "max"', text)
        self.assertIn('model = "gpt-5.6-sol"', text)
        self.assertIn('reasoning_effort = "xhigh"', text)
        self.assertIn('fork_turns = "none"', text)

    def test_design_sensitive_work_uses_sol_max_without_stealing_review(self) -> None:
        skill = (CORE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (CORE_SKILL / "references" / "delegation.md").read_text(
            encoding="utf-8"
        )
        subagents = (
            CORE_SKILL / "references" / "codex-0.147-subagents.md"
        ).read_text(encoding="utf-8")
        combined = "\n".join((skill, delegation, subagents))

        self.assertIn("Design worker: `gpt-5.6-sol` / `max`", skill)
        self.assertIn("## Sol MAX design worker", subagents)
        self.assertIn('task_name = "design_sensitive_interface_work"', subagents)
        self.assertIn('model = "gpt-5.6-sol"', subagents)
        self.assertIn('reasoning_effort = "max"', subagents)
        self.assertIn(
            "Do not route work to Sol merely because it touches frontend files",
            combined,
        )
        self.assertIn(
            "never reuse a design worker as the independent reviewer",
            combined.lower(),
        )
        self.assertIn("## Sol XHIGH reviewer", subagents)
        self.assertIn('reasoning_effort = "xhigh"', subagents)

    def test_runtime_routing_evidence_is_required(self) -> None:
        text = (
            CORE_SKILL / "references" / "codex-0.147-subagents.md"
        ).read_text(encoding="utf-8")
        self.assertIn("requested `spawn_agent` args", text)
        self.assertIn("`turn_context` model/effort", text)
        self.assertIn("`task_complete` event", text)
        self.assertIn("Never rely on a child's self-report alone", text)

    def test_review_continuity_without_numeric_caps(self) -> None:
        text = (CORE_SKILL / "references" / "review.md").read_text(encoding="utf-8")
        self.assertIn("same reviewer agent", text.lower())
        self.assertIn("not an automatic reset rule", text.lower())
        self.assertIn("does not set the user's risk tolerance", text.lower())
        self.assertIn("re-adjudicates", text.lower())
        self.assertIn("no fixed finding count", text.lower())
        self.assertIn("no fixed review-round limit", text.lower())
        self.assertNotIn("Maximum five findings", text)
        self.assertNotIn("Default maximum: two review rounds", text)

    def test_lifecycle_and_waiting_guidance_preserves_main_judgment(self) -> None:
        subagents = (
            CORE_SKILL / "references" / "codex-0.147-subagents.md"
        ).read_text(encoding="utf-8")
        context = (
            CORE_SKILL / "references" / "context-management.md"
        ).read_text(encoding="utf-8")
        self.assertIn("one child turn returned", subagents)
        self.assertIn("does not imply that Main accepted the work", subagents)
        self.assertIn("Polling cadence remains task-specific", subagents)
        self.assertIn("context-cost heuristic, not an ownership rule", context)
        self.assertIn("The right cadence depends on the task", context)

        trace_evals = (ROOT / "docs" / "TRACE_EVALS.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("diagnostic, not gates", trace_evals)
        self.assertIn("no single count", trace_evals)
        self.assertIn("does not modify sessions", trace_evals)

    def test_proactive_parallel_luna_fleet(self) -> None:
        skill = (CORE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (CORE_SKILL / "references" / "delegation.md").read_text(
            encoding="utf-8"
        )
        combined = (skill + "\n" + delegation).lower()
        self.assertIn("prefer parallel luna", combined)
        self.assertIn("spawn the independent luna workers before waiting", combined)
        self.assertIn("no fixed worker count", combined)
        self.assertIn("do not split", combined)

    def test_luna_worker_economics_are_explicit(self) -> None:
        skill = (CORE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (CORE_SKILL / "references" / "delegation.md").read_text(
            encoding="utf-8"
        )
        combined = (skill + "\n" + delegation).lower()
        self.assertIn("luna compute is almost free", combined)
        self.assertIn("main context is expensive", combined)
        self.assertIn("do not avoid a useful luna spawn", combined)
        self.assertIn(
            "do not keep such work in main merely to save luna usage", combined
        )
        self.assertIn("coordination", combined)
        self.assertIn("integration", combined)

    def test_no_custom_agent_toml(self) -> None:
        self.assertEqual(list((CORE_SKILL / "agents").glob("*.toml")), [])

    def test_core_only_ci_and_packager(self) -> None:
        release = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8"
        )
        validate = (ROOT / ".github" / "workflows" / "validate.yml").read_text(
            encoding="utf-8"
        )
        packager = (ROOT / "tools" / "package_release.py").read_text(
            encoding="utf-8"
        )
        for text in (release, validate, packager):
            self.assertNotIn("dashboard-binaries", text)
            self.assertNotIn("require-dashboard-binaries", text)
        self.assertNotIn("rust-toolchain", release + validate)
        self.assertNotIn("setup-node", validate)
        self.assertNotIn("cargo ", release + validate)
        self.assertNotIn("npm ", validate)

    def test_release_packager_creates_core_only_archives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    "python3",
                    str(ROOT / "tools" / "package_release.py"),
                    "--output",
                    tmp,
                ],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plugin_zip = Path(tmp) / "axiom-v0.1.8-plugin.zip"
            source_zip = Path(tmp) / "axiom-codex-plugin-v0.1.8-source.zip"
            self.assertTrue(plugin_zip.is_file())
            self.assertTrue(source_zip.is_file())
            with zipfile.ZipFile(plugin_zip) as archive:
                names = set(archive.namelist())
                self.assertIn("axiom/.codex-plugin/plugin.json", names)
                self.assertIn("axiom/skills/axiom/SKILL.md", names)
                lowered = {name.lower() for name in names}
                self.assertFalse(any("dashboard" in name for name in lowered))
                self.assertFalse(
                    any(
                        name.endswith(("cargo.toml", "cargo.lock", "package.json"))
                        for name in lowered
                    )
                )
                self.assertFalse(
                    any(
                        "/target/" in name
                        or "/node_modules/" in name
                        or "/web/" in name
                        for name in lowered
                    )
                )


if __name__ == "__main__":
    unittest.main()
