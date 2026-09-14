# Start here: target-specific safe evaluation

## Deliverables and present evidence

Read CODEX_PROMPT.md for the complete autonomous execution assignment. Read AGENTS.md before running anything. The current submission is an English, template-based report with eight main pages; references and appendices are additional. The underlying question has not changed: which behavior can still be evaluated when simulation is detectable, and which behavior depends on evidence no allowed safe audit supplies?

This release contains 960 scripted local episodes, 375 population cases, 600 exact checks, 3,000 sampling replicates, six exact certificate-crossing calculations, and rechecked prior certificates. It contains **zero real LLM runs**. Mock completions are transport tests only. The six-hour LLM experiment is prospective and conditional on credentials, exact model IDs, and spending authorization.

## Quick reproduction (no network or API key needed)

Use Python 3.10 or later. From this directory:

```bash
python -m unittest discover -s tests -v
python scripts/run_local.py --out results/reproduced
python legacy_v5/code/check_certificates.py legacy_v5/verification/full_class_certificates.json --output verification/rechecked_full.json
python legacy_v5/code/check_certificates.py legacy_v5/verification/certificates.json --output verification/rechecked_restricted.json
python scripts/run_llm.py --config configs/halfday.json --out results/mock_new --mock --limit 12
python scripts/analyze_llm.py --input results/mock_new/runs.jsonl --out results/mock_new/analysis.json
```

The core calculations and mock transport use the standard library. Figure generation needs matplotlib. Document building needs python-docx, lxml, and the `pandoc` executable; rendering needs LibreOffice. PDF verification uses PyMuPDF. Never install packages globally without authorization. `requirements.txt` lists optional release dependencies; `verification/software_versions.json` records what was used here.

## Authorized model execution

Copy configs/halfday.json to configs/authorized.json. Fill exact model snapshot IDs and verified endpoint/provider settings, authorize network access, and set the permitted spending ceiling and sourced current per-token prices. Set the named API key only in the execution environment. Do not put it in a config, prompt, log, or report. A local inference endpoint still requires explicit network authorization. No public endpoint other than the configured inference host is permitted.

```bash
python scripts/run_llm.py --config configs/authorized.json --out results/llm_confirmatory
python scripts/analyze_llm.py --input results/llm_confirmatory/runs.jsonl --out results/llm_confirmatory/analysis.json
```

Run a separate pilot first. Source/config changes after a freeze require a new output directory and an explicit deviation. The default configuration deliberately blocks real inference. One model yields 240 episodes; two yield 480. A complete two-model core has at most 2,592 requests without retries. The 4,000-request ceiling is not authorization to spend. Monetary reservations are conservative estimates, not provider-enforced account limits. A real provider smoke test has not been executed here.

## Rebuild the report

`paper/submission_blocks.json` is the authoritative editable manuscript. Replace unmeasured outcomes only using immutable artifacts. Main sections follow the supplied Word template. The abstract is exactly 150 whitespace-delimited words, satisfying both the template's 150–250 recommendation and the sprint file's at-most-150 requirement.

```bash
python scripts/make_figures.py
python scripts/build_report.py
python scripts/render_report.py --pdf submission_report.pdf --images verification/rendered
python scripts/verify_report.py --pdf submission_report.pdf
```

The report preserves the original template's Letter page size, one-inch margins, serif typography, title rules, and section order. Old Standard TT must be installed externally to reproduce typography. No font files are distributed. In the creation environment, an installed Old Standard OpenType font was mapped to that family. Do not shrink type or margins to conceal overflow. Edit prose, tables, or placement, rerender, and inspect every page. References must begin on PDF page nine. `verify_report.py` detects pagination and text-level failures; it does not replace visual inspection.

## Submission gates

Human theorem and novelty review; author affiliation; a real artifact location or acceptable attachment; authorship approval and truthful AI disclosure; current venue requirements and submission eligibility; dual-use review; final page/abstract checks. The supplied rubric requires the team's own writing. No submission, public repository, email, or provider payment was made automatically.

Budget ceilings are enforced per output directory. Deduct all pilot and earlier-run expenditure from the single user-authorized total before configuring the confirmatory ceiling. Do not obtain a fresh full budget merely by changing output directories. Report the combined request and spending ledger across pilots and confirmatory runs. Configure provider-side limits where available; local reservations are estimates rather than a billing guarantee.
