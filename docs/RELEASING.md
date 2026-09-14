# Preparing the paper, code and presentation for publication

This repository is a publication workspace, not an automatically published artifact. The author supplied the paper v1 PDF and six-slide deck on 2026-09-14, then confirmed that its author block and abstract are authoritative. The manuscript source has been reconciled with that revision, with documented repository-path and execution-status corrections. A new typeset build remains pending.

## Current deliverables

| Deliverable | Available | Remaining work |
|---|---|---|
| Paper PDF | [Paper v1](../paper/Certifying%20Behavior%20Without%20Hiding%20the%20Sandbox%20v1.pdf), 14 pages; references on page 9 | Full visual/scientific review and matching editable DOCX |
| Editable paper source | `paper/submission_blocks.json`, `paper/manuscript.md` | Build, inspect and verify the updated outputs |
| Reproducible code/data | Core scripts, tests, canonical results, source freeze and history index | Review license and public disclosure scope |
| Presentation PDF | [REALGAME_deck.pdf](../slides/REALGAME_deck.pdf), 6 slides | Add matching editable source and complete review |
| Human submission details | Author name and affiliation follow the author-confirmed PDF | Scientific/authorship/disclosure review, artifact location and venue eligibility |

No license has been selected on behalf of the authors. Choose the intended licenses for code, manuscript and data before external publication. Do not infer human authorship, scientific review or permission to submit from automated verification.

## Source-only artifact

```bash
make reproduce
make package-source
```

This produces a timestamped `build/realgame-v8-source-only-…zip`, a SHA-256 sidecar and an integrity-check JSON file. The ZIP includes repository source, data, documentation, archive, required code, and both author-supplied PDFs at their original paths. It excludes build outputs, locks, Python caches and standalone fonts. Its internal manifest covers every member except the manifest itself. The retained `source-only` command/label means that verified manuscript-build gates were not required; it does not mean that supplied PDFs are omitted. The PDFs' availability does not certify their source correspondence or visual review.

## Rendered publication artifact

1. Review the [documented reconciliation](../verification/paper_sync/README.md), then run `make paper` on a host with the documented toolchain. The build writes to `build/paper/` and preserves the supplied PDF. Its six tables and three figures must all be present.
2. Check that all current manuscript text is present, main text occupies exactly eight rendered pages and references start on page nine. Keep the 150-word abstract, limitations/dual-use section, LLM usage statement and four specified extensions.
3. Inspect every image in `build/paper/pages/` for clipping, overlap, equations, font substitution and readability. Preserve the original template geometry.
4. Record the actual inspection in `build/paper/visual_review.json`. It must identify the current PDF hash and each page/image hash with inspection notes. Do not assert inspection without viewing the page.
5. Review the supplied `slides/REALGAME_deck.pdf` and add its matching editable source. The packager recognizes this PDF; its presence check does not certify deck review or reproducibility.
6. Run `make package`. It rejects missing paper/deck files, stale source/document hashes, incorrect page counts or incomplete visual-review records.

The visual-review record has this shape; repeat the page entry for every rendered page, using actual hashes and observations:

```json
{
  "pdf_sha256": "SHA256_OF_CURRENT_PDF",
  "pages": [
    {
      "page": 1,
      "image_sha256": "SHA256_OF_CURRENT_PAGE_IMAGE",
      "visual_inspected": true,
      "notes": "Actual page-specific inspection findings"
    }
  ]
}
```

The record links visual inspection to the files; it is not independent proof of review. The paper checker and release packager are separate from human scientific, authorship, disclosure, licensing and submission decisions. No command submits, emails, publishes or creates a public repository.
