from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
CORE_SKILL = PLUGIN / "skills" / "axiom"
DASHBOARD_SKILL = PLUGIN / "skills" / "axiom-dashboard"
DASHBOARD = PLUGIN / "dashboard"


class AxiomPluginTests(unittest.TestCase):
    def test_validator(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "validate_plugin.py")],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_and_marketplace_names(self) -> None:
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "axiom")
        self.assertEqual(manifest["version"], "0.1.4")
        self.assertEqual(marketplace["plugins"][0]["name"], "axiom")

    def test_core_is_proactive_dashboard_is_explicit(self) -> None:
        core = (CORE_SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        dashboard = (DASHBOARD_SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", core)
        self.assertIn("allow_implicit_invocation: false", dashboard)

    def test_direct_spawn_roles(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [CORE_SKILL / "SKILL.md", *sorted((CORE_SKILL / "references").glob("*.md"))]
        )
        self.assertIn('model = "gpt-5.6-luna"', text)
        self.assertIn('reasoning_effort = "max"', text)
        self.assertIn('model = "gpt-5.6-sol"', text)
        self.assertIn('reasoning_effort = "xhigh"', text)
        self.assertIn('fork_turns = "none"', text)

    def test_review_continuity_without_numeric_caps(self) -> None:
        text = (CORE_SKILL / "references" / "review.md").read_text(encoding="utf-8")
        self.assertIn("same reviewer agent", text.lower())
        self.assertIn("no fixed finding count", text.lower())
        self.assertIn("no fixed review-round limit", text.lower())
        self.assertNotIn("Maximum five findings", text)
        self.assertNotIn("Default maximum: two review rounds", text)

    def test_proactive_parallel_luna_fleet(self) -> None:
        skill = (CORE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (CORE_SKILL / "references" / "delegation.md").read_text(encoding="utf-8")
        combined = (skill + "\n" + delegation).lower()
        self.assertIn("prefer parallel luna", combined)
        self.assertIn("spawn the independent luna workers before waiting", combined)
        self.assertIn("no fixed worker count", combined)
        self.assertIn("do not split", combined)

    def test_luna_worker_economics_are_explicit(self) -> None:
        skill = (CORE_SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (CORE_SKILL / "references" / "delegation.md").read_text(encoding="utf-8")
        combined = (skill + "\n" + delegation).lower()
        self.assertIn("luna compute is almost free", combined)
        self.assertIn("main context is expensive", combined)
        self.assertIn("do not avoid a useful luna spawn", combined)
        self.assertIn("do not keep such work in main merely to save luna usage", combined)
        self.assertIn("coordination", combined)
        self.assertIn("integration", combined)

    def test_no_custom_agent_toml(self) -> None:
        self.assertEqual(list((CORE_SKILL / "agents").glob("*.toml")), [])

    def test_dashboard_is_read_only_observation_plane(self) -> None:
        skill = (DASHBOARD_SKILL / "SKILL.md").read_text(encoding="utf-8")
        git_source = (DASHBOARD / "src" / "git.rs").read_text(encoding="utf-8").lower()
        self.assertIn("observation plane, not a control plane", skill)
        self.assertIn("Do not modify the target repository", skill)
        for command in ("git reset", "git checkout", "git clean", "git commit", "git add"):
            self.assertNotIn(command, git_source)

    def test_dashboard_web_bundle_is_local_and_embedded(self) -> None:
        main = (DASHBOARD / "src" / "main.rs").read_text(encoding="utf-8")
        index = (DASHBOARD / "web" / "dist" / "index.html").read_text(encoding="utf-8")
        app = (DASHBOARD / "web" / "dist" / "app.js").read_text(encoding="utf-8")
        self.assertIn("include_str!", main)
        self.assertIn("/vendor/react.production.min.js", index)
        self.assertNotIn("https://", index + app)
        self.assertNotIn("http://", index + app)

    def test_release_packager_creates_plugin_and_source_archives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(ROOT / "tools" / "package_release.py"), "--output", tmp],
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            plugin_zip = Path(tmp) / "axiom-v0.1.4-plugin.zip"
            source_zip = Path(tmp) / "axiom-codex-plugin-v0.1.4-source.zip"
            self.assertTrue(plugin_zip.is_file())
            self.assertTrue(source_zip.is_file())
            with zipfile.ZipFile(plugin_zip) as archive:
                names = set(archive.namelist())
                self.assertIn("axiom/.codex-plugin/plugin.json", names)
                self.assertIn("axiom/dashboard/Cargo.toml", names)
                self.assertIn("axiom/dashboard/web/dist/index.html", names)
                self.assertIn("axiom/dashboard/web/dist/app.js", names)
                self.assertIn("axiom/dashboard/web/dist/styles.css", names)
                self.assertIn("axiom/dashboard/web/dist/vendor/react.production.min.js", names)
                self.assertIn("axiom/skills/axiom-dashboard/SKILL.md", names)
                self.assertFalse(any("/target/" in name or "/node_modules/" in name for name in names))


if __name__ == "__main__":
    unittest.main()
