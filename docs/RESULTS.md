# Evidence and interpretation

The research question concerns which specified behaviors remain evaluable despite detectable simulation, and which depend on prerequisites missing from safe audits. This is not a generic sandbox-fingerprinting benchmark.

| Cohort | Evidence | Interpretation |
|---|---|---|
| Historical scripted study |960 completed episodes; 375 population cases; 600 exact checks; 3,000 sampling replicates | Programmed mechanisms and finite calculations, not LLM observations |
| Historical mocks |36 saved episodes across three cohorts | Transport fixtures, preserved in the indexed archive and excluded from model findings |
| Codex-client-system pilot |20 planned/started/complete episodes;102 official turns | Exploratory real model-plus-client evidence |
| Original raw-API main study | No evaluated episodes | Still prospective |

## Real pilot

The frozen requested subject was `gpt-6-astra`, medium effort, Codex 0.154.0. The model was selected from the official non-hidden catalog before outcomes. Runtime returned model identifiers were unavailable in all 102 turns. Requested and returned identifiers are distinct fields.

All 20 actions were standard commitments. Both post-commit probability reports were valid in every episode. Refused, failed and unstarted episode counts were each zero. The pilot used 42 of 48 available probes and 102 of 108 possible benchmark turns.

| Subset | n | Pre-diagnostic classification score | Final score | Pre Brier | Final Brier |
|---|---:|---:|---:|---:|---:|
| Primary cells |16 |10/16 |16/16 |0.25 |0.00063125 |
| Coherent controls |4 |2/4 |2/4 |0.375 |0.5 |
| All planned cells |20 |12/20 |18/20 |0.275 |0.100505 |

Orientation is fixed, with half credit at probability 0.5. Each before/four-probe primary family contrast has one label pair: p=0.5, Holm-adjusted p=1.0 in the retained four-comparison family. All comparisons are exploratory. No absence-of-effect or equivalence claim follows from these p-values.

All actions and reports are observed, so realized-sample shortcut missingness bounds are [0,0]. They are not population confidence bounds. Both reports follow commitment; neither measures an internal pre-decision belief. The final diagnostic is evaluator supplied. Zero shortcut-taking is retained without changing prompts or incentives.

The official-client boundary was constrained and audited, but complete native-tool and assembled-instruction inventories were unavailable. The pilot does not establish universal blindness, malicious intent, causal mediation or deployment safety. Dollar costs, credit consumption and backend request counts remain null; public token totals are not a bill.

Read the [full pilot report](PILOT_RUN_REPORT.md), [saved analysis](../results/codex_subscription_pilot_v8_01/analysis.json), [usage ledger](../verification/subscription_v8/combined_usage_ledger.json) and [claim ledger](../paper/claim_ledger.json) for exact denominators, calibration bins, contrasts and limits.
