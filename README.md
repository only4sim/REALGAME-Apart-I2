# Certifying Behavior Without Hiding the Sandbox

**Li Quan** · The Pioneer Centre for Artificial Intelligence, Denmark

Which claims about a specified deployment behavior can a safe audit support even when the simulation is detectable, and which depend on prerequisites the audit cannot provide?

This repository contains the author-supplied **paper PDF (v1)** and **presentation deck**, together with synchronized editable manuscript source, reproducible code and recorded evidence. The completed client-pilot protocol remains v8. It has not been submitted or published by this execution.

| Component | Current status | Entry point |
|---|---|---|
| Paper | Author-supplied PDF, 14 pages; references begin on page 9 | [Read the paper](paper/Certifying%20Behavior%20Without%20Hiding%20the%20Sandbox%20v1.pdf), [source and version notes](paper/README.md) |
| Code and evidence | Offline checks and saved-pilot reanalysis need only Python 3.10+ | [Reproduction guide](docs/REPRODUCING.md) |
| Presentation | Author-supplied PDF, 6 slides | [View the deck](slides/REALGAME_deck.pdf), [deck notes](slides/README.md) |
| Release preparation | Rebuild and inspect the editable paper, then complete scientific review and licensing | [Release guide](docs/RELEASING.md) |

The [editable manuscript](paper/manuscript.md) follows the supplied PDF's author block, exact 150-word abstract, scientific text, tables and disclosures. Repository paths and execution-status statements have been corrected where necessary; see the [reconciliation record](verification/paper_sync/README.md). The updated source has not yet been typeset on this host. File hashes and check scope are recorded in [the artifact inventory](verification/publication_artifacts.json).

## Reproduce the recorded results

From the repository root:

```bash
python3 scripts/reproduce.py
# Equivalent convenience target:
make reproduce
```

The command runs offline tests, verifies immutable evidence and frozen source hashes, checks finite certificates, reconstructs all pilot request histories, and reanalyzes the saved pilot and usage ledger. It writes logs into a fresh `build/reproduction-…/` directory. It does not call a model, use credentials, regenerate a CPU study, or replace recorded evidence.

## Evidence at a glance

- Historical mechanism evidence: 960 scripted episodes. These are not model observations.
- Real exploratory pilot: 20/20 completed Codex-client-system episodes through 102 official-client turns; all 20 actions followed the standard rule, and both probability reports were retained in every episode.
- Requested subject: `gpt-6-astra`, medium effort, Codex 0.154.0. Effective per-turn model IDs, dollar cost and credit consumption were unavailable and remain null.
- The original raw-API main study remains prospective. The pilot does not establish internal beliefs, equivalence, intent or deployment safety.

See [results and limitations](docs/RESULTS.md), the [pilot execution report](docs/PILOT_RUN_REPORT.md), and the [claim ledger](paper/claim_ledger.json).

## Repository layout

| Directory | Purpose |
|---|---|
| `paper/`, `template/`, `figures/` | Supplied paper PDF, synchronized editable source, original Apart template and figures from saved data |
| `src/`, `scripts/`, `tests/` | Benchmark implementation, explicit entry points and offline tests |
| `results/` | Canonical scripted results and the immutable real pilot, including its source freeze |
| `certificates/` | Finite certificates, independent checker and supporting theory |
| `protocol/`, `access/`, `configs/` | Experimental specification, historical access evidence and separately gated inference configuration |
| `verification/` | Evidence manifest and retained v8 verification records |
| `docs/`, `slides/` | User documentation and the supplied presentation PDF |
| `archive/` | Indexed, deduplicated history; excluded from normal execution paths |
| `build/` | Regenerable local outputs, ignored by Git |

Use `make help` for the supported commands. See the [cleanup execution record](docs/EXECUTION_REPORT.md) for validation. The [provenance guide](docs/PROVENANCE.md) explains what was removed from the active tree and how to recover any historical file. Old v7 PDF/DOCX are archived rather than presented as current v8 documents.
