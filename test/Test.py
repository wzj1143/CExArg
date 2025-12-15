from pathlib import Path
from af_io import parse_apx
from min_edit_solver import find_minimal_edit
from ce_builder import build_contrastive_explanation, print_contrastive_explanation
import time
from test.paths import DATA_DIR, SEMANTICS_DIR
apx_path = DATA_DIR/"examples"/"ce1.apx"
af = parse_apx(apx_path.read_text(encoding="utf-8"))
print("|arguments| =", len(af.arguments))
print("|attacks| =", len(af.attacks))
# fact / foil / semantics
fact = "d"
foil = "e"
semantics   = "preferred"
print("fact =", fact)
print("foil =", foil)
print("start MaxSAT")
start_time = time.time()

res = find_minimal_edit(
    af, fact=fact, foil=foil, semantics=semantics,
    semantics_dir=SEMANTICS_DIR,
    edit_mode="del",     # "del", "add", "both"
    radius=2,
    given_extension = {"a", "b", "d"},
    ce_variant="keep_fact",# ["baseline", "keep_fact", "status_reversal"]
    verbose=True
)
end_time = time.time()
print("end MaxSAT")
elapsed = end_time - start_time

ce = build_contrastive_explanation(res)
print_contrastive_explanation(ce, label=f"CE({fact}, {foil})")
print(f"\nTotal runtime: {elapsed:.3f} seconds")