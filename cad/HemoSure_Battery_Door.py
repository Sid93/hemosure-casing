"""HemoSure battery door, ABS -- generated from hemosure_casing.py (edit parameters there, not here)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import hemosure_casing as H


def gen_step():
    return H.build_door()
