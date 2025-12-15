from pathlib import Path
from af_io import parse_apx
from min_edit_solver import find_minimal_edit
from ce_builder import build_contrastive_explanation, print_contrastive_explanation
import time
from test.paths import DATA_DIR, SEMANTICS_DIR

apx_path = DATA_DIR / "instances" / "A-1-BA_40_80_5.apx"

af = parse_apx(apx_path.read_text(encoding="utf-8"))

# 设定 fact / foil / 语义
fact = "a10"
foil = "a0"
semantics = "stable"
print("fact =", fact)
print("foil =", foil)
print("start MaxSAT")
start_time = time.time()

res = find_minimal_edit(
    af, fact=fact, foil=foil, semantics=semantics,
    semantics_dir=SEMANTICS_DIR,
    edit_mode="both",     # 只删: "del", 只加: "add", 增删均可: "both"
    radius=2,             # 邻域裁剪
    verbose=True,
    ce_variant="baseline"
)
end_time = time.time()
print("end MaxSAT")
elapsed = end_time - start_time

ce = build_contrastive_explanation(res)
print("|arguments| =", len(af.arguments))
print("|attacks| =", len(af.attacks))
print_contrastive_explanation(ce, label=f"CE({fact}, {foil})")
print(f"\nTotal runtime: {elapsed:.3f} seconds")