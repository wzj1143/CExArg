# Minimal Counterfactual Editing
# RC2 (PySAT) + ASPARTIX (clingo)
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Set, Tuple, Iterable, Optional, Literal
from pysat.formula import WCNF
from pysat.examples.rc2 import RC2
import time
from af_io import ArgumentationFramework
from aspartix_solver import compute_extensions
from helpers import *

EditMode = Literal["add", "del", "both"]
Semantics = Literal["admissible", "complete", "preferred", "stable"]
Attack = Tuple[str, str]
CEVariant = Literal["baseline", "keep_fact", "status_reversal"]

# ---------------------------
# Minimal Counterfactual Editing (RC2 + Clingo)
# ---------------------------
@dataclass
class MinEditResult:
    kmin: int
    witness_Eq: Set[str]
    fact_Ep: Optional[Set[str]]
    formatted_delta: List[str]

def find_minimal_edit(
    af: ArgumentationFramework,
    fact: str,
    foil: str,
    semantics: Semantics,
    semantics_dir: str = "semantics",
    edit_mode: EditMode = "both",   # {"add","del","both"}
    radius: int = 2,
    # additional controls
    given_extension: Optional[Set[str]] = None,
    ce_variant: CEVariant = "baseline",
    max_iters: int = 10000,   #  maximum number of iterations
    time_budget_sec: float | None = None, #  maximum seconds of solver
    verbose: bool = False,
) -> MinEditResult:
    """
    Compute a minimal counterfactual edit set using RC2 (MaxSAT) and Clingo.
    - Outer loop: RC2 minimizes the number of flips (edits)
    - Inner loop: Clingo verifies whether the foil becomes σ-accepted

    Returns:
        The optimal edit set δ*, its size kmin, and the counterfactual witness E_q.
    """
    # 0. Check fact and foil
    if given_extension is not None:
        # the given extension is used directly as factual witness
        Ep = set(given_extension)
    else:
        # otherwise use the first extension including the fact
        Ep = validate_fact_and_foil(
            af, fact=fact, foil=foil,
            semantics=semantics, semantics_dir=semantics_dir
        )
    start_time = time.perf_counter()


    # 1. Build the candidate domain
    edits = candidate_domain(af, foil=foil, radius=radius, mode=edit_mode)
    if verbose:
        print(f"[MinEdit] candidate edits = {len(edits)} (mode={edit_mode}, radius={radius})")

    if not edits:
        # no editable edges, direct failure
        raise RuntimeError("Candidate edit domain is empty. Try increasing radius or mode='both'.")

    # 2. Construct WCNF: one variable per candidate attack (True=flip；False=keep)
    wcnf = WCNF()
    # variables start with 1
    var_of_idx: Dict[int, Attack] = {}
    idx_of_attack: Dict[Attack, int] = {}

    for i, e in enumerate(edits, start=1):
        var_of_idx[i] = e
        idx_of_attack[e] = i
        # soft clause: (¬t_i) with weight=1 (penalty for performing an edit)
        wcnf.append([-i], weight=1)

    # 3. CEGAR loop
    # initialize RC2 instance
    rc2 = RC2(wcnf)
    hard_counter = 0
    iteration = 0
    try:
        while iteration < max_iters:
            if time_budget_sec is not None:
                elapsed = time.perf_counter() - start_time
                if elapsed > time_budget_sec:
                    raise RuntimeError(
                        f"Time budget exceeded ({elapsed:.2f}s > {time_budget_sec}s)."
                    )
            iteration += 1
            model = rc2.compute()  # get current optimal model
            if model is None:
                raise RuntimeError("MaxSAT: UNSAT — no feasible solution under current constraints.")

            # decode RC2 model: true variables correspond to edited attacks
            chosen_delta: Set[Attack] = set()
            # the RC2 model is a list of truth values for all variables (positive = True, negative = False).
            true_vars = {lit for lit in model if lit > 0}
            for lit in true_vars:
                if abs(lit) in var_of_idx:
                    chosen_delta.add(var_of_idx[abs(lit)])

            if verbose:
                print(f"[RC2] iteration {iteration}, hard={hard_counter}, |δ|={len(chosen_delta)}")

            # 4. Check if the foil becomes accepted after applying δ
            af_prime = apply_delta(af, chosen_delta)
            if ce_variant in ("baseline", "keep_fact"):
                exts = compute_extensions(af_prime, semantics=semantics, semantics_dir=semantics_dir, models=1,
                                            force_in=foil, ep_for_max_commonality=Ep, ep_for_min_difference=None)
            else:
                exts = compute_extensions(af_prime, semantics=semantics, semantics_dir=semantics_dir, models=1,
                                          force_in=foil, ep_for_max_commonality=None, ep_for_min_difference=Ep)
            Eq = exts[0] if exts else None

            if Eq is None:
                # if infeasible, block this model (add a hard clause)
                # clauses: for each variable i, if the current value is True, add (¬i); if False, add (i).
                block: List[int] = []
                for i in range(1, len(edits) + 1):
                    if i in true_vars:
                        block.append(-i)  # Current True -> Future at least one different => Take negative
                    else:
                        block.append(+i)  # Current False -> Future at least one different => Take positive
                rc2.add_clause(block)  # hard clause (default weight=None)
                hard_counter += 1
                continue

            # 4.2 Additional constraints for facts based on variants
            if ce_variant == "keep_fact":
                # keep_fact: fact and foil must appear together in Eq.
                if fact not in Eq:
                    block: List[int] = []
                    for i in range(1, len(edits) + 1):
                        if i in true_vars:
                            block.append(-i)
                        else:
                            block.append(+i)
                    rc2.add_clause(block)
                    hard_counter += 1
                    continue

            if ce_variant == "status_reversal":
                # status reversal: require that fact is not σ-accepted in AF'.
                fact_exts = compute_extensions(
                    af_prime,
                    semantics=semantics,
                    semantics_dir=semantics_dir,
                    force_in=fact,
                    models=1,
                )
                if fact_exts:
                    # there is also an extension that includes fact -> reversal failed -> continue CEGAR
                    block: List[int] = []
                    for i in range(1, len(edits) + 1):
                        if i in true_vars:
                            block.append(-i)
                        else:
                            block.append(+i)
                    rc2.add_clause(block)
                    hard_counter += 1
                    continue

            if verbose:
                print(f"[OK] minimal δ found: kmin={len(chosen_delta)}")
            formatted_strs = format_delta(chosen_delta, af.attacks)
            return MinEditResult(
                kmin=len(chosen_delta),
                witness_Eq=Eq,
                fact_Ep=Ep,
                formatted_delta=formatted_strs,
            )


        # No solution found after exceeding the maximum number of iterations.
        raise RuntimeError("Maximum iterations reached without finding a feasible edit set. "
                    "Try increasing radius or relaxing edit_mode.")

    finally:
        rc2.delete()