# Inference configuration scope

Offline reproduction needs no inference configuration, account or credentials.

- `halfday.json` is the prospective API configuration. Its defaults intentionally block inference. The API route requires separate approved access, exact models, supplied prices and budget.
- `codex_subscription_pilot_v8.json` is a historical configuration for the completed 20-episode pilot. Its pre-call status text records the freeze time, not a currently pending experiment. The global allowance ledger under `results/` records completed usage and prevents an automatic replacement cohort. Do not remove or reset it.

The exact evaluated configuration is also inside the cohort's `frozen_plan.json` and `source_snapshot/`. Current maintenance scripts can differ from those frozen sources. A new run requires fresh explicit authorization and a new compatible protocol/source/configuration freeze; archived approvals do not transfer to new experiments.

API and official ChatGPT-client access have different credential/metering gates. Neither the source-only package nor `make reproduce` performs model inference or inspects credential contents.
