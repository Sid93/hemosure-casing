"""
HemoSure hemoglobin meter (Levram) -- parametric injection-moulded ABS casing.

Coordinate system (all mm):
  X = across the width (0 = centre line), Y = along the length (+Y = top / USB-C end,
  -Y = bottom / cuvette end), Z = thickness (z = 0 rear outer face, z = T front outer face).
  The parting plane between rear and front housing is z = ZP (the USB-C centre height),
  so the USB-C opening and the cuvette slot are split half/half between the housings and
  need NO slides or lifters.

Parts (4 moulded ABS parts + 2 bought-in flat parts):
  rear housing, front housing, battery door, power button cap   -> injection moulded ABS
  display lens (0.8 PMMA, laser-cut), decorative overlay (printed PC, die-cut)

Everything is driven by the parameters below; drafts are built into the geometry
(lofts / cones), not left as a note.
"""
from math import tan, radians

from build123d import (
    Polygon, Box, Cone, Cylinder, Plane, Pos, RectangleRounded, Rectangle, Circle, loft, fillet,
    extrude, Align, Part, Compound, Color, Axis, Location, Solid,
)

# ----------------------------------------------------------------------------- parameters
W, L, R = 62.0, 122.0, 12.0          # outer plan size at the parting line, plan corner radius
T = 22.0                             # overall thickness (excl. button)
WALL = 2.0                           # nominal wall (ABS: 1.5-3.0; 2.0 chosen)
DRAFT_OUT = 1.5                      # deg, outer cosmetic walls (VDI 3400 Ref 24 texture)
DRAFT_IN = 1.0                       # deg, inner (core) walls
DRAFT_BOSS = 0.5                     # deg, bosses / ribs (per side)
R_OUT = 3.0                          # outer edge fillet, front + rear perimeter
R_IN = R_OUT - WALL                  # matching inner fillet -> uniform wall at corners

# Stack-up in Z
Z_FLOOR = WALL                       # rear inner floor
Z_PCB_BOT = 11.0                     # PCB underside (rear standoff seat)
PCB_T = 1.6                          # FR4 1.6 +/-10 %
Z_PCB_TOP = Z_PCB_BOT + PCB_T        # 12.6
USB_H = 3.26                         # USB-C receptacle shell height (top-mount)
ZP = round(Z_PCB_TOP + USB_H / 2, 1)  # 14.2  parting plane = USB-C centre
Z_FRONT_IN = T - WALL                # 20.0 front inner face

# PCB (from the supplied outline: 76.7507 x 49.9383, 4 corner holes 3.31 from edges)
PCB_L, PCB_W, PCB_R = 76.75, 49.94, 3.0
PCB_HOLE_D, PCB_HOLE_INSET = 3.2, 3.31
PCB_Y_TOP = L / 2 - WALL - 1.5       # 57.5 : PCB top edge 1.5 below the inner top wall
PCB_Y_BOT = PCB_Y_TOP - PCB_L        # -19.25
PCB_YC = (PCB_Y_TOP + PCB_Y_BOT) / 2
HOLE_X = PCB_W / 2 - PCB_HOLE_INSET  # 21.66
HOLE_Y_TOP = PCB_Y_TOP - PCB_HOLE_INSET   # 54.19
HOLE_Y_BOT = PCB_Y_BOT + PCB_HOLE_INSET   # -15.94

# USB-C (receptacle must overhang PCB top edge by ~3.0 so its face sits 0.5 behind skin)
USB_OPEN_W, USB_OPEN_H, USB_OPEN_R = 9.6, 4.0, 1.4   # 0.33 / 0.37 clearance per side to the 8.94 x 3.26 shell

# Display: 1.8" ST7735 TFT, 128x160 portrait. Glass 34.0 x 45.83 x 2.6, active 28.03 x 35.04
TFT_GLASS = (34.0, 45.83, 2.6)
TFT_YC = 29.0                        # glass centre; active area sits 2.0 towards +Y
WIN_W, WIN_L, WIN_YC = 30.0, 37.0, 31.0   # through window = active area + ~1 mm / side
LENS_W, LENS_L, LENS_T = 34.0, 41.0, 0.8  # lens pocket (lens part is 0.1/side smaller)
LENS_POCKET_D = 0.95                 # lens 0.80 + 0.05 tape -> sits 0.10 below overlay floor (never proud, WC)
OVL_INSET, OVL_D = 3.5, 0.25         # overlay recess inset from outer edge, depth

# Power button (tact switch 6x6x5.0 on the PCB at (0, BTN_Y))
BTN_Y = -8.0
BTN_D, BTN_HOLE_D = 10.0, 10.3       # 0.15 radial clearance
BTN_FLANGE_D, BTN_FLANGE_T = 13.0, 0.75
TACT_H = 5.0                         # 6x6 tact, H 5.0 +/-0.1, travel 0.25
BTN_PLAY = 0.45                      # flange-to-face gap when the cap rests on the switch
PCB_HOLD_GAP = 0.3                   # front top boss to PCB top (WC 0.04..0.56 with PCB 1.6 +/-0.16)

# Strip-tray channel (the channel in the optical block that the strip TRAY slides in)
CH_W, CH_H = 14.3, 3.3               # groove in the optical block
CH_Y_END = -25.0                     # tray end stop (inner face) = axial datum for the strip

# Test strip (ASSUMED -- replace with the Hb strip drawing) and the strip tray HS-106
STRIP_W, STRIP_L, STRIP_T = 6.0, 30.0, 0.50
STRIP_WIN_FROM_FRONT = 13.95          # read-window centre from the strip's front (insertion) edge
TRAY_W, TRAY_T = 14.10, 3.10          # tray body: 0.10 / side to the groove, 0.20 under the LED board
TRAY_FRONT_WALL = 1.0                 # tray front face to strip-pocket front wall
TRAY_PREGAP = 0.05                    # modelled gap to the end stop (detent preloads it closed)
POCKET_CLR = 0.05                     # strip pocket clearance per side / depth
STRIP_FACE = "rear"                   # 'rear': pocket on the tray UNDERSIDE, strip read side faces the battery side (Rev C)
POCKET_RECESS = 0.25                  # rear-facing strip sits this far inside the tray -> never rubs the groove floor
RET_INTERF = 0.08                     # strip retention crush ribs: interference per side (strip snaps in, stays in)
HANDLE_W, HANDLE_H, HANDLE_L = 24.0, 8.0, 8.5
HANDLE_FACE_GAP = 0.5                 # handle face to housing skin (at P/L)
PLUG_DEPTH, PLUG_GAP = 1.4, 0.3       # light-seal plug into the mouth funnel, radial gap
CH_RIB = 1.2                         # channel wall (0.6 x WALL, avoids sink)
CH_PLATE = 1.5                       # optical floor / ceiling plate
OPT_Y = -40.0                        # optical axis (LED above, sensor below)
FUNNEL_W, FUNNEL_H = 18.0, 6.0       # lead-in at the outer skin

# Optical block (separate BLACK ABS part: light-tight cell, LED board on top, sensor underneath)
OB_WALL = 1.5
OB_X = CH_W / 2 + OB_WALL                 # 8.65 half width
OB_Y0, OB_Y1 = -L / 2 + WALL + 0.2, CH_Y_END + 1.2   # -58.8 .. -23.8
OB_Z0 = 7.0                               # underside (sits on 2 rear bosses)
OB_Z1 = ZP + CH_H / 2                     # 15.85 top face = channel top, LED board rests here
OB_EAR_X = 12.0
LEDPCB_T = 0.8
SENSOR_POCKET_D = 3.5                     # sensor board space under the block floor

DET_Y = -36.0                        # detent bump centre (tray, inserted); clear of the LED-board heat-stake pins at y -31 / -49
DET_PRELOAD = 0.15                   # notch offset towards +Y -> bump rides the notch ramp, pushes tray to the stop

# Battery: LiPo 503035 (5.0 x 30 x 35, ~500 mAh) behind a user door
BAT = (30.0, 35.0, 5.0)
DOOR_YC = 9.0
DOOR_OPEN = (32.0, 39.0)             # through-opening in the floor
DOOR_LEDGE = 2.5                     # ledge width all round the opening
DOOR_GAP = 0.15                      # door-to-recess clearance per side
DOOR_T = 1.2
DOOR_RECESS_D = 1.25                 # door sits 0.05 below the skin (flush 0 / -0.15)

# Fasteners: EJOT PT K25 (2.5 mm thread-forming for plastics)
PILOT_D = 2.0                        # 0.8 x d for ABS
CLEAR_D = 2.9
CB_D = 5.3                           # counterbore for PT K25 pan head (dk 4.5)
HOUSING_SCREW_BOT = (20.0, -45.0)    # +/-X
FEET = [(12.0, 45.0), (-12.0, 45.0), (12.0, -52.0), (-12.0, -52.0)]
FOOT_D, FOOT_D_DEPTH = 8.4, 0.5      # 3M Bumpon SJ5302 (7.9 dia)

# Lap joint: tongue on the rear housing, step in the front housing
TONGUE_T, TONGUE_H = 0.9, 1.5
LAP_CLEAR_SIDE, LAP_CLEAR_TOP = 0.1, 0.2

SHRINK_ABS = 0.005                   # 0.5 % mould shrink allowance for ABS

# ----------------------------------------------------------------------------- helpers

def rr(w, l, r, z, x=0.0, y=0.0):
    """Rounded-rectangle face at height z."""
    return Plane.XY.offset(z) * Pos(x, y) * RectangleRounded(w, l, max(r, 0.05))


TAN1 = tan(radians(1.0))


def ring(offset_out, offset_in, z0, z1, narrow_to_z1=True):
    """Perimeter ring between two inward offsets of the parting-line outline, 1 deg draft on both
    faces. narrow_to_z1: ring gets thinner towards z1 (a tongue), else thinner towards z0."""
    d = abs(z1 - z0) * TAN1
    oo0, oo1 = (offset_out, offset_out + d) if narrow_to_z1 else (offset_out + d, offset_out)
    oi0, oi1 = (offset_in, offset_in - d) if narrow_to_z1 else (offset_in - d, offset_in)
    o = loft([rr(W - 2 * oo0, L - 2 * oo0, R - oo0, z0), rr(W - 2 * oo1, L - 2 * oo1, R - oo1, z1)])
    i = loft([rr(W - 2 * oi0, L - 2 * oi0, R - oi0, z0 - 0.01), rr(W - 2 * oi1, L - 2 * oi1, R - oi1, z1 + 0.01)])
    return o - i


def taper_box(x0, x1, y0, y1, z0, z1, g=None, gx=None, gy=None):
    """Box whose section at z1 is grown by g per side relative to z0 (negative = shrinks).
    Default g: shrink by 1 deg towards z1."""
    h = abs(z1 - z0)
    g = -h * TAN1 if g is None else g
    gx = g if gx is None else gx
    gy = g if gy is None else gy
    lx, ly, xc, yc = abs(x1 - x0), abs(y1 - y0), (x0 + x1) / 2, (y0 + y1) / 2
    a = Plane.XY.offset(z0) * Pos(xc, yc) * Rectangle(lx, ly)
    b = Plane.XY.offset(z1) * Pos(xc, yc) * Rectangle(lx + 2 * gx, ly + 2 * gy)
    return loft([a, b]) if z0 < z1 else loft([b, a])


def box(x0, x1, y0, y1, z0, z1):
    return Pos((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2) * Box(abs(x1 - x0), abs(y1 - y0), abs(z1 - z0))


def cone_z(x, y, z0, z1, d0, d1):
    """Truncated cone along Z: diameter d0 at z0, d1 at z1 (either direction)."""
    lo, hi = (z0, z1) if z0 < z1 else (z1, z0)
    dlo, dhi = (d0, d1) if z0 < z1 else (d1, d0)
    return Pos(x, y, lo) * Cone(dlo / 2, dhi / 2, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def cone1(x, y, z_open, z_deep, d_open):
    """Round recess / pin with 1 deg draft: d_open at the mould-open side."""
    return cone_z(x, y, z_open, z_deep, d_open, d_open - 2 * abs(z_open - z_deep) * TAN1)


def cyl_z(x, y, z0, z1, d):
    lo, hi = min(z0, z1), max(z0, z1)
    return Pos(x, y, lo) * Cylinder(d / 2, hi - lo, align=(Align.CENTER, Align.CENTER, Align.MIN))


def drafted_boss(x, y, z_root, z_tip, d_tip):
    """Boss with DRAFT_BOSS: d_tip at the free end, larger at the root."""
    d_root = d_tip + 2 * abs(z_tip - z_root) * tan(radians(DRAFT_BOSS))
    return cone_z(x, y, z_root, z_tip, d_root, d_tip)


def drafted_hole(x, y, z_open, z_bottom, d_open):
    """Blind/through hole, d_open at the mouth, 0.25 deg taper (core pin draft)."""
    d_bot = d_open - 2 * abs(z_open - z_bottom) * tan(radians(0.25))
    return cone_z(x, y, z_open, z_bottom, d_open, d_bot)


def rib(x0, x1, y0, y1, z_root, z_tip):
    """Rib with DRAFT_BOSS per side on its thin faces. Thickness taken at the tip."""
    h = abs(z_tip - z_root)
    grow = 2 * h * tan(radians(DRAFT_BOSS))
    lx, ly = abs(x1 - x0), abs(y1 - y0)
    xc, yc = (x0 + x1) / 2, (y0 + y1) / 2
    tip = Plane.XY.offset(z_tip) * Pos(xc, yc) * Rectangle(lx, ly)
    root = Plane.XY.offset(z_root) * Pos(xc, yc) * Rectangle(lx + grow, ly + grow)   # draft on all 4 faces
    return loft([root, tip]) if z_root < z_tip else loft([tip, root])


def half_space(z_lo, z_hi):
    return box(-200, 200, -200, 200, z_lo, z_hi)


# ----------------------------------------------------------------------------- envelope

A0 = tan(radians(DRAFT_OUT)) * ZP           # outer shrink per side, rear face
A1 = tan(radians(DRAFT_OUT)) * (T - ZP)     # outer shrink per side, front face
B0 = tan(radians(DRAFT_IN)) * (ZP - Z_FLOOR)
B1 = tan(radians(DRAFT_IN)) * (Z_FRONT_IN - ZP)


def outer_envelope():
    rear = loft([rr(W - 2 * A0, L - 2 * A0, R - A0, 0.0), rr(W, L, R, ZP)])
    front = loft([rr(W, L, R, ZP), rr(W - 2 * A1, L - 2 * A1, R - A1, T)])
    rear = fillet(rear.edges().group_by(Axis.Z)[0], R_OUT)
    front = fillet(front.edges().group_by(Axis.Z)[-1], R_OUT)
    return rear, front


def inner_void():
    wi, li, ri = W - 2 * WALL, L - 2 * WALL, R - WALL
    rear = loft([rr(wi - 2 * B0, li - 2 * B0, ri - B0, Z_FLOOR), rr(wi, li, ri, ZP)])
    front = loft([rr(wi, li, ri, ZP), rr(wi - 2 * B1, li - 2 * B1, ri - B1, Z_FRONT_IN)])
    rear = fillet(rear.edges().group_by(Axis.Z)[0], R_IN)
    front = fillet(front.edges().group_by(Axis.Z)[-1], R_IN)
    return rear, front


def usb_tool():
    face = Plane.XZ.offset(-(L / 2 - WALL - 1.0)) * Pos(0, ZP) * RectangleRounded(USB_OPEN_W, USB_OPEN_H, USB_OPEN_R)
    return extrude(face, -6.0)  # Plane.XZ normal is -Y; offset(-a) sits at y=+a; negative amount -> +Y


def cuvette_tools():
    """Lead-in funnel + throat through the bottom end wall. Full-round (stadium) ends: the side
    faces are curved, so they carry draft everywhere except the tangent line on the parting plane.
    Throat straight length = CH_W, so the 14.1 x 3.1 strip tray passes."""
    y_skin = -L / 2
    tw = CH_W + CH_H
    funnel = loft([
        Plane.XZ.offset(-(y_skin - 0.5)) * Pos(0, ZP) * RectangleRounded(FUNNEL_W + CH_H + 1.0, FUNNEL_H, FUNNEL_H / 2 - 0.01),
        Plane.XZ.offset(-(y_skin + WALL + 0.5)) * Pos(0, ZP) * RectangleRounded(tw, CH_H, CH_H / 2 - 0.01),
    ])
    throat = extrude(Plane.XZ.offset(-(y_skin + WALL - 0.6)) * Pos(0, ZP) * RectangleRounded(tw, CH_H, CH_H / 2 - 0.01), -1.6)
    return funnel + throat


# ----------------------------------------------------------------------------- rear housing

def rear_cavity_side_cuts():
    """Features formed by the CAVITY (outside) steel of the rear housing mould."""
    dw, dl = DOOR_OPEN[0] + 2 * DOOR_LEDGE + 2 * DOOR_GAP, DOOR_OPEN[1] + 2 * DOOR_LEDGE + 2 * DOOR_GAP
    cuts = [
        extrude(rr(dw, dl, 3.0 + DOOR_GAP, 0.0, 0, DOOR_YC), DOOR_RECESS_D, taper=1.0)
        + extrude(rr(dw + 0.2, dl + 0.2, 3.1 + DOOR_GAP, -0.5, 0, DOOR_YC), 0.51),            # door recess
        extrude(rr(DOOR_OPEN[0], DOOR_OPEN[1], 1.5, -0.5, 0, DOOR_YC), Z_FLOOR + 0.6, taper=1.0),  # through opening
        extrude(rr(36.0, 22.0, 2.0, -0.5, 0, -28.0), 0.65, taper=1.0),                     # label recess 0.15
    ]
    for (x, y) in FEET:
        cuts.append(cone1(x, y, -0.5, FOOT_D_DEPTH, FOOT_D + 0.02))
    for sx in (1, -1):
        cuts.append(cone1(sx * HOLE_X, HOLE_Y_TOP, -0.5, 2.2, CB_D + 0.05))                       # top screw c'bore
        cuts.append(cone1(sx * HOUSING_SCREW_BOT[0], HOUSING_SCREW_BOT[1], -0.5, 3.2, CB_D + 0.07))  # bottom c'bore
    return cuts


def build_rear():
    o_rear, _ = outer_envelope()
    v_rear, _ = inner_void()
    shell = o_rear - v_rear

    feats = []
    # tongue (lap joint)
    feats.append(ring(WALL - TONGUE_T, WALL, ZP - 0.01, ZP + TONGUE_H, narrow_to_z1=True))
    for sx in (1, -1):
        # PCB standoffs, bottom holes: pilot for PT K25x6
        feats.append(drafted_boss(sx * HOLE_X, HOLE_Y_BOT, Z_FLOOR - 0.5, Z_PCB_BOT, 5.0))
        # PCB standoffs, top holes: housing screw passes through
        feats.append(drafted_boss(sx * HOLE_X, HOLE_Y_TOP, Z_FLOOR - 0.5, Z_PCB_BOT, 5.6))
        # housing screw bosses, bottom zone
        bx, by = sx * HOUSING_SCREW_BOT[0], HOUSING_SCREW_BOT[1]
        feats.append(drafted_boss(bx, by, Z_FLOOR - 0.5, ZP, 5.6))
        # gussets to the side wall (0.6 x wall)
        x_in, x_wall = sx * (HOUSING_SCREW_BOT[0] + 2.6), sx * (W / 2 - WALL + 0.3)
        feats.append(rib(min(x_in, x_wall), max(x_in, x_wall), by - 0.5, by + 0.5, Z_FLOOR - 0.2, ZP - 3.0))
        x_in, x_wall = sx * (HOLE_X + 2.3), sx * (W / 2 - WALL + 0.3)
        feats.append(rib(min(x_in, x_wall), max(x_in, x_wall), HOLE_Y_BOT - 0.5, HOLE_Y_BOT + 0.5, Z_FLOOR - 0.2, Z_PCB_BOT - 2.0))
        # battery side rails (on the ledge)
        x0 = sx * (DOOR_OPEN[0] / 2)
        x1 = sx * (DOOR_OPEN[0] / 2 + 1.0)
        feats.append(rib(min(x0, x1), max(x0, x1), DOOR_YC - 14.0, DOOR_YC + 14.0, Z_FLOOR - 0.2, 8.0))
        # PCB edge-locating crush ribs, long sides (tip 0.05 from the PCB edge)
        for yc in (PCB_YC - 22.0, PCB_YC + 22.0):
            x_tip, x_wall = sx * (PCB_W / 2 + 0.05), sx * (W / 2 - WALL + 0.3)
            feats.append(rib(min(x_tip, x_wall), max(x_tip, x_wall), yc - 0.6, yc + 0.6, Z_FLOOR - 0.2, Z_PCB_TOP + 0.6))
        # PCB top-edge ribs (either side of the USB-C) and bottom-edge posts
        feats.append(rib(sx * 12 - 0.6, sx * 12 + 0.6, PCB_Y_TOP + 0.05, L / 2 - WALL + 0.3, Z_FLOOR - 0.2, Z_PCB_TOP + 0.6))
        feats.append(rib(sx * 12 - 2.0, sx * 12 + 2.0, PCB_Y_BOT - 0.05 - 1.2, PCB_Y_BOT - 0.05, Z_FLOOR - 0.2, Z_PCB_TOP + 0.6))
        # optical-block mounting bosses (pilot for PT K25x6)
        feats.append(drafted_boss(sx * OB_EAR_X, OPT_Y, Z_FLOOR - 0.5, OB_Z0, 5.0))
    for f in feats:
        shell = shell + f

    cuts = rear_cavity_side_cuts()
    cuts += [usb_tool(), cuvette_tools()]
    # tongue is interrupted with straight-sided gaps at both openings (rounded corners there would be undercuts)
    cuts.append(taper_box(-USB_OPEN_W / 2, USB_OPEN_W / 2, L / 2 - WALL - 1.0, L / 2 + 1, ZP - 0.01, ZP + TONGUE_H + 0.1, gx=0.05, gy=0))
    cuts.append(taper_box(-(FUNNEL_W + CH_H + 1.0) / 2, (FUNNEL_W + CH_H + 1.0) / 2, -L / 2 - 1, -L / 2 + WALL + 1.0, ZP - 0.01, ZP + TONGUE_H + 0.1, gx=0.05, gy=0))
    for sx in (1, -1):
        cuts.append(drafted_hole(sx * HOLE_X, HOLE_Y_BOT, Z_PCB_BOT + 0.01, Z_PCB_BOT - 6.5, PILOT_D))
        cuts.append(drafted_hole(sx * HOLE_X, HOLE_Y_TOP, Z_PCB_BOT + 0.01, 2.0, CLEAR_D))
        cuts.append(drafted_hole(sx * HOUSING_SCREW_BOT[0], HOUSING_SCREW_BOT[1], ZP + 0.01, 3.0, CLEAR_D))
    for sx in (1, -1):
        cuts.append(drafted_hole(sx * OB_EAR_X, OPT_Y, OB_Z0 + 0.01, OB_Z0 - 4.5, PILOT_D))
    for c in cuts:
        shell = shell - c

    shell = shell & half_space(-1, ZP + TONGUE_H + 0.01)
    shell.label = "rear_housing"
    shell.color = Color(0.95, 0.95, 0.93)
    return shell


# ----------------------------------------------------------------------------- front housing

def front_cavity_side_cuts():
    """Features formed by the CAVITY (outside) steel of the front housing mould."""
    return [
        extrude(rr(W - 2 * OVL_INSET, L - 2 * OVL_INSET, R - OVL_INSET, T - OVL_D), 1.0, taper=-1.0),           # overlay recess
        extrude(rr(LENS_W, LENS_L, 2.0, T - OVL_D - LENS_POCKET_D, 0, WIN_YC), LENS_POCKET_D + 0.01, taper=-1.0),  # lens pocket
        extrude(rr(WIN_W - 0.06, WIN_L - 0.06, 0.97, Z_FRONT_IN - 0.6, 0, WIN_YC), WALL + 1.0, taper=-1.0),     # window (nominal at the lens-pocket floor)
        cone1(0, BTN_Y, T + 1, Z_FRONT_IN - 0.01, BTN_HOLE_D + 0.05),                                           # button hole (nominal mid-wall)
    ]


def build_front():
    _, o_front = outer_envelope()
    _, v_front = inner_void()
    shell = o_front - v_front

    feats = []
    for sx in (1, -1):
        # top bosses: land 0.2 above the PCB (PCB hold-down stop, not a clamp)
        feats.append(drafted_boss(sx * HOLE_X, HOLE_Y_TOP, Z_FRONT_IN + 0.5, Z_PCB_TOP + PCB_HOLD_GAP, 5.0))
        # bottom bosses: 0.1 short of the rear bosses -> perimeter closes first
        feats.append(drafted_boss(sx * HOUSING_SCREW_BOT[0], HOUSING_SCREW_BOT[1], Z_FRONT_IN + 0.5, ZP + 0.1, 5.0))
    # LED-board hold-down ribs (0.2 above the LED board -> limits lift, no clamp load)
    for x in (-5.0, 5.0):
        feats.append(rib(x - 0.6, x + 0.6, OPT_Y - 6, OPT_Y + 6, Z_FRONT_IN + 0.2, OB_Z1 + LEDPCB_T + 0.2))
    # TFT locating ribs (0.15 clearance to the glass), 2.2 deep
    gx, gy = TFT_GLASS[0] / 2 + 0.15, TFT_GLASS[1] / 2 + 0.15
    zt = Z_FRONT_IN - 2.2
    for sx in (1, -1):
        feats.append(rib(min(sx * gx, sx * (gx + 1.0)), max(sx * gx, sx * (gx + 1.0)), TFT_YC - 8, TFT_YC + 8, Z_FRONT_IN + 0.2, zt))
    for sy in (1, -1):
        y0, y1 = TFT_YC + sy * gy, TFT_YC + sy * (gy + 1.0)
        feats.append(rib(-8, 8, min(y0, y1), max(y0, y1), Z_FRONT_IN + 0.2, zt))
    # button guide sleeve
    sleeve = cone_z(0, BTN_Y, Z_FRONT_IN + 0.2, Z_FRONT_IN - 1.4, 15.4, 15.2) - cone1(0, BTN_Y, Z_FRONT_IN - 2, Z_FRONT_IN + 1, BTN_FLANGE_D + 0.6)
    feats.append(sleeve)
    for f in feats:
        shell = shell + f

    cuts = front_cavity_side_cuts()
    cuts.append(ring(WALL - TONGUE_T - LAP_CLEAR_SIDE, WALL + 0.1, ZP - 0.5, ZP + TONGUE_H + LAP_CLEAR_TOP, narrow_to_z1=True))
    cuts += [usb_tool(), cuvette_tools()]
    for sx in (1, -1):
        cuts.append(drafted_hole(sx * HOLE_X, HOLE_Y_TOP, Z_PCB_TOP + PCB_HOLD_GAP - 0.01, Z_FRONT_IN - 0.6, PILOT_D))
        cuts.append(drafted_hole(sx * HOUSING_SCREW_BOT[0], HOUSING_SCREW_BOT[1], ZP + 0.09, Z_FRONT_IN - 0.6, PILOT_D))
    for c in cuts:
        shell = shell - c

    shell = shell & half_space(Z_PCB_TOP + 0.1, T + 1)
    shell.label = "front_housing"
    shell.color = Color(0.97, 0.97, 0.96)
    return shell


# ----------------------------------------------------------------------------- battery door

def build_door():
    """Parting at the plate top (z = DOOR_T): plate edges from the cavity, hooks/latch from the core,
    hook undersides formed by cavity pins through moulding windows. 1 deg draft everywhere."""
    ow = DOOR_OPEN[0] + 2 * DOOR_LEDGE      # door outline (recess minus gap)
    ol = DOOR_OPEN[1] + 2 * DOOR_LEDGE
    y_top_edge = DOOR_YC + DOOR_OPEN[1] / 2   # opening edge, hinge end
    y_bot_edge = DOOR_YC - DOOR_OPEN[1] / 2   # opening edge, latch end
    zl = Z_FLOOR                              # ledge top
    door = extrude(rr(ow, ol, 3.0, 0.0, 0, DOOR_YC), DOOR_T, taper=-1.0)   # nominal outline at the skin

    # hinge hooks (2): post rises through the opening, hook reaches 1.3 over the ledge
    for x in (-10.0, 10.0):
        door = door + taper_box(x - 3, x + 3, y_top_edge - 1.3, y_top_edge - 0.2, DOOR_T - 0.01, zl + 0.9)
        door = door + taper_box(x - 3, x + 3, y_top_edge - 0.25, y_top_edge + 1.3, zl + 0.1, zl + 0.9)
        door = door - taper_box(x - 3.1, x + 3.1, y_top_edge - 0.3, y_top_edge + 1.4, -0.1, zl + 0.1)   # moulding window
    # latch: cantilever 0.8 thick x 6.3 long, 0.8 bump (0.5 engagement), 45 deg release face
    arm_y0, arm_y1 = y_bot_edge + 0.3, y_bot_edge + 1.1
    door = door + taper_box(-4, 4, arm_y0, arm_y1, DOOR_T - 0.01, DOOR_T + 6.3, gx=-6.3 * TAN1, gy=-0.05)
    bump = loft([
        Plane.XY.offset(zl + 0.1) * Pos(0, arm_y0 - 0.39) * Rectangle(7.94, 0.82),
        Plane.XY.offset(zl + 0.9) * Pos(0, arm_y0 + 0.1) * Rectangle(7.86, 0.2),
    ])
    door = door + bump
    door = door - taper_box(-4.1, 4.1, arm_y0 - 0.9, arm_y0 + 0.06, -0.1, zl + 0.1)                   # moulding window
    # finger notch on the outside at the latch end
    door = door - taper_box(-6, 6, DOOR_YC - ol / 2 - 0.1, DOOR_YC - ol / 2 + 3.0, -0.1, 0.5, gx=-0.02, gy=-0.02)
    door.label = "battery_door"
    door.color = Color(0.93, 0.93, 0.91)
    return door


# ----------------------------------------------------------------------------- optical block

def build_optical_block():
    """Parting at the underside (z = OB_Z0). Core (+Z) forms the outside, ears and the open-top
    cuvette groove; cavity (-Z) forms the sensor pocket. 1 deg draft on every wall."""
    ob = taper_box(-OB_X, OB_X, OB_Y0, OB_Y1, OB_Z0, OB_Z1)                 # outside narrows upward
    for sx in (1, -1):                                                         # mounting ears
        x0, x1 = sorted((sx * (OB_X - 0.5), sx * (OB_EAR_X + 2.8)))
        ob = ob + taper_box(x0, x1, OPT_Y - 3.5, OPT_Y + 3.5, OB_Z0, OB_Z0 + 2.0)
        ob = ob - cone1(sx * OB_EAR_X, OPT_Y, OB_Z0 + 2.1, OB_Z0 - 0.1, CLEAR_D + 0.04)
    # cuvette groove, open to the top (+Z) and to the mouth (-Y), end stop at CH_Y_END; nominal at mid-depth
    zg0 = ZP - CH_H / 2
    ob = ob - taper_box(-CH_W / 2 + 0.03, CH_W / 2 - 0.03, OB_Y0 - 1.0, CH_Y_END + 0.03, zg0, OB_Z1 + 0.1, gx=(CH_H + 0.1) * TAN1, gy=(CH_H + 0.1) * TAN1)
    # tray detent notch in the +X groove wall (open top), shifted +Y so the bump preloads the tray to the stop
    notch = [(CH_W / 2 - 0.05, DET_Y - 1.25 + DET_PRELOAD), (CH_W / 2 + 0.40, DET_Y - 0.35 + DET_PRELOAD),
             (CH_W / 2 + 0.40, DET_Y + 0.15 + DET_PRELOAD), (CH_W / 2 - 0.05, DET_Y + 1.1 + DET_PRELOAD)]
    ob = ob - extrude(Plane.XY.offset(zg0 - 0.01) * Polygon(*notch, align=None), OB_Z1 - zg0 + 0.2, taper=-1.0)
    # sensor pocket, open to the underside (-Z); 1.5 floor under the groove
    ob = ob - taper_box(-CH_W / 2, CH_W / 2, OB_Y0 + OB_WALL, CH_Y_END - 0.5, OB_Z0 - 0.1, zg0 - CH_PLATE)
    # sensor aperture
    ob = ob - cone1(0, OPT_Y, zg0 - CH_PLATE - 0.1, zg0 + 0.1, 2.0)
    # heat-stake pins for LED board (top) - 4 x dia 1.2 x 1.2
    for y in (OPT_Y - 9.0, OPT_Y + 9.0):
        for sx in (1, -1):
            ob = ob + cone_z(sx * (CH_W / 2 + OB_WALL / 2), y, OB_Z1 - 0.01, OB_Z1 + 1.2, 1.2, 1.1)
    ob.label = "optical_block_BLACK_ABS"
    ob.color = Color(0.08, 0.08, 0.09)
    return ob


# ----------------------------------------------------------------------------- strip tray

def dbox(x0, x1, y0, y1, z0, z1, zp, grow=False):
    """Box split at the parting plane zp with 1 deg draft each way (shrinks away from zp; grow=True
    for cut tools, which must widen away from zp)."""
    sgn = 1 if grow else -1
    parts = []
    if z1 > zp:
        parts.append(taper_box(x0, x1, y0, y1, zp - 0.001, z1, g=sgn * (z1 - zp) * TAN1))
    if z0 < zp:
        parts.append(taper_box(x0, x1, y0, y1, zp + 0.001, z0, g=sgn * (zp - z0) * TAN1))
    out = parts[0]
    for q in parts[1:]:
        out = out + q
    return out


def dprism(pts, z0, z1, zp):
    """Polygon prism split at zp, 1 deg draft each way."""
    f = Plane.XY.offset(zp) * Polygon(*pts, align=None)
    return extrude(f, z1 - zp, taper=1.0) + extrude(f, -(zp - z0), taper=1.0)


def funnel_size(y):
    """Stadium size of the housing mouth funnel at y (linear from skin-0.5 to skin+WALL+0.5)."""
    t = (y - (-L / 2 - 0.5)) / (WALL + 1.0)
    return (FUNNEL_W + CH_H + 1.0) + t * ((CH_W + CH_H) - (FUNNEL_W + CH_H + 1.0)), FUNNEL_H + t * (CH_H - FUNNEL_H)


TRAY_Z0 = ZP - CH_H / 2                         # tray rides on the groove floor
TRAY_Y1 = CH_Y_END - TRAY_PREGAP                # tray front face (inserted)
POCKET_Y1 = TRAY_Y1 - TRAY_FRONT_WALL           # strip front edge sits here
HANDLE_Y0 = -L / 2 - HANDLE_FACE_GAP            # handle face


def build_tray():
    """HS-106 strip tray (black ABS). The user drops the strip into the pocket outside the meter,
    slides the tray home (hard stop + detent click); the handle plugs the mouth (light seal).
    Parting at ZP (same plane as the housings), 1 deg draft both ways."""
    z0, z1 = TRAY_Z0, TRAY_Z0 + TRAY_T
    hw = TRAY_W / 2
    tray = dbox(-hw, hw, HANDLE_Y0 - 0.5, TRAY_Y1, z0, z1, ZP)
    # handle + light-seal plug
    tray = tray + dbox(-HANDLE_W / 2, HANDLE_W / 2, HANDLE_Y0 - HANDLE_L, HANDLE_Y0, ZP - HANDLE_H / 2, ZP + HANDLE_H / 2, ZP)
    w0, h0 = funnel_size(HANDLE_Y0); w1, h1 = funnel_size(HANDLE_Y0 + PLUG_DEPTH)
    sec = lambda y, w, h: Plane.XZ.offset(-y) * Pos(0, ZP) * RectangleRounded(w, h, h / 2 - 0.01)
    # plug + sloped nose in one ruled loft (keeps every plug face drafted to the Z draw)
    tray = tray + loft([sec(HANDLE_Y0 - 0.3, w0 - 2 * PLUG_GAP, h0 - 2 * PLUG_GAP),
                        sec(HANDLE_Y0 + PLUG_DEPTH, w1 - 2 * PLUG_GAP, h1 - 2 * PLUG_GAP),
                        sec(HANDLE_Y0 + PLUG_DEPTH + 0.35, w1 - 2 * PLUG_GAP - 0.3, 0.4)], ruled=True)
    # grip ribs on the handle (top + bottom), 0.4 deep
    for y in (HANDLE_Y0 - 2.5, HANDLE_Y0 - 4.5, HANDLE_Y0 - 6.5):
        tray = tray - taper_box(-9, 9, y - 0.4, y + 0.4, ZP + HANDLE_H / 2 - 0.4, ZP + HANDLE_H / 2 + 0.1, g=0.02)
        tray = tray - taper_box(-9, 9, y - 0.4, y + 0.4, ZP - HANDLE_H / 2 + 0.4, ZP - HANDLE_H / 2 - 0.1, g=0.02)
    pw, pl = STRIP_W + 2 * POCKET_CLR, STRIP_L + 2 * POCKET_CLR
    if STRIP_FACE == "rear":
        # strip pocket on the UNDERSIDE (open -Z, formed by the cavity), strip recessed POCKET_RECESS
        pd = STRIP_T + POCKET_RECESS
        z_pc = z0 + pd                                        # pocket ceiling = strip's back face
        tray = tray - taper_box(-pw / 2, pw / 2, POCKET_Y1 - pl, POCKET_Y1, z0 - 0.1, z_pc, g=-(pd + 0.1) * TAN1)
        # retention crush ribs: 2 per long wall, RET_INTERF interference -> strip snaps in, cannot drop out
        for yr in (POCKET_Y1 - 6.0, POCKET_Y1 - pl + 6.0):
            for sx in (1, -1):
                xa, xb = sorted((sx * (pw / 2 + 0.02), sx * (pw / 2 - POCKET_CLR - RET_INTERF)))
                tray = tray + taper_box(xa, xb, yr - 0.4, yr + 0.4, z0 + 0.15, z_pc + 0.01, g=0.004)
        # tweezer notch at the pocket's rear end (underside)
        tray = tray - taper_box(-3.5, 3.5, POCKET_Y1 - pl - 3.6, POCKET_Y1 - pl + 2.0, z0 - 0.1, z0 + 1.2, g=-0.03)
        # read aperture: pocket ceiling -> top face, narrowest at the P/L
        ap = 2.4
        tray = tray - cone1(0, OPT_Y, z_pc - 0.01, ZP + 0.001, ap + 2 * (ZP - z_pc + 0.01) * TAN1)
        tray = tray - cone1(0, OPT_Y, z1 + 0.1, ZP - 0.001, ap + 2 * (z1 + 0.1 - ZP) * TAN1)
    else:
        # strip pocket (open top)
        pd = STRIP_T + POCKET_CLR
        tray = tray - taper_box(-pw / 2, pw / 2, POCKET_Y1 - pl, POCKET_Y1, z1 - pd, z1 + 0.1, g=(pd + 0.1) * TAN1)
        tray = tray - taper_box(-3.5, 3.5, POCKET_Y1 - pl - 3.6, POCKET_Y1 - pl + 2.0, z1 - 1.2, z1 + 0.1, g=0.03)
        ap = 2.4
        tray = tray - cone1(0, OPT_Y, z0 - 0.1, ZP + 0.001, ap + 2 * (ZP - z0 + 0.1) * TAN1)
        tray = tray - cone1(0, OPT_Y, z1 - pd + 0.01, ZP - 0.001, ap + 2 * (z1 - pd + 0.01 - ZP) * TAN1)
    # detent: cantilever arm on +X side (slot through, free end towards +Y) with a ramped bump
    tray = tray - dbox(hw - 1.7, hw - 1.1, DET_Y - 12.0, DET_Y + 1.1, z0 - 0.1, z1 + 0.1, ZP, grow=True)
    tray = tray - dbox(hw - 1.7, hw + 0.3, DET_Y + 1.1, DET_Y + 1.6, z0 - 0.1, z1 + 0.1, ZP, grow=True)
    bump = [(hw - 0.05, DET_Y - 1.4), (hw + 0.45, DET_Y - 0.4), (hw + 0.45, DET_Y + 0.1), (hw - 0.05, DET_Y + 1.05)]
    tray = tray + dprism(bump, z0 + 0.1, z1 - 0.1, ZP)
    # core-outs under the pocket side walls (uniform ~1.1 walls, no sink)
    for (x0, x1, y0, y1) in [(-5.85, -3.9, -57.0, -45.0), (3.9, 5.85, -57.0, -49.5), (-5.85, -3.9, -36.0, -28.5)]:
        tray = tray - taper_box(x0, x1, y0, y1, z0 - 0.1, ZP - 0.15, g=-0.03)     # stays below the P/L
    tray.label = "strip_tray_BLACK_ABS"
    tray.color = Color(0.1, 0.1, 0.11)
    return tray


# ----------------------------------------------------------------------------- button cap

def build_button():
    """Parting at the flange underside. Cavity (+Z) forms the cap + flange rim, core (-Z) the
    core-out and the stem. Stem rests on the tact actuator; flange sits BTN_PLAY below the face."""
    z_tact = Z_PCB_TOP + TACT_H                      # 17.6  stem rests here
    z_flange_top = Z_FRONT_IN - BTN_PLAY             # 19.55
    z_flange_bot = z_flange_top - BTN_FLANGE_T       # 18.80
    z_top = T + 0.6                                  # 0.6 proud of the front face at rest
    cap = cone_z(0, BTN_Y, z_flange_bot, z_top, BTN_D + 0.03, BTN_D - 0.09)   # nominal 10.0 inside the hole
    cap = fillet(cap.edges().group_by(Axis.Z)[-1], 1.0)
    cap = cap + cone_z(0, BTN_Y, z_flange_bot, z_flange_top, BTN_FLANGE_D, BTN_FLANGE_D - 0.03)
    cap = cap - cone1(0, BTN_Y, z_flange_bot - 0.1, z_top - 1.8, 7.0)       # core-out (1.5 side / 1.8 top)
    cap = cap + cone_z(0, BTN_Y, z_tact, z_top - 1.79, 3.9, 4.0)            # stem, tip dia 3.9
    cap.label = "button_cap"
    cap.color = Color(0.2, 0.2, 0.22)
    return cap


# ----------------------------------------------------------------------------- bought-in / reference parts

def build_lens():
    lens = extrude(rr(LENS_W - 0.2, LENS_L - 0.2, 1.9, T - OVL_D - LENS_POCKET_D + 0.05, 0, WIN_YC), LENS_T)
    lens.label = "display_lens_PMMA"
    lens.color = Color(0.75, 0.85, 0.95, 0.35)
    return lens


def build_overlay(color=(0.10, 0.20, 0.42)):
    ovl = extrude(rr(W - 2 * OVL_INSET - 0.4, L - 2 * OVL_INSET - 0.4, R - OVL_INSET - 0.2, T - OVL_D + 0.025), 0.225)
    ovl = ovl - extrude(rr(WIN_W + 0.6, WIN_L + 0.6, 1.2, T - 1, 0, WIN_YC), 2)  # clear window region (modelled open)
    ovl = ovl - cyl_z(0, BTN_Y, T - 1, T + 1, 11.0)
    ovl.label = "overlay_PC_printed"
    ovl.color = Color(*color)
    return ovl


def build_pcb():
    pcb = extrude(rr(PCB_W, PCB_L, PCB_R, Z_PCB_BOT, 0, PCB_YC), PCB_T)
    for sx in (1, -1):
        for y in (HOLE_Y_TOP, HOLE_Y_BOT):
            pcb = pcb - cyl_z(sx * HOLE_X, y, Z_PCB_BOT - 1, Z_PCB_TOP + 1, PCB_HOLE_D)
    pcb.label = "REF_pcb_76.75x49.94"
    pcb.color = Color(0.1, 0.45, 0.2)
    return pcb


def build_ref_components():
    parts = []
    tft = box(-TFT_GLASS[0] / 2, TFT_GLASS[0] / 2, TFT_YC - TFT_GLASS[1] / 2, TFT_YC + TFT_GLASS[1] / 2,
              Z_FRONT_IN - 0.3 - TFT_GLASS[2], Z_FRONT_IN - 0.3)
    tft.label, tft.color = "REF_tft_1.8in_ST7735", Color(0.05, 0.05, 0.08)
    usb = extrude(Plane.XZ.offset(-(PCB_Y_TOP - 4.35)) * Pos(0, Z_PCB_TOP + USB_H / 2) * RectangleRounded(8.94, USB_H, 1.3), -7.35)
    usb.label, usb.color = "REF_usb_c_receptacle", Color(0.7, 0.7, 0.72)
    tact = box(-3, 3, BTN_Y - 3, BTN_Y + 3, Z_PCB_TOP, Z_PCB_TOP + TACT_H)
    tact.label, tact.color = "REF_tact_6x6x5", Color(0.2, 0.2, 0.2)
    bat = box(-BAT[0] / 2, BAT[0] / 2, DOOR_YC - BAT[1] / 2, DOOR_YC + BAT[1] / 2, DOOR_T + 0.05, DOOR_T + 0.05 + BAT[2])
    bat.label, bat.color = "REF_lipo_503035", Color(0.6, 0.6, 0.65)
    zs = (TRAY_Z0 + POCKET_RECESS) if STRIP_FACE == "rear" else (TRAY_Z0 + TRAY_T - STRIP_T - POCKET_CLR)
    cuv = box(-STRIP_W / 2, STRIP_W / 2, POCKET_Y1 - STRIP_L, POCKET_Y1, zs, zs + STRIP_T)
    cuv.label, cuv.color = "REF_hb_strip_6x30x0.5", Color(0.85, 0.2, 0.2)
    led = box(-OB_X, OB_X, OPT_Y - 12, OPT_Y + 12, OB_Z1, OB_Z1 + LEDPCB_T)
    for y in (OPT_Y - 9.0, OPT_Y + 9.0):
        for sx in (1, -1):
            led = led - cyl_z(sx * (CH_W / 2 + OB_WALL / 2), y, OB_Z1 - 1, OB_Z1 + 2, 1.5)
    led.label, led.color = "REF_led_board", Color(0.1, 0.4, 0.2)
    return [tft, usb, tact, bat, cuv, led]


def build_all():
    return {
        "rear": build_rear(), "front": build_front(), "door": build_door(), "button": build_button(),
        "lens": build_lens(), "overlay": build_overlay(), "pcb": build_pcb(), "optical": build_optical_block(), "tray": build_tray(),
    }
