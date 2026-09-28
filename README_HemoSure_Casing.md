# HemoSure Hb meter casing (Levram) - Rev A, 28 Sep 2026 (DRAFT for DFM review)

Everything is generated from `cad/hemosure_casing.py` (parameters at the top). To change anything, edit a
parameter and re-run:

    V=".../text-to-cad/.venv/bin/python"
    $V .claude/skills/cad/scripts/step cad/HemoSure_*.py mold/HemoSure_*_{CORE,CAVITY}.py   # STEP files
    $V cad/tolerance_stack.py     # 15 stack-ups (WC + RSS)
    $V cad/dfm_checks.py          # draft check
    (mold check block in mold/hemosure_mold.py -> mold/mold_check_report.json)
    $V cad/make_drawings.py       # drawings/HemoSure_Casing_Drawings_(Levram).pdf (10 sheets)

## Contents
- cad/     part STEPs (HS-101 front, HS-102 rear, HS-103 door, HS-104 button, HS-105 optical block,
           HS-201 lens, HS-202 overlay), assembly + exploded STEP
- mold/    core + cavity insert STEPs for all 5 moulded parts (steel size, ABS shrink 0.5 % applied)
- drawings/ article drawings, tolerance/stack-up sheet, mould layout Tool A (front+rear+door family)
           and Tool B (button+optical block, black), DFM report
- renders/ verification snapshots

## Key design decisions
- 62 x 122 x 22 mm, ABS 2.0 wall; parting plane at z 14.2 = USB-C centre, so USB-C and cuvette mouth
  split half/half: NO slides or lifters in any tool (verified: 0 mm3 undercut on all parts).
- Optical cell is a separate BLACK ABS block (white ABS leaks light).
- Colour variants = printed overlay only; one tool set.

## Open items to confirm (assumptions in the model)
PCB component heights (<= 3 mm under, TFT FPC), USB-C 3.0 mm overhang past PCB top edge, tact switch at
(0,-8) 6x6x5.0, PCB thickness spec 1.6 +/-0.10, cuvette 14.0 x 3.0, LiPo 503035, TFT module drawing,
whether the edge "8 mm" features on the PCB outline are tabs or notches (envelope 76.75 x 49.94 used).

## 3D view in the browser
Open any file in `stl/` on GitHub for an interactive 3D view (drag to rotate, scroll to zoom):
`stl/HemoSure_Assembly.stl`, `stl/HemoSure_Exploded.stl`, individual parts, and `*_CORE` / `*_CAVITY` mould inserts.
Regenerate with `cad/export_stl.py` logic (import STEP -> export_stl, tol 0.02).
