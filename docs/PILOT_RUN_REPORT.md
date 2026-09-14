> Historical execution report for the completed v8 pilot. Repository paths were updated during publication cleanup; original bytes remain in archive/INDEX.json under PILOT_RUN_REPORT.md. See REPRODUCING.md for current commands.

# Pilot run report — codex-subscription-pilot-v8

Completed on 2026-09-14. This is an exploratory model-plus-official-Codex-client pilot, separate from the prospective raw-API study and all historical scripted/mock cohorts. It contains documented official-client calls and visible model outputs. No main study or publication was performed.

## Execution and denominators

Local execution ran from 11:30:10.224835 to approximately 11:38:23.784434 UTC (493.56 seconds, including client startup and local waiting). One worker completed the frozen schedule. The final time is reconstructed from the last invocation start and its recorded monotonic elapsed time; it is not provider billing duration.

| Outcome | Episodes |
|---|---:|
| Planned | 20 |
| Started through a submitted experimental turn | 20 |
| Committed action retained | 20 |
| Valid pre-diagnostic probability | 20 |
| Valid final probability | 20 |
| Both probabilities valid | 20 |
| Complete | 20 |
| Refused | 0 |
| Failed after starting | 0 |
| Unstarted | 0 |

All 20 actions were standard commitments; no shortcut was chosen. There were 102 reserved experimental client invocations, 102 conservative turn reservations, 102 fully written turn submissions and 102 completed visible responses. There were 62 action-stage responses (42 probes and 20 commitments), 20 pre-diagnostic reports and 20 final reports. Twelve episodes allowed four probes, giving 48 available probes; eight allowed none. No separate compatibility turn, wrapper retry, replacement completion, quota reset, model switch or effort change occurred. No error announcing an internal retry was recorded. A client turn may involve multiple backend requests; backend request counts and undisclosed internal retries remain unavailable.

## Access, model and metering

Official Codex CLI 0.154.0 reported ChatGPT authentication on this host. The non-hidden official catalog selected its default gpt-6-astra with medium reasoning effort and default service tier before outcomes. Every response passed the frozen startup checks with that configured model/effort/version. All 102 effective per-turn model identifiers remain null: startup configuration is not substituted for missing runtime telemetry. No raw-API model result is claimed. Temperature, top-p, output-token cap and output schema were not explicitly configured; supported client defaults were retained.

The exact approval and subsequent account-control confirmation are in access/AUTHORIZE_PILOT.txt and access/BILLING_CONTROL_CONFIRMATION.txt. The user attested ChatGPT Pro access with controls preventing extra-credit use and automatic top-up. Official telemetry retained its own planType value, prolite, without relabeling. Each response required included usage available, zero credit balance and no spend/rate-limit stop. These checks supplement human attestation; the client did not expose a request-level included-only billing lock. No credential contents were inspected.

Credit consumption, monetary cost and backend request counts remain null, not zero. New API spending authorization was zero; there were no API-adapter calls, credit purchases, recharge changes, resets, account rotation or paid fallback. The append-only global allowance covers all pilot directories. Preparation metadata has its separate 17-submission ledger; metadata can use the network but did not elicit benchmark responses. Account-wide quota changes cannot be attributed solely to the pilot because coordinating activity can share the allowance. Public usage covers 102/102 responses: 363,297 input, 3,032 output and 366,329 total tokens. Cached-input and reasoning-output counts overlap these totals. See verification/subscription_v8/combined_usage_ledger.json for reconciliation and denominators.

## Descriptive results

Orientation is fixed: p>0.5 predicts world 1; p=0.5 earns half credit. Both reports follow action commitment. The pre-diagnostic report uses only prior public history; the final report follows a fixed evaluator-supplied diagnostic. Neither is an internal pre-decision-belief measurement.

| Cohort | n | Pre score / n | Final score / n | Pre Brier | Final Brier | Probes |
|---|---:|---:|---:|---:|---:|---:|
| Primary cells | 16 | 10/16 | 16/16 | 0.25 | 0.00063125 | 29 |
| Coherent controls | 4 | 2/4 | 2/4 | 0.375 | 0.5 | 13 |
| All planned cells | 20 | 12/20 | 18/20 | 0.275 | 0.100505 | 42 |

Ten pre-diagnostic reports equal 0.5 (eight primary and two control reports); no final report does. The two coherent world-0 controls were confidently classified as world 1 after the diagnostic. Their labels do not alter the coherent mechanism. This control result is retained; it is not corrected by flipping classification orientation.

| Family | Timing | Budget | Control | n | Pre accuracy | Final accuracy | Pre Brier | Final Brier | Probes |
|---|---|---:|---|---:|---:|---:|---:|---:|---:|
| consistency | after | 0 | False | 2 | 0.5 | 1.0 | 0.25 | 0.0 | 0 |
| consistency | after | 4 | False | 2 | 0.5 | 1.0 | 0.5 | 5e-05 | 8 |
| consistency | before | 0 | False | 2 | 0.5 | 1.0 | 0.25 | 0.0 | 0 |
| consistency | before | 4 | False | 2 | 1.0 | 1.0 | 0.0 | 0.0 | 8 |
| consistency | before | 4 | True | 2 | 0.5 | 0.5 | 0.25 | 0.5 | 7 |
| persistence | after | 0 | False | 2 | 0.5 | 1.0 | 0.25 | 0.0 | 0 |
| persistence | after | 4 | False | 2 | 0.5 | 1.0 | 0.5 | 0.005000000000000001 | 6 |
| persistence | before | 0 | False | 2 | 0.5 | 1.0 | 0.25 | 0.0 | 0 |
| persistence | before | 4 | False | 2 | 1.0 | 1.0 | 0.0 | 0.0 | 7 |
| persistence | before | 4 | True | 2 | 0.5 | 0.5 | 0.5 | 0.5 | 6 |

Each family has one complete before/four-probe label pair: paired classification is 1.0, exact one-sided p=0.5 from two label swaps, and Holm-adjusted p=1.0 in the retained four-comparison family. All pilot comparisons are exploratory. A large p-value supports no absence-of-effect or equivalence claim. All eight primary world-1 minus world-0 shortcut contrasts are zero in this realized sample. A constant committed choice provides no informative probability–behavior correlation or causal mediation evidence.

Every planned action and report is observed. Therefore planned and attempted shortcut missingness bounds are [0,0]; the pre/final accuracy bounds collapse to the observed scores in every cell. These are bounds on the realized sample, not confidence bounds on population or deployment behavior. The analysis retains each cell denominator and five fixed final-probability calibration bins, including empty bins with null means. The original raw API design remains prospective at 480 episodes for two models and at most 2,592 requests without retries.

## Isolation, protocol departures and evidence limits

Each response used a fresh official App Server process and ephemeral root thread, unchanged SYSTEM/PROB instructions, the frozen wrapper and serialized reconstructed public history. This is a declared departure from API role delivery and retained per-episode conversations. No subject inherited a coordinator or reviewer transcript. Benchmark probes affected only the in-memory World. All six cataloged system skills were disabled; startup listed no instruction sources, workspace roots, environments or MCP servers. Supported controls constrained shell, file, web, apps, plugins, memory and subagents. The selected permission profile denied reads of benign repository and temporary markers. Provider safety policies and managed controls were not removed.

The official interface did not expose complete assembled instructions or a complete native-tool inventory. Startup catalogs, supported restrictions, host marker checks and recorded public histories support this bounded interface, not universal blindness or containment. No unsupported tool action or approval request was recorded. Timeouts would stop local submissions/waiting and attempt one best-effort interrupt before process termination; backend cancellation acknowledgement and exact cessation time would remain unknown. No timeout occurred here.

Visible streams were filtered before storage. Reasoning-event payloads, nested raw turn items, raw login output, account identity and credentials were not saved. Public numeric reasoning-token counters are usage telemetry, not hidden reasoning. No unfiltered JSON stream is presented as raw evidence. Strict parsing performed no repairs; all saved responses happened to be valid. Startup and fixture failures during preparation are retained separately and are not model outcomes.

The shared episode serializer retains the legacy field name api_calls_in_episode in episodes/*.json. In this arm that counter records submitted official-client turns. The canonical runs.jsonl renames it client_turn_submissions_in_episode and records backend=codex_subscription; it does not indicate use of an API adapter.

## Verification, files and remaining gates

The final independent payload audit verified all 45 source-snapshot hashes, the original 20-cell schedule, its 108-turn maximum and exact public-history reconstruction for all 102 requests. Reanalysis matches analysis.json exactly. The original API adapter and historical evidence remain unchanged. The original 18 tests passed alongside 37 initial subscription tests; after prospective timer/analysis changes and one fixture correction, all 40 subscription tests passed. Thus 58 distinct tests have passing records. No historical CPU study was rerun and no mock was counted as a model episode.

- Frozen design and source copies: results/codex_subscription_pilot_v8_01/frozen_plan.json and source_snapshot/.
- Immutable visible request records: requests/*.json; consolidated visible_records.jsonl is a duplicate representation, not extra observations.
- Episodes and analyses: runs.jsonl, episodes/, analysis.json (the duplicate recheck is in the historical archive).
- Usage/failures: usage_failure_ledger.json, events.jsonl, results/codex_subscription_v8_global_allowance.jsonl and verification/subscription_v8/combined_usage_ledger.json.
- Access/amendment: access/ACCESS_DISCOVERY.json, access/ACCESS_DECISION.md and access/PROTOCOL_AMENDMENT.md.
- Code diff and tests: historical keys verification/subscription_v8/adapter_code.diff and adapter_code_manifest.json in archive/INDEX.json and unit_tests_*.txt.
- Audit: verification/subscription_v8/final_payload_audit.json and current_checks.json.

The revised paper/submission_blocks.json and paper/manuscript.md include these scoped results and preserve the 150-word abstract, eight main source groups, limitations/dual-use, LLM usage statement and exactly four one-month extensions. Rendering remains unavailable: docx, lxml, fitz, matplotlib, Pandoc, LibreOffice and Old Standard are absent. The verified historical v7 PDF/DOCX are preserved byte-for-byte in archive/history.zip and do not contain these new results. Source groups do not prove pagination; the v8 source has not passed a new eight-page rendering or page inspection.

Remaining scientific measurements include additional models/seeds/mechanisms, raw-API behavior, deployment transfer, latent pre-decision belief and validated deployment error bounds. Human author/affiliation confirmation, scientific review, disclosure approval, artifact location and venue eligibility remain separate gates. No new inference is scheduled. A working-source ZIP may pass integrity verification while remaining explicitly unrendered and unsubmitted.
