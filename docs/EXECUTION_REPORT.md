# Repository execution record

## Author-confirmed PDF reconciliation: 2026-09-14

The author designated the supplied paper PDF as authoritative for the author block and abstract and requested correction of other inconsistencies. The editable JSON and generated Markdown now use Li Quan, The Pioneer Centre for Artificial Intelligence, Denmark, and the PDF's exact 150-word abstract. Scientific prose, six tables, three figure captions, thirteen references, the LLM usage statement and four extensions were reconciled. The six display equations remain editable LaTeX. The figure script now includes the pilot classification panel from saved analysis.

Four prose changes and one reference-path correction keep the repository's current paths and execution/build status truthful; the [reconciliation record](../verification/paper_sync/README.md) lists each departure and the complete source diff. Neither supplied PDF, the original template, experimental records nor the frozen evaluated source was modified.

The alignment check verified 114 source blocks and thirteen references, exact author/abstract correspondence, and both pilot tables against saved analysis. All 61 existing offline tests passed. `make paper` regenerated Markdown and then stopped at the documented missing rendering dependencies. No new DOCX/PDF, page inspection or successful rendering gate is claimed. Scientific review, authorship/disclosure approval, artifact location, licensing and venue eligibility remain separate from the author's metadata instruction. No new inference or CPU sampling was performed.

Current checks are in [final_checks.json](../verification/final_checks.json); details and source hashes are in [verification/paper_sync/](../verification/paper_sync/README.md). The earlier sections below describe the state at their respective revisions.

## Supplied paper and deck: 2026-09-14

The author added `paper/Certifying Behavior Without Hiding the Sandbox v1.pdf` and `slides/REALGAME_deck.pdf`. These are now the reading entry points in the root and folder READMEs. Reproduction and release guides distinguish the supplied revisions from the earlier v8 editable manuscript snapshot. The supplied paper has a different abstract and completed author/affiliation text; no matching editable DOCX or deck source was supplied. The PDFs and manuscript JSON were preserved without edits.

Offline inspection checked PDF headers, explicit page-tree counts, page sizes and readable literal text in decompressed content streams. The paper has 14 pages, with References on page 9 and appendices from page 10; the deck has six pages. This limited inspection is not full PDF parsing, visual page review or an abstract-word-count verification. Optional PDF rendering tools remain unavailable. File hashes and check scope are in [publication_artifacts.json](../verification/publication_artifacts.json).

The repository verifier and release packager now recognize the supplied deck's actual filename. The source-package command includes both supplied PDFs; its label does not assert a matching manuscript build. Complete packaging still requires current source/DOCX/PDF correspondence and actual page inspection. No paper content, experiment, inference, submission or publication was performed in this update.

Validation for this update is recorded in [publication_artifacts_update.json](../verification/publication_artifacts_update.json). Earlier cleanup checks below describe their original state before the two PDFs were added.

## Earlier publication repository cleanup

The earlier revision organized the repository around the paper, reproducible code and a future presentation deck. The author deferred slide content during that cleanup; the subsequent supplied PDFs are recorded above.

The current manuscript source is in `paper/`, user documentation in `docs/`, finite certificates and their checker in `certificates/`, and transient outputs in ignored `build/` directories. The root now has one user entry point, `README.md`, and a small Makefile. Core benchmark semantics, recorded outcomes and the exact evaluated source snapshot remain unchanged.

The cleanup removed 841 obsolete/duplicate/cache paths from the working tree and moved 14 useful files to their current locations. It removed 18 generated cache paths from the Git index and added ignore rules for build outputs, caches and local environment files. Historical versions, old reports, failed checks and raw mock records are recoverable through the verified archive: 2,581 logical paths stored as 410 unique content objects. Original old-ZIP member bytes remain available; original containers are recoverable through the baseline Git commit.

`make reproduce` is the supported offline entry point. It passed 61 tests, verified 212 evidence files and 45 frozen source hashes, reconstructed all 102 request histories, reproduced the 20-episode pilot analysis exactly, reconciled usage, and checked 38 finite certificate cases containing 2,031 rational constraints. A source-only ZIP was also extracted into a clean temporary directory without Git metadata or installed third-party dependencies; the full reproduction workflow passed there. No new model calls or CPU sampling study occurred.

The Markdown manuscript was regenerated from its authoritative JSON source. Its abstract remains 150 words, with eight main source groups, both required disclosure sections and four specified extensions. Optional build/render scripts were syntax-checked. The actual `make paper` attempt stopped at dependency preflight because docx, lxml, fitz, matplotlib, Pandoc, LibreOffice and Old Standard are unavailable. No historical PDF was substituted. The complete-artifact packager correctly rejected missing current paper rendering and deck content; source-only packaging remains usable.

Current source/evidence checks are in `verification/final_checks.json`. Maintenance results and the 61-test log are in `verification/repository_cleanup.json` and `repository_cleanup_tests.txt`. Older verification statements remain historical; current cleanup does not imply a new experiment, rendering approval, scientific review or publication.

At cleanup completion, the remaining work included paper rendering and inspection, deck content, and human publication decisions. See [RELEASING.md](RELEASING.md) for the updated list after the PDFs were supplied. No external publication or submission was performed.
