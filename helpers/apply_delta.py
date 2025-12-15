# Apply the “Counterfactual Editing Set” δ to AF

from af_io import ArgumentationFramework
from typing import Iterable, Tuple, Set

Attack = Tuple[str, str]

def apply_delta(af: ArgumentationFramework, delta: Iterable[Attack]) -> ArgumentationFramework:
    """
    Given the original AF and the Editing Set δ, Return the modified AF'
    - if (u,v) ∈ R: remove it
    - if (u,v) ∉ R: add it
    """
    A = set(af.arguments)
    R = set(af.attacks)
    for (u, v) in delta:
        if u not in A or v not in A:
            raise ValueError(f"Invalid edit ({u},{v}): arguments not in AF.")
        if (u, v) in R:
            R.remove((u, v))
        else:
            R.add((u, v))

    return ArgumentationFramework.from_sets(A, R)