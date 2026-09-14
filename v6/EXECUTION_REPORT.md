# Execution report: 14 September 2026 reproduction

## Outcome and release status

The CPU assignment is complete and reproducible. Report-source revisions and a working release are prepared. Final publication engineering is **blocked by missing build dependencies and a pending network exception**. The top-level `submission_report.pdf`, `submission_report.docx`, and `submission_report.md` remain the supplied, mutually corresponding report files. They were not regenerated in this execution. The revised English manuscript is `paper/submission_blocks.json`, with a dependency-free text export at `submission_revision.md`; its abstract has exactly 150 whitespace-separated words and it specifies eight main pages. Revised DOCX/PDF pagination and visual inspection remain unverified. The working ZIP must not be represented as the requested final rendered release.

The research question is preserved: which behavioral claims remain valid despite detectable simulation, and which fail because safe audits lack relevant prerequisites. No evaluated LLM request, provider pilot, payment, submission, publication, or external audit was performed.

## Executed checks and evidence

The initial commands were the prescribed unit tests and CPU reproduction, before changes to code or manuscript. All 12 original tests passed. The CPU runner generated seven files in `results/reproduced/`; every file matched the supplied counterpart byte for byte. This reproduces 960 scripted episodes, 384 matching decision-input pairs, 375 population cases, 600 exact identities/bounds, 3,000 sampling replicates containing 384,000 draws, six exact crossing calculations, and the cached-bit control. There were no failed or excluded scripted episodes. Reproduction copies are not additional independent scientific observations.

Both inherited certificate files were independently checked, covering 38 cases and 2,031 rational constraints. The checks returned `all_certificates_verified`; no optimizer status was used as proof. A separate saved-record audit rechecked episode IDs, control counts, matching pairs, exact population intervals, all sampling count vectors and estimates, reported MSEs, crossing outputs, and inherited evidence hashes. All 77 original evidence files remained unchanged.

The incoming manifest matched all 118 supplied files. A complete baseline snapshot is retained in `provenance/inherited_v6/`, and every snapshot file matches its incoming SHA-256. Modified source files were recovered by reversing the recorded changes and accepted only after exact hash verification. The inherited manuscript, check reports, sources, records, and execution history are therefore available separately from this execution.

Two saved current mock smoke tests each completed 12 episodes and 36 requests: `results/mock_new/` reproduced the original transport, and `results/mock_verified/` exercised the corrected code under a fresh freeze. The inherited 12-episode mock cohort is retained separately. These records are labeled `mock` and `MOCK-NOT-LLM`, never LLM observations. Temporary unit-test fixtures are offline controls rather than experiment cohorts. `verification/combined_inference_ledger.json` records all saved mock cohorts and zero real inference spending.

## Changes and verification

The provider adapter now retains public refusal/truncation metadata, visible partial output, usage, and actual returned model identifiers without substituting a requested ID for a missing one. Hidden reasoning is excluded. It distinguishes explicit provider refusals, truncations, timeouts, malformed output, and resource stops. A failed probability report preserves the earlier committed action. JSON parsing rejects duplicate keys and non-finite numeric constants; no repair or replacement completion is attempted. Arbitrary transport exception text is not written to new raw request records.

The analyzer now reports the entire frozen design, including absent and unstarted ledger rows, separate attempted/planned denominators, action and probability-report missingness bounds, world-specific counts, planned behavior-contrast bounds, request failures, and cost reservations. Holm correction reserves the four planned model/family comparisons even when fewer model comparisons can run. Provider prose refusals without an explicit refusal field can still appear as invalid JSON; offline fixtures do not establish compatibility with a real provider.

Five additional offline tests cover retained visible refusal/truncation fields, exclusion of hidden reasoning content, preservation of completed actions, strict JSON, missing planned episodes, and fixed-orientation label randomization with half credit for ties. All 17 tests passed. A deliberate rerun into the existing reproduction directory was rejected, verifying the new guard against overwriting evidence. The local computation, scientific estimands, sampling seed, scenario prompts, and default model configuration were not tuned.

The report source now distinguishes reproduction from new experiments, identifies absent literature attachments, updates the execution disclosure, and marks the inherited author name for confirmation. The original template bytes and its section organization are preserved. The report builder and verifier were strengthened to check source/abstract agreement, template geometry, native equations, fonts, and document/source hashes, but these document checks could not run without their dependencies. These edits do not constitute visual or rendering verification.

## Build blocker

Startup checks found no python-docx, lxml, PyMuPDF, matplotlib, Pandoc, LibreOffice, or Old Standard font. No offline cached copies of the required tools were found. The build command failed with `ModuleNotFoundError: No module named 'lxml'`; rendering failed with the explicit LibreOffice requirement. The observed commands and errors are saved in `verification/build_dependency_preflight.json`.

A narrowly scoped request to download official build dependencies into an isolated local directory remains unanswered. AGENTS.md permits network access only for explicitly authorized inference, so no dependency download or global package installation was attempted. A historical PDF, a source page-break count, or a previous visual-review flag cannot replace rendering and inspecting the revised manuscript. Current `verification/final_checks.json` records this blocked state; inherited verification files are historical evidence only.

Once the dependency exception is authorized, install the required tools locally, inspect/render the supplied report, regenerate figures from saved results, build `submission_report.docx` from `paper/submission_blocks.json` using `scripts/build_report.py`, render through LibreOffice, and inspect every page image. Edit prose or placement if needed; retain Letter pages, one-inch margins, Old Standard, exactly 150 abstract words, and references starting on page nine. Then update current document checks and package the final ZIP with `scripts/package_release.py` without its working-state option.

## Inference and author gates

Only `configs/halfday.json` exists. It has no exact model IDs, disables network/paid calls, sets no positive spending authorization, and lacks prices and a price source. The named `OPENAI_API_KEY` variable is absent; only its presence was checked. No unrelated account or credential was searched. The 480-episode two-model study remains a conceptual prospective design, not an attempted experiment. A resource or authorization failure is not evidence of indistinguishability.

Author identity/affiliation, human ownership of the final writing, independent theorem/novelty/source review, artifact location or accepted attachment, disclosure review, and current submission eligibility remain unresolved. Source attachments for references [1] and [3] are absent; other literature metadata is inherited and was not re-fetched. No public preregistration, human authorship approval, external peer review, Lean verification, real-deployment validity, or submission completion is claimed.

See `DEVIATIONS.md` for the complete change log, and `verification/release_archive_check.json` for the working archive's byte/hash verification. Archive integrity does not resolve the blocked manuscript rendering.
