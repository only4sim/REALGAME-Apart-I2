# Canonical recorded evidence

Files in this directory are immutable inputs, not default output destinations.

| Location | Evidence |
|---|---|
| `scripted_runs.jsonl`, `scripted_summary.json`, `totals.json` | Historical 960-episode scripted study; `llm_runs=0` in its totals refers only to that cohort |
| `coverage.json`, `coverage_replicates.jsonl`, `coverage_sampling.json` | Exact population checks and saved scripted sampling counts |
| `robustness.json` | Exact finite-state crossing calculations |
| `codex_subscription_pilot_v8_01/` | Separate 20-episode, 102-turn real Codex-client-system pilot |
| `codex_subscription_v8_global_allowance.jsonl` | Consumed global allowance; never delete or reset it to start a replacement cohort |

The pilot directory retains its 20 episode JSON files, 102 sanitized request JSON files, `runs.jsonl`, saved analysis, usage/failure/event ledgers, public-record consolidation, source/config freeze and source snapshot. The consolidated visible JSONL duplicates the request content for convenience and is not another cohort. The duplicate reanalysis file and historical mock/reproduction directories are recoverable from the history archive.

Current scripts may differ from the exact evaluated source snapshot. `make reproduce` checks the snapshot hashes and analyzes these saved records without invoking the client. No old cohort should be resumed after source changes. Write new derived outputs only under a fresh `build/` directory.
