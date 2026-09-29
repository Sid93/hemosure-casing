"""Export every part / assembly / mould STEP to STL (GitHub renders .stl as an interactive 3D view)."""
import glob, os, pathlib
from build123d import import_step, export_stl

ROOT = pathlib.Path(__file__).resolve().parent.parent
(ROOT / "stl").mkdir(exist_ok=True)
for f in sorted(glob.glob(str(ROOT / "cad" / "HemoSure_*.step")) + glob.glob(str(ROOT / "mold" / "HemoSure_*.step"))):
    out = ROOT / "stl" / os.path.basename(f).replace(".step", ".stl")
    export_stl(import_step(f), str(out), tolerance=0.02, angular_tolerance=0.2)
    print(out.name, out.stat().st_size // 1024, "KB")
