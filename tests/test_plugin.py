from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
SKILL = PLUGIN / "skills" / "axiom"


class AxiomPluginTests(unittest.TestCase):
    def test_validator(self) -> None:
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "validate_plugin.py")],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_manifest_and_marketplace_names(self) -> None:
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        marketplace = json.loads(
            (ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["name"], "axiom")
        self.assertEqual(manifest["version"], "0.1.2")
        self.assertEqual(marketplace["plugins"][0]["name"], "axiom")

    def test_proactive_invocation(self) -> None:
        metadata = (SKILL / "agents" / "openai.yaml").read_text(encoding="utf-8")
        self.assertIn("allow_implicit_invocation: true", metadata)

    def test_direct_spawn_roles(self) -> None:
        text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in [SKILL / "SKILL.md", *sorted((SKILL / "references").glob("*.md"))]
        )
        self.assertIn('gpt-5.6-luna', text)
        self.assertIn('reasoning_effort = "max"', text)
        self.assertIn('gpt-5.6-sol', text)
        self.assertIn('reasoning_effort = "xhigh"', text)
        self.assertIn('fork_turns = "none"', text)

    def test_no_custom_agent_toml(self) -> None:
        self.assertEqual(list((SKILL / "agents").glob("*.toml")), [])

    def test_same_reviewer_convergence_without_hard_caps_or_verdict_schema(self) -> None:
        review = (SKILL / "references" / "review.md").read_text(encoding="utf-8")
        self.assertIn("same reviewer agent/session", review)
        self.assertIn("no arbitrary finding-count limit and no arbitrary review-round limit", review)
        self.assertNotIn("VERDICT: SHIP | FIX_FIRST | RETHINK", review)
        self.assertNotIn("[CRITICAL|MAJOR]", review)
        self.assertNotIn("maximum five", review.lower())
        self.assertNotIn("two review rounds", review.lower())

    def test_rigid_workflow_artifacts_removed(self) -> None:
        main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        delegation = (SKILL / "references" / "delegation.md").read_text(encoding="utf-8")
        review = (SKILL / "references" / "review.md").read_text(encoding="utf-8")
        git = (SKILL / "references" / "git.md").read_text(encoding="utf-8")
        subagents = (SKILL / "references" / "codex-0.147-subagents.md").read_text(encoding="utf-8")
        self.assertNotIn("## Default decision process", main)
        self.assertNotIn("Every delegated task must be self-contained", delegation)
        self.assertNotIn("multi-file implementation", review)
        self.assertNotIn("workers do not commit", git)
        self.assertNotIn("send a follow-up only when", subagents)
        self.assertIn("## Three kinds of guidance", main)

    def test_wait_agent_uses_sixty_minute_default(self) -> None:
        config = (PLUGIN / "config" / "codex-0.147.example.toml").read_text(encoding="utf-8")
        subagents = (SKILL / "references" / "codex-0.147-subagents.md").read_text(encoding="utf-8")
        self.assertIn("default_wait_timeout_ms = 3600000", config)
        self.assertIn("max_wait_timeout_ms = 3600000", config)
        self.assertIn("wait_agent(timeout_ms = 3600000)", subagents)


if __name__ == "__main__":
    unittest.main()
