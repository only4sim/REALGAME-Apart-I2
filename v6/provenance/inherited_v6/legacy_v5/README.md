# Target-specific behavioral certification — v0.5

## Status

This release continues the same question: which deployment behaviors can be evaluated despite detectable simulation, and which remain unidentified because safe evaluations cannot provide necessary preceding information?

It supplies mathematical results and local finite-model verification. **No LLM experiment was run.** No probability matrix or script in this package establishes operational containment, model intent, or transport to an actual deployment. The theory needs independent specialist review. It is not proof-assistant certified.

## Read first

- `paper_theory_core.pdf` / `.md`: compact paper-ready theory draft. Provisional typesetting, not an official venue template.
- `theory_report.pdf` / `.md`: complete statements, proofs, scope restrictions, comparisons, red-team audit, and verification description.
- `claim_ledger.json`: individual claims, evidence, assumptions, and remaining checks.
- `verification/full_class_certificates.json`: the primary unrestricted-agent results, including exact indistinguishable cross-threshold pairs.
- `verification/full_class_check.json`: independent standard-library certificate check.

## Main results

1. A cross-threshold equal-law pair blocks complete, uniformly sound certification under all allowed adaptive reset audits.
2. With a finite compact convex model and known audit/target maps, positive directed information permits an anytime-valid certificate. Its first-order minimax expected cost is `log(1/delta)/Gamma` as `delta` tends to zero with the model and risk thresholds fixed.
3. Virtual observation regularization handles zero probabilities without changing agents, raw logs, or physical environments. The computed score is pulled back deterministically to the original record.
4. In an explicitly narrower alarm-only model, the optimal false-certificate probability under clean completeness `1-eta` and budget `N` is exactly `(1-eta)*(1-beta)**N`.
5. A target-relevant uncovered-information mass creates a certification floor. Final sandbox detectability alone does not specify that mass.

## Reproduction

Tested with Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0. The certificate checker and boundary calculations need only Python's standard library. Optimization uses SciPy, not a conic solver. Install the proposer dependencies from `requirements.txt` in a suitable environment.

Run from this directory:

```bash
python code/check_certificates.py verification/full_class_certificates.json --output full_class_recheck.json
python code/check_certificates.py verification/certificates.json --output restricted_recheck.json
python code/boundary_checks.py --output boundary_recheck.json

# Recompute candidate designs; all claimed certificates are checked separately.
python code/threshold_design.py --full-class --output full_class_recomputed.json
python code/check_certificates.py full_class_recomputed.json --output full_class_recomputed_check.json
python code/threshold_design.py --output restricted_recomputed.json
python code/check_certificates.py restricted_recomputed.json --output restricted_recomputed_check.json
```

The **default** design run deliberately restricts the agent mixture to minimum coordinate mass. Its results are a comparison, not assurance for all agents. `--full-class` is the primary test: it imposes no such strategy restriction. Its optimization uses virtual smoothing `1/1000`; scores are evaluated and certified on original record laws.

The proposer records every final case, numeric solver status, and allocation fallback. Exact rational normalization enforces the null moment constraint; numerical optimizer success is never treated as a certificate. Information brackets use rigorous rational log bounds and outward dyadic rounding. The independent checker regenerates hypothesis-polytope vertices, checks all null moments and good log drifts, validates the counterexample pair, and checks the directed-information bound. It shares the elementary rational interval arithmetic module with the proposer; it is not an independently developed proof kernel.

## Files and provenance

`finite_model.py` is carried forward from the project's v0.4 artifact. Its small two-decision tree supports endogenous agent action selection and history-dependent responses. Full policy mixtures are represented by distributions over eight pure strategies. These toy instances do not exhaust the model class in the theorem.

`exact_math.py` contains rational arithmetic and rigorous logarithm intervals. `threshold_design.py` proposes and certifies finite audit scores. `check_certificates.py` verifies saved certificates without NumPy or SciPy. `boundary_checks.py` checks exact zero-alarm budgets, 128 three-step adaptive alarm-controller rules, and a 200-step evidence-crossing dynamic program.

`notes/v4_rechecked.json` records a rerun of the earlier artifact's certificate checker only: 35 cases and 382 constraints. We did not rerun all v0.4 experiments or obtain independent academic review.

The three `attempt*failure.log` files preserve development failures (serialization, simplex rounding, and numerical allocation proposal). All 38 final design cases were subsequently retained and checked. None of those logs is an agent failure or an LLM run.

`verification/build_verification.json` records page/abstract counts, exact output hashes, and clean-directory reproduction. Raw third-party PDFs and fonts are not redistributed in this package.

## Rebuild documents

Pandoc and a LaTeX installation with the listed standard packages are needed:

```bash
pandoc theory_report.md --pdf-engine=pdflatex -o theory_report.pdf
pandoc paper_theory_core.md --pdf-engine=pdflatex -o paper_theory_core.pdf
```

Rebuilt PDF bytes may differ because of PDF metadata. JSON verification outputs reproduced byte-for-byte in a clean working directory in the tested environment.

## Submission gates

Independently review the zero-support limit, stopping-time lower bound, exact alarm-only scope, and minimax quantifiers. Check overlap with Safe Testing, convex testing, and interactive estimation before making novelty claims. Justify deployment and reset assumptions before any actual safety assertion. Obtain the official template and verify authorship requirements. Review dual use and report all missing LLM outcomes honestly.
