from dataclasses import dataclass
from typing import Set, Tuple, Iterable, Optional, List, Union, TextIO
import re

Arg = str
Attack = Tuple[str, str]

@dataclass(frozen=True)
class ArgumentationFramework:
    """Immutable AF container."""
    arguments: frozenset
    attacks: frozenset

    def __post_init__(self):
        # Ensure attacks reference only declared arguments
        for (u, v) in self.attacks:
            if u not in self.arguments or v not in self.arguments:
                raise ValueError(f"Attack ({u},{v}) references undeclared argument.")

    @staticmethod
    def from_sets(args: Iterable[Arg], attacks: Iterable[Attack]) -> 'ArgumentationFramework':
        # Quickly create AF
        return ArgumentationFramework(frozenset(args), frozenset(attacks))

    def to_aspartix(self) -> str:
        """Return ASPARTIX/APX facts string (arg/att)."""
        lines = []
        for a in sorted(self.arguments):
            lines.append(f"arg({a}).")
        for u, v in sorted(self.attacks):
            lines.append(f"att({u},{v}).")
        return "\n".join(lines) + "\n"

    def neighborhood(self, a: Arg, radius: int = 1) -> Set[Arg]:
        """
        Return nodes within given attack-graph distance from a (including a).
        Useful for candidate editor domain clipping.
        """
        if a not in self.arguments:
            raise KeyError(f"Unknown argument: {a}")
        if radius < 0:
            return set()
        # Breadth-First Search
        adj = {x: set() for x in self.arguments}
        for u, v in self.attacks:
            adj[u].add(v)
            adj[v].add(u)
        visited = {a}
        frontier = {a}
        for _ in range(radius):
            nxt = set()
            for x in frontier:
                nxt.update(adj[x])
            nxt -= visited
            visited |= nxt
            frontier = nxt
            if not frontier:
                break
        return visited


# Regex: arg(a).  att(a,b).
_APX_LINE_RE = re.compile(
    r'\s*(arg|att)\s*\(\s*([^\s,()]+)\s*(?:,\s*([^\s,()]+)\s*)?\)\s*\.\s*',
    re.IGNORECASE
)

def parse_apx(content: Union[str, TextIO]) -> ArgumentationFramework:
    """
    Parse APX/ASPARTIX text into an ArgumentationFramework.
    Supports:
      - 'arg(a).' and 'att(a,b).'
      - comments starting with '%' or '//'
      - multiple statements per line
    If attacks reference undeclared args, they are implicitly added to the argument set.
    """
    if hasattr(content, "read"):
        text = content.read()
    else:
        text = str(content)

    args: Set[Arg] = set()
    atts: Set[Attack] = set()

    # Strip comments and whitespace, but allow multiple facts per line
    cleaned_lines: List[str] = []
    for line in text.splitlines():
        # remove '//' and '%' comments
        l2 = line
        idx = l2.find("//")
        if idx != -1:
            l2 = l2[:idx]
        idx = l2.find("%")
        if idx != -1:
            l2 = l2[:idx]
        l2 = l2.strip()
        if l2:
            cleaned_lines.append(l2)

    # Merge multiple lines into a single string for regular matching
    blob = " ".join(cleaned_lines)

    for m in _APX_LINE_RE.finditer(blob):
        kind = m.group(1).lower()
        a1 = m.group(2)
        a2 = m.group(3)
        if kind == "arg":
            args.add(a1)
        elif kind == "att":
            if a2 is None:
                raise ValueError(f"Malformed att statement near: {m.group(0)}")
            atts.add((a1, a2))

    # Include any implicitly referenced args from attacks
    all_args = set(args)
    for u, v in atts:
        all_args.add(u)
        all_args.add(v)

    return ArgumentationFramework.from_sets(all_args, atts)
