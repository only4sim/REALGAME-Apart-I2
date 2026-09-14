# Reproducing the current artifact

All commands below start at the repository root. Core verification uses the Python standard library; no installation, account, API key or network is required. Use Python 3.10 or newer. `requirements.txt` intentionally has no third-party dependencies.

## Recommended offline workflow

```bash
make reproduce
```

Each invocation creates a fresh `build/reproduction-<UTC timestamp>/`. Read `summary.json` and the individual `.log` files there. The command stops at the first failure and preserves its outputs.

The workflow runs the unit tests, verifies current evidence and historical archive hashes, checks both finite certificate sets, reanalyzes the 20 saved pilot episodes, independently reconstructs 102 allowed request histories, and reconciles official-client usage. It compares the regenerated pilot analysis with the saved analysis. These are reproduction checks, not additional scientific observations.

For a chosen fresh output location:

```bash
python3 scripts/reproduce.py --out build/my-reproduction
```

`results/` and `archive/` are inputs. Outputs must not be written into either. Existing output directories are rejected. No command in `make reproduce` imports credentials or invokes an inference client.

## Individual entry points

```bash
make test
mkdir -p build
python3 scripts/verify_repository.py
python3 scripts/analyze_codex_pilot.py \
  --input results/codex_subscription_pilot_v8_01/runs.jsonl \
  --out build/pilot-analysis.json
python3 scripts/audit_frozen_payloads.py \
  --cohort results/codex_subscription_pilot_v8_01 \
  --out build/pilot-payload-audit.json
```

Choose fresh output files. The full workflow creates their parent directories automatically. For individual commands, create `build/` first if needed. Every saved client response is under `results/codex_subscription_pilot_v8_01/requests/`; `visible_records.jsonl` is a convenience representation of those same responses, not additional observations.

`certificates/code/check_certificates.py` independently checks the finite rational certificates without the optimizer or SciPy. `make reproduce` checks both files in `certificates/data/`; together they contain 38 cases and 2,031 checked constraints. See [certificate scope](../certificates/README.md).

## Optional complete CPU regeneration

The default workflow audits the saved CPU records. To explicitly regenerate the original scripted study:

```bash
python3 scripts/run_local.py --out build/cpu-regenerated
```

The directory must be fresh. Compare its seven output files with the corresponding files directly under `results/`. This command repeats the historical scripted study; it creates no independent model evidence. It is intentionally excluded from the default workflow.

## Manuscript source and rendering

```bash
make paper-source
make doctor
```

`paper/submission_blocks.json` is the authoritative build input, reconciled with the author-supplied PDF. `make paper-source` exports `paper/manuscript.md`, with correct relative figure links. Source checks enforce 150 abstract words, eight main source groups, the required disclosure sections, and four one-month extensions. Eight source groups are not proof of eight rendered pages.

The [paper v1 PDF](../paper/Certifying%20Behavior%20Without%20Hiding%20the%20Sandbox%20v1.pdf) governs the author block and abstract. The source also incorporates its scientific text, tables and disclosures; [documented corrections](../verification/paper_sync/README.md) update repository paths and build/verification status. The new source has not yet passed a typeset rebuild. Figure 1 links to page 1 of the supplied PDF in Markdown; `scripts/make_figures.py` generates its PNG/PDF from saved pilot analysis when the optional toolchain is available. The supplied [deck PDF](../slides/REALGAME_deck.pdf) is available for reading; its editable source and build instructions are still pending. Neither supplied PDF is overwritten by these commands.

The current host lacks the optional rendering toolchain. On an approved build host, provision the dependencies in `requirements-paper.txt`, Pandoc, LibreOffice and a locally installed Old Standard font. The recorded historical reference environment was Python 3.13.5, Pandoc 3.1.11.1 and LibreOffice 25.2.3.2; its package versions are pinned in the optional requirements file. The original version record is recoverable as historical key `verification/software_versions.json`.

The optional Python packages can be installed by the operator in a dedicated environment on that build host:

```bash
python3.13 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-paper.txt
```

Pandoc, LibreOffice and the font remain system prerequisites. An already installed Old Standard font may be registered locally:

```bash
python3 scripts/register_existing_fonts.py --apply
make paper
```

No command here downloads fonts. `make paper` checks dependencies before building, regenerates figures from saved data, and writes DOCX/PDF, structural checks and page images under `build/paper/`. It fails clearly if the toolchain is missing. Inspect every page image; require eight main pages with references beginning on page nine, the original Letter geometry, one-inch margins and readable Old Standard type. See [release checks](RELEASING.md) before packaging rendered artifacts.

## Fresh inference is separate

No saved approval is a grant to launch new observations. The 20-episode subscription pilot is complete; its global allowance ledger must remain in place and must not be reset. Its exact source/configuration freeze is in the cohort's `source_snapshot/` and `frozen_plan.json`.

Current maintenance code can differ from that snapshot. Never resume a historical cohort after source changes. A new experiment requires its own explicit approval, model/settings/access checks, billing controls, protocol and fresh freeze. The API and official-client routes retain separate gates. See [configuration scope](../configs/README.md) and [protocol amendment](../access/PROTOCOL_AMENDMENT.md).
