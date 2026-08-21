from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins" / "axiom" / "skills" / "axiom" / "scripts" / "audit_rollout.py"


def load_auditor():
    spec = importlib.util.spec_from_file_location("audit_rollout", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AUDITOR = load_auditor()


def write_rollout(path: Path, records: list[object]) -> None:
    path.write_text(
        "".join(json.dumps(record) + "\n" for record in records),
        encoding="utf-8",
    )


def function_call(name: str, arguments: object) -> dict[str, object]:
    return {
        "timestamp": "2026-08-22T00:00:04Z",
        "type": "response_item",
        "payload": {
            "type": "function_call",
            "name": name,
            "arguments": arguments,
        },
    }


class RolloutAuditTests(unittest.TestCase):
    def test_multi_file_aggregation_and_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.jsonl"
            second = Path(tmp) / "second.jsonl"
            write_rollout(
                first,
                [
                    {
                        "timestamp": "2026-08-22T00:00:00Z",
                        "type": "session_meta",
                        "payload": {
                            "session_id": "session-one",
                            "cwd": "/work/one",
                            "originator": "codex",
                        },
                    },
                    {
                        "timestamp": "2026-08-22T00:00:01Z",
                        "type": "turn_context",
                        "payload": {
                            "model": "gpt-5.6-sol",
                            "effort": "xhigh",
                        },
                    },
                    {
                        "timestamp": "2026-08-22T00:00:02Z",
                        "type": "event_msg",
                        "payload": {"type": "task_started"},
                    },
                    function_call("spawn_agent", {"task_name": "worker"}),
                ],
            )
            write_rollout(
                second,
                [
                    {
                        "timestamp": "2026-08-22T00:00:05Z",
                        "type": "event_msg",
                        "payload": {"type": "task_complete"},
                    },
                    function_call("list_agents", {}),
                ],
            )

            summary = AUDITOR.summarize([first, second])

        self.assertEqual(summary["paths"], [str(first), str(second)])
        self.assertEqual(len(summary["sessions"]), 2)
        self.assertEqual(summary["sessions"][0]["session_id"], "session-one")
        self.assertEqual(summary["sessions"][1], {"path": str(second)})
        self.assertEqual(
            summary["first_turn_context"],
            {"model": "gpt-5.6-sol", "effort": "xhigh"},
        )
        self.assertEqual(
            summary["timestamp_range"],
            {
                "first": "2026-08-22T00:00:00Z",
                "last": "2026-08-22T00:00:05Z",
            },
        )

    def test_lifecycle_and_open_turn_balance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lifecycle.jsonl"
            write_rollout(
                path,
                [
                    {"type": "event_msg", "payload": {"type": "task_started"}},
                    {"type": "event_msg", "payload": {"type": "task_started"}},
                    {"type": "event_msg", "payload": {"type": "task_complete"}},
                    {"type": "event_msg", "payload": {"type": "turn_aborted"}},
                    {"type": "compacted", "payload": {}},
                ],
            )
            summary = AUDITOR.summarize([path])

        self.assertEqual(
            summary["lifecycle"],
            {
                "task_started": 2,
                "task_complete": 1,
                "turn_aborted": 1,
                "compacted": 1,
            },
        )
        self.assertEqual(summary["open_turn_balance"], 0)

    def test_collaboration_calls_timeout_distribution_and_encrypted_body(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "collaboration.jsonl"
            write_rollout(
                path,
                [
                    function_call("spawn_agent", {"task_name": "worker"}),
                    function_call("wait_agent", {"timeout_ms": 30000}),
                    function_call("wait_agent", '{"timeout_ms": 60000}'),
                    function_call(
                        "send_message",
                        {"encrypted_content": "opaque message body"},
                    ),
                    function_call("followup_task", {"target": "worker"}),
                    function_call("interrupt_agent", {"target": "worker"}),
                    function_call("list_agents", {}),
                ],
            )
            summary = AUDITOR.summarize([path])

        self.assertEqual(
            summary["collaboration"]["calls"],
            {
                "spawn_agent": 1,
                "wait_agent": 2,
                "send_message": 1,
                "followup_task": 1,
                "list_agents": 1,
                "interrupt_agent": 1,
            },
        )
        self.assertEqual(
            summary["collaboration"]["wait_timeout_ms"],
            {
                "count": 2,
                "distribution": {"30000": 1, "60000": 1},
            },
        )

    def test_malformed_input_fails_with_concise_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.jsonl"
            path.write_text('{"type":"event_msg"\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path)],
                text=True,
                capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("malformed JSON", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_missing_input_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.jsonl"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(missing)],
                text=True,
                capture_output=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("file not found", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
