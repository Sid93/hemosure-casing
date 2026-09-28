"""HemoSure casing -- tolerance stack-ups (worst case + RSS) and the fit/critical-dimension table.

Each stack is a list of contributors (name, signed nominal, +/- tolerance). The result is the
gap/clearance; 'req' is the acceptance band. Values are pulled from hemosure_casing where they
are geometry, and from the component datasheet spec where they are bought-in.
"""
from math import sqrt
import hemosure_casing as H

PCB_T_TOL = 0.10        # specify 1.6 +/-0.10 to the PCB fab (IPC default is +/-10 % = 0.16)
TACT_H_TOL = 0.10
MOULD_TOL_S = 0.05      # tool-bound small dims (< 6 mm) on critical features, T1-tuned (steel-safe)


def stack(title, contributors, req_min=None, req_max=None, why=""):
    nom = sum(c[1] for c in contributors)
    wc = sum(abs(c[2]) for c in contributors)
    rss = sqrt(sum(c[2] ** 2 for c in contributors))
    lo_wc, hi_wc, lo_rss, hi_rss = nom - wc, nom + wc, nom - rss, nom + rss
    ok_wc = (req_min is None or lo_wc >= req_min - 1e-9) and (req_max is None or hi_wc <= req_max + 1e-9)
    ok_rss = (req_min is None or lo_rss >= req_min - 1e-9) and (req_max is None or hi_rss <= req_max + 1e-9)
    return dict(title=title, contributors=contributors, nominal=nom, wc=(lo_wc, hi_wc), rss=(lo_rss, hi_rss),
                req=(req_min, req_max), ok_wc=ok_wc, ok_rss=ok_rss, why=why)


def stacks():
    zp = H.ZP
    seat = zp - H.Z_PCB_BOT                       # 3.2 : PCB seat below P/L
    fboss_top = zp - (H.Z_PCB_TOP + H.PCB_HOLD_GAP)  # 1.3 : front top boss end below P/L
    face = H.Z_FRONT_IN - zp                      # 5.8 : front inner face above P/L
    z_tact = H.Z_PCB_TOP + H.TACT_H
    stem_to_flange = (H.Z_FRONT_IN - H.BTN_PLAY) - z_tact
    S = []
    S.append(stack("Housing closure: front vs rear bottom screw bosses", [
        ("front boss end above P/L", +0.10, 0.05), ("rear boss top at P/L", 0.0, 0.05)],
        0.0, 0.25, "Gap must stay >= 0 so the perimeter lap closes first (no visible P/L gap)."))
    S.append(stack("PCB hold-down gap (front top boss to PCB top)", [
        ("rear standoff seat below P/L", +seat, 0.05), ("PCB thickness", -H.PCB_T, 0.16),
        ("front top boss end below P/L", -fboss_top, 0.05)],
        0.0, 0.6, "Boss must never crush the PCB; PCB taken at IPC +/-10 % here."))
    S.append(stack("Button: flange-to-face play with cap resting on the switch", [
        ("front inner face above P/L", +face, 0.05), ("rear standoff seat below P/L", +seat, 0.05),
        ("PCB thickness", -H.PCB_T, PCB_T_TOL), ("tact switch height", -H.TACT_H, TACT_H_TOL),
        ("cap: stem tip to flange top", -stem_to_flange, 0.05)],
        0.05, 0.9, "Play > 0 => the housing can never pre-press the switch."))
    S.append(stack("Button protrusion above the front face at rest", [
        ("cap: flange top to cap top", (H.T + 0.6) - (H.Z_FRONT_IN - H.BTN_PLAY), 0.05),
        ("flange-top position (= face - play)", -(H.T - H.Z_FRONT_IN) - H.BTN_PLAY, 0.35 + 0.05)],
        0.15, 1.1, "Stays proud of the overlay for a tactile press."))
    S.append(stack("Lens below overlay floor (flush)", [
        ("lens pocket depth", +H.LENS_POCKET_D, 0.05), ("lens thickness (PMMA)", -H.LENS_T, 0.05),
        ("lens tape (3M 9471LE 0.05)", -0.05, 0.01)],
        -0.02, 0.25, "Lens must not push the overlay up (max 0.02 proud accepted)."))
    S.append(stack("Overlay flush in its recess", [
        ("recess depth", +H.OVL_D, 0.03), ("overlay 0.175 PC + 0.05 adhesive", -0.225, 0.025)],
        -0.03, 0.10, "Overlay edge must not stand proud (lift / peel)."))
    S.append(stack("Battery door flush with the rear skin", [
        ("door recess depth", +H.DOOR_RECESS_D, 0.05), ("door plate thickness", -H.DOOR_T, 0.05)],
        -0.05, 0.20, "0.05 proud to 0.15 sunk accepted."))
    S.append(stack("Battery door gap per side", [
        ("recess width / 2", (H.DOOR_OPEN[0] + 2 * H.DOOR_LEDGE + 2 * H.DOOR_GAP) / 2, 0.05),
        ("door width / 2", -(H.DOOR_OPEN[0] + 2 * H.DOOR_LEDGE) / 2, 0.05)],
        0.05, 0.30, "Visible gap; door must drop in freely."))
    S.append(stack("Door latch engagement over the ledge", [
        ("bump reach from arm face", +0.8, 0.05), ("arm-to-edge clearance", -0.3, 0.05),
        ("door float in recess", 0.0, H.DOOR_GAP), ("opening edge position", 0.0, 0.05)],
        0.2, 0.8, "Engagement > 0.2; max deflection sets the latch strain (see note)."))
    S.append(stack("Lap joint radial clearance (tongue to front step)", [
        ("step face offset (front)", +(H.WALL - H.TONGUE_T - H.LAP_CLEAR_SIDE), 0.03),
        ("tongue outer offset (rear)", -(H.WALL - H.TONGUE_T), 0.03), ("front/rear profile mismatch", 0.0, 0.05)],
        None, None, "")
    )
    S[-1]["nominal"] = H.LAP_CLEAR_SIDE; S[-1]["wc"] = (H.LAP_CLEAR_SIDE - 0.11, H.LAP_CLEAR_SIDE + 0.11)
    S[-1]["rss"] = (H.LAP_CLEAR_SIDE - sqrt(0.03**2 * 2 + 0.05**2), H.LAP_CLEAR_SIDE + sqrt(0.03**2 * 2 + 0.05**2))
    S[-1]["req"] = (-0.02, 0.25); S[-1]["ok_wc"] = S[-1]["wc"][0] >= -0.02; S[-1]["ok_rss"] = S[-1]["rss"][0] >= 0
    S[-1]["why"] = "Tongue 0.90 0/-0.05 makes the real minimum 0.02 (+0.05 thinner tongue); zero-clearance local touch is acceptable."
    S.append(stack("Lap joint: tongue height vs step depth", [
        ("step depth (front)", +(H.TONGUE_H + H.LAP_CLEAR_TOP), 0.05), ("tongue height (rear)", -H.TONGUE_H, 0.05)],
        0.05, 0.35, "Tongue must never bottom out."))
    S.append(stack("USB-C: vertical clearance in the opening (worst side)", [
        ("half opening height", +H.USB_OPEN_H / 2, 0.05), ("half receptacle height", -H.USB_H / 2, 0.03),
        ("receptacle centre vs P/L (seat, PCB, part)", 0.0, 0.05 + PCB_T_TOL + 0.05)],
        0.0, None, "Plug must enter without touching the housing."))
    S.append(stack("USB-C: lateral clearance in the opening (worst side)", [
        ("half opening width", +H.USB_OPEN_W / 2, 0.05), ("half receptacle width", -8.94 / 2, 0.03),
        ("PCB lateral float (crush-rib clearance + outline)", 0.0, 0.05 + 0.10), ("receptacle placement on PCB", 0.0, 0.10)],
        0.0, None, ""))
    S.append(stack("PCB hole vs M2.5 housing screw (top holes)", [
        ("(hole - screw) / 2", (H.PCB_HOLE_D - 2.5) / 2, 0.05), ("PCB float", 0.0, 0.15),
        ("hole position on PCB", 0.0, 0.10), ("boss position", 0.0, 0.05)],
        0.0, None, "Screw must pass without loading the PCB sideways."))
    S.append(stack("Cuvette lateral clearance in the groove (per side)", [
        ("groove width / 2", H.CH_W / 2, 0.025), ("cuvette width / 2", -H.CUV_W / 2, 0.025)],
        0.05, 0.25, "Confirm the cuvette drawing: this assumes 14.00 +/-0.05."))
    return S


# Critical / functional dimensions: (part, feature, nominal, +tol, -tol, basis, steel-safe direction)
CRITICAL = [
    ("Front", "Outer profile at P/L", "62.00 x 122.00", "+0.10", "-0.10", "match rear (step <= 0.10)", "-"),
    ("Front", "Display window (at pocket floor)", f"{H.WIN_W:.2f} x {H.WIN_L:.2f}", "+0.10", "0", "active area 28.03 x 35.04 + 1/side", "cut small"),
    ("Front", "Lens pocket", f"{H.LENS_W:.2f} x {H.LENS_L:.2f}", "+0.10", "0", "lens 33.80 x 40.80 +/-0.05", "cut small"),
    ("Front", "Lens pocket depth", f"{H.LENS_POCKET_D:.2f}", "+0.05", "-0.05", "stack 5", "cut shallow"),
    ("Front", "Overlay recess", f"{H.W - 2*H.OVL_INSET:.2f} x {H.L - 2*H.OVL_INSET:.2f}", "+0.10", "0", "overlay 54.60 x 114.60 +/-0.10", "cut small"),
    ("Front", "Overlay recess depth", f"{H.OVL_D:.2f}", "+0.03", "-0.03", "stack 6", "cut shallow"),
    ("Front", "Button hole", f"dia {H.BTN_HOLE_D:.2f}", "+0.08", "0", "cap dia 10.00 0/-0.05", "cut small"),
    ("Front", "Screw pilot (PT K25)", f"dia {H.PILOT_D:.2f}", "+0.05", "0", "EJOT PT K25 in ABS: 0.8 d", "pin small"),
    ("Front", "Top boss end below P/L", f"{H.ZP - H.Z_PCB_TOP - H.PCB_HOLD_GAP:.2f}", "+0.05", "-0.05", "stack 2", "leave long"),
    ("Front", "Bottom boss end above P/L", "0.10", "+0.05", "-0.05", "stack 1", "leave long"),
    ("Front", "Lap step width x depth", f"{H.TONGUE_T + H.LAP_CLEAR_SIDE:.2f} x {H.TONGUE_H + H.LAP_CLEAR_TOP:.2f}", "+0.05", "0", "stacks 10-11", "cut narrow"),
    ("Front/Rear", "Boss pattern (both halves)", f"{2*H.HOLE_X:.2f} x {H.HOLE_Y_TOP - H.HOLE_Y_BOT:.2f}", "+0.05", "-0.05", "PCB hole pattern", "-"),
    ("Rear", "Outer profile at P/L", "62.00 x 122.00", "+0.10", "-0.10", "match front", "-"),
    ("Rear", "PCB seat below P/L", f"{H.ZP - H.Z_PCB_BOT:.2f}", "+0.05", "-0.05", "stacks 2, 3, 12", "leave long"),
    ("Rear", "Tongue thickness x height", f"{H.TONGUE_T:.2f} x {H.TONGUE_H:.2f}", "0 / +0.05", "-0.05 / -0.05", "stacks 10-11", "cut thick"),
    ("Rear", "USB-C opening (split on P/L)", f"{H.USB_OPEN_W:.2f} x {H.USB_OPEN_H:.2f}", "+0.10", "0", "receptacle 8.94 x 3.26", "cut small"),
    ("Rear", "Door recess", f"{H.DOOR_OPEN[0]+2*H.DOOR_LEDGE+2*H.DOOR_GAP:.2f} x {H.DOOR_OPEN[1]+2*H.DOOR_LEDGE+2*H.DOOR_GAP:.2f}", "+0.10", "0", "door 37.00 x 44.00 0/-0.10", "cut small"),
    ("Rear", "Door recess depth", f"{H.DOOR_RECESS_D:.2f}", "+0.05", "-0.05", "stack 7", "cut shallow"),
    ("Rear", "Screw clearance / c'bore", f"dia {H.CLEAR_D:.1f} / dia {H.CB_D:.1f}", "+0.10", "0", "PT K25 pan head dk 4.5", "-"),
    ("Rear", "PCB crush-rib tip to PCB edge", "0.05", "+0.05", "-0.05", "stack 13 (rib tips crush 0.1 max)", "cut tight"),
    ("Rear", "Optical-block boss top below P/L", f"{H.ZP - H.OB_Z0:.2f}", "+0.05", "-0.05", "groove aligns to throat", "leave long"),
    ("Door", "Plate outline x thickness", f"{H.DOOR_OPEN[0]+2*H.DOOR_LEDGE:.2f} x {H.DOOR_OPEN[1]+2*H.DOOR_LEDGE:.2f} x {H.DOOR_T:.2f}", "0", "-0.10 / -0.05", "stacks 7-8", "cut large"),
    ("Door", "Latch arm t x bump reach", "0.80 x 0.80", "+0.03 / +0.05", "-0.03 / -0.05", "stack 9, strain", "-"),
    ("Button", "Cap dia / flange dia", f"{H.BTN_D:.2f} / {H.BTN_FLANGE_D:.2f}", "0 / +0.05", "-0.05 / -0.05", "stack 4", "cut large"),
    ("Button", "Stem tip to flange top", f"{(H.Z_FRONT_IN - H.BTN_PLAY) - (H.Z_PCB_TOP + H.TACT_H):.2f}", "+0.05", "-0.05", "stack 3", "leave long"),
    ("Optical", "Cuvette groove width x depth", f"{H.CH_W:.2f} x {H.CH_H:.2f}", "+0.05", "0", "cuvette 14.0 x 3.0 (confirm)", "cut small"),
    ("Optical", "Floor under groove / aperture", f"{H.CH_PLATE:.2f} / dia 2.00", "+/-0.05", "+/-0.03", "optical path", "-"),
    ("Optical", "Ear hole pitch", f"{2*H.OB_EAR_X:.2f}", "+0.05", "-0.05", "rear bosses", "-"),
]

GENERAL_TOL = [  # ISO 20457-style general tolerances used for ABS on these drawings (non-critical dims)
    ("0 - 6", "+/-0.10", "+/-0.15"), ("> 6 - 30", "+/-0.15", "+/-0.20"),
    ("> 30 - 120", "+/-0.25", "+/-0.35"), ("> 120 - 315", "+/-0.40", "+/-0.55"),
]

if __name__ == "__main__":
    for i, s in enumerate(stacks(), 1):
        print(f"{i:2d} {s['title'][:58]:58s} nom {s['nominal']:+.3f}  WC {s['wc'][0]:+.3f}..{s['wc'][1]:+.3f} "
              f"RSS {s['rss'][0]:+.3f}..{s['rss'][1]:+.3f}  req {s['req']}  WC {'OK' if s['ok_wc'] else 'FAIL'} RSS {'OK' if s['ok_rss'] else 'FAIL'}")
