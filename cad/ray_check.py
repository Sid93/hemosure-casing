"""Ray-casting mouldability check (robust replacement for the boolean sweep test).

A 2-plate mould only moves along Z. Cast vertical rays on a fine XY grid:
  * part: every ray must cross the part in at most ONE interval (a gap between two part
    intervals is steel that can leave neither up nor down = undercut);
  * inserts: along every ray the order bottom->top must be CAVITY, PART, CORE -- cavity steel
    never above core steel, each insert a single interval (so each half can withdraw).
Rays are offset by an irrational fraction of the pitch so they never graze mesh edges.
"""
import numpy as np

SHIFT = 0.0137


def _mesh(shape, tol=0.004):
    vs, ts = shape.tessellate(tol, 0.05)   # fine: facets must not fake gaps on curved walls
    V = np.array([[v.X, v.Y, v.Z] for v in vs])
    return V, np.array(ts, dtype=int)


def column_hits(shape, pitch=0.25, bbox=None):
    V, T = _mesh(shape)
    bb = shape.bounding_box() if bbox is None else bbox
    x0, y0 = bb.min.X - pitch, bb.min.Y - pitch
    nx = int((bb.max.X - x0) / pitch) + 3
    ny = int((bb.max.Y - y0) / pitch) + 3
    hits = {}
    A, B, C = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    for a, b, c in zip(A, B, C):
        d = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if abs(d) < 1e-12:
            continue  # vertical facet: no Z crossing
        i0 = int(np.floor((min(a[0], b[0], c[0]) - x0 - SHIFT * pitch) / pitch))
        i1 = int(np.ceil((max(a[0], b[0], c[0]) - x0 - SHIFT * pitch) / pitch))
        j0 = int(np.floor((min(a[1], b[1], c[1]) - y0 - SHIFT * pitch) / pitch))
        j1 = int(np.ceil((max(a[1], b[1], c[1]) - y0 - SHIFT * pitch) / pitch))
        ii, jj = np.meshgrid(np.arange(i0, i1 + 1), np.arange(j0, j1 + 1), indexing="ij")
        px = x0 + (ii + SHIFT) * pitch
        py = y0 + (jj + SHIFT * 1.618) * pitch
        l1 = ((b[0] - px) * (c[1] - py) - (c[0] - px) * (b[1] - py)) / d
        l2 = ((c[0] - px) * (a[1] - py) - (a[0] - px) * (c[1] - py)) / d
        l3 = 1 - l1 - l2
        m = (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        if not m.any():
            continue
        z = l1 * a[2] + l2 * b[2] + l3 * c[2]
        for i, j, zz in zip(ii[m], jj[m], z[m]):
            hits.setdefault((int(i), int(j)), []).append(float(zz))
    return hits, (x0, y0, pitch)


def intervals(zs, eps=1e-4):
    zs = sorted(zs)
    ded = []
    for z in zs:  # drop duplicates from rays through shared edges
        if ded and abs(z - ded[-1]) < eps:
            ded.pop()  # a double hit at the same z is a touch (enter+exit) -> cancels
            continue
        ded.append(z)
    if len(ded) % 2:
        return None  # open / non-manifold along this ray
    return [(ded[k], ded[k + 1]) for k in range(0, len(ded), 2)]


def part_check(shape, pitch=0.25, min_gap=0.01):
    hits, _ = column_hits(shape, pitch)
    bad, odd = [], 0
    for key, zs in hits.items():
        iv = intervals(zs)
        if iv is None:
            odd += 1
            continue
        gaps = [iv[k + 1][0] - iv[k][1] for k in range(len(iv) - 1)]
        if any(g > min_gap for g in gaps):
            bad.append(key)
    return dict(columns=len(hits), undercut_columns=len(bad), open_rays=odd), bad


def insert_check(part, core, cavity, pitch=0.35, tol=0.01):
    """Order along every ray must be cavity (bottom) -> part -> core (top)."""
    bb = core.bounding_box()
    res = {}
    H = {}
    for name, shp in (("part", part), ("core", core), ("cavity", cavity)):
        H[name], _ = column_hits(shp, pitch, bb)
    bad_order, multi_core, multi_cav = 0, 0, 0
    keys = set(H["core"]) | set(H["cavity"])
    for k in keys:
        ivc = intervals(H["core"].get(k, [])) or []
        ivv = intervals(H["cavity"].get(k, [])) or []
        ivp = intervals(H["part"].get(k, [])) or []
        # merge touching intervals (insert interfaces at the P/L are coincident)
        if len(ivc) > 1:
            multi_core += 1
        if len(ivv) > 1:
            multi_cav += 1
        if ivc and ivv and max(b for _, b in ivv) > min(a for a, _ in ivc) + tol:
            bad_order += 1
        if ivp and ivv and max(b for _, b in ivv) > min(a for a, _ in ivp) + tol:
            bad_order += 1
        if ivp and ivc and min(a for a, _ in ivc) < max(b for _, b in ivp) - tol:
            bad_order += 1
    res.update(columns=len(keys), wrong_order=bad_order, core_split_columns=multi_core, cavity_split_columns=multi_cav)
    return res
