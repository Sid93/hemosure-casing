"""Minimal engineering-drawing kit on matplotlib: A3 sheets, title block, HLR views from
build123d, hatched sections, linear/diameter dimensions, tables. Units on paper = mm."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch, Rectangle as MRect, FancyArrowPatch, Polygon
from build123d import Box, Pos, Vector

PT = 72 / 25.4            # points per mm
LW_VIS, LW_HID, LW_THIN = 0.35 * PT, 0.18 * PT, 0.13 * PT
TXT = 2.6 * PT            # 2.6 mm text
INK = "#111111"
DIM = "#0b3d91"

VIEWS = {
    # name: (camera position direction, up)
    "front": ((0, 0, 1), (0, 1, 0)),     # from +Z (outside of front housing)
    "back": ((0, 0, -1), (0, 1, 0)),     # from -Z
    "right": ((1, 0, 0), (0, 1, 0)),     # from +X: shows Z horizontally, Y up
    "left": ((-1, 0, 0), (0, 1, 0)),
    "top": ((0, 1, 0), (0, 0, 1)),       # from +Y end
    "bottom": ((0, -1, 0), (0, 0, 1)),
}


def _cam(view, dist=500):
    d, up = VIEWS[view]
    return tuple(dist * c for c in d), up


def mapping(view):
    """Linear map 3D -> 2D consistent with build123d project_to_viewport for this view."""
    cam, up = _cam(view)
    pts = []
    for p in [(0, 0, 0), (10, 0, 0), (0, 10, 0), (0, 0, 10)]:
        b = Pos(*p) * Box(0.5, 0.5, 0.5)
        vis, hid = b.project_to_viewport(cam, up, (0, 0, 0))
        xy = np.array([[(e @ t).X, (e @ t).Y] for e in list(vis) + list(hid) for t in (0, 1)])
        pts.append(xy.mean(axis=0))
    o = pts[0]
    M = np.stack([(pts[1] - o) / 10, (pts[2] - o) / 10, (pts[3] - o) / 10], axis=1)  # 2x3
    return lambda p: M @ np.asarray(p, float) + o


def _poly(e, n=None):
    L = e.length
    if n is None:
        n = 2 if e.geom_type.name == "LINE" else max(6, min(80, int(L / 0.4)))
    return np.array([[(e @ t).X, (e @ t).Y] for t in np.linspace(0, 1, n)])


def hlr(shape, view, hidden=True):
    cam, up = _cam(view)
    vis, hid = shape.project_to_viewport(cam, up, (0, 0, 0))
    V = [_poly(e) for e in vis]
    Hh = [_poly(e) for e in hid] if hidden else []
    return V, Hh


def section_faces(shape_cut, axis, value, view):
    """Planar faces of shape_cut lying on the cutting plane -> list of (outer, [inners]) 2D polylines."""
    f3 = mapping(view)
    out = []
    k = "XYZ".index(axis)
    for f in shape_cut.faces():
        c = f.center()
        if abs([c.X, c.Y, c.Z][k] - value) > 1e-3:
            continue
        bb = f.bounding_box()
        if [bb.size.X, bb.size.Y, bb.size.Z][k] > 1e-3:
            continue
        def wire2d(w):
            pts = []
            for e in w.order_edges() if hasattr(w, "order_edges") else w.edges():
                n = 2 if e.geom_type.name == "LINE" else max(6, int(e.length / 0.3))
                for t in np.linspace(0, 1, n):
                    p = e @ t
                    pts.append(f3((p.X, p.Y, p.Z)))
            return np.array(pts)
        try:
            outer = wire2d(f.outer_wire())
            inners = [wire2d(w) for w in f.inner_wires()]
            out.append((outer, inners))
        except Exception:
            pass
    return out


class Sheet:
    def __init__(self, title, dwg_no, part, material, scale, sheet_no, n_sheets, rev="A", finish="", mass=""):
        self.fig = plt.figure(figsize=(420 / 25.4, 297 / 25.4))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 420); self.ax.set_ylim(0, 297); self.ax.set_aspect("equal"); self.ax.axis("off")
        a = self.ax
        a.add_patch(MRect((10, 10), 400, 277, fill=False, lw=0.7 * PT, ec=INK))
        a.add_patch(MRect((5, 5), 410, 287, fill=False, lw=0.25 * PT, ec=INK))
        # grid refs
        for i in range(8):
            a.text(10 + 50 * i + 25, 7.5, str(i + 1), ha="center", va="center", fontsize=6)
            a.text(10 + 50 * i + 25, 289.5, str(i + 1), ha="center", va="center", fontsize=6)
        for j, ch in enumerate("ABCDEF"):
            a.text(7.5, 287 - 46 * j - 23, ch, ha="center", va="center", fontsize=6)
        self._title_block(title, dwg_no, part, material, scale, sheet_no, n_sheets, rev, finish, mass)

    def _title_block(self, title, dwg_no, part, material, scale, sheet_no, n_sheets, rev, finish, mass):
        a = self.ax
        x0, y0, w, h = 250, 10, 160, 44
        a.add_patch(MRect((x0, y0), w, h, fill=True, fc="white", lw=0.5 * PT, ec=INK, zorder=5))
        rows = [
            (y0 + 36, "LEVRAM LIFESCIENCES", 8.5, "bold"),
            (y0 + 29.5, title, 7.5, "bold"),
        ]
        for yy, t, fs, fw in rows:
            a.text(x0 + 3, yy, t, fontsize=fs, fontweight=fw, va="center", zorder=6)
        a.plot([x0, x0 + w], [y0 + 25, y0 + 25], lw=0.3 * PT, c=INK, zorder=6)
        cells = [
            ("PART", part), ("DWG NO.", dwg_no), ("REV", rev),
            ("MATERIAL", material), ("SCALE", scale), ("SHEET", f"{sheet_no} / {n_sheets}"),
            ("FINISH", finish or "-"), ("UNITS", "mm"), ("PROJ.", "1st angle (ISO E)"),
            ("MASS", mass or "-"), ("DATE", "2026-09-28"), ("STATUS", "DRAFT - DFM review"),
        ]
        cw = [70, 50, 40]
        for i, (k, v) in enumerate(cells):
            r, c = divmod(i, 3)
            cx = x0 + sum(cw[:c]); cy = y0 + 25 - (r + 1) * 6.25
            a.add_patch(MRect((cx, cy), cw[c], 6.25, fill=False, lw=0.25 * PT, ec=INK, zorder=6))
            a.text(cx + 1, cy + 4.6, k, fontsize=4.2, color="#555", va="center", zorder=7)
            a.text(cx + 1, cy + 2.0, v, fontsize=5.6, va="center", zorder=7)
        a.text(x0 + w - 2, y0 + 36, "HemoSure Hb meter casing", fontsize=6, ha="right", va="center", zorder=6, color="#444")
        a.text(x0 + w - 2, y0 + 31, "Drawn: Claude (AI) for S. Saboo  |  Chk: ____  |  Appr: ____", fontsize=4.6,
               ha="right", va="center", zorder=6, color="#444")

    # ------------------------------------------------------------------ geometry placement
    def anchor(self, view, cx, cy, s=1.0, p3=(0, 0, 0)):
        """Offsets so that 3D point p3 lands on paper (cx, cy)."""
        q = mapping(view)(p3)
        return cx - s * q[0], cy - s * q[1]

    def _clip(self, arts, clip):
        if clip is None:
            return
        r = MRect((clip[0], clip[1]), clip[2] - clip[0], clip[3] - clip[1], transform=self.ax.transData)
        for a in arts:
            a.set_clip_path(r)

    def view(self, shape, view, ox, oy, s=1.0, hidden=False, label=None, lw=LW_VIS, clip=None, color=INK):
        V, Hh = hlr(shape, view, hidden)
        arts = []
        for p in V:
            arts += self.ax.plot(ox + s * p[:, 0], oy + s * p[:, 1], c=color, lw=lw, solid_capstyle="round")
        for p in Hh:
            arts += self.ax.plot(ox + s * p[:, 0], oy + s * p[:, 1], c="#555", lw=LW_HID, ls=(0, (3, 1.5)))
        self._clip(arts, clip)
        f = mapping(view)
        if label:
            allp = np.vstack(V) if V else np.zeros((1, 2))
            self.ax.text(ox + s * (allp[:, 0].min() + allp[:, 0].max()) / 2, oy + s * allp[:, 1].max() + 17, label,
                         ha="center", va="bottom", fontsize=7, fontweight="bold")
        return lambda p: np.array([ox, oy]) + s * f(p)

    def section(self, shape, axis, value, keep, view, ox, oy, s=1.0, label=None, hatch="////", fc="none", clip=None, color=INK):
        """keep = '+' or '-' : which side of the plane stays."""
        big = 400
        lo, hi = (value, value + big) if keep == "+" else (value - big, value)
        k = "XYZ".index(axis)
        c = [0, 0, 0]; sz = [2 * big, 2 * big, 2 * big]
        c[k] = (lo + hi) / 2; sz[k] = hi - lo
        cut = shape & (Pos(*c) * Box(*sz))
        P = self.view(cut, view, ox, oy, s, hidden=False, label=label, clip=clip, color=color)
        from matplotlib.collections import PolyCollection
        f3 = K_mapping = mapping(view)
        kk = "XYZ".index(axis)
        tris2d = []
        for f in cut.faces():
            c = f.center()
            bb = f.bounding_box()
            if abs([c.X, c.Y, c.Z][kk] - value) > 1e-3 or [bb.size.X, bb.size.Y, bb.size.Z][kk] > 1e-3:
                continue
            try:
                vs, ts = f.tessellate(0.02, 0.2)
            except Exception:
                continue
            pts = np.array([f3((v.X, v.Y, v.Z)) for v in vs])
            pts = np.column_stack([ox + s * pts[:, 0], oy + s * pts[:, 1]])
            tris2d += [pts[list(t)] for t in ts]
        if tris2d:
            pc = PolyCollection(tris2d, facecolors=fc if fc != "none" else "none", edgecolors=color,
                                linewidths=0.0, hatch=hatch or None, zorder=0.5)
            if fc != "none" and not hatch:
                pc.set_edgecolor(fc); pc.set_linewidth(0.2)
            self.ax.add_collection(pc)
            self._clip([pc], clip)
        matplotlib.rcParams["hatch.linewidth"] = 0.35
        return P

    # ------------------------------------------------------------------ annotation
    def text(self, x, y, t, fs=6.5, **kw):
        self.ax.text(x, y, t, fontsize=fs, **kw)

    def dim(self, p1, p2, off, text, orient="h", fs=6.2, color=DIM):
        """Linear dimension between paper points p1, p2; off = offset of the dim line (mm on paper)."""
        a = self.ax
        p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
        if orient == "h":
            y = max(p1[1], p2[1]) + off if off > 0 else min(p1[1], p2[1]) + off
            q1, q2 = np.array([p1[0], y]), np.array([p2[0], y])
            for p, q in ((p1, q1), (p2, q2)):
                a.plot([p[0], q[0]], [p[1] + np.sign(off) * 1, q[1] + np.sign(off) * 1.5], c=color, lw=LW_THIN)
            tx, ty, rot = (q1[0] + q2[0]) / 2, y + 0.8, 0
        else:
            x = max(p1[0], p2[0]) + off if off > 0 else min(p1[0], p2[0]) + off
            q1, q2 = np.array([x, p1[1]]), np.array([x, p2[1]])
            for p, q in ((p1, q1), (p2, q2)):
                a.plot([p[0] + np.sign(off) * 1, q[0] + np.sign(off) * 1.5], [p[1], q[1]], c=color, lw=LW_THIN)
            tx, ty, rot = x - 0.8, (q1[1] + q2[1]) / 2, 90
        a.add_patch(FancyArrowPatch(q1, q2, arrowstyle="<|-|>,head_length=2.2,head_width=0.7", mutation_scale=1,
                                    lw=LW_THIN, color=color, shrinkA=0, shrinkB=0))
        a.text(tx, ty, text, fontsize=fs, color=color, ha="center", va="bottom", rotation=rot,
               bbox=dict(fc="white", ec="none", pad=0.3))

    def leader(self, p, dx, dy, text, fs=6.0, color=DIM):
        p = np.asarray(p, float)
        q = p + np.array([dx, dy])
        self.ax.annotate(text, xy=p, xytext=q, fontsize=fs, color=color, ha="left" if dx >= 0 else "right", va="center",
                         arrowprops=dict(arrowstyle="-|>,head_length=0.35,head_width=0.12", lw=LW_THIN, color=color),
                         bbox=dict(fc="white", ec="none", pad=0.2))

    def cutline(self, p1, p2, name):
        a = self.ax
        a.plot([p1[0], p2[0]], [p1[1], p2[1]], c="#b00", lw=0.25 * PT, ls=(0, (8, 2, 1, 2)))
        for p in (p1, p2):
            a.text(p[0], p[1], name, fontsize=7, fontweight="bold", color="#b00", ha="center", va="center",
                   bbox=dict(fc="white", ec="none", pad=0.2))

    def table(self, x, y, col_w, rows, fs=5.6, row_h=4.6, header=True, title=None, wrap=None):
        a = self.ax
        if title:
            a.text(x, y + 1.5, title, fontsize=fs + 1.4, fontweight="bold", va="bottom")
        yy = y
        for i, r in enumerate(rows):
            cx = x
            for j, (w, v) in enumerate(zip(col_w, r)):
                a.add_patch(MRect((cx, yy - row_h), w, row_h, fill=(header and i == 0), fc="#e8edf5",
                                  lw=0.2 * PT, ec="#777"))
                a.text(cx + 0.8, yy - row_h / 2, str(v), fontsize=fs, va="center",
                       fontweight="bold" if (header and i == 0) else "normal", clip_on=True)
                cx += w
            yy -= row_h
        return yy

    def notes(self, x, y, lines, fs=5.8, title="NOTES", lh=3.6):
        self.ax.text(x, y, title, fontsize=fs + 1.4, fontweight="bold", va="top")
        yy = y - lh - 1
        for ln in lines:
            self.ax.text(x, yy, ln, fontsize=fs, va="top")
            yy -= lh
        return yy

    def image(self, path, x, y, w):
        img = plt.imread(path)
        h = w * img.shape[0] / img.shape[1]
        self.ax.imshow(img, extent=(x, x + w, y, y + h), zorder=1)
        return h

    def save(self, pdf):
        pdf.savefig(self.fig)
        plt.close(self.fig)
