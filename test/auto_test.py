import random
import time
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
from typing import List

from af_io import parse_apx
from min_edit_solver import find_minimal_edit
from ce_builder import build_contrastive_explanation
from helpers import *
from test.paths import DATA_DIR, SEMANTICS_DIR, RESULT_DIR

"""
Automated evaluation script for baseline contrastive explanations.
All parameters except the AF instance and the number of trials
are fixed to the experimental settings reported in the thesis.
"""
def run_baseline_random_tests(
    apx_path: str,
    semantics_dir: str = "semantics",
    n_trials: int = 10,
    output_file: str = "baseline_ce_results.csv",
    radius: int = 2,
    edit_mode: str = "both",
    seed: int = 2025,
):
    """
      1. For each semantics in {stable, complete, admissible}, compute fact/foil candidates.
      2. In each trial, randomly choose (semantics, fact, foil) and solve for a baseline CE.
      3. Record |C_cap|, |C_p|, |C_q|, |C_delta| and solving time for each trial.
      4. Compute averages over all successful trials for this instance and write them to CSV.
    """

    random.seed(seed)

    apx_path = Path(apx_path)
    if not apx_path.exists():
        raise FileNotFoundError(f"APX file not found: {apx_path}")

    semantics_dir = Path(semantics_dir)
    if not semantics_dir.exists():
        raise FileNotFoundError(f"Semantics dir not found: {semantics_dir}")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    instance_name = apx_path.name
    print(f"[Info] Loading AF from: {apx_path}")

    af_text = apx_path.read_text(encoding="utf-8")
    af_base = parse_apx(af_text)
    arg_count = len(af_base.arguments)
    
    # 1. Collect candidate facts/foils for three semantics
    sem_choices = ["stable", "complete", "admissible"]

    facts_per_sem = {}
    foils_per_sem = {}
    active_semantics: List[str] = []

    for sem in sem_choices:
        try:
            facts, foils = find_fact_and_foil_candidates(
                str(apx_path),
                semantics=sem,
                semantics_dir=str(semantics_dir),
            )
        except Exception as e:
            print(f"[Warn] Failed to compute candidates for semantics='{sem}': {e}")
            continue

        if facts and foils:
            facts_per_sem[sem] = facts
            foils_per_sem[sem] = foils
            active_semantics.append(sem)
            print(
                f"[Info] semantics='{sem}': #facts={len(facts)}, #foils={len(foils)}"
            )
        else:
            print(
                f"[Info] semantics='{sem}' has no valid (fact, foil) pairs, skipped."
            )

    if not active_semantics:
        raise RuntimeError(
            "No semantics yielded non-empty fact/foil candidate sets. "
            "Check your AF or candidate generation."
        )

    # 2. Prepare CSV
    out_path = Path(output_file)
    new_file = not out_path.exists()

    with out_path.open("a", encoding="utf-8") as f_out:
        if new_file:
            # write header
            f_out.write(
                "instance,arg_count,trial,fact,foil,semantics,"
                "C_cap_size,C_p_size,C_q_size,C_delta_size,"
                "time_sec\n"
            )
        else:
            f_out.write("\n")

        C_cap_sizes: List[float] = []
        C_p_sizes: List[float] = []
        C_q_sizes: List[float] = []
        C_delta_sizes: List[float] = []
        times: List[float] = []

        success_trials = 0
        attempts = 0
        max_attempts = n_trials * 10  # safety bound to avoid infinite loop

        while success_trials < n_trials and attempts < max_attempts:
            attempts += 1

            # 2.1 Randomly pick a semantics with available candidates
            semantics = random.choice(active_semantics)
            facts = facts_per_sem[semantics]
            foils = foils_per_sem[semantics]

            fact = random.choice(facts)
            foil = random.choice(foils)

            print(
                f"[Trial {success_trials + 1}] instance={instance_name}, "
                f"semantics={semantics}, fact={fact}, foil={foil} (attempt {attempts})"
            )

            try:
                af = parse_apx(apx_path.read_text(encoding="utf-8"))

                t_start = time.perf_counter()
                res = find_minimal_edit(
                    af=af,
                    fact=fact,
                    foil=foil,
                    semantics=semantics,
                    semantics_dir=str(semantics_dir),
                    edit_mode=edit_mode,
                    radius=radius,
                    ce_variant="baseline",
                    time_budget_sec=300.0,
                    verbose=False,
                )
                t_end = time.perf_counter()
                elapsed = t_end - t_start

            except RuntimeError as e:
                print(
                    f"  [Skip] No feasible baseline CE for this (fact, foil, semantics): {e}"
                )
                continue
            except Exception as e:
                print(f"  [Error] Unexpected exception: {e}")
                continue

            # 3. Build CE and measure component sizes
            ce = build_contrastive_explanation(res)

            C_cap_size = len(ce["C_cap"])
            C_p_size = len(ce["C_p"])
            C_q_size = len(ce["C_q"])
            C_delta_size = len(ce["C_delta"])

            C_cap_sizes.append(C_cap_size)
            C_p_sizes.append(C_p_size)
            C_q_sizes.append(C_q_size)
            C_delta_sizes.append(C_delta_size)
            times.append(elapsed)

            success_trials += 1

            # write record
            f_out.write(
                f"{instance_name},{arg_count},{success_trials},{fact},{foil},{semantics},"
                f"{C_cap_size},{C_p_size},{C_q_size},{C_delta_size},{elapsed:.6f}\n"
            )
            f_out.flush()

            print(
                f"  [OK], "
                f"|C_cap|={C_cap_size}, |C_p|={C_p_size}, |C_q|={C_q_size}, "
                f"|C_delta|={C_delta_size}, time={elapsed:.4f}s"
            )

        if success_trials == 0:
            print("[Warning] No successful baseline CE found in all attempts.")
            return

        # 4. Compute averages
        avg_C_cap = sum(C_cap_sizes) / len(C_cap_sizes)
        avg_C_p = sum(C_p_sizes) / len(C_p_sizes)
        avg_C_q = sum(C_q_sizes) / len(C_q_sizes)
        avg_C_delta = sum(C_delta_sizes) / len(C_delta_sizes)
        avg_time = sum(times) / len(times)


        f_out.write(
            f"{instance_name},{arg_count},AVERAGE,,,"
            f"{avg_C_cap:.3f},{avg_C_p:.3f},{avg_C_q:.3f},{avg_C_delta:.3f},,"
            f"{avg_time:.6f}\n"
        )
        f_out.flush()

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Automated baseline CE evaluation for a given AF"
    )
    parser.add_argument(
        "--apx",
        required=True,
        type=str,
        help="Path to the APX argumentation framework",
    )
    parser.add_argument(
        "--n_trials",
        default=10,
        type=int,
        help="Number of successful baseline CEs to compute (default: 10)",
    )

    args = parser.parse_args()

    run_baseline_random_tests(
        apx_path=args.apx,
        semantics_dir=str(SEMANTICS_DIR),
        n_trials=args.n_trials,
        output_file=str(RESULT_DIR / "baseline_ce_results.csv"),
        radius=2,
        edit_mode="both",
        seed=2025,
    )


if __name__ == "__main__":
    main()
