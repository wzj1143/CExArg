from typing import Dict, List, Set, Tuple
from helpers import *
from min_edit_solver import MinEditResult

# CE type aliases
Attack = Tuple[str, str]
CEComponents = Dict[str, Set[str] | List[str]]


def build_contrastive_explanation(result: MinEditResult) -> CEComponents:
    """
    Build a Contrastive Explanation (CE) from a minimal counterfactual edit result.

    CE = (C_cap, C_p, C_q, C_delta)
    where:
        C_cap   = E_p ∩ E_q
        C_p     = E_p \ E_q
        C_q     = E_q \ E_p
        C_delta = δ (formatted)
    """

    if result.fact_Ep is None or result.witness_Eq is None:
        raise ValueError("Both fact and foil witnesses must be available to construct CE.")

    E_p = set(result.fact_Ep)
    E_q = set(result.witness_Eq)

    # Compute CE components
    C_cap = sorted(E_p.intersection(E_q))
    C_p = sorted(E_p - E_q)
    C_q = sorted(E_q - E_p)

    C_delta = result.formatted_delta  # ['-(d,e)', '+(b,f)', ...]

    ce = {
        "C_cap": C_cap,
        "C_p": C_p,
        "C_q": C_q,
        "C_delta": C_delta,
    }

    return ce


def print_contrastive_explanation(ce: CEComponents, label: str = "CE"):
    """
    Nicely format and print the CE components (for paper-style output).
    """
    print(f"\n{label} = (C_∩, C_p, C_q, C_δ)")
    print("──────────────────────────────────────────────")
    print(f"C_∩   = {ce['C_cap']}")
    print(f"C_p   = {ce['C_p']}")
    print(f"C_q   = {ce['C_q']}")
    print(f"C_δ   = {ce['C_delta']}")
    print("──────────────────────────────────────────────\n")