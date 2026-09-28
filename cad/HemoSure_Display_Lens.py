"""HemoSure display lens, 0.8 PMMA laser-cut -- generated from hemosure_casing.py (edit parameters there, not here)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hemosure_casing as H


def gen_step():
    return H.build_lens()
