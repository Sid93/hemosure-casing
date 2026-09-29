"""HemoSure with the strip tray pulled out 30 mm (review render: how the strip is loaded)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build123d import Compound, Pos
import hemosure_casing as H


def gen_step():
    P = H.build_all()
    R = {r.label: r for r in H.build_ref_components()}
    kids = []
    for k in ("rear", "front", "button", "lens", "overlay", "door"):
        kids.append(P[k])
    for shp in (P["tray"], R["REF_hb_strip_6x30x0.5"]):
        m = Pos(0, -30, 0) * shp
        m.label, m.color = shp.label, shp.color
        kids.append(m)
    asm = Compound(children=kids)
    asm.label = "HemoSure_Tray_Open"
    return asm
