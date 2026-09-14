#!/usr/bin/env python3
"""Posthoc, read-only accounting of the separate official-client pilot.

This script never imports the subject adapter, calls a client, or reads credentials.
It reads only explicitly supplied evidence directories and saved sanitized records.
Run without --prefix only after the pilot has terminated and written its final ledger.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any


TOKEN_FIELDS = (
    "inputTokens", "cachedInputTokens", "cacheWriteInputTokens", "outputTokens",
    "reasoningOutputTokens", "totalTokens",
)
PROTOCOL = "codex-subscription-pilot-v8"


def reject_constant(value: str) -> None:
    raise ValueError(f"Nonfinite JSON constant: {value}")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def check_finite(value: Any) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite JSON number, including exponent overflow")
    if isinstance(value, dict):
        for child in value.values():
            check_finite(child)
    elif isinstance(value, list):
        for child in value:
            check_finite(child)


def parse_json(data: bytes | str) -> Any:
    value = json.loads(data, object_pairs_hook=unique_object, parse_constant=reject_constant)
    check_finite(value)
    return value


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def counter_value(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def subtotal(values: list[Any], *, integer: bool = True) -> dict[str, Any]:
    predicate = counter_value if integer else numeric
    known = [value for value in values if predicate(value)]
    return {
        "denominator": len(values),
        "numeric_records": len(known),
        "missing_or_invalid_records": len(values) - len(known),
        "known_only_subtotal": sum(known) if known else None,
        "complete_total": sum(known) if len(known) == len(values) and values else None,
    }


def utc(value: str) -> datetime:
    date = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if date.tzinfo is None:
        raise ValueError("Timestamp lacks timezone")
    return date.astimezone(timezone.utc)


def iso(value: float | None) -> str | None:
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if value is not None else None


def key(row: dict[str, Any]) -> tuple[str, int]:
    run_id, index = row.get("run_id"), row.get("index")
    if not isinstance(run_id, str) or not run_id or not counter_value(index):
        raise ValueError("Evidence row lacks a valid run_id/index")
    return run_id, index


class Evidence:
    def __init__(self, prefix: bool):
        self.prefix = prefix
        self.inputs: list[dict[str, Any]] = []
        self.partial_lines: list[str] = []

    def read(self, path: Path) -> bytes:
        data = path.read_bytes()
        self.inputs.append({"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        return data

    def json(self, path: Path) -> Any:
        return parse_json(self.read(path))

    def jsonl(self, path: Path) -> list[dict[str, Any]]:
        data = self.read(path)
        lines = data.splitlines(keepends=True)
        if self.prefix and lines and not lines[-1].endswith(b"\n"):
            self.partial_lines.append(str(path))
            lines.pop()
        rows = [parse_json(line) for line in lines if line.strip()]
        if not all(isinstance(row, dict) for row in rows):
            raise ValueError(f"Non-object ledger row: {path}")
        return rows


def public_quota(record: dict[str, Any]) -> dict[str, Any] | None:
    """Whitelist passive quota fields; do not retain account identity or credit balances."""
    usage = record.get("preturn_boundary", {}).get("included_usage_check", {})
    limits = usage.get("rateLimits")
    if not isinstance(limits, dict):
        return None
    result: dict[str, Any] = {"plan_type_as_returned": limits.get("planType")}
    for name in ("primary", "secondary"):
        window = limits.get(name)
        result[name] = ({field: window.get(field) if numeric(window.get(field)) else None
                         for field in ("usedPercent", "windowDurationMins", "resetsAt")}
                        if isinstance(window, dict) else None)
    result["ordinary_usage_allowed"] = usage.get("ordinaryUsageAllowed")
    return result


def summarize(pilots: list[Path], global_path: Path, metadata_path: Path, *, prefix: bool) -> dict[str, Any]:
    evidence = Evidence(prefix)
    requests: dict[tuple[str, int], dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    plans: list[dict[str, Any]] = []
    final_ledgers: list[dict[str, Any]] = []
    request_paths: dict[tuple[str, int], str] = {}
    planned_run_ids: set[str] = set()
    for directory in pilots:
        final_path = directory / "usage_failure_ledger.json"
        if not prefix and not final_path.is_file():
            raise ValueError(f"Final pilot ledger absent; use --prefix only for a /tmp snapshot: {directory}")
        plan = evidence.json(directory / "frozen_plan.json")
        if plan.get("protocol_version") != PROTOCOL or plan["config"].get("provider") != "codex_subscription":
            raise ValueError("Only the separate official-client v8 pilot is accepted")
        if plan["config"].get("api_fallback") is not False:
            raise ValueError("API fallback must remain forbidden")
        plans.append(plan)
        # Read episode records for provenance hashing, without copying behavioral outputs.
        if (directory / "runs.jsonl").exists():
            evidence.jsonl(directory / "runs.jsonl")
        if final_path.exists():
            final_ledgers.append(evidence.json(final_path))
        events.extend(evidence.jsonl(directory / "events.jsonl"))
        for path in sorted((directory / "requests").glob("*.json")):
            row = evidence.json(path)
            if row.get("backend") != "codex_subscription" or row.get("transport") != "official_codex_app_server":
                raise ValueError(f"Non-official or mock/API request provenance: {path}")
            if row.get("hidden_reasoning_retained") is not False or row.get("raw_stream_retained") is not False:
                raise ValueError(f"Request does not attest filtered storage: {path}")
            if row.get("model_requested") not in plan["config"]["models"]:
                raise ValueError(f"Requested model differs from frozen selection: {path}")
            if row.get("turn_submission_confirmed") is not True:
                raise ValueError(f"Saved request is not a confirmed full-frame submission: {path}")
            for missing_field in ("monetary_cost_usd", "credit_consumption", "backend_request_count"):
                if row.get(missing_field) is not None:
                    raise ValueError(f"Unexpected telemetry requires explicit accounting review: {missing_field}")
            ident = key(row)
            if ident in requests:
                raise ValueError("Duplicate request across supplied directories")
            requests[ident] = row
            request_paths[ident] = str(path)
        for item in plan.get("planned", []):
            if isinstance(item, dict) and isinstance(item.get("run_id"), str):
                planned_run_ids.add(item["run_id"])

    global_rows = evidence.jsonl(global_path)
    expected_scopes = {plan["config"]["global_allowance_scope"] for plan in plans}
    if len(expected_scopes) != 1:
        raise ValueError("Supplied pilots do not share one authorized allowance scope")
    reservations: dict[str, dict[tuple[str, int], dict[str, Any]]] = {
        "invocation_started": {}, "turn_submitted": {},
    }
    for row in global_rows:
        if row.get("scope") not in expected_scopes or row.get("event") not in reservations:
            raise ValueError("Unexpected scope or event in the global allowance ledger")
        ident = key(row)
        event_type = row["event"]
        if ident in reservations[event_type]:
            raise ValueError("Duplicate global allowance reservation")
        if not numeric(row.get("unix_time")):
            raise ValueError("Invalid global reservation timestamp")
        utc(row["recorded_at_utc"])
        if event_type == "turn_submitted" and ident not in reservations["invocation_started"]:
            raise ValueError("Turn reservation without a prior process reservation")
        reservations[event_type][ident] = row

    event_by_type: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    count_types = {
        "client_invocation_started", "client_invocation_finished", "turn_submission_reserved",
        "turn_submitted_to_official_client", "turn_start_accepted",
    }
    event_counts = Counter()
    failure_events = Counter()
    for row in events:
        event_type = row.get("type")
        if not isinstance(event_type, str):
            raise ValueError("Event type missing")
        event_counts[event_type] += 1
        if event_type in count_types:
            ident = key(row)
            group = event_by_type.setdefault(event_type, {})
            if ident in group:
                raise ValueError(f"Duplicate lifecycle event: {event_type}")
            group[ident] = row
        if event_type in {"pilot_stop", "rpc_failure", "client_error", "forbidden_server_request", "forbidden_native_tool_attempt"}:
            failure_events[event_type] += 1

    process_keys = set(reservations["invocation_started"])
    reserved_keys = set(reservations["turn_submitted"])
    submitted_keys = set(event_by_type.get("turn_submitted_to_official_client", {}))
    accepted_keys = set(event_by_type.get("turn_start_accepted", {}))
    request_keys = set(requests)
    started_keys = set(event_by_type.get("client_invocation_started", {}))
    finished_keys = set(event_by_type.get("client_invocation_finished", {}))
    invariant_errors: list[str] = []
    for condition, message in (
        (reserved_keys <= process_keys, "Turn reservations lack process reservations"),
        (submitted_keys <= reserved_keys, "Confirmed writes lack conservative turn reservations"),
        (accepted_keys <= submitted_keys, "Accepted turns lack confirmed writes"),
        (request_keys <= submitted_keys, "Saved requests lack confirmed write events"),
        (started_keys <= process_keys, "Invocation events lack global reservations"),
        (request_keys == submitted_keys, "Confirmed writes and saved request files differ"),
        (started_keys == process_keys, "Invocation events and global process reservations differ"),
        (set(event_by_type.get("turn_submission_reserved", {})) == reserved_keys, "Local and global turn reservation events differ"),
    ):
        if not condition:
            invariant_errors.append(message)
    for ident, row in requests.items():
        if (row.get("turn_start_accepted") is True) != (ident in accepted_keys):
            invariant_errors.append("Saved turn acceptance differs from lifecycle event")
        if row.get("turn_submission_reserved") is not True or row.get("turn_submitted") is not True:
            invariant_errors.append("Saved request reservation/submission aliases disagree")
    if invariant_errors and not prefix:
        raise ValueError("; ".join(sorted(set(invariant_errors))))

    ordered = sorted(requests.values(), key=lambda row: row["invocation_ordinal"])
    token_summaries = {}
    for group in ("total", "last"):
        token_summaries[group] = {
            field: subtotal([(row.get("usage") or {}).get(group, {}).get(field) for row in ordered])
            for field in TOKEN_FIELDS
        }
    returned = Counter(row["model_returned"] for row in ordered if isinstance(row.get("model_returned"), str) and row["model_returned"])
    known_returned = sum(returned.values())
    runtime_missing = len(ordered) - known_returned
    starts = event_by_type.get("client_invocation_started", {})
    finishes = event_by_type.get("client_invocation_finished", {})
    start_times: list[float] = []
    finish_times: list[float] = []
    durations: list[Any] = []
    for ident in process_keys:
        start = starts.get(ident, {}).get("started_at_utc")
        start_time = utc(start).timestamp() if isinstance(start, str) else None
        duration = finishes.get(ident, {}).get("elapsed_seconds")
        if not numeric(duration):
            duration = requests.get(ident, {}).get("elapsed_seconds")
        durations.append(duration)
        if start_time is not None:
            start_times.append(start_time)
            if numeric(duration):
                finish_times.append(start_time + duration)
    earliest_start = min(start_times) if start_times else None
    latest_finish = max(finish_times) if finish_times else None
    global_times = [row["unix_time"] for row in global_rows]

    preparation = evidence.json(metadata_path)
    metadata_rows = preparation.get("records", [])
    if any(row.get("experimental_turn_submissions") != 0 for row in metadata_rows):
        raise ValueError("Pre-inference metadata ledger unexpectedly reports an experimental turn")
    metadata_summary = {
        "saved_preparation_records": len(metadata_rows),
        "metadata_rpc_attempts": subtotal([row.get("metadata_rpc_attempts") for row in metadata_rows]),
        "metadata_rpc_submissions": subtotal([row.get("metadata_rpc_submissions") for row in metadata_rows]),
        "experimental_turn_submissions": 0,
        "source_artifacts": [row.get("artifact") for row in metadata_rows],
        "note": "Saved preparation metadata only; network metadata is not benchmark inference. Local version/help/login/schema/sandbox diagnostics are separate.",
    }
    request_rpc = {
        field: subtotal([requests.get(ident, {}).get(field) for ident in sorted(process_keys)])
        for field in ("metadata_rpc_attempts", "metadata_rpc_submissions", "cancellation_rpc_attempts", "cancellation_rpc_submissions")
    }
    request_rows = [{
        "source": request_paths[key(row)], "run_id": row["run_id"], "index": row["index"],
        "invocation_ordinal": row["invocation_ordinal"], "kind": row.get("kind"),
        "model_requested": row["model_requested"], "model_returned": row.get("model_returned"),
        "status": row.get("status"), "failure_category": row.get("failure_category"),
        "turn_submission_reserved": row.get("turn_submission_reserved"),
        "turn_submission_confirmed": row.get("turn_submission_confirmed"),
        "turn_start_accepted": row.get("turn_start_accepted"),
        "elapsed_seconds": row.get("elapsed_seconds") if numeric(row.get("elapsed_seconds")) else None,
        "public_thread_total_tokens": (row.get("usage") or {}).get("total", {}).get("totalTokens")
        if counter_value((row.get("usage") or {}).get("total", {}).get("totalTokens")) else None,
    } for row in ordered]
    cap = min(plan["config"]["max_client_invocations"] for plan in plans)
    deadline = min(plan["config"]["inference_wallclock_seconds"] for plan in plans)
    if len(process_keys) > cap or len(reserved_keys) > cap:
        raise ValueError("The global authorized invocation or turn reservation ceiling was exceeded")
    if global_times and max(global_times) - min(global_times) > deadline:
        invariant_errors.append("Global reservation span exceeds the authorized wallclock")
        if not prefix:
            raise ValueError(invariant_errors[-1])
    summary = {
        "schema": "independent-subscription-v8-usage-audit-1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "active_prefix_not_final" if prefix else "final_saved_evidence",
        "protocol_version": PROTOCOL,
        "scope": next(iter(expected_scopes)),
        "pilot_directories": [str(path) for path in pilots],
        "planned_pilot_episodes": sum(len(plan["planned"]) for plan in plans),
        "planned_compatibility_turns": sum(plan["compatibility_turns_planned"] for plan in plans),
        "maximum_planned_benchmark_turns": sum(plan["maximum_benchmark_turns"] for plan in plans),
        "allowance": {
            "process_invocation_ceiling": cap, "turn_reservation_ceiling": cap,
            "wallclock_seconds": deadline, "process_reservations": len(process_keys),
            "turn_reservations": len(reserved_keys),
            "confirmed_full_frame_turn_submissions": len(submitted_keys),
            "accepted_turns": len(accepted_keys),
            "saved_submitted_turn_records": len(requests),
            "process_reservations_without_confirmed_turn": len(process_keys - submitted_keys),
            "turn_reservations_without_confirmed_turn": len(reserved_keys - submitted_keys),
            "confirmed_turns_without_acceptance": len(submitted_keys - accepted_keys),
            "processes_without_finished_event": len(process_keys - finished_keys),
            "note": "Global turn_submitted rows are conservative reservations before writing. Process and turn caps are separate, not added together. A client turn may involve multiple backend requests; startup failures consume the process allowance.",
        },
        "timestamps": {
            "first_global_reservation_utc": iso(min(global_times)) if global_times else None,
            "last_global_reservation_utc": iso(max(global_times)) if global_times else None,
            "global_reservation_span_seconds": max(global_times) - min(global_times) if global_times else None,
            "first_local_invocation_start_utc": iso(earliest_start),
            "last_local_invocation_start_utc": iso(max(start_times)) if start_times else None,
            "last_derived_local_invocation_finish_utc": iso(latest_finish),
            "local_wall_span_seconds": latest_finish - earliest_start if earliest_start is not None and latest_finish is not None else None,
            "invocation_duration_seconds": subtotal(durations, integer=False),
            "invocations_with_start_timestamp": len(start_times),
            "invocations_with_derived_finish_timestamp": len(finish_times),
            "note": "Finish timestamps are derived from saved local starts plus elapsed_seconds. Local timing is not provider billing duration or an acknowledged server-side cancellation time.",
        },
        "public_token_accounting": {
            "saved_turn_denominator": len(ordered),
            "confirmed_turns_missing_saved_usage_record": len(submitted_keys - request_keys),
            "counter_groups": token_summaries,
            "note": "Each saved fresh-thread request contributes its final usage.total once. usage.last is reported separately; groups and overlapping fields must not be added. Numeric reasoning-token counts are public telemetry, not reasoning content. Missing values remain unknown; known-only subtotals are not complete totals when records are missing.",
        },
        "model_identifiers": {
            "requested_identifiers": dict(Counter(row["model_requested"] for row in ordered)),
            "runtime_returned_identifiers": dict(returned),
            "returned_identifier_denominator": len(ordered),
            "returned_identifier_present": known_returned,
            "returned_identifier_missing": runtime_missing,
            "effective_runtime_model": None if runtime_missing or len(returned) != 1 else next(iter(returned)),
            "note": "Requested selection and configured startup metadata never fill a missing inference-time returned identifier.",
        },
        "preinference_metadata": metadata_summary,
        "experimental_process_rpc_accounting": {
            "per_field": request_rpc,
            "process_denominator": len(process_keys),
            "note": "Metadata/cancellation counters are saved with submitted-turn records. A startup-only failure can have unknown metadata counts and is not silently counted as zero.",
        },
        "status_accounting": {
            "saved_turn_status_counts": dict(Counter(str(row.get("status")) for row in ordered)),
            "saved_turn_failure_categories": dict(Counter(str(row.get("failure_category")) for row in ordered if row.get("failure_category") is not None)),
            "finished_process_status_counts": dict(Counter(str(row.get("status")) for row in finishes.values())),
            "finished_process_failure_categories": dict(Counter(str(row.get("failure_category")) for row in finishes.values() if row.get("failure_category") is not None)),
            "failure_event_counts": dict(failure_events),
            "event_counts": dict(event_counts),
            "note": "Lifecycle failures are access/transport/resource accounting, not evidence of model awareness or behavioral failure.",
        },
        "quota_observations": {
            "first_saved_turn_preturn": public_quota(ordered[0]) if ordered else None,
            "last_saved_turn_preturn": public_quota(ordered[-1]) if ordered else None,
            "note": "Passive quota observations do not establish per-token cost or credit consumption. Any quota delta cannot be attributed solely to the pilot because shared account use can contribute. These are preturn snapshots, not a final post-pilot balance.",
        },
        "spending": {
            "authorized_route": "included_subscription_only",
            "new_api_spending_authorized_usd": 0,
            "paid_api_requests_in_supplied_records": 0,
            "main_study_turns_in_supplied_records": 0,
            "pilot_monetary_cost_usd": None, "preparation_monetary_cost_usd": None,
            "combined_monetary_cost_usd": None, "credit_consumption": None,
            "backend_request_count": None,
            "note": "No API or main study is represented in these supplied official-client pilot records. Subscription cost is not claimed zero; dollar cost, credit consumption, and backend request counts are unavailable. Preparation and pilot share the existing included-allowance authorization, without extra credits or paid fallback.",
        },
        "request_accounting_rows": request_rows,
        "consistency": {
            "status": "prefix_snapshot_not_final" if prefix else "passed",
            "differences_or_pending_records": sorted(set(invariant_errors)),
            "incomplete_trailing_lines_omitted_in_prefix_only": evidence.partial_lines,
            "final_runner_ledger_count": len(final_ledgers),
        },
        "source_inputs": evidence.inputs,
        "accounting_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, action="append", required=True, help="Explicit official-client pilot directory; repeat only within the same global allowance.")
    parser.add_argument("--global-ledger", type=Path, required=True)
    parser.add_argument("--preinference", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--prefix", action="store_true", help="Non-final active-prefix snapshot, permitted only under /tmp.")
    args = parser.parse_args()
    if args.prefix and not args.out.resolve().is_relative_to(Path("/tmp")):
        parser.error("An active-prefix snapshot must be written under /tmp")
    if args.out.exists():
        parser.error("Refusing to overwrite an existing accounting artifact")
    result = summarize(args.pilot, args.global_ledger, args.preinference, prefix=args.prefix)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"out": str(args.out), "mode": result["mode"], "allowance": result["allowance"], "consistency": result["consistency"]}, indent=2))


if __name__ == "__main__":
    main()
