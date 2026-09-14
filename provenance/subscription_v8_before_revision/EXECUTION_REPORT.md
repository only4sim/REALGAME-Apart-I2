# v7 execution report: Codex return audit and rendered release

## Outcome

The Codex build blocker is resolved in this environment. The revised manuscript was regenerated from `paper/submission_blocks.json` through the supplied native Apart template, exported to DOCX/PDF/Markdown, and visually checked on all 13 pages. Main text is exactly 8 pages; references start on page 9; four appendix pages follow. The abstract is exactly 150 whitespace-separated words. This is a rendered submission candidate, not human-approved or submitted work.

No evaluated LLM request, provider pilot, paid inference, external environment audit, public repository creation, submission or publication occurred. The existing results remain CPU/scripted experiments and explicitly labeled mock fixtures. Web tools were used separately for selected primary bibliography checks, not to query target models or execute environmental probes. No dependency or font download was required.

## Incoming package and provenance

The uploaded working ZIP had 371 entries. All 370 manifest-listed files passed byte/hash checks; its SHA-256 is `e2d19f4a22b3aab50b2d3f122291c04748218cf9b621bcc15cb1514346a5a7e7`. Safe extraction rejected path traversal and link hazards. Selected Codex sources, report binaries, manuscript text and checks were preserved in `provenance/codex_received/` before edits. The received complete older baseline remains in `provenance/inherited_v6/`. The original input archive was not modified.

## Reproduction and retained observations

All 17 incoming unit tests passed. The CPU runner was executed into `results/reproduced_v7/`; all seven files matched the original results byte-for-byte. The saved-record audit again checked 960 scripted episodes, 384 matching decision-input pairs, 375 population cases, 600 exact checks, 3,000 sampling records containing 384,000 draws, and six exact crossing outputs. All 77 inherited evidence files are unchanged.

Both inherited certificate sets were independently checked with the supplied rational checker: 38 cases and 2,031 constraints passed. These checks concern saved finite certificates, not a new general proof-assistant verification. Reproduction copies are not additional independent scientific observations.

Three incoming mock cohorts contain 12 episodes and 36 requests each (36 episodes/108 requests total). No new saved mock cohort was created in this continuation. Temporary test fixtures are offline tests, not study participants. No real model evidence exists in this release.

## New parser defect and regression

A targeted review found that strict JSON parsing rejected NaN/Infinity constants but accepted exponent-overflow literals such as `1e400`, including nested forms. Python converted them to non-finite floats. The `parse_float` callback now verifies `math.isfinite` and rejects such values without response repair. A new test covers positive/negative and nested overflow as well as valid finite controls. The final suite has **18 passing tests**. Before/after demonstrations are retained in `verification/v7/parser_overflow_*.json`.

No scientific prompts, CPU seeds, sampling calculations, scenario definitions, or recorded outputs were tuned. The changed parser and added scripts change future source freezes; do not resume an inherited frozen cohort using the new sources.

## Source and manuscript corrections

Penumbra and Rajakumar–Laine PDFs, absent from Codex's workspace, were available among the conversation attachments. Their relevant pages were re-read. The report now states exact locations and no longer calls them unavailable. Missing exact-PDF publication metadata is still marked, not guessed. Other close attached sources were checked at their cited locations. Primary-web bibliography checks were supplemental. An ICML 2024 partial-identification reference was added to narrow, not enlarge, the novelty claim. The source audit records which checks remain partial.

The report preserves the same question and evidence. It clarifies that a committed decision precedes later diagnostics, reported probabilities are not internal beliefs, synthetic conditional-error bounds are injected specifications rather than measured deployment guarantees, and replication adds no model observations. It does not add a new theorem or claim independent human correctness review.

## Publication engineering and QA

Required Python libraries, Pandoc and LibreOffice were already installed. Fontconfig was pointed to an existing local TeX Live Old Standard installation; only a user configuration file was written. No font binaries are packaged. The package includes a local-only preflight and an optional existing-font registration helper, preventing a future executor from discovering these build requirements only at the end.

The first actual rendering revealed that the Codex source's eight declared page groups overflowed: a redundant reproduction paragraph created a ninth main page. The paragraph was removed while its information remained in the Introduction and Appendix C; margins and body size were not reduced. Two source-string escaping mistakes introduced during this editorial pass were corrected. An inline supremum expression rendered incorrectly, so its equivalent definition was written as “maximum minus minimum.” Intermediate build records remain in `verification/v7/`.

The final build uses Letter pages, one-inch margins, 11-point body type, native editable equations, four tables and two figures. All pages were inspected for clipping, overlap, illegible figures and malformed equations. A second build using the package's portable LibreOffice renderer matched all 13 pages in text and rendered pixels. Current hashes are in `verification/v7/report_checks.json` and the final archive manifest.

## Remaining work and permission boundaries

The local preflight finds no exact models, network/spending permission or sourced prices in the default config; the specifically configured credential variable is absent. Only its presence was checked. No unrelated credential or account was searched. A separate authorized pilot is required to establish provider compatibility; no offline mock can do that. `NEXT_CODEX_PROMPT.md` focuses the next execution on this gap rather than another duplicate CPU cycle.

Human author/affiliation confirmation, independent theory/novelty review, remaining bibliography metadata, an accepted artifact attachment or real URL, disclosure approval and current submission eligibility remain gates. The engineering checks can pass while these gates remain open. No inference, scientific or submission approval is implied by the archive filename.
