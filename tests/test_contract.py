from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "axiom"
SKILL = PLUGIN / "skills" / "axiom"


class ContractTests(unittest.TestCase):
    def test_single_primary_skill(self):
        skills = list((PLUGIN / "skills").glob("*/SKILL.md"))
        self.assertEqual([p.parent.name for p in skills], ["axiom"])

    def test_no_custom_agent_profiles_or_hooks(self):
        self.assertEqual(list(PLUGIN.rglob("*.toml")), [])
        self.assertFalse((PLUGIN / "hooks").exists())
        self.assertFalse((PLUGIN / ".mcp.json").exists())

    def test_plugin_manifest(self):
        manifest = json.loads((PLUGIN / ".codex-plugin" / "plugin.json").read_text())
        self.assertEqual(manifest["name"], "axiom")
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
        self.assertEqual(manifest["skills"], "./skills/")

    def test_model_contract(self):
        text = "\n".join(p.read_text() for p in [
            SKILL / "SKILL.md",
            SKILL / "references" / "codex-0.147-subagents.md",
            SKILL / "references" / "review.md",
        ])
        self.assertIn("gpt-5.6-luna", text)
        self.assertIn("reasoning_effort: max", text)
        self.assertIn("gpt-5.6-sol", text)
        self.assertIn("reasoning_effort: xhigh", text)
        self.assertIn("fork_turns: none", text)
        self.assertNotRegex(text, re.compile(r"Terra\s+Reviewer", re.I))

    def test_finding_freeze_contract(self):
        review = (SKILL / "references" / "review.md").read_text()
        self.assertIn("Finding Freeze", review)
        self.assertIn("ACCEPT", review)
        self.assertIn("DEFER", review)
        self.assertIn("REJECT", review)
        self.assertIn("Two review rounds are the default ceiling", review)
        self.assertIn("Do not add new general findings in Round 2", review)

    def test_skill_is_implicitly_invokable_but_scoped(self):
        skill = (SKILL / "SKILL.md").read_text()
        self.assertIn("non-trivial software engineering", skill)
        meta = (SKILL / "agents" / "openai.yaml").read_text()
        self.assertIn("allow_implicit_invocation: true", meta)

    def test_v0147_reference_has_schema_guard(self):
        ref = (SKILL / "references" / "codex-0.147-subagents.md").read_text()
        self.assertIn("expose_spawn_agent_model_overrides = true", ref)
        self.assertIn("Do not send undeclared arguments", ref)
        self.assertIn("Do not silently substitute Terra", ref)
        self.assertIn("fork_context is not supported", ref)


if __name__ == "__main__":
    unittest.main()
