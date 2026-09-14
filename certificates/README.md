# Finite certificates and independent checking

These inherited finite-model artifacts support the paper's conditional theory. They are not real-model or deployment certificates.

- `data/full_class_certificates.json` and `data/certificates.json` contain the full and restricted comparison classes.
- `code/check_certificates.py` independently validates rational inequalities and bounds using `code/exact_math.py`. It does not import the optimizer and needs only the Python standard library.
- `code/finite_model.py`, `threshold_design.py` and `boundary_checks.py` preserve the original model/proposal code. Optimizer-based proposal generation is outside the default reproduction workflow and can need additional packages.
- [THEORY.md](THEORY.md) preserves the detailed inherited theory report; historical path references can be resolved through `archive/INDEX.json`.

`make reproduce` checks both certificate sets: 38 cases and 2,031 constraints. Rechecking a finite certificate is neither a new model experiment nor an independent human proof review. A restricted candidate class cannot confer assurance on the full class.
