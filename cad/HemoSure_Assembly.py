"""HemoSure full assembly: 4 moulded parts, lens, overlay + reference PCB/TFT/USB-C/tact/LiPo/cuvette."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build123d import Compound
import hemosure_casing as H


def gen_step():
    P = H.build_all()
    kids = [P["rear"], P["front"], P["door"], P["button"], P["optical"], P["tray"], P["lens"], P["overlay"], P["pcb"]] + H.build_ref_components()
    asm = Compound(children=kids)
    asm.label = "HemoSure_Assembly"
    return asm
