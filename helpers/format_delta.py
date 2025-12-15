# Format δ into symbolic representation (+/-)

from typing import Iterable, Tuple, List

Attack = Tuple[str, str]

def format_delta(delta: Iterable[Attack], original_attacks: Iterable[Attack]):
    """
    Convert a set of flipped attacks δ (e.g., {('b','d'), ('d','e')}) into
    readable symbols relative to the original AF:
      - formatted_strs: ['-(d,e)', '+(b,d)', ...]
    """
    R = set(original_attacks)
    formatted_strs = []
    for (u, v) in sorted(delta):
        if (u, v) in R:
            formatted_strs.append(f"-({u},{v})")
        else:
            formatted_strs.append(f"+({u},{v})")
    return formatted_strs