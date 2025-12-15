# main.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Set

from af_io import parse_apx
from min_edit_solver import find_minimal_edit
from ce_builder import build_contrastive_explanation, print_contrastive_explanation


ROOT_DIR = Path(__file__).resolve().parent
SEMANTICS_DIR = ROOT_DIR / "semantics"


def _parse_extension(ext: Optional[str]) -> Optional[Set[str]]:
    if ext is None:
        return None
    s = ext.strip()
    if not s:
        return None
    # remove optional braces
    if s.startswith("{") and s.endswith("}"):
        s = s[1:-1].strip()
    # split by comma or whitespace
    parts = [p.strip() for p in s.replace(",", " ").split()]
    return set(p for p in parts if p)


def compute_ce(
    apx_path: Path,
    fact: str,
    foil: str,
    semantics: str,
    edit_mode: str = "both",
    radius: int = 2,
    given_extension: Optional[Set[str]] = None,
    ce_variant: str = "baseline",
    max_iters: int = 10000,
    time_budget_sec: Optional[float] = None,
    semantics_dir: Path = SEMANTICS_DIR,
    verbose: bool = False,
):
    """
    Compute a CE:
      APX -> AF -> minimal edit (RC2 + clingo) -> CE construction.
    """
    apx_path = apx_path.expanduser().resolve()
    if not apx_path.exists():
        raise FileNotFoundError(f"APX file not found: {apx_path}")

    if not semantics_dir.exists():
        raise FileNotFoundError(f"Semantics directory not found: {semantics_dir}")

    af = parse_apx(apx_path.read_text(encoding="utf-8"))

    min_edit_res = find_minimal_edit(
        af=af,
        fact=fact,
        foil=foil,
        semantics=semantics,
        semantics_dir=str(semantics_dir),
        edit_mode=edit_mode,
        radius=radius,
        given_extension=given_extension,
        ce_variant=ce_variant,
        max_iters=max_iters,
        time_budget_sec=time_budget_sec,
        verbose=verbose,
    )

    ce = build_contrastive_explanation(min_edit_res)
    return ce, min_edit_res


def main():
    parser = argparse.ArgumentParser(
        description="Compute a contrastive explanation (CE) with CExArg."
    )
    parser.add_argument("--apx", required=True, type=str, help="Path to the .apx file")
    parser.add_argument("--fact", required=True, type=str, help="Fact argument name (e.g., a)")
    parser.add_argument("--foil", required=True, type=str, help="Foil argument name (e.g., b)")
    parser.add_argument(
        "--semantics",
        required=True,
        type=str,
        choices=["admissible", "complete", "preferred", "stable"],
        help="Semantics to use",
    )
    parser.add_argument(
        "--edit_mode",
        default="both",
        choices=["add", "del", "both"],
        help="Allowed edit operations",
    )
    parser.add_argument("--radius", default=2, type=int, help="Neighborhood radius for candidate domain")
    parser.add_argument(
        "--given_extension",
        default=None,
        type=str,
        help='Optional given extension, e.g. "a,b,d" or "{a, b, d}"',
    )
    parser.add_argument(
        "--ce_variant",
        default="baseline",
        choices=["baseline", "keep_fact", "status_reversal"],
        help="CE variant",
    )
    parser.add_argument("--max_iters", default=10000, type=int, help="Max CEGAR iterations")
    parser.add_argument(
        "--time_budget_sec",
        default=None,
        type=float,
        help="Optional time budget (seconds) for a single CE; None = no explicit budget",
    )
    parser.add_argument(
        "--semantics_dir",
        default=str(SEMANTICS_DIR),
        type=str,
        help='Directory containing ASP semantics files (default: "<repo>/semantics")',
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose solver output")

    args = parser.parse_args()

    ce, _ = compute_ce(
        apx_path=Path(args.apx),
        fact=args.fact,
        foil=args.foil,
        semantics=args.semantics,
        edit_mode=args.edit_mode,
        radius=args.radius,
        given_extension=_parse_extension(args.given_extension),
        ce_variant=args.ce_variant,
        max_iters=args.max_iters,
        time_budget_sec=args.time_budget_sec,
        semantics_dir=Path(args.semantics_dir),
        verbose=args.verbose,
    )

    # Pretty print
    print_contrastive_explanation(ce)


if __name__ == "__main__":
    main()
