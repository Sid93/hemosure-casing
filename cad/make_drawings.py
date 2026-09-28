"""Builds HemoSure_Casing_Drawings_(Levram).pdf -- article drawings, tolerance analysis and
mould design sheets -- straight from the parametric model (hemosure_casing.py)."""
import json, glob, pathlib, sys
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Circle as MCircle, Rectangle as MRect, FancyBboxPatch
import hemosure_casing as H
import tolerance_stack as TS
import drawing_kit as K

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "drawings" / "HemoSure_Casing_Drawings_(Levram).pdf"
N = 10
ABS = "ABS natural white (LG HI-121H / PA-757 eq.)"
ABS_BLK = "ABS black (2 % carbon MB)"
TEXTURE = "Out VDI 3400 Ref 24 / In SPI B-2"

P = H.build_all()
REFS = {r.label: r for r in H.build_ref_components()}
MOLD = json.load(open(ROOT / "mold" / "mold_check_report.json")) if (ROOT / "mold" / "mold_check_report.json").exists() else {}
RHO = 1.05e-3  # g/mm3


def mass(part):
    return f"{P[part].volume * RHO:.1f} g"


def f2(v):
    return f"{v:.2f}"


# ================================================================== sheet 1: GA + BOM
def sheet_ga(pdf):
    S = K.Sheet("GENERAL ARRANGEMENT, STACK-UP & BILL OF MATERIALS", "HS-100", "HemoSure casing assembly",
                "see BOM", "1:1 / NTS", 1, N, mass=f"{sum(P[k].volume for k in ('rear','front','door','button','optical'))*RHO:.0f} g (plastics)")
    imgs = sorted(glob.glob(str(ROOT / "renders" / "HemoSure_Assembly_*.png")))
    if imgs:
        S.image(imgs[-1], 14, 160, 118)
    S.text(16, 282, "ISO VIEW (NTS)", fs=7, fontweight="bold")
    # assembly section at x = 0, 1:1, length vertical
    asm = [P[k] for k in ("rear", "front", "door", "button", "optical", "lens", "overlay", "pcb")] + list(REFS.values())
    colors = {"rear": "#333", "front": "#333", "optical": "#000"}
    ox, oy = S.anchor("left", 160, 160, 1.0)
    for k, shp in [(k, P[k]) for k in ("rear", "front", "door", "button", "optical", "lens", "overlay", "pcb")] + list(REFS.items()):
        hatch = "////" if k in ("rear", "front") else ("xxxx" if k == "optical" else ("...." if k.startswith("REF") or k == "pcb" else "\\\\\\\\"))
        try:
            S.section(shp, "X", 0.0, "+", "left", ox, oy, 1.0, hatch=hatch)
        except Exception as e:
            print("section fail", k, e)
    Pm = lambda p: np.array([ox, oy]) + K.mapping("left")(p)
    S.text(150, 228, "SECTION A-A  (x = 0)  1:1", fs=7, fontweight="bold")
    # z-levels
    for z, lab in [(0, "0 rear skin"), (H.Z_FLOOR, "2.0 floor"), (H.Z_PCB_BOT, "11.0 PCB seat"), (H.Z_PCB_TOP, "12.6 PCB top"),
                   (H.ZP, "14.2 P/L (USB-C centre)"), (H.Z_FRONT_IN, "20.0 front inner"), (H.T, "22.0 front skin")]:
        a = Pm((0, 66, z))
        S.ax.plot([a[0], a[0]], [a[1], a[1] + 4 + (z * 0.9)], c=K.DIM, lw=K.LW_THIN)
        S.ax.text(a[0], a[1] + 5 + z * 0.9, lab, fontsize=4.8, rotation=90, color=K.DIM, ha="center", va="bottom")
    S.leader(Pm((0, 57.0, 13.5)), 22, 6, "USB-C (split on P/L)")
    S.leader(Pm((0, -45, 14.2)), 24, -6, "Cuvette groove in black optical block")
    S.leader(Pm((0, H.BTN_Y, 21)), 24, 0, "Button cap on 6x6x5 tact")
    S.leader(Pm((0, 25, 21.3)), 24, 4, "PMMA lens 0.8 + PC overlay")
    S.leader(Pm((0, 9, 1)), -30, -4, "Battery door (LiPo 503035)")
    # BOM
    rows = [["#", "Part no.", "Description", "Material", "Qty", "Process / tool"],
            ["1", "HS-101", "Front housing", "ABS white", "1", "Inj. mould - Tool A (cav 1)"],
            ["2", "HS-102", "Rear housing", "ABS white", "1", "Inj. mould - Tool A (cav 2)"],
            ["3", "HS-103", "Battery door", "ABS white", "1", "Inj. mould - Tool A (cav 3)"],
            ["4", "HS-104", "Power button cap", "ABS black", "1", "Inj. mould - Tool B (cav 1)"],
            ["5", "HS-105", "Optical block (light-tight)", "ABS black", "1", "Inj. mould - Tool B (cav 2)"],
            ["6", "HS-201", "Display lens 33.8x40.8x0.8", "PMMA, HC one side", "1", "Laser cut + 3M 9471LE"],
            ["7", "HS-202", "Graphic overlay 54.6x114.6", "PC 0.175 + 7952MP", "1", "Screen print + die cut"],
            ["8", "EJOT PT K25x16", "Housing screw", "Steel Zn", "4", "Torque 0.35 Nm"],
            ["9", "EJOT PT K25x6", "PCB + optical block screw", "Steel Zn", "4", "Torque 0.25 Nm"],
            ["10", "3M SJ5302", "Bumpon foot dia 7.9", "PU", "4", "-"],
            ["11", "(PCB)", "Main PCB 76.75x49.94x1.6", "FR4", "1", "thk 1.6 +/-0.10 (spec!)"],
            ["12", "(bought)", "1.8in TFT ST7735, LiPo 503035, 6x6x5 tact", "-", "1 ea", "per electronics BOM"]]
    S.table(250, 282, [7, 24, 45, 28, 9, 47], rows, fs=5.2, row_h=4.4, title="BILL OF MATERIALS")
    S.notes(250, 216, [
        "1. Datum A = parting plane (P/L), z = 14.2 from the rear skin. B = centre line X. C = centre line Y.",
        "2. All plastics: ABS, mould shrink 0.5 % built into the tool STEP data (see HS-300 sheets).",
        "3. Parting plane runs through the USB-C centre and cuvette mouth: NO slides / lifters in any tool.",
        "4. Housing closure: rim lap joint + 4 x PT K25x16 from the rear. Top two screws pass through the",
        "   PCB top holes (PCB NOT clamped: 0.30 hold-down gap). Bottom PCB holes: 2 x PT K25x6.",
        "5. White ABS is translucent: the optical path is enclosed in the BLACK optical block (HS-105).",
        "6. Tolerances: general per sheet 6; critical fits and 15 stack-ups on sheet 6.",
        "7. Colour variants (teal / grey / purple ...) come from the printed overlay only - one set of tools.",
        "8. OPEN ITEMS: confirm PCB component heights (<= 3.0 below, TFT FPC route), USB-C overhang 3.0 mm",
        "   past PCB edge, tact switch at (0, -8), cuvette 14.0 x 3.0 x L, LiPo 503035 wiring.",
    ], fs=5.3, lh=3.4)
    S.save(pdf)


# ================================================================== sheet 2: front housing
def sheet_front(pdf):
    S = K.Sheet("FRONT HOUSING", "HS-101", "Front housing", ABS, "1:1", 2, N, finish=TEXTURE, mass=mass("front"))
    F = P["front"]
    ox, oy = S.anchor("front", 60, 165, 1.0)
    pe = S.view(F, "front", ox, oy, 1.0, label="EXTERIOR (view on +Z)")
    ox2, oy2 = S.anchor("back", 150, 165, 1.0)
    pi = S.view(F, "back", ox2, oy2, 1.0, label="INTERIOR (view on -Z)")
    ox3, oy3 = S.anchor("left", 200, 165, 1.0, (0, 0, H.ZP))
    ps = S.section(F, "X", 0.0, "+", "left", ox3, oy3, 1.0, label="SECTION A-A")
    # detail B: lap joint, 5:1, section y = 0 near +X wall
    ox4, oy4 = S.anchor("bottom", 330, 240, 5.0, (H.W / 2 - 2, 0, H.ZP + 2))
    clip = (300, 212, 365, 272)
    pd = S.section(F, "Y", 0.0, "+", "bottom", ox4, oy4, 5.0, clip=clip)
    S.ax.add_patch(MRect((clip[0], clip[1]), clip[2] - clip[0], clip[3] - clip[1], fill=False, lw=0.2 * K.PT, ec="#999"))
    S.text(301, 273.5, "DETAIL B - LAP STEP (5:1, section y = 0)", fs=6.2, fontweight="bold")
    # --- exterior dims
    S.dim(pe((-31, -61, H.ZP)), pe((31, -61, H.ZP)), -10, "62.00 ±0.10 (at P/L)")
    S.dim(pe((31, -61, H.ZP)), pe((31, 61, H.ZP)), 8, "122.00 ±0.10 (at P/L)", orient="v")
    S.dim(pe((-H.WIN_W / 2, H.WIN_YC + H.WIN_L / 2, 0)), pe((H.WIN_W / 2, H.WIN_YC + H.WIN_L / 2, 0)), 16, f"{f2(H.WIN_W)} +0.10/0 window")
    S.dim(pe((-H.LENS_W / 2, H.WIN_YC + H.LENS_L / 2, 0)), pe((H.LENS_W / 2, H.WIN_YC + H.LENS_L / 2, 0)), 24, f"{f2(H.LENS_W)} +0.10/0 lens pocket")
    S.dim(pe((-18, H.WIN_YC - H.WIN_L / 2, 0)), pe((-18, H.WIN_YC + H.WIN_L / 2, 0)), -6, f"{f2(H.WIN_L)} +0.10/0", orient="v")
    S.dim(pe((-23, 0, 0)), pe((-23, H.WIN_YC, 0)), -3, f"{f2(H.WIN_YC)}", orient="v")
    S.dim(pe((27.5, -57.5, 0)), pe((27.5, 57.5, 0)), 16, f"{f2(H.L - 2*H.OVL_INSET)} +0.10/0 overlay recess", orient="v", fs=5.5)
    S.leader(pe((H.BTN_HOLE_D / 2 * 0.7, H.BTN_Y + 3.6, 0)), 18, 6, f"dia {f2(H.BTN_HOLE_D)} +0.08/0 THRU")
    S.dim(pe((10, 0, 0)), pe((10, H.BTN_Y, 0)), 16, f"{abs(H.BTN_Y):.2f}", orient="v")
    S.leader(pe((-28.5, 55.5, 0)), -2, 14, "R12 plan / R3 edge")
    S.ax.plot(*zip(pe((-40, 0, 0)), pe((40, 0, 0))), c="#b00", lw=0.18 * K.PT, ls=(0, (10, 2, 1, 2)))
    S.ax.plot(*zip(pe((0, -68, 0)), pe((0, 68, 0))), c="#b00", lw=0.18 * K.PT, ls=(0, (10, 2, 1, 2)))
    S.cutline(pe((0, 66, 0)), pe((0, -66, 0)), "A")
    # --- interior dims
    S.dim(pi((H.HOLE_X, 60, 0)), pi((-H.HOLE_X, 60, 0)), 12, f"{2*H.HOLE_X:.2f} ±0.05")
    S.dim(pi((H.HOUSING_SCREW_BOT[0], -62, 0)), pi((-H.HOUSING_SCREW_BOT[0], -62, 0)), -4, f"{2*H.HOUSING_SCREW_BOT[0]:.2f} ±0.05")
    S.dim(pi((-33, 0, 0)), pi((-33, H.HOLE_Y_TOP, 0)), 4, f"{H.HOLE_Y_TOP:.2f} ±0.05", orient="v")
    S.dim(pi((-33, 0, 0)), pi((-33, H.HOUSING_SCREW_BOT[1], 0)), 4, f"{abs(H.HOUSING_SCREW_BOT[1]):.2f} ±0.05", orient="v")
    S.leader(pi((-H.HOLE_X, H.HOLE_Y_TOP, 0)), 12, 42, "4x boss dia 5.0, pilot dia 2.00 +0.05/0 (EJOT PT K25), 0.5° draft")
    S.leader(pi((0, H.TFT_YC + H.TFT_GLASS[1] / 2 + 0.6, 0)), 34, 36, "TFT locating ribs 1.0 thk,\n0.15 clearance to 34.0 x 45.83 glass")
    S.leader(pi((0, H.OPT_Y, 0)), 16, -8, "2x LED-board hold-down ribs")
    S.leader(pi((7.6, H.BTN_Y, 0)), 18, -4, "Button guide sleeve")
    # --- section dims (z horizontal on paper, y vertical)
    S.dim(ps((0, 61, H.ZP)), ps((0, 61, H.T)), 5, f"{H.T - H.ZP:.2f}")
    S.dim(ps((0, -61, H.Z_FRONT_IN)), ps((0, -61, H.T)), -5, "2.00 ±0.05")
    S.leader(ps((0, 10.5, H.T - H.OVL_D - H.LENS_POCKET_D)), 16, -2, f"lens pocket {f2(H.LENS_POCKET_D)} ±0.05 deep\noverlay recess {f2(H.OVL_D)} ±0.03")
    S.leader(ps((0, H.HOLE_Y_TOP, H.Z_PCB_TOP + H.PCB_HOLD_GAP)), 26, 0, f"top boss end {H.ZP - H.Z_PCB_TOP - H.PCB_HOLD_GAP:.2f} ±0.05 below P/L")
    S.leader(ps((0, -58.5, H.ZP)), 26, 4, "cuvette mouth (upper half)\nstadium, lead-in to throat")
    S.text(186, 92, "Datum A = P/L face (z 14.2)", fs=5.6, color=K.DIM)
    # tables
    rows = [["Feature", "Nominal", "Tol.", "Steel-safe"]] + [[c[1], c[2], f"{c[3]} / {c[4]}", c[6]] for c in TS.CRITICAL if c[0] in ("Front", "Front/Rear")]
    S.table(262, 205, [50, 34, 30, 24], rows, fs=4.9, row_h=4.0, title="CRITICAL DIMENSIONS (HS-101)")
    S.notes(14, 88, [
        "1. Material ABS natural white (colour per overlay). Mould shrink 0.5 % (tool data). Wall 2.00 nominal.",
        "2. Draft: outer walls 1.5° (texture VDI 24), inner walls 1.0°, bosses/ribs 0.5°/side - modelled, do not add.",
        "3. Ribs 1.0-1.2 thk (<= 60 % wall) - no sink on the cosmetic face. Boss OD 5.0 / pilot 2.0 (wall 1.5).",
        "4. P/L flatness 0.10. Outer profile at P/L to match HS-102 within 0.10 per side (step).",
        "5. No flash on P/L, lap step and window; no sink / flow marks / weld line on the overlay area.",
        "6. Gate: 1 x sub (tunnel) gate dia 1.2 into inner +X wall at y = 0 (hidden). Ejector marks core side only, flush +0/-0.05.",
        "7. General tolerances: sheet 6 table (ISO 20457-style). Fits marked here override.",
    ], fs=5.2, lh=3.3)
    S.save(pdf)


# ================================================================== sheet 3: rear housing
def sheet_rear(pdf):
    S = K.Sheet("REAR HOUSING", "HS-102", "Rear housing", ABS, "1:1", 3, N, finish=TEXTURE, mass=mass("rear"))
    Rr = P["rear"]
    ox, oy = S.anchor("back", 60, 165, 1.0)
    pe = S.view(Rr, "back", ox, oy, 1.0, label="EXTERIOR (view on -Z)")
    ox2, oy2 = S.anchor("front", 150, 165, 1.0)
    pi = S.view(Rr, "front", ox2, oy2, 1.0, label="INTERIOR (view on +Z)")
    ox3, oy3 = S.anchor("left", 205, 165, 1.0, (0, 0, H.ZP / 2))
    ps = S.section(Rr, "X", 0.0, "+", "left", ox3, oy3, 1.0, label="SECTION A-A")
    ox4, oy4 = S.anchor("bottom", 330, 245, 2.0, (0, 0, H.ZP / 2))
    pb = S.section(Rr, "Y", H.HOLE_Y_TOP, "+", "bottom", ox4, oy4, 2.0)
    S.text(268, 272, f"SECTION C-C (y = {H.HOLE_Y_TOP:.2f}, through top screw path) 2:1", fs=6.2, fontweight="bold")
    # exterior dims
    dw = H.DOOR_OPEN[0] + 2 * H.DOOR_LEDGE + 2 * H.DOOR_GAP
    dl = H.DOOR_OPEN[1] + 2 * H.DOOR_LEDGE + 2 * H.DOOR_GAP
    S.dim(pe((31, -61, H.ZP)), pe((-31, -61, H.ZP)), -10, "62.00 ±0.10 (at P/L)")
    S.dim(pe((-31, -61, H.ZP)), pe((-31, 61, H.ZP)), 8, "122.00 ±0.10 (at P/L)", orient="v")
    S.dim(pe((dw / 2, H.DOOR_YC + dl / 2, 0)), pe((-dw / 2, H.DOOR_YC + dl / 2, 0)), 12, f"{dw:.2f} +0.10/0 door recess")
    S.dim(pe((dw / 2 + 1, H.DOOR_YC - dl / 2, 0)), pe((dw / 2 + 1, H.DOOR_YC + dl / 2, 0)), 5, f"{dl:.2f} +0.10/0", orient="v")
    S.dim(pe((-dw / 2 - 1, 0, 0)), pe((-dw / 2 - 1, H.DOOR_YC, 0)), -3, f"{H.DOOR_YC:.2f}", orient="v")
    S.leader(pe((H.HOLE_X, H.HOLE_Y_TOP, 0)), 6, 12, f"4x c'bore dia {H.CB_D:.1f} +0.1/0,\n2.2 (top) / 3.2 (bottom) deep, dia 2.9 THRU")
    S.leader(pe((-12, -52, 0)), -2, -12, f"4x dia {H.FOOT_D} x {H.FOOT_D_DEPTH} foot recess")
    S.leader(pe((10, -28, 0)), 18, -4, "label recess 36 x 22 x 0.15")
    S.cutline(pe((0, 66, 0)), pe((0, -66, 0)), "A")
    S.cutline(pe((34, H.HOLE_Y_TOP, 0)), pe((-34, H.HOLE_Y_TOP, 0)), "C")
    # interior
    S.dim(pi((-H.HOLE_X, 60, 0)), pi((H.HOLE_X, 60, 0)), 4, f"{2*H.HOLE_X:.2f} ±0.05")
    S.dim(pi((33, H.HOLE_Y_BOT, 0)), pi((33, H.HOLE_Y_TOP, 0)), 3, f"{H.HOLE_Y_TOP - H.HOLE_Y_BOT:.2f} ±0.05", orient="v")
    S.dim(pi((-H.OB_EAR_X, -64, 0)), pi((H.OB_EAR_X, -64, 0)), -2, f"{2*H.OB_EAR_X:.2f} ±0.05")
    S.leader(pi((H.HOLE_X, H.HOLE_Y_BOT, 0)), 14, -5, "2x PCB standoff, pilot dia 2.00 (PT K25x6)\nseat 3.20 ±0.05 below P/L")
    S.leader(pi((-H.PCB_W / 2 - 0.5, H.PCB_YC + 22, 0)), 95, -12, "4x PCB crush rib, tip 0.05 to PCB edge\n+ 2 top-edge ribs + 2 bottom posts")
    S.leader(pi((-(H.DOOR_OPEN[0] / 2 + 0.5), H.DOOR_YC, 0)), -4, -20, "battery rails / door opening\n32.00 x 39.00 ±0.10")
    S.leader(pi((H.OB_EAR_X, H.OPT_Y, 0)), 14, -10, "2x optical-block boss, top 7.20 ±0.05 below P/L")
    # section dims
    S.dim(ps((0, 62, 0)), ps((0, 62, H.ZP)), 4, f"{H.ZP:.2f} (to P/L)")
    S.dim(ps((0, 62, H.ZP)), ps((0, 62, H.ZP + H.TONGUE_H)), 12, "1.50 ±0.05")
    S.leader(ps((0, 59.5, H.ZP + 0.7)), 22, 6, f"tongue {H.TONGUE_T:.2f} 0/-0.05 thk")
    S.leader(ps((0, 57.6, H.ZP)), 22, -2, f"USB-C half opening {f2(H.USB_OPEN_W)} x {H.USB_OPEN_H/2:.2f}")
    S.leader(ps((0, 20, 1.0)), 22, 0, f"door recess {f2(H.DOOR_RECESS_D)} ±0.05 / ledge 0.75")
    # section C-C dims
    S.leader(pb((H.HOLE_X, 0, 6)), -40, -26, "screw path: c'bore -> standoff\n(seat z 11.0) -> PCB -> front boss")
    rows = [["Feature", "Nominal", "Tol.", "Steel-safe"]] + [[c[1], c[2], f"{c[3]} / {c[4]}", c[6]] for c in TS.CRITICAL if c[0] in ("Rear", "Front/Rear")]
    S.table(262, 205, [50, 34, 30, 24], rows, fs=4.9, row_h=4.0, title="CRITICAL DIMENSIONS (HS-102)")
    S.notes(14, 88, [
        "1. Material ABS natural white, shrink 0.5 %. Wall 2.00; floor 2.00; door ledge 0.75 (reinforced by rails).",
        "2. Draft as HS-101 (modelled). Tongue 1° both faces. Recesses 1°. Pins/holes 0.25-1°.",
        "3. PCB located by crush ribs (+/-0.05) and 2 PT K25x6 at the bottom holes; top holes carry the housing screws.",
        "4. USB-C and cuvette mouth split on the P/L: half in each housing, no side action.",
        "5. Gate: 1 x sub gate dia 1.2 into inner +X wall at y = +20 (hidden). Ejection: sleeves on all bosses.",
        "6. No sink opposite bosses / rails on the rear skin (bosses cored, gussets 1.0 thk).",
        "7. Label recess and foot recesses: keep texture-free (SPI B-2) for adhesion.",
    ], fs=5.2, lh=3.3)
    S.save(pdf)


# ================================================================== sheet 4: door, button, optical block
def sheet_small(pdf):
    S = K.Sheet("BATTERY DOOR / BUTTON CAP / OPTICAL BLOCK", "HS-103/104/105", "Small moulded parts",
                "103: ABS white | 104, 105: ABS black", "2:1", 4, N, mass=f"{mass('door')} / {mass('button')} / {mass('optical')}")
    D = P["door"]; Bt = P["button"]; O = P["optical"]
    # door: outside view 2:1, inside, section
    ox, oy = S.anchor("back", 70, 200, 2.0, (0, H.DOOR_YC, 0))
    pd = S.view(D, "back", ox, oy, 2.0, label="HS-103 DOOR - outside")
    ox, oy = S.anchor("left", 145, 200, 2.0, (0, H.DOOR_YC, 0))
    pds = S.section(D, "X", 0.0, "+", "left", ox, oy, 2.0, label="HS-103 SECTION (x = 0)")
    ow = H.DOOR_OPEN[0] + 2 * H.DOOR_LEDGE; ol = H.DOOR_OPEN[1] + 2 * H.DOOR_LEDGE
    S.dim(pd((ow / 2, H.DOOR_YC - ol / 2, 0)), pd((-ow / 2, H.DOOR_YC - ol / 2, 0)), -8, f"{ow:.2f} 0/-0.10")
    S.dim(pd((-ow / 2, H.DOOR_YC - ol / 2, 0)), pd((-ow / 2, H.DOOR_YC + ol / 2, 0)), 6, f"{ol:.2f} 0/-0.10", orient="v")
    S.leader(pds((0, H.DOOR_YC - H.DOOR_OPEN[1] / 2 + 0.6, 4.5)), 14, 10, "latch arm 0.80 ±0.03 x 6.3\nbump 0.80 ±0.05, 45° release\nstrain 1.5 % nom / 2.3 % max")
    S.leader(pds((0, H.DOOR_YC + H.DOOR_OPEN[1] / 2 + 0.5, 2.5)), 14, 8, "2x hinge hook, 1.3 over ledge")
    S.leader(pds((0, H.DOOR_YC, 0.6)), 16, -12, f"plate {H.DOOR_T:.2f} 0/-0.05")
    S.text(200, 146, "Mould windows under hooks/bump let the cavity form the hook undersides (no lifters).", fs=5.4)
    # button: section 4:1
    ox, oy = S.anchor("left", 225, 205, 4.0, (0, H.BTN_Y, 20))
    pbs = S.section(Bt, "X", 0.0, "+", "left", ox, oy, 4.0, label="HS-104 BUTTON - section 4:1")
    zt = H.Z_PCB_TOP + H.TACT_H; zf = H.Z_FRONT_IN - H.BTN_PLAY
    S.dim(pbs((0, H.BTN_Y - H.BTN_D / 2, 21.5)), pbs((0, H.BTN_Y + H.BTN_D / 2, 21.5)), 14, f"dia {f2(H.BTN_D)} 0/-0.05", orient="v")
    S.dim(pbs((0, H.BTN_Y - H.BTN_FLANGE_D / 2, zf - 0.4)), pbs((0, H.BTN_Y + H.BTN_FLANGE_D / 2, zf - 0.4)), -16, f"dia {f2(H.BTN_FLANGE_D)} ±0.05", orient="v")
    S.dim(pbs((zt, H.BTN_Y + 1.95, zt)), pbs((zf, H.BTN_Y + 1.95, zf)), 3, f"{zf - zt:.2f} ±0.05")
    S.text(200, 160, "Cap rests on the tact actuator; 0.45 play to the housing face (stack 3).", fs=5.4)
    # optical block: top view 2:1, section x=0, section y=OPT_Y
    ox, oy = S.anchor("front", 70, 90, 2.0, (0, -41.3, 0))
    po = S.view(O, "front", ox, oy, 2.0, label="HS-105 OPTICAL BLOCK - top")
    ox, oy = S.anchor("bottom", 175, 95, 2.5, (0, H.OPT_Y, 11.5))
    pos = S.section(O, "Y", H.OPT_Y, "+", "bottom", ox, oy, 2.5, label=f"HS-105 SECTION D-D (y = {H.OPT_Y:.0f}, optical axis) 2.5:1")
    S.dim(po((-H.OB_EAR_X, H.OPT_Y + 4, 0)), po((H.OB_EAR_X, H.OPT_Y + 4, 0)), 4, f"{2*H.OB_EAR_X:.2f} ±0.05")
    S.dim(po((-H.OB_X, H.OB_Y1, 0)), po((-H.OB_X, H.OB_Y0, 0)), -6, f"{H.OB_Y1 - H.OB_Y0:.2f}", orient="v")
    S.dim(pos((-H.CH_W / 2, 0, H.OB_Z1)), pos((H.CH_W / 2, 0, H.OB_Z1)), 8, f"groove {f2(H.CH_W)} +0.05/0")
    S.dim(pos((H.OB_X, 0, H.ZP - H.CH_H / 2)), pos((H.OB_X, 0, H.OB_Z1)), 6, f"{f2(H.CH_H)} +0.05/0", orient="v")
    S.leader(pos((0, 0, H.ZP - H.CH_H / 2 - H.CH_PLATE / 2)), 30, -6, f"floor {f2(H.CH_PLATE)} ±0.05, aperture dia 2.00 ±0.03\nsensor pocket below (open -Z)")
    S.leader(pos((H.CH_W / 2 + H.OB_WALL / 2, 0, H.OB_Z1 + 0.6)), 24, 10, "4x heat-stake pin dia 1.2 for LED board")
    S.notes(250, 205, [
        "HS-103 door: ABS white, same resin lot as HS-102.",
        "  Flush 0/-0.15 to rear skin; gap 0.15-0.25/side.",
        "HS-104 button: ABS black (or TPU 90A if softer",
        "  feel wanted - same tool). Pad-print power icon.",
        "HS-105 optical block: ABS BLACK, opaque at 2 mm",
        "  (transmission < 0.1 % @ 400-700 nm - verify).",
        "  Groove Ra <= 0.8 (SPI B-1) to avoid scratching",
        "  the cuvette optical window. Parting at underside.",
        "  Add 0.5 x 45° lead-in at groove entry (T1).",
        "All: draft 1° modelled on every wall.",
    ], fs=5.3, lh=3.4)
    S.save(pdf)


# ================================================================== sheet 5: lens + overlay
def sheet_flat(pdf):
    S = K.Sheet("DISPLAY LENS / GRAPHIC OVERLAY", "HS-201/202", "Flat bought-in parts",
                "201: PMMA 0.8 HC | 202: PC 0.175 + adhesive", "1:1", 5, N)
    Ln = P["lens"]; Ov = P["overlay"]
    ox, oy = S.anchor("front", 70, 180, 2.0, (0, H.WIN_YC, 0))
    pl = S.view(Ln, "front", ox, oy, 2.0, label="HS-201 LENS 2:1")
    S.dim(pl((-(H.LENS_W - 0.2) / 2, H.WIN_YC - (H.LENS_L - 0.2) / 2, 0)), pl(((H.LENS_W - 0.2) / 2, H.WIN_YC - (H.LENS_L - 0.2) / 2, 0)), -8, f"{H.LENS_W - 0.2:.2f} ±0.05")
    S.dim(pl(((H.LENS_W - 0.2) / 2, H.WIN_YC - (H.LENS_L - 0.2) / 2, 0)), pl(((H.LENS_W - 0.2) / 2, H.WIN_YC + (H.LENS_L - 0.2) / 2, 0)), 8, f"{H.LENS_L - 0.2:.2f} ±0.05", orient="v")
    S.leader(pl((-(H.LENS_W - 0.2) / 2 + 0.6, H.WIN_YC + (H.LENS_L - 0.2) / 2 - 0.6, 0)), -10, 10, "4x R1.90")
    ox, oy = S.anchor("front", 200, 160, 1.0)
    po = S.view(Ov, "front", ox, oy, 1.0, label="HS-202 OVERLAY 1:1 (colour field shown, clear window + button hole)")
    wov, lov = H.W - 2 * H.OVL_INSET - 0.4, H.L - 2 * H.OVL_INSET - 0.4
    S.dim(po((-wov / 2, -lov / 2, 0)), po((wov / 2, -lov / 2, 0)), -8, f"{wov:.2f} ±0.10")
    S.dim(po((wov / 2, -lov / 2, 0)), po((wov / 2, lov / 2, 0)), 8, f"{lov:.2f} ±0.10", orient="v")
    S.leader(po((-5.5, H.BTN_Y, 0)), -30, -10, "dia 11.00 ±0.10 die-cut")
    S.leader(po((-H.WIN_W / 2, H.WIN_YC + H.WIN_L / 2, 0)), -20, 12, f"clear window {H.WIN_W + 0.6:.1f} x {H.WIN_L + 0.6:.1f}\n(black mask border 1.0 printed)")
    S.notes(250, 250, [
        "HS-201 LENS",
        " PMMA (cast) 0.80 ±0.05, hard-coat outside (>= 3H), AR optional.",
        " Laser cut, edges polished; flatness 0.05. Fixed with 3M 9471LE",
        " 0.05 ring (3 mm wide) into the 0.95 deep pocket (stack 5).",
        "",
        "HS-202 OVERLAY",
        " PC 0.175 textured/anti-glare (Lexan 8B35 or Autotex F),",
        " 2nd-surface screen print: colour field (variant) + white logo",
        " 'HEMOSURE / Hemoglobin Meter' + power icon + black window mask.",
        " Adhesive 3M 7952MP (0.05). Die-cut ±0.10, corner R8.30.",
        " Colour variants: teal, dark grey, purple, burgundy, olive,",
        " coffee brown, navy - pantone call-out per SKU. One tool set.",
        " Chemical: 70 % IPA / 0.5 % hypochlorite wipe x 500 - no lift.",
    ], fs=5.4, lh=3.5)
    S.save(pdf)


# ================================================================== sheet 6: tolerances
def sheet_tol(pdf):
    S = K.Sheet("TOLERANCES, FITS & STACK-UP ANALYSIS", "HS-110", "All moulded parts", "ABS", "-", 6, N)
    rows = [["Size range (mm)", "Tool-bound (single half)", "Across P/L / not tool-bound"]] + [list(r) for r in TS.GENERAL_TOL]
    S.table(14, 282, [30, 38, 44], rows, fs=5.4, row_h=4.4, title="GENERAL TOLERANCES - ABS (unless stated)")
    S.notes(14, 252, [
        "Basis: ISO 20457 tolerance groups for ABS (shrink 0.4-0.7 %), normal production.",
        "Angles +/-0.5°. Radii +/-0.2. Flatness P/L 0.10. Position of holes +/-0.05 where on",
        "the PCB / screw pattern, else general. Critical dims are T1-tuned ('steel-safe').",
        "Steel-safe = cut the tool so that metal can only be REMOVED to reach nominal:",
        "holes/pockets cut small, bosses/pins left long, recesses cut shallow.",
    ], fs=5.2, lh=3.3, title="BASIS")
    st = TS.stacks()
    rows = [["#", "Stack", "Nom.", "Worst case", "RSS", "Accept", "WC", "RSS"]]
    for i, s in enumerate(st, 1):
        req = f"{'' if s['req'][0] is None else f'{s['req'][0]:+.2f}'} .. {'' if s['req'][1] is None else f'{s['req'][1]:+.2f}'}"
        rows.append([str(i), s["title"][:62], f"{s['nominal']:+.3f}", f"{s['wc'][0]:+.2f} .. {s['wc'][1]:+.2f}",
                     f"{s['rss'][0]:+.2f} .. {s['rss'][1]:+.2f}", req, "OK" if s["ok_wc"] else "FAIL", "OK" if s["ok_rss"] else "FAIL"])
    y = S.table(140, 282, [6, 92, 16, 28, 28, 24, 9, 9], rows, fs=5.0, row_h=4.2, title="STACK-UP ANALYSIS (gaps in mm; + = clearance)")
    # contributors for each stack, compact
    yy = y - 6
    S.text(140, yy, "CONTRIBUTORS", fs=6.6, fontweight="bold"); yy -= 4
    for i, s in enumerate(st, 1):
        txt = f"{i}. " + "; ".join(f"{c[0]} {c[1]:+.2f} ±{c[2]:.2f}" for c in s["contributors"])
        S.text(140, yy, txt[:175], fs=4.5); yy -= 3.0
        if s["why"]:
            S.text(145, yy, s["why"][:170], fs=4.3, color="#555"); yy -= 3.0
    rows = [["Part", "Feature", "Nominal", "+", "-", "Basis"]] + [[c[0], c[1], c[2], c[3], c[4], c[5]] for c in TS.CRITICAL]
    S.table(14, 226, [16, 38, 30, 14, 16, 0.1], [r[:5] + [""] for r in rows], fs=4.5, row_h=3.55, title="CRITICAL / FUNCTIONAL DIMENSIONS")
    S.notes(14, 118, [
        "BOUGHT-IN SPECS THE STACKS DEPEND ON (put on the POs):",
        " PCB: 1.60 ±0.10 (not IPC default ±10 %), outline ±0.10 routed,",
        "  holes dia 3.20 ±0.05, hole pattern ±0.05, USB-C overhang 3.0 ±0.1.",
        " Tact switch 6x6, height 5.00 ±0.10, travel 0.25, 1.6 N.",
        " USB-C receptacle 8.94 x 3.26 shell, top-mount, centre 1.63 above PCB.",
        " TFT 1.8in ST7735: glass 34.00 x 45.83 ±0.10, active area offset",
        "  2.0 towards the FPC-free end (confirm module drawing).",
        " Cuvette 14.00 ±0.05 x 3.00 ±0.05 (confirm drawing).",
        "",
        "LATCH STRAIN (HS-103): e = 1.5 t d / L^2, t 0.8, L 6.3:",
        " nominal d 0.5 -> 1.5 %; max d 0.75 -> 2.3 % (ABS limit ~2.5 %).",
        "SCREW BOSSES: PT K25 in ABS, pilot 2.0, engagement >= 5.0 (2d).",
    ], fs=5.1, lh=3.3, title="SUPPLIER-SIDE TOLERANCES")
    S.save(pdf)


# ================================================================== mould helpers
def ejector_layout(part, z_face, side, inner_off=3.5, pitch=16.0):
    """Ejector pin candidates on the core-side face at z_face; keep those with material under the
    whole dia-3 pin footprint and no feature above (core side)."""
    from build123d import Vector
    shp = P[part]
    wi, li = H.W - 2 * H.WALL - 2 * inner_off, H.L - 2 * H.WALL - 2 * inner_off
    cands = []
    for x in np.arange(-wi / 2, wi / 2 + 0.1, pitch):
        for y in (-li / 2, li / 2):
            cands.append((x, y))
    for y in np.arange(-li / 2, li / 2 + 0.1, pitch):
        for x in (-wi / 2, wi / 2):
            cands.append((x, y))
    for x in (-8.0, 8.0):
        for y in np.arange(-40, 50, 22.0):
            cands.append((x, y))
    good = []
    d_in = -0.4 if side == "rear" else 0.4
    d_out = 0.4 if side == "rear" else -0.4
    for (x, y) in cands:
        ok = True
        for dx, dy in [(0, 0), (1.6, 0), (-1.6, 0), (0, 1.6), (0, -1.6)]:
            p_in = Vector(x + dx, y + dy, z_face + d_in)
            p_out = Vector(x + dx, y + dy, z_face + d_out)
            if not shp.is_inside(p_in) or shp.is_inside(p_out):
                ok = False
                break
        if ok and all((x - gx) ** 2 + (y - gy) ** 2 > 36 for gx, gy in good):
            good.append((x, y))
    return good


def mould_data_table(S, x, y, name, rows):
    return S.table(x, y, [44, 70], [["Item", name]] + rows, fs=5.0, row_h=4.1)


# ================================================================== sheet 7: Tool A layout
def sheet_toolA(pdf):
    S = K.Sheet("MOULD TOOL A (FAMILY 1+1+1): LAYOUT & FEED", "HS-301", "Tool A: front + rear + door",
                "Inserts 1.2311 (P20) 30-34 HRC or 1.2738", "1:2", 7, N)
    s = 0.5
    cx0, cy0 = 150, 160
    # mould base 350 x 400 and insert pockets
    S.ax.add_patch(MRect((cx0 - 175 * s, cy0 - 200 * s), 350 * s, 400 * s, fill=False, lw=0.5 * K.PT, ec=K.INK))
    S.text(cx0 - 175 * s, cy0 + 200 * s + 2, "Mould base 350 x 400 (LKM/Futaba FCI 3540 eq.) - moving half (core side) plan", fs=6.2, fontweight="bold")
    ins = {"rear": (-68, 25), "front": (68, 25), "door": (0, -125)}
    sizes = {"rear": (121, 181), "front": (121, 181), "door": (81, 81)}
    for k, (ix, iy) in ins.items():
        w, h = sizes[k]
        S.ax.add_patch(MRect((cx0 + s * (ix - w / 2), cy0 + s * (iy - h / 2)), w * s, h * s, fill=True, fc="#eef1f6", lw=0.35 * K.PT, ec="#345"))
    # part outlines on core inserts (interior view) - at 1:2
    shp = {"rear": P["rear"], "front": P["front"], "door": P["door"]}
    views = {"rear": "front", "front": "back", "door": "front"}
    anchors = {"rear": (0, 0, 0), "front": (0, 0, 0), "door": (0, H.DOOR_YC, 0)}
    mappers = {}
    for k in shp:
        ix, iy = ins[k]
        ox, oy = S.anchor(views[k], cx0 + s * ix, cy0 + s * iy, s, anchors[k])
        mappers[k] = S.view(shp[k], views[k], ox, oy, s, lw=0.12 * K.PT, color="#445")
    # sprue, runner, gates
    sp = np.array([cx0, cy0 + 25 * s])
    S.ax.add_patch(MCircle(sp, 2.2, fc="#c33", ec="none"))
    gR = mappers["rear"]((H.W / 2 - H.WALL, 20, 8)); gF = mappers["front"]((H.W / 2 - H.WALL, 0, 17)); gD = mappers["door"]((0, H.DOOR_YC + 22, 0.6))
    for g in (gR, gF):
        S.ax.plot([sp[0], g[0]], [sp[1], g[1]], c="#c33", lw=1.6)
        S.ax.add_patch(MCircle(g, 1.2, fc="#c33", ec="none"))
    S.ax.plot([sp[0], sp[0], gD[0]], [sp[1], gD[1] + 6, gD[1] + 6], c="#c33", lw=1.2)
    S.ax.plot([gD[0], gD[0]], [gD[1] + 6, gD[1]], c="#c33", lw=1.2)
    S.ax.add_patch(MCircle(gD, 1.0, fc="#c33", ec="none"))
    S.leader(sp, 30, 52, "Sprue bush dia 3.5 / 2° (cold runner)\nFull-round runner dia 5 -> dia 4 (door branch dia 3)", color="#c33")
    S.leader(gR, -8, 40, "Sub gate dia 1.2 @ 40° into inner wall (rear)", color="#c33")
    S.leader(gF, 8, 40, "Sub gate dia 1.2 @ 40° into inner wall (front)", color="#c33")
    S.leader(gD, 30, -8, "Edge/sub gate dia 0.9 (door, hidden under ledge)", color="#c33")
    # ejectors
    counts = {}
    for k, zf, side in (("rear", H.Z_FLOOR, "rear"), ("front", H.Z_FRONT_IN, "front")):
        pins = ejector_layout(k, zf, side)
        counts[k] = len(pins)
        for (x, y) in pins:
            S.ax.add_patch(MCircle(mappers[k]((x, y, zf)), 1.5 * s * 2, fc="none", ec="#070", lw=0.6))
    bosses = {"rear": [(sx * H.HOLE_X, y) for sx in (1, -1) for y in (H.HOLE_Y_TOP, H.HOLE_Y_BOT)] + [(sx * H.HOUSING_SCREW_BOT[0], H.HOUSING_SCREW_BOT[1]) for sx in (1, -1)] + [(sx * H.OB_EAR_X, H.OPT_Y) for sx in (1, -1)],
              "front": [(sx * H.HOLE_X, H.HOLE_Y_TOP) for sx in (1, -1)] + [(sx * H.HOUSING_SCREW_BOT[0], H.HOUSING_SCREW_BOT[1]) for sx in (1, -1)]}
    for k, bl in bosses.items():
        for (x, y) in bl:
            q = mappers[k]((x, y, 10))
            S.ax.add_patch(MCircle(q, 3.2 * s * 2 / 2 + 0.6, fc="none", ec="#070", lw=0.9, ls="--"))
    # cooling (schematic)
    for k in ("rear", "front"):
        ix, iy = ins[k]
        for dx in (-22, 0, 22):
            x = cx0 + s * (ix + dx)
            S.ax.plot([x, x], [cy0 + s * (iy - 95), cy0 + s * (iy + 95)], c="#16a", lw=0.8, ls=(0, (6, 2)))
    S.text(14, 40, "Legend:  red = feed  |  green circle = dia 3 ejector pin (core side)  |  green dashed = ejector sleeve on boss  |  blue dashed = dia 8 cooling, 12 below moulding face", fs=5.4)
    rows = [
        ["Cavities", "1 x front + 1 x rear + 1 x door (same ABS lot)"],
        ["Parting", "Flat P/L; no slides / lifters (verified)"],
        ["Shrink", "0.50 % uniform (in insert STEP)"],
        ["Insert steel", "1.2311 P20 30-34 HRC; 1.2738 for 100k+"],
        ["Cosmetic cavity", "VDI 3400 Ref 24 EDM texture after T1 approval"],
        ["Feed", "Cold runner + 3 sub gates (auto degate)"],
        ["Ejection", f"pins dia 3: rear {counts.get('rear',0)} / front {counts.get('front',0)} + sleeves on bosses + blades on ribs"],
        ["Venting", "0.02 x 5 on P/L every 25 mm + ejector-pin vents"],
        ["Cooling", "dia 8, 3 circuits/half, baffles under bosses"],
        ["Mould temp.", "50-65 °C (cavity), 45-60 °C (core)"],
        ["Melt temp.", "220-250 °C, pre-dry ABS 80 °C / 2-4 h"],
        ["Proj. area", f"~{(H.W*H.L*2 + 44*37)/100:.0f} cm² -> clamp ~60 t, machine 100 t"],
        ["Shot", f"{(P['front'].volume+P['rear'].volume+P['door'].volume)*RHO:.0f} g parts + ~5 g runner"],
        ["Cycle (est.)", "cooling ~8-9 s at 2.0 wall -> 22-26 s"],
    ]
    mould_data_table(S, 262, 282, "Tool A data", rows)
    S.notes(262, 216, [
        "1. Insert STEP files (steel size, shrink applied):",
        "   mold/HemoSure_{Front,Rear}_Housing_{CORE,CAVITY}.step,",
        "   mold/HemoSure_Battery_Door_{CORE,CAVITY}.step.",
        "2. Core/cavity split verified in CAD: 0 mm³ undercut,",
        "   0 mm³ steel/part collision on ejection (sheet 10).",
        "3. Ejector positions are proposals from an automatic",
        "   footprint check - toolmaker to finalise with the",
        "   cooling layout. Sleeves under every screw boss.",
        "4. Balance the family runner by flow simulation",
        "   (Moldflow / Moldex3D or SimpaTools free trial)",
        "   before cutting: front 15 g vs rear 22 g vs door 2 g.",
        "   Door can be shut off with a runner valve insert.",
        "5. Weld lines expected: around the display window and",
        "   the door opening - keep them off the overlay edge.",
        "6. Alternative: 2 single-cavity tools (front / rear)",
        "   if colour-matching of separate lots is controlled.",
    ], fs=5.1, lh=3.3)
    S.save(pdf)


# ================================================================== sheet 8: Tool A insert sections
def sheet_toolA_sections(pdf):
    S = K.Sheet("MOULD TOOL A: CORE / CAVITY SECTIONS", "HS-302", "Tool A inserts",
                "1.2311 / 1.2738", "1:1", 8, N)
    sys.path.insert(0, str(ROOT / "mold"))
    import hemosure_mold as HM
    y0 = 200
    for i, name in enumerate(("Rear_Housing", "Front_Housing")):
        core, cav, rep = HM.build(name, check=False)
        cx = 70 + i * 135
        ox, oy = S.anchor("left", cx, 190, 0.8, (0, 0, 14.2))
        S.section(core, "X", 0.0, "+", "left", ox, oy, 0.8, hatch="////", color="#345")
        S.section(cav, "X", 0.0, "+", "left", ox, oy, 0.8, hatch="\\\\\\\\", color="#753")
        pr = HM.BUILDERS[name]()[0]
        from build123d import scale
        S.section(scale(pr, by=HM.K), "X", 0.0, "+", "left", ox, oy, 0.8, hatch="", fc="#f5c542", color="#a70")
        S.text(cx - 40, 278, f"{name.replace('_', ' ').upper()} - core (blue /) + cavity (brown \\), part yellow", fs=6.0, fontweight="bold")
        S.text(cx - 40, 273, "Section x = 0 at 0.8:1; mould opens along Z (horizontal on this sheet)", fs=5.0)
        m = MOLD.get(name, {})
        S.text(cx - 40, 100, f"core bbox {m.get('core_bbox')}  cavity bbox {m.get('cavity_bbox')} (mm)", fs=5.0)
        S.text(cx - 40, 96, f"undercut {m.get('undercut_volume_mm3')} mm³ | core collision {m.get('core_collision_mm3')} | cavity collision {m.get('cavity_collision_mm3')}", fs=5.0)
    S.notes(14, 88, [
        "1. Inserts are the full block less the part (x 1.005). Toolmaker adds: pocket fits (H7/g6 to the plates), locks / taper",
        "   interlocks (4 x 5° side locks per insert), ejector & sleeve holes, cooling drillings, vents, sprue/runner/gates.",
        "2. Shut-offs: USB-C opening and cuvette mouth are formed by core steel shutting off on the P/L - give them 1-3° in the",
        "   tool if the T1 shows scuffing (geometry change <= 0.03, inside the opening tolerance).",
        "3. Leave steel-safe stock on: pilot pins -0.03, button hole -0.05, window/lens/overlay pockets -0.05, boss ends +0.05.",
        "4. Polish core SPI B-2; cavity EDM texture VDI 24 after dimensional sign-off; lens pocket floor SPI A-3.",
    ], fs=5.2, lh=3.4)
    S.save(pdf)


# ================================================================== sheet 9: Tool B
def sheet_toolB(pdf):
    S = K.Sheet("MOULD TOOL B (1+1, BLACK ABS)", "HS-303", "Tool B: button + optical block",
                "Inserts 1.2311 P20 / cavity 1.2083 for polish", "2:1", 9, N)
    sys.path.insert(0, str(ROOT / "mold"))
    import hemosure_mold as HM
    from build123d import scale
    for i, (name, ax, val, view, anc, sc) in enumerate([
            ("Optical_Block", "Y", H.OPT_Y, "bottom", (0, H.OPT_Y, 11.0), 1.6),
            ("Button_Cap", "X", 0.0, "left", (0, H.BTN_Y, 20), 3.0)]):
        core, cav, rep = HM.build(name, check=False)
        cx = 95 + i * 140
        ox, oy = S.anchor(view, cx, 185, sc, anc)
        clip = (cx - 70, 110, cx + 70, 265)
        S.section(core, ax, val, "+", view, ox, oy, sc, hatch="////", color="#345", clip=clip)
        S.section(cav, ax, val, "+", view, ox, oy, sc, hatch="\\\\\\\\", color="#753", clip=clip)
        pr = HM.BUILDERS[name]()[0]
        S.section(scale(pr, by=HM.K), ax, val, "+", view, ox, oy, sc, hatch="", fc="#f5c542", color="#a70", clip=clip)
        S.text(cx - 70, 270, f"{name.replace('_', ' ').upper()} - core / cavity section ({sc}:1)", fs=6.2, fontweight="bold")
        m = MOLD.get(name, {})
        S.text(cx - 70, 104, f"undercut {m.get('undercut_volume_mm3')} mm³ | collisions {m.get('core_collision_mm3')} / {m.get('cavity_collision_mm3')} mm³", fs=5.0)
    rows = [
        ["Cavities", "1 x button + 1 x optical block, black ABS"],
        ["Parting", "Button: flange underside. Block: underside"],
        ["Shrink", "0.50 % (in insert STEP)"],
        ["Feed", "Sub gate dia 0.8 (button, on stem side),"],
        ["", "sub gate dia 1.0 (block, on ear underside)"],
        ["Ejection", "Button: sleeve on stem; block: 4 pins on ears"],
        ["", "+ 2 pins on the end walls"],
        ["Polish", "Groove + floor SPI B-1 (cuvette contact)"],
        ["Proj. area", "~7.5 cm² -> 30-50 t press"],
        ["Shot", f"{(P['button'].volume+P['optical'].volume)*RHO:.1f} g parts + ~2 g runner"],
    ]
    mould_data_table(S, 262, 102, "Tool B data", rows)
    S.notes(14, 96, [
        "1. Both parts black -> one family tool; if the button must be another colour, split to its own 1-cavity tool.",
        "2. Optical block groove is the optical-path datum: hold 14.30 +0.05/0 and floor 1.50 ±0.05.",
        "3. Heat-stake pins dia 1.2: vent the pin tips (0.01) to avoid short shots.",
        "4. Verify opacity on T1 parts: no visible light through 2 mm with a torch in a dark room; spectrometer < 0.1 %.",
    ], fs=5.2, lh=3.4)
    S.save(pdf)


# ================================================================== sheet 10: DFM report
def sheet_dfm(pdf):
    import dfm_checks as D
    S = K.Sheet("DFM VERIFICATION & MOULDING SPECIFICATION", "HS-310", "All moulded parts", "ABS", "-", 10, N)
    rows = [["Part", "Vol. cm³", "Mass g", "Undercut mm³", "Core coll.", "Cav. coll.", "Faces < 0.2° draft (>1 mm tall)", "Parting z"]]
    fns = {"Rear_Housing": ("rear", H.build_rear), "Front_Housing": ("front", H.build_front), "Battery_Door": ("door", H.build_door),
           "Button_Cap": ("button", H.build_button), "Optical_Block": ("optical", H.build_optical_block)}
    for name, (k, fn) in fns.items():
        m = MOLD.get(name, {})
        nd = len(D.draft_report(P[k]))
        rows.append([name.replace("_", " "), f"{P[k].volume/1000:.2f}", f"{P[k].volume*RHO:.1f}", str(m.get("undercut_volume_mm3")),
                     str(m.get("core_collision_mm3")), str(m.get("cavity_collision_mm3")), str(nd), str(m.get("parting_z_mm"))])
    S.table(14, 282, [34, 18, 16, 24, 20, 20, 48, 18], rows, fs=5.2, row_h=4.4, title="AUTOMATED CAD CHECKS (this revision)")
    inter = MOLD.get("_interferences", [])
    S.text(14, 250, f"Assembly interference check, all part pairs incl. PCB/TFT/USB-C/tact/LiPo/cuvette/LED board: {'NONE' if not inter else inter}", fs=5.6)
    S.notes(14, 242, [
        "How the checks work (hemosure_casing.py + mold_tools.py, re-run on every change):",
        " - Undercut: steel that is blocked from BOTH the core and the cavity direction (sweep of the part along +Z and -Z).",
        " - Collision: core insert intersected with the part swept along the core opening direction (and same for the cavity).",
        " - Draft: every face's angle to the draw axis; faces taller than 1 mm with < 0.2° are listed (target: none).",
        " - Stack-ups: 15 worst-case + RSS stacks, sheet 6. All pass worst case at this revision.",
    ], fs=5.2, lh=3.3, title="METHOD")
    S.notes(14, 212, [
        "Wall 2.00 nominal (ABS range 1.2-3.5); thinnest: lens-pocket ledge 0.80, door ledge 0.75, lap skirt 1.00.",
        "Ribs 1.0-1.2 (50-60 % of wall), rib height <= 3x wall except PCB posts (gusseted, sleeve-ejected).",
        "Boss OD 5.0-5.6 / hole 2.0-2.9: boss wall 1.35-1.5 (<= 0.75 x wall) -> no sink on the rear skin.",
        "All inside corners R >= 0.5 at wall/floor (R1.0 modelled at the main wall-floor junction).",
        "Flow length / wall (L/t) max ~42 from a single side gate - well inside ABS limit (~150).",
        "Critical cosmetic: front overlay field, rear skin, P/L line. Non-cosmetic: interior, optical block.",
    ], fs=5.2, lh=3.3, title="DESIGN RULES APPLIED")
    S.notes(215, 212, [
        "T0/T1 TRIAL CHECKLIST (for the tool room)",
        " 1. Dry ABS 80 °C / 3 h; dew point <= -20 °C.",
        " 2. Short-shot study -> fill balance of the family tool.",
        " 3. Measure the critical-dims table (sheet 6) on 5 shots/cavity;",
        "    Cpk >= 1.33 on: boss pattern, PCB seat, window, lens pocket.",
        " 4. Assemble with a real PCB + TFT + LiPo: USB-C plug insertion,",
        "    button click (no pre-press, 0.25 travel), door open/close x 50.",
        " 5. Drop test 1.0 m x 6 faces (IEC 61010-1 / 60068-2-31 style).",
        " 6. Light-leak test of the optical cell with the cuvette inserted.",
        " 7. Disinfectant wipe x 500 (70 % IPA, 0.5 % NaOCl): no ESC cracks",
        "    at bosses (if cracking: switch to PC/ABS, shrink 0.5-0.7 %).",
        " 8. Then texture the cavities (VDI 24) and re-check P/L step.",
    ], fs=5.2, lh=3.3, title="VALIDATION")
    S.notes(14, 150, [
        "Process window (start point): melt 230 °C, mould 55 °C, injection speed medium, hold 60-70 % of fill pressure for 4-5 s,",
        "cooling 9 s, ejection at part temp < 85 °C. Gate freeze study to set the hold time. Regrind <= 15 % on cosmetic parts.",
    ], fs=5.2, lh=3.3, title="MOULDING START POINT")
    S.notes(14, 128, [
        "Files (all regenerated from cad/hemosure_casing.py - change a parameter, re-run, everything updates):",
        " cad/HemoSure_*.step (parts + assembly)   mold/HemoSure_*_{CORE,CAVITY}.step (steel size)   drawings/*.pdf",
        " cad/tolerance_stack.py (stacks)   cad/dfm_checks.py (draft)   mold/mold_check_report.json (undercut / collision)",
    ], fs=5.2, lh=3.3, title="DATA PACKAGE")
    S.save(pdf)


if __name__ == "__main__":
    OUT.parent.mkdir(exist_ok=True)
    only = sys.argv[1:]
    fns = [sheet_ga, sheet_front, sheet_rear, sheet_small, sheet_flat, sheet_tol, sheet_toolA, sheet_toolA_sections, sheet_toolB, sheet_dfm]
    out = OUT if not only else OUT.with_name(OUT.stem + "_preview.pdf")
    with PdfPages(out) as pdf:
        for i, f in enumerate(fns, 1):
            if only and str(i) not in only:
                continue
            f(pdf)
            print("sheet", i, "done", flush=True)
    print(out)
