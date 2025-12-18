from typing import Set
from af_io import ArgumentationFramework
from aspartix_solver import compute_extensions

def validate_fact_and_foil(
    af: ArgumentationFramework,
    fact: str,
    foil: str,
    semantics: str,
    semantics_dir: str = "sementics",
) -> Set[str]:
    """
    Efficiently validate that:
      1. fact is accepted under the given semantics (returns one witness extension E_p);
      2. foil is unaccepted under the same semantics.
    """

    # 1) Check that `fact` is σ-accepted: ∃ E_p s.t. fact ∈ E_p
    fact_exts = compute_extensions(
        af,
        semantics=semantics,
        semantics_dir=semantics_dir,
        models=1,               # find at most one extension containing `fact`
        force_in=fact,
        ep_for_max_commonality=None,
    )

    if not fact_exts:
        raise ValueError(
            f"[Error] The factual argument '{fact}' is NOT accepted under "
            f"'{semantics}' semantics. Please select a valid fact that appears "
            f"in at least one σ-extension."
        )

    fact_witness = fact_exts[0]

    # 2) Ensure that `foil` is NOT σ-accepted: ¬∃ E s.t. foil ∈ E
    foil_exts = compute_extensions(
        af,
        semantics=semantics,
        semantics_dir=semantics_dir,
        models=1,
        force_in=foil,
        ep_for_max_commonality=None,
    )

    if foil_exts:
        raise ValueError(
            f"[Error] The foil argument '{foil}' is ALREADY accepted under "
            f"'{semantics}' semantics. Contrastive reasoning requires the foil "
            f"to be initially unaccepted."
        )

    return fact_witness

def is_credulously_accepted(
    af: ArgumentationFramework,
    arg: str,
    semantics: str,
    semantics_dir: str = "semantics",
) -> bool:
    """
    Check whether `arg` is credulously σ-accepted in `af`.
    """
    exts = compute_extensions(
        af,
        semantics=semantics,
        semantics_dir=semantics_dir,
        models=1,
        force_in=arg,
    )
    return bool(exts)