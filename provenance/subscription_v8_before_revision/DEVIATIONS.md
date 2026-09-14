# v7 changes relative to the received Codex working release

The received change log is retained at `provenance/codex_received/DEVIATIONS.md`. That log, and the older baseline, must not be treated as current execution claims.

| Change | Reason | Effect on evidence |
|---|---|---|
| Reproduced seven CPU files in a fresh directory | Verify the return before relying on it | Byte-identical; no additional observations |
| Added finite-float JSON parsing and a regression test | Numeric exponent overflow bypassed the prior constant filter | Future parser change; no recorded output rewritten |
| Restored source locations for references [1,3] | The original attachments are available here | Removes a workspace-specific source gap; exact-PDF metadata caveats remain |
| Added partial-identification prior work [12] | Narrow novelty against relevant precedent | No theorem or numerical change |
| Regenerated PDF/DOCX/Markdown | Received rendered documents were stale | Current source now has actual rendering and QA |
| Removed a duplicate reproduction paragraph | Actual rendering overflowed the 8-page main-text requirement | Same information retained elsewhere; no type/margin shrink |
| Replaced malformed inline supremum with equivalent words | Math renderer produced the wrong visual form | Definition unchanged |
| Added local build/inference preflight and local-font registration helper | Prevent another late dependency blocker | No downloads, secrets, provider calls or model observations |
| Added a focused next-stage Codex instruction | The remaining empirical gap is authorized real inference | No permission assumed or model chosen |

The experimental prompts, world mechanisms, target policy, CPU seed, 480-episode prospective design and raw evidence remain unchanged. No real provider pilot was run. The preliminary editorial build failures and their fixes are recorded rather than erased. The final checks apply to the newly rendered v7 report, not inherited binaries.
