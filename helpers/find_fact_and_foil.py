from pathlib import Path
from typing import List, Tuple
from af_io import parse_apx, ArgumentationFramework
from aspartix_solver import compute_extensions

def find_fact_and_foil_candidates(
    apx_path: str,
    semantics: str,
    semantics_dir: str = "sementics",
) -> Tuple[List[str], List[str]]:
    """
    Identify potential fact and foil arguments in a given AF file
    under a chosen semantics, using credulous acceptance checks.
    """

    # 1. Load AF
    apx_path = Path(apx_path)
    af: ArgumentationFramework = parse_apx(apx_path.read_text(encoding="utf-8"))

    all_args = sorted(af.arguments)
    facts: List[str] = []
    foils: List[str] = []

    print(f"\n[Info] Checking credulous acceptance under '{semantics}' "
          f"for {len(all_args)} arguments.\n")

    # 2. For each argument a, check whether there exists a σ-extension containing a.
    for a in all_args:
        exts = compute_extensions(
            af,
            semantics=semantics,
            semantics_dir=semantics_dir,
            models=1,
            force_in=a,               # search only for extensions containing a
            ep_for_max_commonality=None,
        )
        if exts:
            facts.append(a)
        else:
            foils.append(a)

    print(f"[Result] Under semantics '{semantics}':")
    print(f"  #facts = {len(facts)}")
    print(f"  #foils = {len(foils)}\n")

    return facts, foils