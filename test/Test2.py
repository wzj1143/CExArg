from pathlib import Path
from af_io import parse_apx
from min_edit_solver import find_minimal_edit
from ce_builder import build_contrastive_explanation, print_contrastive_explanation
from helpers.find_fact_and_foil import find_fact_and_foil_candidates
import time
from test.paths import DATA_DIR, SEMANTICS_DIR

apx_path = DATA_DIR / "instances" / "A-1-BA_40_80_5.apx"

facts, foils = find_fact_and_foil_candidates(apx_path, "stable",SEMANTICS_DIR)
print(facts)
print(foils)