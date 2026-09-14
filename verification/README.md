# Verification records

- `evidence_manifest.json` is the integrity inventory of retained data, frozen source, historical access/check records, template and archive.
- `final_checks.json` states current source/repository status and supplied PDF availability. Availability is separate from verified source correspondence and visual review.
- `publication_artifacts.json` inventories the author-supplied paper and deck PDFs, their exact hashes, basic inspection results, and outstanding source correspondence.
- `publication_artifacts_update.json` records the focused maintenance checks after those PDFs were added; `publication_artifacts_tests.txt` contains their test log.
- `paper_sync/` records the subsequent author-confirmed PDF-to-source reconciliation, exact source diff, text/math mapping, saved-table checks, 61-test log and blocked rendering attempt.
- `repository_cleanup.json` records maintenance verification and the absence of new model calls.
- `subscription_v8/` retains selected immutable records from the completed pilot, including exact denominators, combined usage, original tests and payload verification. Their dates/hashes describe that historical execution, not later source maintenance.

Run `make reproduce` for fresh checks. Regenerated logs and analyses are written under `build/`, rather than overwriting the records here. Older verification passes and failures remain recoverable from `archive/INDEX.json`.

A passing integrity test is distinct from correct scientific claims, rendered pagination, actual page inspection and permission to publish.
