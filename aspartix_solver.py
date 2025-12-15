import clingo
from pathlib import Path
from typing import List, Set, Union, Optional
from af_io import ArgumentationFramework


# Semantics -> ASPARTIX Encoding File
SEM_FILES = {
    "stable": "stable.dl",
    "preferred": "prefex_gringo.lp",
    "complete": "comp.dl",
    "admissible": "adm.dl",
}


def compute_extensions(
    af: Union[ArgumentationFramework, str, Path],
    semantics: str,
    semantics_dir: Union[str, Path] = "semantics",
    models: int = 0,
    force_in: Optional[str] = None, # force an argument to be in/1
    ep_for_max_commonality: Optional[Set[str]] = None,  # if provided, maximize |in/1∩Ep|
    ep_for_min_difference: Optional[Set[str]] = None,   # if provided, minimize |Cp ∪ Cq|
) -> List[Set[str]]:
    """
    Compute all extensions for a given AF under a chosen semantics using ASPARTIX + clingo.

    Parameters
    ----------
    af : ArgumentationFramework | str | Path
        The AF object or .apx file path or string content.
    semantics : str
        One of {'stable', 'preferred', 'complete', 'admissible'}.
    semantics_dir : str | Path
        Directory containing ASPARTIX.dl semantics encodings.
    models : int
        Max number of models/extensions to compute (0 = all).

    Returns
    -------
    List[Set[str]]
        A list of extensions, each represented as a set of argument names.
    """
    semantics = semantics.lower().strip()
    if semantics not in SEM_FILES:
        raise ValueError(f"Unsupported semantics: {semantics}. "
                         f"Available: {', '.join(SEM_FILES.keys())}")

    sem_path = Path(semantics_dir) / SEM_FILES[semantics]
    if not sem_path.exists():
        raise FileNotFoundError(f"Semantics file not found: {sem_path}")

    # Prepare the AF input: write to temporary .apx file if needed
    if isinstance(af, ArgumentationFramework):
        af_text = af.to_aspartix()
    elif isinstance(af, Path) or Path(str(af)).exists():
        af_text = Path(af).read_text(encoding="utf-8")
    else:
        af_text = str(af)

    sem_text = sem_path.read_text(encoding="utf-8")

    # Build program parts
    parts = [sem_text, af_text]

    # Enforce foil/fact inclusion if requested
    if force_in is not None:
        parts.append(f":- not in({force_in}).")

    #   1) ep_for_max_commonality: maximize |in ∩ Ep|
    #   2) ep_for_min_difference: minimize |Cp ∪ Cq|
    #      Cp = Ep \ in, Cq = in \ Ep
    optimizing_common = ep_for_max_commonality is not None and len(ep_for_max_commonality) > 0
    optimizing_diff = ep_for_min_difference is not None and len(ep_for_min_difference) > 0
    if optimizing_common:
        ep_facts = "\n".join(f"ep({a})." for a in ep_for_max_commonality)
        parts.append(ep_facts)
        # maximize |in ∩ Ep|
        parts.append("#maximize { 1,X : in(X), ep(X) }.")

    elif optimizing_diff:
        ep_facts = "\n".join(f"ep({a})." for a in ep_for_min_difference)
        parts.append(ep_facts)
        #   C_q = { X | in(X), not ep(X) }
        #   C_p = { X | ep(X), not in(X) }
        # minimize |C_p| + |C_q|
        parts.append("#minimize { 1,X : in(X), not ep(X) }.")
        parts.append("#minimize { 1,X : ep(X), not in(X) }.")

    program_text = "\n".join(parts)

    extensions: List[Set[str]] = []

    # Define model callback functions
    def on_model(model: clingo.Model):
        # Extract all accepted arguments from a clingo model
        ext = {str(sym.arguments[0]) for sym in model.symbols(atoms=True) if sym.name == "in"}
        if not ext:
            return

        if optimizing_common or optimizing_diff:
            # in optimization mode, we keep only the “current best” (the last one being the global best).
            extensions.clear()
            extensions.append(ext)
        else:
            extensions.append(ext)
            if models > 0 and len(extensions) >= models:
                raise StopIteration

    # -n 0 indicates “all models”; -n k indicates “the first k models”
    args = ["--warn=no-atom-undefined"]
    if optimizing_common or optimizing_diff:
        args += ["-n", "0", "--opt-mode=opt"]
    else:
        args += ["-n", "0" if models <= 0 else str(models)]

    ctl = clingo.Control(args)
    ctl.add("base", [], program_text)
    ctl.ground([("base", [])])

    try:
        ctl.solve(on_model=on_model)
    except StopIteration:
        pass

    return extensions

