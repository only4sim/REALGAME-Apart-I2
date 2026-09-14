# Evidence preservation and repository cleanup

The publication cleanup changes repository organization and reproduction tooling, not the research question or model outcomes. It started from the Git commit recorded in [archive/INDEX.json](../archive/INDEX.json). No new model call or CPU sampling study was performed.

## Active evidence

The seven canonical scripted-result files remain directly under `results/`. The real Codex-client pilot remains under `results/codex_subscription_pilot_v8_01/`, with 20 episode records, 102 saved request records, its immutable ledger, analysis, configuration and 45-file source snapshot. The global allowance ledger remains at its original path. Current experimental records were neither rewritten nor resumed.

[verification/evidence_manifest.json](../verification/evidence_manifest.json) hashes the retained data, frozen source, access/check records, template and history archive. `make reproduce` verifies those bytes before analyzing the records. It verifies the evaluated snapshot separately from current maintenance code; source reorganization must not invalidate the historical freeze or imply compatibility for a new run.

## Removed from the active working tree

| Material | Current treatment |
|---|---|
| Complete `v6/` clone and nested `provenance/` copies | Indexed historical archive, with duplicate bytes stored once |
| Repeated CPU-output directories | Canonical original outputs retained; historical copies recoverable from the archive |
| Historical mock cohorts and blocked/unstarted plans | Preserved as history; excluded from real-model results |
| Old agent handoff prompts and competing root entry documents | Archived; current entry is `README.md` with focused guides in `docs/` |
| Old root PDF/DOCX/Markdown and generated release ZIPs | Historical document/member bytes archived, no stale binary presented as the current paper |
| One-off v7 rewriting and prior-layout packaging scripts | Archived; replaced by current source/build/reproduction/package entry points |
| Old verification passes, failed preparation records and original code diffs | Historical archive, with selected v8 checks also retained for direct inspection |
| Numeric certificate implementation | Moved to `certificates/`, with checker/data and explicit scope |
| Bytecode caches and empty runtime lock | Discarded; `.gitignore` prevents their return to version control |
| Duplicate `analysis_rechecked.json` | Saved analysis remains canonical; the identical recheck is archived |

The history index covers 2,581 logical paths using 410 distinct content objects. Every object and index entry was verified before files were removed. All obsolete ZIP member bytes are recoverable; original ZIP container bytes can be recovered through the recorded baseline Git commit. See [archive recovery commands](../archive/README.md).

## Reading historical references

Original paths inside frozen manifests, source snapshots and historical reports are provenance identifiers. Do not rewrite raw evidence to update those paths. Search `archive/INDEX.json` for a missing historical path and retrieve that exact file with `scripts/restore_history.py`. Current commands and destinations are in [REPRODUCING.md](REPRODUCING.md).

The v7 document verification applies to its archived binaries. It does not validate pagination of the current v8 source. The retained v8 verification records similarly describe their recorded execution/source state; `verification/final_checks.json` states the current repository status.

The author subsequently supplied the paper v1 PDF and `REALGAME_deck.pdf` on 2026-09-14. They are separate publication artifacts, not new experimental evidence or recovered v7 binaries. Their hashes and inspection scope are in [publication_artifacts.json](../verification/publication_artifacts.json). After the author confirmed the PDF as the authority for name, affiliation and abstract, the editable source was reconciled with its scientific text and disclosures. The [reconciliation record](../verification/paper_sync/README.md) retains the exact source diff and documents current-path and execution-status corrections. Historical cleanup and PDF-intake records continue to describe their original state.

The archive is evidence retention, not approval to rerun old cohorts or publish their contents. Human review, disclosure scope, authorship, licensing and venue gates remain separate from byte integrity.
