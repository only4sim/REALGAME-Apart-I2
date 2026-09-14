# Certifying Behavior Without Hiding the Sandbox

A local research artifact and six-hour Codex handoff for target-specific behavioral identification and conditional certification. Start with START_HERE.md. The complete execution prompt is CODEX_PROMPT.md.

## Layout

- `submission_report.{pdf,docx,md}`: current English report; eight main pages plus references and appendices.
- `paper/submission_blocks.json`: editable manuscript source.
- `template/apart_original.docx`: the supplied submission template, unchanged.
- `protocol/`: scope, causal design, statistical restrictions, theory bridge, and model-facing prompts.
- `configs/halfday.json`: safe-by-default inference configuration, real calls disabled.
- `src/`, `scripts/`, `tests/`: runnable local worlds, analysis, provider scaffold, tests, and report build.
- `results/`: executed CPU results and immutable ledgers. No real LLM outcomes.
- `legacy_v5/`: inherited theory and independent certificate checkers, explicitly distinguished from new work.
- `verification/`: software versions, exact checks, mock transport results, reproduction, and document gates.
- `claim_ledger.json`: support and assumptions for report claims.
- `EXECUTION_REPORT.md`: what actually ran and what remains unexecuted.

No external targets, system fingerprinting, arbitrary model code execution, or network tools are available to the evaluated policy. Hosted model inference, when authorized, is distinct from the in-memory world. The Python implementation is not a secure sandbox for arbitrary hostile code; it never accepts such code. All live-model claims are currently unmeasured.

The finite theory is conditional on declared interfaces, deployment reference kernels, reset behavior, and strategy classes. Numerical examples are not a production safety certificate. The artifact demonstrates separations and assumption failures without assuming an LLM is deceptive.
