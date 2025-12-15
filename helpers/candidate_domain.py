# Generate Candidate Editing Domains

from typing import List, Set, Tuple
from af_io import ArgumentationFramework

Attack = Tuple[str, str]
EditMode = str

def candidate_domain(
    af: ArgumentationFramework,
    foil: str,
    radius: int = 2,
    mode: EditMode = "both",
) -> List[Attack]:
    """
    Generate candidate attacks for editing based on neighborhood restriction.
    - radius: only consider attacks whose endpoints are within distance ≤ radius from the foil.
    - mode:
        * "del"  -> only allow deletions: edges in R connected to the neighborhood
        * "add"  -> only allow additions: edges (u,v) not in R, with at least one endpoint in the neighborhood
        * "both" -> combine both types
    """
    if foil not in af.arguments:
        raise KeyError(f"foil '{foil}' not in AF")

    hood = af.neighborhood(foil, radius=radius)
    R = set(af.attacks)
    A = set(af.arguments)

    cands: Set[Attack] = set()

    if mode in ("del", "both"):
        for (u, v) in R:
            if (u in hood) or (v in hood):
                cands.add((u, v))

    if mode in ("add", "both"):
        # Generate potential new attacks restricted to the neighborhood
        # Consider only pairs where at least one endpoint lies within the neighborhood
        # not self-loops, and no such pair currently exists.
        hood_plus = hood  # extend by one more hop, if need
        for u in hood_plus:
            for v in A:
                if u == v:
                    continue
                if (u, v) not in R:
                    cands.add((u, v))
            for v in hood_plus:
                if u == v:
                    continue
                if (u, v) not in R:
                    cands.add((u, v))

    return sorted(cands)
