"""Core/cavity inserts for the 4 HemoSure moulded parts (ABS, 0.5 % shrink applied).

Housings: feature-based split (cavity = outside of the envelope minus cavity-side features,
core = everything else), then verified with the sweep test in mold_tools.verify().
Door + button: pure sweep split. Every insert is scaled by (1 + SHRINK_ABS) about the
part origin, so the steel is oversize and the moulded part shrinks to nominal.
"""
import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "cad"))
from build123d import scale, Color
import hemosure_casing as H
import mold_tools as M
import ray_check as RC

K = 1 + H.SHRINK_ABS


def _union(tools):
    u = tools[0]
    for t in tools[1:]:
        u = u + t
    return u


def rear_inserts():
    P = H.build_rear()
    o_rear, _ = H.outer_envelope()
    fill = o_rear - _union(H.rear_cavity_side_cuts())
    B = H.box(-60, 60, -90, 90, -25, H.ZP + 30)
    cavity = (B & H.half_space(-300, H.ZP)) - fill
    core = B - P - cavity
    return P, core, cavity, -1, H.ZP


def front_inserts():
    P = H.build_front()
    _, o_front = H.outer_envelope()
    fill = o_front - _union(H.front_cavity_side_cuts())
    B = H.box(-60, 60, -90, 90, H.ZP - 30, H.T + 25)
    cavity = (B & H.half_space(H.ZP, 300)) - fill
    core = B - P - cavity
    return P, core, cavity, +1, H.ZP


def door_inserts():
    P = H.build_door()
    B = H.box(-40, 40, -30, 50, -20, 25)
    core, cavity, _ = M.split_by_sweep(P, B, H.DOOR_T, -1)
    return P, core, cavity, -1, H.DOOR_T


def button_inserts():
    P = H.build_button()
    zp = H.Z_FRONT_IN - H.BTN_PLAY - H.BTN_FLANGE_T
    B = H.box(-20, 20, -28, 12, zp - 20, H.T + 20)
    core, cavity, _ = M.split_by_sweep(P, B, zp, +1)
    return P, core, cavity, +1, zp


def optical_inserts():
    P = H.build_optical_block()
    B = H.box(-30, 30, -75, -8, H.OB_Z0 - 20, H.OB_Z1 + 20)
    core, cavity, _ = M.split_by_sweep(P, B, H.OB_Z0, -1)
    return P, core, cavity, -1, H.OB_Z0


def tray_inserts():
    """Flat parting at ZP: every void below ZP opens downward, every void above opens upward
    (verified by ray_check), so a plain half-space split is exact."""
    P = H.build_tray()
    B = H.box(-30, 30, -85, -15, H.ZP - 22, H.ZP + 22)
    cavity = (B & H.half_space(-300, H.ZP)) - P
    core = (B & H.half_space(H.ZP, 300)) - P
    return P, core, cavity, -1, H.ZP


BUILDERS = {"Rear_Housing": rear_inserts, "Front_Housing": front_inserts,
            "Battery_Door": door_inserts, "Button_Cap": button_inserts,
            "Optical_Block": optical_inserts, "Strip_Tray": tray_inserts}


def build(name, check=True):
    P, core, cavity, cdir, zp = BUILDERS[name]()
    rep = {"part": name, "part_volume_mm3": round(P.volume, 1), "parting_z_mm": zp,
           "cavity_withdraws": "-Z" if cdir < 0 else "+Z", "shrink_scale": K}
    if check:
        pc, _ = RC.part_check(P)
        bottom, top = (cavity, core) if cdir < 0 else (core, cavity)   # insert_check wants bottom-half steel first
        ic = RC.insert_check(P, top, bottom)
        rep["ray_columns"] = pc["columns"]
        rep["undercut_columns"] = pc["undercut_columns"]
        rep["open_rays"] = pc["open_rays"]
        rep["insert_wrong_order_columns"] = ic["wrong_order"]
        rep["core_split_columns"] = ic["core_split_columns"]
        rep["cavity_split_columns"] = ic["cavity_split_columns"]
        B = core + cavity + P
        rep["closure_error_mm3"] = round(abs(B.volume - core.volume - cavity.volume - P.volume), 3)
    core_s, cav_s = scale(core, by=K), scale(cavity, by=K)
    core_s.label, cav_s.label = f"{name}_CORE_insert", f"{name}_CAVITY_insert"
    core_s.color, cav_s.color = Color(0.55, 0.6, 0.68), Color(0.72, 0.62, 0.45)
    return core_s, cav_s, rep
