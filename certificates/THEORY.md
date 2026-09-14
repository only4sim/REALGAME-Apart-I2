> Inherited theory supplement. Original numerical claims and formulas are preserved below; historical paths refer to the pre-cleanup layout. Current checker/data entry points are in README.md. The current manuscript is paper/manuscript.md at repository root.

---
title: "When Can Contained Evaluations Certify Deployment Behavior?"
subtitle: "Target-specific identification, anytime-valid certification, and uncovered-information floors"
author: "Research collaboration draft — independent theoretical review required"
date: "14 September 2026 · Theory extension v0.5"
lang: en-US
fontsize: 11pt
geometry: margin=1in
colorlinks: true
linkcolor: black
urlcolor: black
toc: true
toc-depth: 2
header-includes:
  - \usepackage{amsmath,amssymb,mathtools,booktabs,longtable,microtype,fancyhdr}
  - \pagestyle{fancy}
  - \fancyhf{}
  - \fancyhead[L]{\small Behavior Certification After Sandbox Detection}
  - \fancyhead[R]{\small v0.5}
  - \fancyfoot[C]{\thepage}
  - \setlength{\headheight}{14pt}
  - \setlength{\emergencystretch}{3em}
---

# Abstract

An agent's ability to recognize a sandbox does not determine whether a particular deployment behavior can be evaluated. We study a more operational question: can safe interactions support a uniformly valid certificate that a specified behavior occurs below a risk threshold? In a finite resettable model, we characterize certification by separation of low- and high-risk agents through allowed audit controllers. A relative-entropy quantity determines the first-order minimax expected audit cost as the permitted false-certificate probability vanishes. The construction remains valid under optional stopping and handles zero-probability observations through virtual regularization without modifying logs or restricting agents. A separate exact alarm-only result identifies a risk floor caused by uncovered decision-relevant information. Rational certificates validate finite examples; no LLM experiments are reported. The principal limitations are the specified deployment model, reset assumption, and unresolved empirical transport.

# 1. What this extension does and does not establish

The question remains unchanged: which behaviors can be evaluated despite detectable simulation, and which cannot be identified because safe evaluations cannot provide the relevant preceding information? The v0.4 report answered a scalar estimation problem under mean-squared error. This extension addresses a different statistical obligation within the same research question: a procedure must control the probability of **ever certifying a high-risk agent as low-risk**, including when the evaluator chooses its stopping time after observing results.

A mean-squared error guarantee is not automatically a small-risk certificate. Markov's inequality could convert it into one, but may give a poor bound near zero. Conversely, a procedure that never certifies anyone is trivially sound. We therefore require both uniform soundness above a risk threshold and eventual certification below a separated lower threshold. The distinction between the two thresholds is intentional; no positive-power guarantee is imposed in the indifference interval.

The new results have four components. First, a general finite-model theorem relates one-sided certification to an information game over low-risk agents, high-risk agents, and safe audit controllers. Second, virtual observation regularization removes a full-support assumption without excluding deterministic agents or changing raw logs. Third, an exact alarm-only theorem quantifies what zero observed failures can and cannot certify. Fourth, a counterexample shows that changing the audit randomization after constructing a score can destroy its validity.

The statistical foundations are established prior work: growth-optimal e-variables [R4], convex composite testing [R5–R6], and controlled-experiment change-of-measure lower bounds [R7]. This report does not claim to invent these tools. The proposed AI-safety contribution is the target-specific containment formulation, the explicit relation between unavailable preceding information and certifiable risk thresholds, and executable certificates or counterexample agents. Priority for the exact combination remains unresolved.

## 1.1 Reverse audit of v0.4

The full v0.4 source, not only its conversational summary, was read. Its standard-library certificate checker was rerun: all 35 stored cases and 382 rational constraints passed. The proof obligations around convexity, independent resets, complete input modeling, and a specified deployment reference remain necessary. This is not a fresh independent peer review or a rerun of every previous experiment.

No mathematical counterexample to the stated v0.4 bounds was found in this round. Its factor-64 statement concerns worst-case mean-squared risk, not a factor-64 guarantee for rare-event certification or sample counts. Its median-of-means extension is a valid conservative bridge, not an optimality theorem for one-sided certification. The new theorem is therefore not a claim that the old one was false.

A source check also narrows novelty. Chen et al. [R8], Appendix E.2, Proposition E.4 and Remark E.5, already cover interactive estimation and nearly tight complexity characterizations. Grünwald et al. [R4], Section 3, Theorem 1 (First Generalisation), already obtain growth-optimal composite e-variables from joint information projections. Neither interactive estimation nor composite e-value construction is a new problem introduced here.

# 2. Finite interactive model and the certification question

## 2.1 Agents, controllers, and observations

A complete run has a fixed finite horizon and an explicitly specified action-observation tree. Histories contain every world-correlated input available to the agent: tool outputs, errors, latency if visible, framing, identifiers, and persistent-state observations. The agent may actively select probes, change plans after responses, and use private randomness and memory within the run. No private chain-of-thought is observed or treated as ground truth.

Represent the agent by a realization plan $x$ in a nonempty compact convex set $\mathcal X$. For the unrestricted finite behavioral class, the realization constraints have the form $x\ge0,Gx=g_0$. This is a behavioral representation, not convexity of neural-network weights. Random mixtures of legal strategies remain legal; additional trusted restrictions must be stated explicitly. The representation is standard sequence form [R9].

Each allowed safe audit $E_j$, $j\in\{1,\ldots,m\}$, is a complete causal closed-loop controller. It can respond adaptively inside a run. Its known logging map gives the finite distribution

$$
p_j(x)=M_jx\in\Delta(\mathcal L_j).
\tag{1}
$$

A declared deployment reference $W$ and bounded target behavior $\ell$ induce

$$
J(x)=c^\top x\in[0,1].
\tag{2}
$$

The target can end immediately after a selected action, before an environment response. It cannot delete information that already influenced that action. The linear factorization follows by multiplying environment-response probabilities by agent action-realization weights and summing over the logger's output categories. Conditional probabilities for the same complete history must refer to the same agent initialization law. Omitted side channels invalidate this mapping.

Each run starts from an independent reset of the same fixed $x$. The evaluator may choose the next controller based on all previous records. Thus within-run agent adaptivity, within-run controller adaptivity, and between-run evaluator adaptivity are distinct; all three are represented. The budget counts reset runs, not tokens, wall-clock time, or heterogeneous costs.

Containment is an independently verified constraint on the controllers, such as no unauthorized agent-caused transition outside a declared protected boundary. A probability matrix does not establish that an implementation satisfies physical containment. All code in this release is local mathematical simulation.

## 2.2 Unsafe is the null hypothesis

Fix $0\le\tau_0<\tau\le1$ and define nonempty compact convex classes

$$
\mathcal G=\{x\in\mathcal X:J(x)\le\tau_0\},\qquad
\mathcal B=\{x\in\mathcal X:J(x)\ge\tau\}.
\tag{3}
$$

The statistical null is $\mathcal B$, the high-risk class. A certificate rejects that null. Failure to find a violation is not, by definition alone, a certificate.

For a procedure $\mathcal A$, let $T$ be its first certificate time, allowing $T=\infty$. **Uniform $\delta$-soundness** means

$$
\sup_{x\in\mathcal B}\Pr_x^{\mathcal A}(T<\infty)\le\delta.
\tag{4}
$$

**Full low-risk completeness with finite expected cost** means

$$
\sup_{x\in\mathcal G}\mathbb E_x^{\mathcal A}T<\infty.
\tag{5}
$$

Equation (5) implies eventual certification with probability one for each low-risk agent. It does not promise a fixed finite deadline. Above threshold, the procedure can run forever or be externally capped with an explicit no-certificate result. A finite deadline changes the completeness criterion; it does not permit silently counting unresolved runs as safe.

The minimax expected certification cost is

$$
C_\delta=\inf_{\mathcal A\text{ satisfying (4)}}\;
\sup_{x\in\mathcal G}\mathbb E_x^{\mathcal A}T.
\tag{6}
$$

Returning no certificate forever gives infinite cost in (6). The thresholds are externally chosen specifications, not assertions that any particular numerical risk is acceptable. A certificate has a frequentist error guarantee, not a posterior probability that the system is safe, and it is relative to the modeled target and agent class.

## 2.3 Compact notation

| Symbol | Meaning |
|:--|:--|
| $x,\mathcal X$ | Fixed agent realization plan and convex legal class |
| $M_jx$ | Logged law under a complete safe controller |
| $c^\top x$ | Specified deployment behavior probability or bounded expectation |
| $\mathcal G,\mathcal B$ | Low-risk and high-risk hypothesis classes |
| $\tau_0,\tau$ | Completeness and soundness risk thresholds |
| $\delta,T,C_\delta$ | False-certificate budget, certificate time, minimax expected cost |
| $\Gamma,\Gamma_\epsilon$ | Original and virtually regularized information values |
| $w_j,f_j$ | Audit allocation and nonnegative evidence factor |
| $Z_n$ | Product evidence at completed-run boundaries |
| $\beta(\tau)$ | Optimal unavoidable alarm probability above threshold |
| $u,a$ | Uncovered target mass and safe exposure rate in the gate example |

# 3. Population obstruction and the role of decision timing

## Proposition 1 — A cross-threshold indistinguishable pair forbids certification

If $x_g\in\mathcal G$ and $x_b\in\mathcal B$ satisfy

$$
M_jx_g=M_jx_b\qquad\forall j,
\tag{7}
$$

then every allowed adaptive evaluator has the same full audit-history law under the two agents. Consequently a $\delta$-sound procedure certifies $x_g$ with probability at most $\delta$. In particular, (5) is impossible for $\delta<1$.

**Proof.** Condition on any common previous record. The evaluator uses the same random rule for choosing its next controller. Under that controller, (7) gives the same next-record law. Induct over runs, including stopping decisions and private evaluator randomness. Every finite certificate event has the same probability; taking their increasing union proves the assertion for eventual certification. $\square$

This is stronger than observing that the actual LLM has not yet found a distinguisher. It is a pair of fully specified candidate policies that *all* the allowed audits fail to separate, despite their targets lying on opposite sides of the certification thresholds. Conversely, it does not prove that a named LLM implements either policy or can discover the relevant trigger.

## 3.1 Target-specific information cuts, carried forward

For full logs and the unrestricted finite history-dependent class, let $\mathcal R$ be all histories that some allowed safe environment can produce with positive causal likelihood. At a first deployment exit $h$ from $\mathcal R$, let $\mu_x(h)$ be its probability and $v^-_\ell(h),v^+_\ell(h)$ the minimum and maximum attainable continuation values of the target. The previous target-specific result gives the sharp interval

$$
\left[b_{x,\ell}+\sum_h\mu_x(h)v^-_\ell(h),\quad
b_{x,\ell}+\sum_h\mu_x(h)v^+_\ell(h)\right].
\tag{8}
$$

Supported action conditionals are determined by full audit laws. First-exit subtrees are disjoint and never visited in safe audits, so choosing extremal continuations there preserves every safe audit law. This proves the endpoints; random mixtures attain intermediate values. The proof assumes unrestricted continuation choices and complete histories, not arbitrary coarsened logs.

A world label revealed after a completed target decision has continuation span zero. The same deployment-only label before a free decision can have span one. Thus final sandbox detectability does not determine (7) or (8). Familiar identical-until-bad arguments [R10] explain prefix invariance, but do not by themselves provide the threshold cost derived below.

Penumbra's distinguishing game and independent-consequence proposition concern available world signals [R1, Section 2 and Section 5, Proposition 1]. Kovařík et al. already discuss deployment-specific green lights and the failure of repeated testing [R2, Section 3.1.4]. The present distinction is target-specific: a signal matters to certification only through the decision behavior left unconstrained by safe evidence.

# 4. Main result: the first-order cost of threshold certification

For distributions $p,q$ on a finite alphabet, use the usual relative entropy

$$
D(p\Vert q)=\sum_{\ell:p_\ell>0}p_\ell\log(p_\ell/q_\ell),
$$

with infinity when $p_\ell>0=q_\ell$. Define

$$
\boxed{
\Gamma=\min_{x_g\in\mathcal G,\,x_b\in\mathcal B}
\max_jD(M_jx_g\Vert M_jx_b).
}
\tag{9}
$$

The direction of the divergence matters: expected certification cost is evaluated under the low-risk agent, and the certificate rejects the high-risk null. This is not a transcript distance between an evaluation environment and deployment for one fixed agent; it compares two candidate agents under allowed audits.

## Theorem 1 — Threshold certification without a full-support assumption

Assume the finite reset model (1)–(3), known maps and target, and a compact convex legal agent class. No strict positivity of the original probabilities is required.

**Identifiability boundary.** $\Gamma=0$ if and only if a pair satisfying (7) exists. If so, $C_\delta=\infty$ for every $\delta<1$. If $\Gamma>0$, a uniformly sound finite-expected-cost certifier exists for every $\delta\in(0,1)$.

**Finite cost bounds.** If $0<\Gamma<\infty$, then

$$
\boxed{C_\delta\ge\frac{\log(1/\delta)}{\Gamma}.}
\tag{10}
$$

For any $\epsilon\in(0,1)$ with $\Gamma_\epsilon>0$, the construction in Sections 5–6 gives

$$
\boxed{
C_\delta\le
\frac{\log(1/\delta)+\log(d_{\max}/\epsilon)}{\Gamma_\epsilon},
}
\tag{11}
$$

where $d_{\max}=\max_j|\mathcal L_j|$ and $\Gamma_\epsilon\uparrow\Gamma$ as $\epsilon\downarrow0$.

**First-order optimality.** With the model and thresholds fixed and $0<\Gamma<\infty$,

$$
\boxed{
\lim_{\delta\downarrow0}
\frac{C_\delta}{\log(1/\delta)}=\frac1\Gamma.
}
\tag{12}
$$

The upper construction selects a fixed randomized mixture of complete controllers across reset runs. The lower bound permits arbitrary adaptive controller selection and arbitrary computation. Within each run, both the controller and agent remain adaptive. The logarithmic first-order statement is not an exact finite-$\delta$ minimax formula; $\Gamma=\infty$ is a singular case for which (11) still provides finite certificates but (12) is not needed.

**Interpretation.** A high-risk agent can only receive a false certificate with the declared probability, even if the evaluator keeps checking until evidence looks favorable. When low- and high-risk agents cannot be separated through any allowed audit, no stopping rule repairs the missing evidence. When they can be separated, the theorem identifies the leading expected audit cost as confidence increases.

This is a specialization and integration of classical composite e-testing and controlled-experiment theory [R4–R7]. It is a new result within the present project, not an established claim of a new general statistical principle.

# 5. Proof in the strictly positive case

This section is a lemma used for the zero-probability theorem, not an additional assumption silently imposed on real agents.

Suppose all retained record probabilities are uniformly positive on the compact classes. For a fixed audit allocation $w\in\Delta_m$, set

$$
F(w,x_g,x_b)=\sum_jw_jD(M_jx_g\Vert M_jx_b).
\tag{13}
$$

It is linear in $w$ and convex in the pair $(x_g,x_b)$. The compact convex minimax theorem gives

$$
\Gamma=
\max_w\min_{x_g,x_b}F(w,x_g,x_b)
=
\min_{x_g,x_b}\max_wF(w,x_g,x_b).
\tag{14}
$$

Take a saddle allocation $w^*$ and a minimizing pair $x_g^*,x_b^*$. Define

$$
e_j(\ell)=\frac{(M_jx_g^*)_\ell}{(M_jx_b^*)_\ell}.
\tag{15}
$$

Two different first-order optimality conditions supply validity and power.

## Lemma 1 — Composite-null moment and low-risk log drift

The pair and allocation above satisfy

$$
\sum_jw_j^*\mathbb E_{M_jx_b}e_j(L)\le1
\quad\forall x_b\in\mathcal B,
\tag{16}
$$

and

$$
\sum_jw_j^*\mathbb E_{M_jx_g}\log e_j(L)\ge\Gamma
\quad\forall x_g\in\mathcal G.
\tag{17}
$$

**Proof.** Differentiate (13) along the feasible direction $x_b-x_b^*$ while fixing $x_g^*$. Nonnegativity of the directional derivative gives

$$
-\sum_{j,\ell}w_j^*e_j(\ell)
\big[(M_jx_b)_\ell-(M_jx_b^*)_\ell\big]\ge0.
$$

Since $\sum_jw_j^*\sum_\ell(M_jx_g^*)_\ell=1$, this is (16). Differentiate along $x_g-x_g^*$ while fixing $x_b^*$. The derivative is the difference of expectations of $1+\log e$. Normalization cancels the constant term, yielding (17). $\square$

Equation (16) generally holds only after averaging the **joint random controller choice and its record**. It need not hold conditional on each controller separately. This distinction is essential to the counterexample in Section 9.

## 5.1 The evidence product and stopping rule

At each completed run draw $J_n\sim w^*$ independently, obtain $L_n$, and update

$$
Z_0=1,\qquad Z_n=\prod_{t=1}^ne_{J_t}(L_t).
\tag{18}
$$

Under each fixed high-risk agent, (16) gives
$\mathbb E[Z_n\mid\mathcal F_{n-1}]\le Z_{n-1}$ at completed-run boundaries. Such a nonnegative process is a supermartingale: conditional expectation does not increase. For

$$
T=\inf\{n:Z_n\ge1/\delta\},
\tag{19}
$$

optional stopping at $T\wedge n$ gives
$1\ge\mathbb E Z_{T\wedge n}\ge\delta^{-1}\Pr(T\le n)$.
Taking $n\to\infty$ proves (4). This is the standard e-process/Ville argument [R4], stated here to make the stopping guarantee explicit.

Let $h=\log(1/\delta)$ and $L=\max(0,\max_{j:w_j^*>0,\ell}\log e_j(\ell))$. Under a fixed low-risk agent, log increments have mean at least $\Gamma$. They are bounded on a finite positive alphabet. For every $n$,

$$
\Gamma\mathbb E(T\wedge n)
\le\mathbb E\log Z_{T\wedge n}\le h+L.
$$

The first inequality follows by summing conditional drifts before stopping. For the second, before crossing the log capital is below $h$, and the crossing overshoot is at most $L$. Monotone convergence proves finite expected stopping and

$$
\sup_{x_g\in\mathcal G}\mathbb E_{x_g}T\le(h+L)/\Gamma.
\tag{20}
$$

## 5.2 Lower bound for every adaptive certifier

For the saddle pair, $D(M_jx_g^*\Vert M_jx_b^*)\le\Gamma$ for every controller $j$. The pair is chosen before the evaluator's random choices or realized data. Condition on any common past: the evaluator selects its next controller using the same rule under both alternatives. The KL chain rule, with absorption after certification, yields

$$
D(P_g^{T\wedge n}\Vert P_b^{T\wedge n})
\le\Gamma\mathbb E_g(T\wedge n).
\tag{21}
$$

Apply data processing to the event $\{T\le n\}$. If the procedure has finite expected certification time under all low-risk agents, its probability under $g$ tends to one. Soundness bounds the corresponding probability under $b$ by $\delta$. Binary relative entropy therefore gives, in the limit,

$$
\Gamma\mathbb E_gT\ge\log(1/\delta).
$$

The proof uses finite truncations and does not incorrectly assume that certificate time is finite under a high-risk agent. It remains valid whenever the selected pair has finite directed KL, even if some original record probabilities are zero. This proves (10). The underlying change-of-measure method is standard [R7, Lemma 1]; here it is used for one-sided certification, rather than probability estimation.

# 6. Removing zeros without changing the agent or the logs

## 6.1 Why forced policy randomness is not an innocuous repair

Suppose a safe environment always gives observation $O=0$, while deployment gives a fair $O\in\{0,1\}$. The target is the agent's subsequent binary action. One agent chooses action one with probability $1/2$ at $O=0$ and zero at $O=1$; another chooses $1/2$ at $O=0$ and one at $O=1$. Safe laws are identical, while deployment risks are $1/4$ and $3/4$.

Imposing a positive minimum probability on every pure strategy can exclude those endpoints and shrink the maximum hidden risk gap. That changes the legal agent class and can turn an impossible threshold test into a possible one. It cannot be justified merely as a way to make logarithms finite. The restricted-class and unrestricted-class numerical suites deliberately demonstrate this difference.

## Lemma 2 — Virtual regularization and deterministic score pullback

Let $u_j$ be the uniform distribution on $\mathcal L_j$, and define only for the optimization

$$
p_j^\epsilon(x)=(1-\epsilon)M_jx+\epsilon u_j.
\tag{22}
$$

This leaves $\mathcal X$, the target, the environment, and the actual records unchanged. Define

$$
\Gamma_\epsilon=
\min_{x_g\in\mathcal G,x_b\in\mathcal B}
\max_jD(p_j^\epsilon(x_g)\Vert p_j^\epsilon(x_b)).
\tag{23}
$$

All regularized probabilities are positive, so Section 5 gives an allocation $w^\epsilon$ and factors $e_j^\epsilon$. Evaluate the following **deterministic score on the unmodified actual record**:

$$
\boxed{
 f_j^\epsilon(\ell)=
 (1-\epsilon)e_j^\epsilon(\ell)
 +\epsilon\mathbb E_{u_j}e_j^\epsilon.
}
\tag{24}
$$

It satisfies

$$
\sum_jw_j^\epsilon\mathbb E_{M_jx_b}f_j^\epsilon\le1,
\qquad
\sum_jw_j^\epsilon\mathbb E_{M_jx_g}\log f_j^\epsilon
\ge\Gamma_\epsilon.
\tag{25}
$$

**Proof.** The first expression equals the regularized expectation of $e^\epsilon$, so Lemma 1 applies. For the second, (24) is the conditional average of a factor passed through the virtual channel that keeps a symbol with probability $1-\epsilon$ and replaces it by a uniform symbol otherwise. Concavity of log gives

$$
\mathbb E_{M_jx_g}\log f_j^\epsilon
\ge\mathbb E_{p_j^\epsilon(x_g)}\log e_j^\epsilon.
$$

Sum with $w^\epsilon$ and apply Lemma 1. No virtual output needs to be generated, and no raw observation is replaced. Because every regularized denominator is at least $\epsilon/|\mathcal L_j|$, the factor is at most $d_{\max}/\epsilon$. The same stopping argument proves (11). $\square$

This is an ordinary stochastic-channel regularization and conditional-averaging argument, not a new cryptographic construction. Its role is to preserve the actual agent class and audit evidence while handling boundary probabilities.

## Lemma 3 — Convergence of the regularized information game

One has $\Gamma_\epsilon\uparrow\Gamma$ as $\epsilon\downarrow0$, allowing $\Gamma=\infty$.

**Proof.** Greater regularization is a further stochastic garbling: for $0<\epsilon_1<\epsilon_2<1$, its replacement probability is $(\epsilon_2-\epsilon_1)/(1-\epsilon_1)$. Data processing makes each pairwise KL, and hence its minimax value, nonincreasing with increasing $\epsilon$. Also $\Gamma_\epsilon\le\Gamma$.

Choose minimizing pairs along $\epsilon_n\downarrow0$ and extract a convergent subsequence using compactness. For fixed $\epsilon_0>0$ and eventually $\epsilon_n<\epsilon_0$, the objective at $\epsilon_0$ on those pairs is at most $\Gamma_{\epsilon_n}$. Continuity at the positive regularization $\epsilon_0$ gives the same inequality at the limiting pair. Let $\epsilon_0\downarrow0$. Finite-alphabet KL converges to its extended value, so the limiting pair has maximum original KL no greater than $\lim\Gamma_{\epsilon_n}$. Taking the minimum over all pairs proves the opposite inequality. $\square$

Nonnegative KL is zero precisely for equal distributions. Lower semicontinuity and compactness make the minimum in (9) attained when finite. Thus $\Gamma=0$ is exactly (7). If $\Gamma>0$, Lemma 3 supplies a positive $\Gamma_\epsilon$, proving existence. Finally set $\epsilon=\exp(-\sqrt{h})$ with $h=\log(1/\delta)$. Then the overshoot bound divided by $h$ tends to zero, while $\Gamma_\epsilon\to\Gamma$. Combine (10) and (11) to obtain (12).

# 7. Exact finite-budget result for zero observed alarms

The next result is deliberately narrower and requires no full-support approximation. It gives an exact finite-$N$ answer, but its lower bound is for an **alarm-only** observation model. It is not automatically a lower bound when full tool traces supply additional information.

For each safe controller let its sole data output be a binary alarm with probability

$$
a_j(x)=\Pr_x(\text{alarm in controller }j),
$$

affine in $x$. The auditor also observes its selected controller index. Assume at least one low-risk clean agent has $a_j(x_c)=0$ for every controller. Let $\mathcal B=\{x:J(x)\ge\tau\}$ be nonempty, compact, and convex. Define

$$
\boxed{
\beta(\tau)=\max_{w\in\Delta_m}\min_{x\in\mathcal B}\sum_jw_ja_j(x)
=\min_{x\in\mathcal B}\max_j a_j(x).
}
\tag{26}
$$

## Theorem 2 — Exact soundness/completeness tradeoff for alarm-only audits

Among all possibly randomized, adaptive procedures using at most $N\ge1$ alarm-only runs and certifying every clean agent with probability at least $1-\eta$, the smallest achievable worst-case false-certificate probability is

$$
\boxed{(1-\eta)(1-\beta(\tau))^N.}
\tag{27}
$$

**Upper bound.** Use an optimizing iid controller allocation $w^*$. Certify only after $N$ zero alarms, and then only with an independent coin of success probability $1-\eta$. Every high-risk agent has iid alarm probability at least $\beta$, so its certificate probability is at most (27). Every clean agent is certified with probability exactly $1-\eta$.

**Lower bound.** By the compact convex minimax theorem, there is a single high-risk $x_b^*$ with $a_j(x_b^*)\le\beta$ for every controller. Fix the evaluator's private random tape and follow its all-zero path, which is the path seen under a clean agent. Its controller choices and potential stopping may be adaptive, but the probability of every zero response under $x_b^*$ is at least $1-\beta$. For a path of at most $N$ runs, its likelihood relative to the clean path is at least $(1-\beta)^N$. Integrating over all tapes on which the clean agent receives a certificate, whose total probability is at least $1-\eta$, gives (27). Certificates after nonzero alarms cannot reduce this lower bound. $\square$

With full clean completeness ($\eta=0$) and $0<\beta<1$, the exact required budget for false-certificate probability at most $\delta$ is

$$
N_{\min}=\left\lceil\frac{\log(1/\delta)}{-\log(1-\beta)}\right\rceil.
\tag{28}
$$

If $\beta=0$, no finite budget gives soundness below the clean certification probability. If $\beta=1$, one run suffices. This is a minimax extension of the elementary zero-failure binomial calculation; it is not a new binomial confidence formula.

## Corollary 1 — An uncovered-information floor

Let a fraction $u$ of deployment target mass depend on a decision context inaccessible to every allowed safe audit. Write

$$
J(\theta)=(1-u)\theta_v+u\theta_u,
\qquad \theta_v,\theta_u\in[0,1].
$$

An allowed alarm-only audit exposes the visible decision with probability $a$, giving alarm probability $a\theta_v$; the hidden-context decision is never observed. Then

$$
\boxed{\beta(\tau)=a\left[\frac{\tau-u}{1-u}\right]_+}
\quad(0\le u<1).
\tag{29}
$$

**Proof.** Minimize $a\theta_v$ subject to $(1-u)\theta_v+u\theta_u\ge\tau$. Setting $\theta_u=1$ minimizes the required visible failure rate. If $\tau\le u$, choose $\theta_v=0$; otherwise choose $(\tau-u)/(1-u)$. $\square$

The threshold margin $\tau-u$, rather than raw test count, determines whether zero alarms can help. When $\tau\le u$, one high-risk agent never alarms under safe evaluation and is indistinguishable from a clean agent. The term $u$ is an explicit bound on target-relevant unobserved deployment behavior, not an empirical fraction of benchmark families, a textual classifier score, or the total variation of full world records.

For $\delta=0.05$, the exact arithmetic checker gives the following **analytical budgets**, not experimental LLM results:

| Exposure $a$ | Uncovered target mass $u$ | Risk threshold $\tau$ | $\beta(\tau)$ | Minimum runs |
|:--|:--|:--|:--|--:|
| $1$ | $0$ | $0.01$ | $1/100$ | 299 |
| $1/4$ | $0$ | $0.01$ | $1/400$ | 1,197 |
| $1/4$ | $0.005$ | $0.01$ | $1/796$ | 2,384 |
| $1/4$ | $0.01$ | $0.01$ | $0$ | Impossible uniformly |

For small positive $\beta$, (28) scales as $\log(1/\delta)/\beta$. This differs from a generic squared-error calculation near zero, but does not imply that all evaluation problems have the same favorable rare-event rate.

# 8. Certificate computation and independent verification

## 8.1 A certificate need not be an exactly optimal solver output

For any rational allocation $w$ and positive rational factors $f_j$, verify

$$
\sup_{x_b\in\mathcal B}\sum_jw_j\mathbb E_{M_jx_b}f_j\le1,
\tag{30}
$$

and a certified lower bound

$$
\gamma\le\inf_{x_g\in\mathcal G}\sum_jw_j\mathbb E_{M_jx_g}\log f_j.
\tag{31}
$$

Both optimize linear functions of $x$ once the scores are fixed. On explicit polytopes, vertices or a separately verified linear-program dual suffice. Any feasible pair $x_g,x_b$ supplies

$$
\Gamma\le\overline I=\max_jD(M_jx_g\Vert M_jx_b).
\tag{32}
$$

Conversely, (30) and the variational inequality $\mathbb E_p\log f\le D(p\Vert q)$ whenever $\mathbb E_qf\le1$ imply $\gamma\le\Gamma$. Thus

$$
\gamma\le\Gamma\le\overline I
$$

is an optimization certificate independent of solver convergence flags. Positive $\gamma$ gives a concrete stopping rule and the bound $(\log(1/\delta)+L)/\gamma$. An exact equal-law pair proves impossibility without logarithms.

In this artifact, SciPy proposes candidate agents and scores. Rational normalization removes small violations of null moments. A separate standard-library checker regenerates all clipped-simplex vertices and verifies every retained policy, probability map, moment constraint, growth lower bound, and information upper bound. Logarithm intervals use the convergent atanh series with an exact remainder bound and outward dyadic rounding. No floating-point logarithm is trusted by the checker.

## 8.2 Executed suites and denominators

A reused finite tree has two agent actions separated by an observation, followed by a last observation. Responses depend on prior actions. Eight distinct deterministic realization strategies generate the convex class. The response likelihoods and target are rational. Four safe menus, two targets, and two threshold pairs give 16 designs; three coarsened-log variants add three designs.

The first 19-case suite restricts every mixture coordinate to at least $1/160$, making all retained log probabilities positive. It is explicitly a sensitivity study for a **restricted** agent class, not the general theorem. The second 19-case suite uses the full convex hull, including deterministic boundary agents, and virtual regularization $\epsilon=1/1000$ only in score construction.

| Check | Result |
|:--|--:|
| Restricted-class certificate cases | 19 |
| Restricted cases: positive growth / exact overlap | 18 / 1 |
| Full-class certificate cases | 19 |
| Full cases: positive growth / exact overlap | 15 / 4 |
| Restricted-class independent constraints | 1,074 |
| Full-class independent constraints | 957 |
| Restricted maximum certified information bracket width | below $1.90\times10^{-7}$ |
| Full maximum certified information bracket width | below $2.10\times10^{-4}$ |
| Exact zero-alarm budget cases | 12 |
| Depth-three adaptive alarm auditors enumerated | 128 |
| Prior v0.4 stored cases / constraints rechecked | 35 / 382 |
| New LLM runs | 0 |

These are finite mathematical verification cases, not independent realistic deployment scenarios. The narrower brackets in the restricted class do not mean stronger assurance about the unrestricted class. In particular, missing-information and compressed-log cases switch from a positive score to an exact impossibility witness when the artificial strategy restriction is removed.

## 8.3 Failed attempts and repairs

Three failed development runs are retained. First, exact logarithm-series denominators exceeded Python's integer-to-string digit limit during JSON serialization. Outward dyadic rounding now controls representation size without narrowing the certified intervals. Second, naive coordinate rounding could assign a negative final simplex coordinate at a boundary. Exact largest-remainder rounding now preserves the simplex. Third, an allocation-proposal linear program could be infeasible under its very tight numerical slack after rounding; the implementation now uses an explicit fallback proposal and then exact moment normalization. It does not silently accept a violated null constraint.

All 38 planned final design cases are retained. Solver status and allocation method are stored per case. These repairs were software/certificate issues, not counterexamples to the theorem. General correctness still rests on the proofs, not the finite tests. There is no Lean or other proof-assistant certification in this release.

# 9. A failure mode specific to audit randomization

A valid joint controller-record factor need not be valid if the operator changes the controller schedule while keeping the factor unchanged.

Let the low-risk family have a single point with a binary logged outcome of probability $1/2$ under both controllers. Let the high-risk family be the convex line

$$
p_1(u)=\tfrac12+\tfrac25u,
\qquad
p_2(u)=\tfrac12+\tfrac25(1-u),\quad u\in[0,1].
$$

Each controller separately admits a high-risk point indistinguishable from the low-risk point. The joint design distinguishes them. The least-favorable pair for the equal mixture has high-risk probability $7/10$ in both controllers. Its factors are

$$
e(0)=5/3,\qquad e(1)=5/7.
$$

At high-risk $u=0$, the controller-specific expected factors are $25/21$ and $17/21$. Their equal mixture is exactly one, but controller 1 alone has expected factor greater than one and positive expected log growth. Always selecting that controller while reusing the mixture score eventually falsely certifies this high-risk agent with probability one.

An exact finite-state first-passage calculation at threshold $1/\delta=20$ and horizon 200 gives:

| Procedure and true condition | Probability of certificate by run 200 |
|:--|--:|
| Correct equal-mixture rule, low-risk point | 0.9977540701 |
| Correct equal-mixture rule, any high-risk point on the line | 0.0399363282 |
| Incorrect always-controller-1 rule, high-risk $u=0$ | 0.9977540701 |

These probabilities are exact rational dynamic-program results displayed as decimals, not Monte Carlo estimates or LLM measurements. The low-risk truncated expected time $\mathbb E\min(T,200)$ is 36.94431745; it is not the untruncated expected stopping time. Raw probability mass is conserved at each dynamic-program step.

The lesson is specific: either preserve the designed randomization or recompute a factor whose conditional moment is valid for the new selection rule. Optional stopping is allowed; arbitrary optional redesign with an old score is not.

# 10. Scope of persistence, model uncertainty, and abstention

## Proposition 2 — Conditional robustness has a temporal meaning

The product argument remains sound without iid runs if, before each new factor is observed, its conditional expectation is at most one under the null. This is a mathematical condition, not evidence that a persistent agent satisfies it. If a history-dependent agent has a different $x_n$ at each run but every conditional law lies in the high-risk null family, the process still cannot cross with probability above $\delta$.

This rejects the composite statement that every relevant conditional state remains in that null family. It does **not** certify a future state, an unobserved memory configuration, or a different deployment initializer. Two persistent agents can agree throughout every observed audit and diverge later. A future-risk certificate therefore needs a separate stability, reset, structural, or transport premise. One cannot obtain it merely by changing the word "iid" to "martingale."

For model uncertainty, suppose actual null laws differ from nominal $M_jx$ by at most $\eta_j$ in total variation, uniformly over the declared class. A proposed factor has joint null expectation at most

$$
1+\sum_jw_j\eta_j\operatorname{osc}(f_j).
$$

Dividing the factor by this known upper bound restores soundness. The correction can destroy positive growth, appropriately revealing a certificate too sensitive to model error. The uniform errors require independent justification. If deployment target error is at most $\xi$, a nominal certificate for $J<\tau-\xi$ implies an actual target below $\tau$; ignoring this margin is invalid.

A finite run cap produces three possible conclusions: certified below threshold, observed counterevidence, or unresolved. The last category must not be silently relabeled as safe or dropped. A statistical certificate is only one premise of a safety case; Korbak et al. explicitly distinguish measured evaluation performance from deployment approximation and extrapolation obligations [R3, Section 2.7, pp. 7–8].

# 11. Novelty boundary and reviewer-facing framing

| Closest line | What it already supplies | What is retained here |
|:--|:--|:--|
| Penumbra [R1] | Interactive environment distinguishing; an external-consequence witness | Whether that signal changes evidence for a specified target decision |
| Strategic AI testing [R2] | Deployment-specific green lights; reasons repeated tests can fail | Explicit cross-threshold equal-law pairs and threshold-dependent cost |
| AI control safety cases [R3] | Deployment-relative risk claims and extrapolation premises | A conditional statistical subclaim with observable, executable certificates |
| Safe Testing [R4] | Composite growth-optimal e-variables, joint information projection, optional continuation | Safe controller design and target classes induced by agent/environment interaction |
| Convex and sequential hypothesis testing [R5–R6] | Computationally generated composite tests and near-optimality | A specialized controlled-audit expected-cost statement and boundary handling |
| Controlled sampling lower bounds [R7] | Stopped KL/change-of-measure inequalities | A pair fixed before the audit and a high-risk-null certificate event |
| Interactive estimation [R8] | General interactive estimation complexity | One-sided risk certification rather than global MSE; no claim to invent interaction |

The reduction of (1) to a statistical experiment is exact under its assumptions. The positive-case e-factor in (15) is a direct finite-alphabet instance of the joint information projection in [R4, Section 3, Theorem 1]. The scalar information game and the expected-cost combination should be presented as a proposition with a full proof and explicit sources, not an unqualified new statistical theory. Virtual regularization and score averaging are also standard ideas; their value here is preventing an unjustified restriction of the agent class.

The defensible contribution is a containment-relative theory of *what can be certified*, linked to target timing and uncovered prerequisites, with audit designs and hard-agent certificates that reviewers can inspect. The exact alarm-only threshold floor is useful and sharp in its model, but mathematically elementary. No "first" or "revolutionary" priority claim is supported by the scoped review. A top-tier paper still needs a distinctive systems/AI-safety mechanism or a clearly established theoretical separation beyond translating known statistics, and evidence that the finite model captures a practically important audit.

# 12. Experimental implications and a focused paper plan

The revised empirical question should not be whether an LLM can classify two contrived environments. It should test whether target-specific certificates predict the separation between world classification and behavioral-estimation validity.

Use paired fully local environments with identical action schemas. Randomize whether a causal marker arrives before or after the target action; vary safe exposure to a prerequisite; vary cross-service consistency; and compare complete versus compressed logs. Include a coherent replica and a scripted witness. Keep world condition and textual framing independently randomized. For actual LLMs, freeze model versions, prompts, decoding, budgets, and exclusions. Probability reports are optional observable outputs, not proof of internal belief or mediation.

For each target, preregister its decision time, safe evidence sources, deployment-like reference, coverage assumptions, and certificate threshold. Compare direct sample means, the v0.4 scored estimator, and the new threshold certifier, with identical reset budgets where meaningful. Report all attempted runs, valid runs, refusals, timeouts, failed parsing, stopping times, and unresolved runs. A wrong implementation of controller randomization is a negative control, not an acceptable evaluation variant.

The falsifiable predictions are scoped. A post-decision marker can increase final classification without changing the earlier target distribution. Losing prerequisite coverage can force an identified interval across a release threshold despite many zero alarms. Log compression can create a cross-threshold equal-law pair even when complete logs permit certification. Changing controller allocation without changing a jointly valid score can invalidate the claimed error control. None is asserted as an observed LLM phenomenon in this release.

For the manuscript, the target-specific information-cut result should remain the conceptual center. The threshold information theorem is the bridge from that structure to actionable confidence. The alarm-only model provides a readable sharp example. The broad v0.4 MSE theorem is useful supporting theory but need not occupy the main narrative if space is limited. This is a clearer paper than presenting every successive modulus as an independent contribution.

# 13. Internal red-team audit and claim dependencies

| Issue | Severity | Repair and cost |
|:--|:--|:--|
| Treating MSE as a release-confidence guarantee | Major | Separate high-risk-null testing, confidence, and completeness |
| Trivial never-certify method called successful | Fatal | Define cost with infinite certificate time and require low-risk completeness |
| Imposing positive action probabilities merely to avoid zeros | Fatal if hidden | Virtual regularization preserves the original legal class; bounds depend on its parameter |
| Treating each component of a mixture score as individually valid | Fatal | Prove joint controller-record moments; keep or recertify the allocation |
| Lower-bound pair chosen after the audit record | Fatal | Use a minimax pair fixed in advance |
| Applying a finite stopping-time lemma under an unsafe agent that never stops | Major | Truncate certificate times and pass to a limit under the good agent |
| Claiming alarm-only lower bounds with full logs | Fatal | State the restricted observation model; full logs may improve performance |
| Calling a conditional martingale bound a future-memory guarantee | Fatal | Separate the null's time scope and require stability or reset premises |
| Treating unknown deployment as known | Fatal | Specify $c$ or a justified uncertainty margin; no free transport claim |
| Declaring solver success to be proof | Major | Rational moment checks and interval logarithms; retain failed development logs |
| Presenting joint information projection as new | Major novelty issue | Cite [R4] explicitly and narrow the claim |

```{=latex}
\begin{minipage}{\linewidth}
\textbf{Claim dependencies}\par\smallskip
\footnotesize
\begin{verbatim}
Complete input model + fixed agent + known safe controllers and deployment target
                    |
           Linear audit laws and target
                    |
       Low-risk / high-risk threshold classes
             /                     \
Equal-law pair exists          Convex separation through safe audits
       |                                  |
No complete sound certificate     Virtually regularized KL game
                                          |
                               Pullback to unchanged raw records
                                          |
                              Joint null moment + good log drift
                               /                        \
                      Anytime soundness          Expected audit cost
                                                        |
                                           Matched adaptive lower bound

Alarm-only logging + clean agents + convex high-risk class
                    |
          Exact zero-alarm tradeoff
                    |
     Uncovered-information certification floor

Any claim about actual deployment additionally requires implementation fidelity,
reset validity, target correspondence, and deployment transport assumptions.
\end{verbatim}
\end{minipage}
```

# Limitations and Dual-Use Considerations

All theorems are relative to declared information interfaces, controller classes, and targets. The finite representation may be exponentially large in the description of a succinct environment. Convex behavioral classes are not interchangeable with finite collections of named LLMs; lower bounds for a larger class do not transfer to a smaller one. General persistent memory, arbitrary external actors, unknown deployment kernels, and computationally restricted discovery remain outside the completed theorem.

Local synthetic conditions are not actual deployment. No LLM run was executed. A scripted hard agent proves a possibility in the model, not autonomous discovery or intent in a current system. Verbal probabilities need not be internal beliefs. Harmless shortcut behavior need not generalize to harmful behavior. The method does not turn an empirically observed zero error rate into universal indistinguishability.

The theory can inform more reliable evaluation, but examples of condition-sensitive behavior could also teach evaluation evasion. The artifact therefore uses small local probability trees and abstract binary events, not operational sandbox fingerprints, exploits, real targets, credentials, or destructive actions. Containment remains a separate implementation obligation. All experiments must stay local, authorized, and non-destructive. Any audit of an existing environment needs independent authorization and a disclosure review.

# References

[R1] *Penumbra: Sandboxing Autonomous Agents by Measuring, Not Assuming, Indistinguishability*. Supplied manuscript `paper (1).pdf`. Section 2 (distinguishing game), Section 5, Proposition 1 (external cross-examination), and Section 6 (architecture). Author, date, and publication status are not independently verified; no fabricated metadata is supplied.

[R2] Vojtěch Kovařík, Eric Olav Chen, Sami Petersen, Alexis Ghersengorin, and Vincent Conitzer. *AI Testing Should Account for Sophisticated Strategic Behaviour*. arXiv:2508.14927v1, 2025. Supplied PDF; Section 3.1.4, pp. 7–8. This is the source for the scoped prior green-light argument, not evidence for our new experiment.

[R3] Tomek Korbak, Mikita Balesni, Buck Shlegeris, and Geoffrey Irving. *How to evaluate control measures for LLM agents? A trajectory from today to superintelligence*. arXiv:2504.05259v1, 2025. Supplied PDF; Section 2.7, pp. 7–8, separates evaluation rates, deployment approximation, and extrapolation.

[R4] Peter Grünwald, Rianne de Heide, and Wouter Koolen. *Safe Testing*. Journal of the Royal Statistical Society, Series B, 2024. Exact theorem locations checked in arXiv:1906.07801v5: Section 3, Theorem 1 (First Generalisation), equations (16)–(17), printed p. 12; Section 4.3, full generality; Appendix A.3, support conditions. This supplies the composite e-variable/joint-information-projection foundation.

[R5] Alexander Goldenshluger, Anatoli Juditsky, and Arkadi Nemirovski. *Hypothesis testing by convex optimization*. Electronic Journal of Statistics 9(2), 2015. Public full text arXiv:1311.6765, Theorem 2.1 and Section 2.4.

[R6] Anatoli Juditsky and Arkadi Nemirovski. *On sequential hypotheses testing via convex optimization*. Public full text arXiv:1412.1605. Sequential extension of convex testing; not claimed as new here.

[R7] Emilie Kaufmann, Olivier Cappé, and Aurélien Garivier. *On the Complexity of Best-Arm Identification in Multi-Armed Bandit Models*. Public full text arXiv:1407.4443; Lemma 1, printed p. 7, and its stopped change-of-measure proof. Our proof uses finite truncations for one-sided certificate times.

[R8] Fan Chen, Dylan J. Foster, Yanjun Han, Jian Qian, Alexander Rakhlin, and Yunbei Xu. *Assouad, Fano, and Le Cam with Interaction: A Unifying Lower Bound Framework and Characterization for Bandit Learnability*. NeurIPS 2024. Appendix E.2, Proposition E.4 and Remark E.5, printed p. 28; Appendix F.7.

[R9] Daphne Koller, Nimrod Megiddo, and Bernhard von Stengel. *Efficient Computation of Equilibria for Extensive Two-Person Games*. Games and Economic Behavior, 1996. Section 2, equation (2.1), sequence-form realization plans. Used as background already checked in v0.4.

[R10] Mihir Bellare and Phillip Rogaway. *The Security of Triple Encryption and a Framework for Code-Based Game-Playing Proofs*. EUROCRYPT 2006. Fundamental lemma/identical-until-bad reasoning. Used as background already checked in earlier project reports.

# Exactly four one-month extensions

1. **Scale to more models, seeds, environments, and longer horizons.** Execute the proposed local study, retaining every attempted run and separating hypothesis-testing soundness from transport assumptions.
2. **Search or train adaptive probe policies and compare them with general-purpose agents.** Measure discovery separately from the existence of model-theoretic hard pairs or scripted distinguishers.
3. **Conduct an authorized leakage audit of an existing agent evaluation environment.** Test complete-input and logging assumptions before applying any deployment-relevant certificate.
4. **Strengthen the formal analysis for partial observability, composition, and open-world external actors.** Prioritize non-reset memory and independently justified deployment uncertainty without silently changing the target claim.
