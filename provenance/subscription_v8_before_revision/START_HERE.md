# Start here: rendered report and next scientific step

## Status

The incoming Codex work reproduced the CPU artifact but could not render its revised manuscript. This environment completed that work using already installed libraries, Pandoc, LibreOffice and an existing Old Standard font. No dependency download was needed. The current report has **eight main pages, references beginning on page nine, 13 total pages and a 150-word abstract**. It was visually inspected page by page. This is a rendered submission candidate, not an approved or submitted paper.

The existing 960 scripted episodes are not LLM data. There are zero real model calls, 36 historical mock episodes, and 18 current unit tests. The remaining high-value scientific task is an explicitly authorized provider pilot and the frozen causal-timing study. Read `NEXT_CODEX_PROMPT.md` rather than replaying the entire previous CPU assignment.

## Offline verification

From the extracted root, using Python 3.10 or newer:

```bash
python -m unittest discover -s tests -v
python scripts/check_readiness.py --config configs/halfday.json
python scripts/verify_evidence.py --out /tmp/realgame_saved_record_check.json
python scripts/run_local.py --out /tmp/realgame_cpu_reproduction
python legacy_v5/code/check_certificates.py legacy_v5/verification/full_class_certificates.json --output /tmp/realgame_full_check.json
python legacy_v5/code/check_certificates.py legacy_v5/verification/certificates.json --output /tmp/realgame_restricted_check.json
```

Choose fresh output locations. The CPU runner rejects a nonempty output directory. The evidence checker also checks the supplied `results/reproduced/` against originals; compare any newly generated files to `results/` before making a new reproduction claim. Core experiments and certificate checking need only the standard library.

## Build and visual inspection

`paper/submission_blocks.json` is authoritative. Plot generation needs matplotlib; document construction needs python-docx, lxml and Pandoc; rendering needs LibreOffice; PDF checks need PyMuPDF. Exact local versions are recorded in `verification/software_versions.json`.

An existing TeX Live Old Standard installation can be registered without downloading anything:

```bash
python scripts/register_existing_fonts.py
python scripts/register_existing_fonts.py --apply
```

The second command writes only a dedicated user fontconfig file. If the local font is absent, supply a properly installed local font under explicit authorization; do not bundle font binaries in this project.

```bash
python scripts/make_figures.py
python scripts/build_report.py
python scripts/render_report.py --pdf submission_report.pdf --images /tmp/realgame_report_pages
python scripts/verify_report.py --out /tmp/realgame_report_check.json
python scripts/export_markdown.py --out submission_revision.md
```

Inspect every page. Retain Letter size, one-inch margins and readable type. Edit content/placement rather than shrinking typography to hide overflow. Main page 1 includes title and abstract; references must start on PDF page 9. The current pass was checked with the canonical document renderer and a portable LibreOffice rebuild. A new edit invalidates prior visual approval.

## Authorized model execution

The default `configs/halfday.json` deliberately blocks actual inference. Supply exact IDs, approved endpoint, explicit network/spending authorization, current sourced prices, and only the configured credential via the environment. Do not place credentials in chat or project files. A loopback endpoint also needs explicit authorization.

Run a separate compatibility pilot before a new frozen main run. See `NEXT_CODEX_PROMPT.md`. Per-directory cost estimates do not replenish the global authorization: deduct all earlier costs, keep a combined ledger, and use provider-side limits where available. A resource failure is not evidence of indistinguishability.

## Release and submission gates

After a future edit, regenerate actual current checks before calling the release packager:

```bash
python scripts/package_release.py --zip /tmp/REALGAME_Apart_rendered_release.zip
```

Its gate concerns reproducible files and rendered pagination, not scientific acceptance, human ownership, or submission permission. Author identity/affiliation, independent theorem and novelty review, remaining bibliography metadata, a real artifact address or accepted attachment, dual-use approval and current submission eligibility must still be resolved by the authors. No automatic publication is authorized.
