"""Finite, local reference models for behavioral identifiability.

All model arithmetic uses fractions.Fraction. This module is an explicit
history-tree model, not a security boundary or an LLM evaluation runner.
SciPy is used only to propose LP solutions; the verification driver checks
rationalized primal/dual certificates separately.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from typing import Callable, Iterable, Sequence

History = tuple[int, ...]
Vec = list[F]
Mat = list[Vec]
ZERO, ONE = F(0), F(1)
LEAVES = tuple(product((0, 1), repeat=4))
DECISIONS = ((),) + tuple(product((0, 1), repeat=2))
SEQUENCES = ((), (0,), (1,)) + tuple(product((0, 1), repeat=3))
INDEX = {s: i for i, s in enumerate(SEQUENCES)}


def dot(a: Sequence[F], b: Sequence[F]) -> F:
    return sum((x*y for x, y in zip(a, b, strict=True)), ZERO)


def mv(a: Mat, x: Sequence[F]) -> Vec:
    return [dot(row, x) for row in a]


def transpose(a: Mat) -> Mat:
    return [list(c) for c in zip(*a, strict=True)]


def zeros(n: int) -> Vec:
    return [ZERO for _ in range(n)]


def rationalize(x: Iterable[float], max_denominator: int = 10**7) -> Vec:
    return [F(float(v)).limit_denominator(max_denominator) for v in x]


def flow_constraints() -> tuple[Mat, Vec]:
    f: Mat = []
    row = zeros(len(SEQUENCES)); row[0] = ONE; f.append(row)
    row = zeros(len(SEQUENCES)); row[0] = -ONE
    row[INDEX[(0,)]] = row[INDEX[(1,)]] = ONE; f.append(row)
    for a, o in product((0, 1), repeat=2):
        row = zeros(len(SEQUENCES)); row[INDEX[(a,)]] = -ONE
        for b in (0, 1): row[INDEX[(a,o,b)]] = ONE
        f.append(row)
    return f, [ONE] + [ZERO]*5


FLOW, RHS = flow_constraints()


@dataclass(frozen=True)
class World:
    name: str
    first: tuple[F, F]
    second: tuple[F, ...]

    def __post_init__(self) -> None:
        if len(self.second) != 8 or any(p < 0 or p > 1 for p in self.first + self.second):
            raise ValueError("Response probabilities must lie in [0,1].")

    def response(self, action_prefix: History, observation: int) -> F:
        if observation not in (0, 1): raise ValueError("Binary observation required.")
        if len(action_prefix) == 1:
            p = self.first[action_prefix[0]]
        elif len(action_prefix) == 3:
            a,o,b = action_prefix
            p = self.second[4*a+2*o+b]
        else:
            raise ValueError("Expected a prefix immediately after an action.")
        return p if observation else ONE-p

    def likelihood(self, h: History) -> F:
        result = ONE
        for pos in range(1, len(h), 2):
            result *= self.response(h[:pos], h[pos])
        return result


def safe_worlds() -> tuple[World, ...]:
    return (
        World("zero_first_zero_last", (ZERO,ZERO), (ZERO,)*8),
        World("one_first_one_last", (ONE,ONE), (ONE,)*8),
        World("action_dependent", (ZERO,ONE), tuple(F(o^b) for a,o,b in product((0,1),repeat=3))),
        World("full_overlap", (F(1,4),F(3,4)), (F(1,2),)*8),
    )


def deployment_worlds() -> tuple[World, ...]:
    return tuple(World(f"reference_{i}_{j}", (p,q),
                tuple((F(1,4),F(1,2),F(3,4))[(a+2*o+b)%3]
                      for a,o,b in product((0,1),repeat=3)))
                 for i,p in enumerate((F(1,4),F(1,2),F(3,4)))
                 for j,q in enumerate((F(1,4),F(1,2),F(3,4))))


def pure_realizations() -> tuple[Vec, ...]:
    outputs = []
    for bits in product((0,1), repeat=len(DECISIONS)):
        policy = {h: F(bits[i]) for i,h in enumerate(DECISIONS)}
        outputs.append(realization(policy))
    return tuple(outputs)


def realization(prob_one: dict[History,F]) -> Vec:
    x = zeros(len(SEQUENCES)); x[0] = ONE
    for a in (0,1): x[INDEX[(a,)]] = prob_one[()] if a else ONE-prob_one[()]
    for a,o,b in product((0,1),repeat=3):
        p = prob_one[(a,o)] if b else ONE-prob_one[(a,o)]
        x[INDEX[(a,o,b)]] = x[INDEX[(a,)]]*p
    assert mv(FLOW,x) == RHS and min(x) >= 0
    return x


def policy_from_x(x: Vec) -> dict[History,F]:
    if mv(FLOW,x) != RHS or min(x) < 0: raise ValueError("Invalid realization plan.")
    result = {(): x[INDEX[(1,)]]}
    for a,o in product((0,1),repeat=2):
        denom=x[INDEX[(a,)]]
        result[(a,o)] = x[INDEX[(a,o,1)]]/denom if denom else F(1,2)
    return result


def transcript_law(world: World, x: Vec) -> Vec:
    p = [world.likelihood(z)*x[INDEX[z[:3]]] for z in LEAVES]
    assert sum(p,ZERO) == ONE
    return p


def observation_matrix(world: World, projection: Callable[[History],tuple] = lambda z:z) -> Mat:
    labels = sorted({projection(z) for z in LEAVES})
    rows = {label:zeros(len(SEQUENCES)) for label in labels}
    for z in LEAVES: rows[projection(z)][INDEX[z[:3]]] += world.likelihood(z)
    return list(rows.values())


def target_vector(world: World, loss: Callable[[History],F]) -> Vec:
    c = zeros(len(SEQUENCES))
    for z in LEAVES: c[INDEX[z[:3]]] += world.likelihood(z)*loss(z)
    return c


def losses() -> dict[str, Callable[[History],F]]:
    return {
        "first_action": lambda z:F(z[0]),
        "second_action": lambda z:F(z[2]),
        "any_action_one": lambda z:F(z[0] or z[2]),
        "second_action_after_one": lambda z:F(z[1]*z[2]),
        "second_action_with_final_success": lambda z:F(z[2]*z[3]),
        "final_observation": lambda z:F(z[3]),
        "path_parity": lambda z:F(sum(z)%2),
        "graded_consequence": lambda z:F(z[0]+2*z[2]*z[3],3),
    }


def safe_supported(h: History, menu: Sequence[World]) -> bool:
    return any(e.likelihood(h)>0 for e in menu)


def sharp_interval(world: World, menu: Sequence[World], x: Vec,
                   loss: Callable[[History],F]) -> dict:
    """Exact full-log identified interval by backward induction and exit decomposition."""
    pi = policy_from_x(x)
    witnesses = []
    endpoints = []
    all_values = []
    for maximize in (False,True):
        choices = dict(pi)
        values: dict[History,F] = {}
        def rec(h: History) -> F:
            if len(h)==4:
                value=loss(h)
            elif len(h)%2:
                value=sum((world.response(h,o)*rec(h+(o,)) for o in (0,1)),ZERO)
            else:
                children=[rec(h+(a,)) for a in (0,1)]
                if safe_supported(h,menu):
                    p=pi[h]; value=(ONE-p)*children[0]+p*children[1]
                else:
                    a=(1 if children[1]>children[0] else 0) if maximize else (1 if children[1]<children[0] else 0)
                    choices[h]=F(a); value=children[a]
            values[h]=value
            return value
        endpoints.append(rec(())); witnesses.append(realization(choices)); all_values.append(values)
    mu: dict[History,F] = {}
    covered=ZERO
    def walk(h: History, prob: F) -> None:
        nonlocal covered
        if not prob: return
        if len(h)%2==0 and not safe_supported(h,menu):
            mu[h]=mu.get(h,ZERO)+prob; return
        if len(h)==4:
            covered+=prob*loss(h); return
        if len(h)%2:
            for o in (0,1): walk(h+(o,),prob*world.response(h,o))
        else:
            for a in (0,1): walk(h+(a,),prob*(pi[h] if a else ONE-pi[h]))
    walk((),ONE)
    decomposed=[covered+sum((m*all_values[i][h] for h,m in mu.items()),ZERO) for i in (0,1)]
    assert endpoints == decomposed
    width=sum((m*(all_values[1][h]-all_values[0][h]) for h,m in mu.items()),ZERO)
    assert endpoints[1]-endpoints[0]==width
    for w,v in zip(witnesses,endpoints,strict=True):
        assert dot(target_vector(world,loss),w)==v
        for e in menu: assert transcript_law(e,w)==transcript_law(e,x)
    return {"lower":endpoints[0],"upper":endpoints[1],"width":width,
            "exit_mass":sum(mu.values(),ZERO),"covered":covered,
            "exit_measure":mu,"witnesses":witnesses}
