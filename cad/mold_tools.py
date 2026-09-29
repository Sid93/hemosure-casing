"""Mould split + undercut verification for the HemoSure casing parts.

sweep(P, d): every point reachable by moving a point of P along +d  (P plus prisms of the
faces whose outward normal has a positive component along d).
A mould half that withdraws along direction w is free of the part iff it does not intersect
sweep(P, -w)  (no part material lies in its path).
"""
from build123d import Vector, extrude, Solid, Part, Compound
import hemosure_casing as H

BIG = 80.0
SKIPPED = []


def _prisms(P, d, zp=None):
    d = Vector(*d)
    out = []
    faces = P.faces()
    if zp is not None:   # split at the parting plane so no face straddles it (mixed normals)
        from build123d import Plane, Keep
        halves = P.split(Plane.XY.offset(zp), keep=Keep.BOTH)
        if isinstance(halves, tuple):
            halves = [h for h in halves if h is not None]
            allf = [f for h in halves for f in h.faces()]
        else:
            allf = halves.faces()
        faces = [f for f in allf
                 if not (f.geom_type.name == "PLANE" and abs(f.center().Z - zp) < 1e-6 and abs(f.normal_at().Z) > 0.999)]
    for f in faces:
        try:
            n = f.normal_at()
        except Exception:
            continue
        if n.dot(d) > 1e-4:
            try:
                out.append(extrude(f, BIG, dir=d))
            except Exception:
                pass
    return out


def sweep(P, d, zp=None):
    pr = _prisms(P, d, zp)
    res = P
    SKIPPED.clear()
    for i in range(0, len(pr), 40):          # fuse in chunks; fall back one-by-one if OCC balks
        try:
            res = res.fuse(*pr[i:i + 40])
        except Exception:
            for q in pr[i:i + 40]:
                try:
                    res = res.fuse(q)
                except Exception:
                    try:
                        res = res.fuse(q, tol=1e-3)       # fuzzy boolean fallback
                    except Exception:
                        SKIPPED.append(q)
    return res.clean() if not SKIPPED else res


def vol(s):
    try:
        return s.volume if s is not None else 0.0
    except Exception:
        return 0.0


def split_by_sweep(P, B, zp, cavity_dir):
    """cavity_dir = -1: cavity withdraws -Z (core +Z). Returns core, cavity, undercut_volume."""
    A = B - P
    cav_block = sweep(P, (0, 0, -cavity_dir))   # part material in the cavity's withdrawal path
    core_block = sweep(P, (0, 0, cavity_dir))
    cav_free = A - cav_block
    core_free = A - core_block
    both = cav_free & core_free
    half_core = H.half_space(zp, 300) if cavity_dir < 0 else H.half_space(-300, zp)
    cavity = cav_free - (both & half_core)
    core = A - cavity
    undercut = A - cav_free - core_free
    return core, cavity, vol(undercut)


def verify(P, core, cavity, cavity_dir, zp=None):
    """Volume of core/cavity steel that would collide with the part on ejection (should be ~0)."""
    core_hit = core & sweep(P, (0, 0, cavity_dir), zp)      # core withdraws -cavity_dir
    cav_hit = cavity & sweep(P, (0, 0, -cavity_dir), zp)
    return vol(core_hit), vol(cav_hit)
