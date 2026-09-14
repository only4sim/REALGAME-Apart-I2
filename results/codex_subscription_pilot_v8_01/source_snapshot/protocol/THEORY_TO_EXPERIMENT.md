# Theory-to-experiment contract

## Proposition R: conditional robustness of an audit e-process
Let F_(t-1) contain the complete audit past. Before observing round t, choose a nonnegative score e_t on the joint controller-record outcome, with finite predictable oscillation r_t = sup e_t - inf e_t. For each agent in the specified high-risk null, suppose a nominal conditional law P_t satisfies E_(P_t)e_t <= 1 + nu_t, where nu_t >= 0 is a certified numerical slack. Suppose the actual conditional law Q_t has TV(P_t,Q_t) <= eta_t almost surely at every round. The bounds and scores are chosen before the current observation. Then

    Z_n = product_(t=1)^n e_t / (1 + nu_t + eta_t*r_t)

is a nonnegative supermartingale under the actual null, with Z_0=1. In particular, P(sup_n Z_n >= 1/delta) <= delta.

Proof. The bounded-function characterization of total variation gives E_(Q_t)e_t <= E_(P_t)e_t + eta_t*r_t <= 1+nu_t+eta_t*r_t. Divide and condition on F_(t-1), then multiply by the preceding product. Apply the maximal inequality for nonnegative supermartingales. Adaptive controller selection is covered only when the joint conditional-law bound covers that selection. Marginal calibration does not suffice. This is an elementary robustification of existing e-process theory, not a new general testing principle.

Tight one-step example: nominal P(Y=1)=7/10, actual Q(Y=1)=7/10-eta, e(0)=5/3, e(1)=5/7. The actual mean is exactly 1 + (20/21)eta. Thus the proposed normalizer cannot be reduced uniformly over a total-variation ball for these scores.

Power limitation. Normalization can eliminate growth. A corrected non-crossing run is unresolved, not a certificate. There is no universal guarantee that a robust score will still certify a low-risk agent quickly.

If a separate frozen calibration study supplies a simultaneous envelope with error alpha, and subsequent audit runs are conditionally independent of that calibration given fixed kernels, the overall error is at most delta+alpha by conditioning and a union bound. An average empirical discrepancy, a confidence interval for one state, or a future-dependent good event is not such an envelope.

## Counterexample: marginal matching without reset
Draw B once with P(B=1)=7/10 and repeat B forever. Each round has exactly the nominal marginal distribution. On B=0, the nominal product reaches 20 at round six, so its crossing probability is 3/10. Conditional on the past, however, the true distribution is a point mass. A valid uniform conditional envelope eta=7/10 yields a normalizer 5/3, making every corrected factor at most one. It restores error control by giving up power.

## Experimental interpretation
E1 targets causal ordering: a post-decision diagnostic can reveal a condition without altering the earlier target. Prefix equality is a simulator-code obligation, while observed finite model differences are sampling estimates. E2 targets positive support versus zero support; large environment TV need not cause identification failure. E3 targets stability of the claimed testing procedure; it is not a test of agent morality.

The v5 directed-information theorem is retained as prior project theory under finite alphabets, compact convex behavioral classes, fixed agents, independent resets, known safe controllers, and a specified deployment reference. Its mathematical ingredients overlap Safe Testing and interactive estimation. This round does not claim a new universal simulator or a general real-deployment guarantee.
