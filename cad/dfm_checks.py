"""Draft + wall checks on moulded parts. Draft measured against the Z draw direction."""
from math import degrees, asin
import hemosure_casing as H


def draft_report(P, min_draft=0.2, min_height=1.0):
    bad = []
    for f in P.faces():
        try:
            n = f.normal_at()
        except Exception:
            continue
        bb = f.bounding_box()
        h = bb.max.Z - bb.min.Z
        dr = degrees(asin(min(1.0, abs(n.Z))))  # angle between face and the draw axis
        if dr < min_draft and h >= min_height:
            c = f.center()
            bad.append((round(h, 2), round(dr, 2), round(f.area, 1), (round(c.X, 1), round(c.Y, 1), round(c.Z, 1)), str(f.geom_type).split(".")[-1]))
    return sorted(bad, reverse=True)


if __name__ == "__main__":
    for n, fn in [("rear", H.build_rear), ("front", H.build_front), ("door", H.build_door), ("button", H.build_button), ("optical", H.build_optical_block), ("tray", H.build_tray)]:
        b = draft_report(fn())
        print(n, len(b))
        for r in b[:40]:
            print("   ", r)
