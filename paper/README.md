# Paper and editable source

Read the author-supplied [Certifying Behavior Without Hiding the Sandbox v1.pdf](Certifying%20Behavior%20Without%20Hiding%20the%20Sandbox%20v1.pdf). It was added on 2026-09-14 and has 14 pages: main text on pages 1–8, references on page 9, and appendices on pages 10–14, as checked through its page tree and visible text. Full visual inspection remains pending.

## Source correspondence

The author confirmed that the supplied PDF governs the author block and abstract. The editable source now uses **Li Quan**, **The Pioneer Centre for Artificial Intelligence, Denmark**, and the PDF's exact 150-word abstract. Its scientific text, six tables, three figure captions, thirteen references, LLM usage statement and four extensions have also been reconciled. The PDF filename's `v1` and the experimental protocol's `v8` are separate version labels.

- [submission_blocks.json](submission_blocks.json): source of the repository's manuscript build.
- [manuscript.md](manuscript.md): readable export of that source; regenerate with `make paper-source`.
- [claim_ledger.json](claim_ledger.json): scoped claims and supporting evidence, retaining historical verification scope.

The source retains eight main page groups, six editable display equations, the required limitations/dual-use and LLM usage sections, and exactly four one-month extensions. Tagged PDF text confirms the author block and 150-word abstract. Typography and regenerated pagination remain unverified.

The [reconciliation record](../verification/paper_sync/README.md) lists the limited departures: current repository paths, the availability of saved audit records, and truthful build status. In particular, the PDF's claim that regenerated DOCX/PDF already correspond has been replaced in the editable source with the actual pending-render status. The supplied PDF itself remains unchanged.

## Building and verification

The original Apart template is [template/apart_original.docx](../template/apart_original.docx). `make paper` builds the checked-in source into `build/paper/`; it does not overwrite the supplied PDF. The current host lacks the optional document toolchain and Old Standard font, so no new DOCX/PDF has been rendered. The figure script now generates the pilot classification panel from saved analysis alongside the two synthetic-study figures. Until it can run, the Markdown figure-1 link opens the supplied PDF's first page.

See the [build instructions](../docs/REPRODUCING.md), [release checks](../docs/RELEASING.md), and [artifact hashes and check scope](../verification/publication_artifacts.json). Historical v7 PDF/DOCX remain recoverable from the [history archive](../archive/README.md).
