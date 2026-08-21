#!/usr/bin/env python3
"""Summarise factual signals from one or more Codex rollout JSONL files.

The command is read-only and intentionally does not decide whether a rollout is
good or bad.  Its deterministic JSON output has this small schema::

    {
      "paths": ["..."],
      "sessions": [{"path": "...", "session_id": "...", ...}],
      "first_turn_context": {"model": "..."|null, "effort": "..."|null},
      "timestamp_range": {"first": value|null, "last": value|null},
      "lifecycle": {"task_started": n, "task_complete": n,
                     "turn_aborted": n, "compacted": n},
      "collaboration": {
        "calls": {"spawn_agent": n, "wait_agent": n,
                  "send_message": n, "followup_task": n,
                  "list_agents": n, "interrupt_agent": n},
        "wait_timeout_ms": {"count": n,
                             "distribution": {"1000": n}}
      },
      "open_turn_balance": n
    }

``sessions`` contains one path entry per input; session fields are included
when a ``session_meta`` record provides them.  ``first_turn_context`` is the
first observed ``turn_context`` across the input order.  Timeout distribution
only includes explicit numeric ``timeout_ms`` arguments; encrypted or opaque
message bodies are ignored.  ``open_turn_balance`` is the factual arithmetic
``task_started - task_complete - turn_aborted`` and is not a threshold or gate.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable, Mapping, Sequence


LIFECYCLE_NAMES = ("task_started", "task_complete", "turn_aborted", "compacted")
COLLABORATION_NAMES = (
    "spawn_agent",
    "wait_agent",
    "send_message",
    "followup_task",
    "list_agents",
    "interrupt_agent",
)
SESSION_FIELDS = (
    "session_id",
    "id",
    "cwd",
    "originator",
    "cli_version",
    "source",
    "thread_source",
    "model_provider",
    "agent_path",
    "agent_role",
    "agent_nickname",
    "parent_thread_id",
    "forked_from_id",
    "rollout_path",
)


class RolloutAuditError(Exception):
    """An input could not be read as a rollout JSONL file."""


def _new_counts(names: Iterable[str]) -> dict[str, int]:
    return {name: 0 for name in names}


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, bool)) or (
        isinstance(value, float) and math.isfinite(value)
    )


def _reject_json_constant(value: str) -> None:
    raise ValueError(f"non-standard JSON constant: {value}")


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _payload(record: Mapping[str, Any]) -> Mapping[str, Any]:
    payload = record.get("payload")
    return _mapping(payload)


def _event_kind(record: Mapping[str, Any]) -> str | None:
    record_type = record.get("type")
    payload = _payload(record)
    if record_type == "event_msg":
        kind = payload.get("type")
        return kind if isinstance(kind, str) else None
    if isinstance(record_type, str):
        return record_type
    return None


def _timestamp_key(value: Any) -> tuple[int, float | str]:
    """Return a total-order key while retaining the original JSON value."""

    if isinstance(value, bool):
        return (2, str(value))
    if isinstance(value, (int, float)):
        number = float(value)
        if math.isfinite(number):
            return (0, number)
        return (2, str(value))
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return (1, value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return (0, parsed.timestamp())
    return (2, repr(value))


def _line_timestamp(record: Mapping[str, Any]) -> Any:
    value = record.get("timestamp")
    if _is_scalar(value) and value is not None:
        return value
    payload = _payload(record)
    value = payload.get("timestamp")
    if _is_scalar(value) and value is not None:
        return value
    return None


def _context_from_record(record: Mapping[str, Any]) -> dict[str, Any] | None:
    if record.get("type") != "turn_context":
        return None
    context: Mapping[str, Any] = _payload(record)
    if not context:
        context = _mapping(record.get("turn_context"))
    nested = context.get("context")
    if isinstance(nested, Mapping):
        context = nested

    model = context.get("model")
    if model is None:
        model = context.get("model_name")
    effort = context.get("effort")
    if effort is None:
        effort = context.get("reasoning_effort")
    collaboration_mode = _mapping(context.get("collaboration_mode"))
    settings = _mapping(collaboration_mode.get("settings"))
    if model is None:
        model = settings.get("model")
    if effort is None:
        effort = settings.get("effort")
    if effort is None:
        effort = settings.get("reasoning_effort")
    return {
        "model": model if _is_scalar(model) else None,
        "effort": effort if _is_scalar(effort) else None,
    }


def _session_from_record(path: str, record: Mapping[str, Any]) -> dict[str, Any] | None:
    if record.get("type") != "session_meta":
        return None
    metadata: Mapping[str, Any] = _payload(record)
    nested = metadata.get("meta")
    if isinstance(nested, Mapping):
        # SessionMetaLine is flattened in current Codex rollouts, while a few
        # producers wrap it in ``meta``.  Supporting both costs no message data.
        metadata = nested

    result: dict[str, Any] = {"path": path}
    for field in SESSION_FIELDS:
        value = metadata.get(field)
        if field == "rollout_path" and value is None:
            value = record.get("rollout_path")
        if _is_scalar(value) and value is not None:
            result[field] = value
    if "session_id" not in result and "id" in result:
        result["session_id"] = result["id"]
    return result


def _canonical_call_name(name: Any) -> str | None:
    if not isinstance(name, str):
        return None
    normalized = name.strip().lower()
    for separator in (".", "__", "/"):
        if separator in normalized:
            normalized = normalized.rsplit(separator, 1)[-1]
    aliases = {
        "spawn": "spawn_agent",
        "spawn_agent": "spawn_agent",
        "wait_agent": "wait_agent",
        "send": "send_message",
        "send_input": "send_message",
        "send_message": "send_message",
        "followup": "followup_task",
        "follow_up": "followup_task",
        "followup_task": "followup_task",
        "list": "list_agents",
        "list_agents": "list_agents",
        "interrupt": "interrupt_agent",
        "interrupt_agent": "interrupt_agent",
    }
    return aliases.get(normalized)


def _function_call_from_record(record: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Find the immediate function-call item without walking message bodies."""

    record_type = record.get("type")
    candidates: list[Mapping[str, Any]] = []
    if record_type in {
        "function_call",
        "tool_call",
        "custom_tool_call",
        "response_item",
        "response.output_item.done",
        "response.output_item.added",
    }:
        candidates.append(record)
        for key in ("payload", "item"):
            value = record.get(key)
            if isinstance(value, Mapping):
                candidates.append(value)
                nested_item = value.get("item")
                if isinstance(nested_item, Mapping):
                    candidates.append(nested_item)

    seen: set[int] = set()
    for candidate in candidates:
        identity = id(candidate)
        if identity in seen:
            continue
        seen.add(identity)
        item_type = candidate.get("type")
        if item_type in {"function_call", "tool_call", "custom_tool_call"}:
            if _canonical_call_name(candidate.get("name")) is not None:
                return candidate
    return None


def _call_arguments(call: Mapping[str, Any]) -> Mapping[str, Any]:
    for field in ("arguments", "input", "args"):
        value = call.get(field)
        if isinstance(value, Mapping):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                # Encrypted arguments and redacted bodies are intentionally
                # opaque.  The call itself is still counted.
                continue
            if isinstance(parsed, Mapping):
                return parsed
    if "timeout_ms" in call:
        return call
    return {}


def _timeout_value(value: Any) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if math.isfinite(value) and value.is_integer() else (
            value if math.isfinite(value) else None
        )
    if isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            return None
        if not math.isfinite(number):
            return None
        return int(number) if number.is_integer() else number
    return None


def _timeout_key(value: int | float) -> str:
    return str(value)


def _scan_path(path: Path) -> dict[str, Any]:
    path_text = str(path)
    lifecycle = _new_counts(LIFECYCLE_NAMES)
    calls = _new_counts(COLLABORATION_NAMES)
    timeout_distribution: Counter[str] = Counter()
    session: dict[str, Any] = {"path": path_text}
    first_context: dict[str, Any] = {"model": None, "effort": None}
    context_seen = False
    first_timestamp: tuple[tuple[int, float | str], Any] | None = None
    last_timestamp: tuple[tuple[int, float | str], Any] | None = None
    direct_compacted = 0
    nested_compacted = 0

    try:
        stream = path.open("r", encoding="utf-8")
    except FileNotFoundError as exc:
        raise RolloutAuditError(f"{path_text}: file not found") from exc
    except OSError as exc:
        detail = exc.strerror or "could not read file"
        raise RolloutAuditError(f"{path_text}: {detail}") from exc

    try:
        with stream:
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line, parse_constant=_reject_json_constant)
                except (
                    json.JSONDecodeError,
                    RecursionError,
                    UnicodeDecodeError,
                    ValueError,
                ) as exc:
                    raise RolloutAuditError(
                        f"{path_text}: line {line_number}: malformed JSON"
                    ) from exc
                if not isinstance(record, Mapping):
                    continue

                timestamp = _line_timestamp(record)
                if timestamp is not None:
                    entry = (_timestamp_key(timestamp), timestamp)
                    if first_timestamp is None or entry[0] < first_timestamp[0]:
                        first_timestamp = entry
                    if last_timestamp is None or entry[0] > last_timestamp[0]:
                        last_timestamp = entry

                metadata = _session_from_record(path_text, record)
                if metadata is not None and session == {"path": path_text}:
                    session = metadata

                context = _context_from_record(record)
                if context is not None and not context_seen:
                    first_context = context
                    context_seen = True

                event_kind = _event_kind(record)
                if record.get("type") == "compacted":
                    direct_compacted += 1
                elif event_kind == "compacted":
                    direct_compacted += 1
                elif event_kind == "context_compacted":
                    nested_compacted += 1
                if event_kind in LIFECYCLE_NAMES and event_kind != "compacted":
                    lifecycle[event_kind] += 1

                call = _function_call_from_record(record)
                if call is None:
                    continue
                call_name = _canonical_call_name(call.get("name"))
                if call_name is None:
                    continue
                calls[call_name] += 1
                if call_name == "wait_agent":
                    arguments = _call_arguments(call)
                    timeout = _timeout_value(arguments.get("timeout_ms"))
                    if timeout is not None:
                        timeout_distribution[_timeout_key(timeout)] += 1
    except UnicodeDecodeError as exc:
        raise RolloutAuditError(f"{path_text}: invalid UTF-8") from exc
    except OSError as exc:
        detail = exc.strerror or "could not read file"
        raise RolloutAuditError(f"{path_text}: {detail}") from exc

    lifecycle["compacted"] = direct_compacted or nested_compacted
    return {
        "path": path_text,
        "session": session,
        "context_seen": context_seen,
        "first_context": first_context,
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "lifecycle": lifecycle,
        "calls": calls,
        "timeouts": timeout_distribution,
    }


def _merge_timestamp(
    current: tuple[tuple[int, float | str], Any] | None,
    candidate: tuple[tuple[int, float | str], Any] | None,
    *,
    first: bool,
) -> tuple[tuple[int, float | str], Any] | None:
    if candidate is None:
        return current
    if current is None:
        return candidate
    if first:
        return candidate if candidate[0] < current[0] else current
    return candidate if candidate[0] > current[0] else current


def summarize(paths: Sequence[str | Path]) -> dict[str, Any]:
    """Return the deterministic factual summary for ``paths``."""

    if not paths:
        raise RolloutAuditError("at least one rollout path is required")

    path_texts = [str(path) for path in paths]
    lifecycle = _new_counts(LIFECYCLE_NAMES)
    calls = _new_counts(COLLABORATION_NAMES)
    timeout_distribution: Counter[str] = Counter()
    sessions: list[dict[str, Any]] = []
    first_context = {"model": None, "effort": None}
    context_seen = False
    first_timestamp: tuple[tuple[int, float | str], Any] | None = None
    last_timestamp: tuple[tuple[int, float | str], Any] | None = None

    for raw_path in paths:
        scan = _scan_path(Path(raw_path))
        sessions.append(scan["session"])
        for name in LIFECYCLE_NAMES:
            lifecycle[name] += scan["lifecycle"][name]
        for name in COLLABORATION_NAMES:
            calls[name] += scan["calls"][name]
        timeout_distribution.update(scan["timeouts"])
        if not context_seen and scan["context_seen"]:
            first_context = scan["first_context"]
            context_seen = True
        first_timestamp = _merge_timestamp(
            first_timestamp, scan["first_timestamp"], first=True
        )
        last_timestamp = _merge_timestamp(
            last_timestamp, scan["last_timestamp"], first=False
        )

    return {
        "paths": path_texts,
        "sessions": sessions,
        "first_turn_context": first_context,
        "timestamp_range": {
            "first": first_timestamp[1] if first_timestamp else None,
            "last": last_timestamp[1] if last_timestamp else None,
        },
        "lifecycle": lifecycle,
        "collaboration": {
            "calls": calls,
            "wait_timeout_ms": {
                "count": sum(timeout_distribution.values()),
                "distribution": dict(sorted(timeout_distribution.items())),
            },
        },
        "open_turn_balance": (
            lifecycle["task_started"]
            - lifecycle["task_complete"]
            - lifecycle["turn_aborted"]
        ),
    }


def _parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        description="Report factual metrics from Codex rollout JSONL files (read-only).",
        epilog=(
            "Output is deterministic JSON. It reports observations only; it does not "
            "enforce a policy or block a turn."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    parser.add_argument("rollouts", nargs="+", metavar="ROLLOUT.jsonl")
    args = parser.parse_args(argv)
    try:
        summary = summarize(args.rollouts)
    except RolloutAuditError as exc:
        print(f"audit_rollout.py: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            summary,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
