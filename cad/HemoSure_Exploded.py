"""HemoSure exploded view (for review renders only)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build123d import Compound, Pos
import hemosure_casing as H


def gen_step():
    P = H.build_all()
    R = {r.label: r for r in H.build_ref_components()}
    lay = [(P["door"], -25), (P["rear"], 0), (R["REF_lipo_503035"], -8), (P["optical"], 12), (Pos(0, -30, 0) * P["tray"], 12), (Pos(0, -30, 0) * R["REF_hb_strip_6x30x0.5"], 18), (R["REF_led_board"], 20),
           (P["pcb"], 22), (R["REF_usb_c_receptacle"], 22), (R["REF_tact_6x6x5"], 22), (R["REF_tft_1.8in_ST7735"], 34),
           (P["front"], 48), (P["button"], 62), (P["lens"], 70), (P["overlay"], 78)]
    kids = []
    for shp, dz in lay:
        m = Pos(0, 0, dz) * shp
        m.label, m.color = shp.label, shp.color
        kids.append(m)
    asm = Compound(children=kids)
    asm.label = "HemoSure_Exploded"
    return asm
