# Paper source reconciliation: 2026-09-14

The author instructed that the supplied paper PDF governs the author block and abstract, and requested correction of other inconsistencies. [author_instruction.json](author_instruction.json) records that scope. The supplied PDF and slide PDF remain byte-for-byte unchanged.

The editable source now follows the paper's author block, exact 150-word abstract, scientific prose, six tables, three numbered figure captions, thirteen references, LLM usage statement and four one-month extensions. Six display equations retain their editable LaTeX. The figure-generation script adds the pilot panel using saved analysis; until the optional plotting toolchain is available, the Markdown link opens that figure in the supplied PDF.

## Explicit corrections relative to the PDF

| Location | Correction | Reason |
|---|---|---|
| Section 4.4, final paragraph | Describe the report as a summary of the saved pilot records | The repository contains the underlying records as well as the report |
| Code and Data | State that source has been reconciled but a new DOCX/PDF build is pending | No matching regenerated document has been rendered on this host |
| Appendix B, final paragraph | Use `certificates/` and the archive index for historical `legacy_v5/` files | The active repository was reorganized |
| Appendix C, verification paragraph | Distinguish the supplied PDF's report-only revision from subsequent repository verification | The retained checks document 45 source hashes, 102 reconstructed histories and exact saved-record reanalysis |
| Reference 13 | Use `docs/PILOT_RUN_REPORT.md` | This is the report's current path |

These corrections change provenance, paths and build status, not experimental outcomes or the research question. [source_revision.diff](source_revision.diff) preserves the complete before/after manuscript change. Historical cleanup/intake records remain historical; their earlier hashes are not claims about the revised source.

## Checks and reproducibility

[alignment_check.json](alignment_check.json) checks all 114 source blocks, thirteen references, the author block and abstract. It verifies the three aggregate pilot rows and ten paired-cell rows against the immutable saved analysis. [source_mapping.json](source_mapping.json) connects blocks to PDF structure objects and lists the four prose corrections; [math_mapping.json](math_mapping.json) records the fifty formula-object mappings, including six display equations.

From the repository root, choose a fresh output path:

```bash
python3 verification/paper_sync/verify_alignment.py --out build/paper-alignment.json
# Optional tagged-text inspection:
python3 verification/paper_sync/extract_supplied_pdf.py --out build/paper-tagged-text.json
```

The extraction helper uses only the standard library, accepts only the inventoried PDF hash, and reads its explicit/compressed objects, Unicode font maps and document tags. It is a restricted audit helper, not a general PDF parser or a visual renderer. Text/formula correspondence does not establish font metrics, exact figure appearance or regenerated pagination.

All 61 existing offline tests passed; see [unit_tests.txt](unit_tests.txt). The actual `make paper` attempt stopped at dependency preflight; [build_attempt.txt](build_attempt.txt) records the missing docx, lxml, fitz, matplotlib, Pandoc, LibreOffice and Old Standard font. The original Apart template and readable font sizes were preserved in the build code. A fresh eight-page-main-text render and inspection remain pending. No new model calls, CPU sampling experiment, submission or publication occurred.
