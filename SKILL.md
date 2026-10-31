---
name: skillfusion
description: Turn an engineering drawing or picture (2D exercise, "3D DRAWING EXERCISE" sheet with front/top/side/section views, a logo or outline to colour) into an exact Autodesk Fusion model through the Fusion MCP tools (mcp__fusion__*). Use whenever the user says skillfusion, or gives a drawing/picture and asks to make, model, build, draw, dimension, colour or check it in Fusion. Provides a step-by-step drawing-reading method, a tested helper library (fz.py) that hides the Fusion API, and a verification loop, so even a small model gets the geometry exactly right.
---

# skillfusion - drawing -> exact Fusion model

You will (1) read the drawing into a written list of dimensions, (2) plan the part as a
short list of simple features, (3) build them with the tested helper `fz`, (4) prove the
model is right with numbers and screenshots, (5) report. Do the steps in order. Do not skip
the written parts: they are what makes the model correct.

Skill folder `C:\Users\2263171\.claude\skills\skillfusion\` (always use these full paths):
- `fz.py` - helper library used by every Fusion script (tested; do not edit it during a task)
- `drawtool.py` - zoom/grid/measure tool for drawing images
- `reference\drawings.md` - how to read drawings. READ IT before Step 1 every time.
- `reference\recipes.md` - fz code for common features + volume formulas. READ IT before Step 2.
- `examples\example_3d_161.md` - a complete worked 3D exercise (ledger, plan, scripts, checks)
- `examples\example_2d_sketch_dims.py` - a complete 2D sketch with dimensions

## 0. Rules (never break these)

1. One drawing = one NEW design tab. Make it with a script that contains ONLY `fz.new_design()`.
   Never change, close or save other documents. Never save unless the user says "save".
   fz remembers that tab: if the user clicks another tab between your scripts, fz switches back and
   prints `!! another tab was active`. To change an EXISTING design instead (the user asks you to
   fix/check the model in a tab), make sure that tab is active and run `fz.use_active()` first.
2. No tutorial / step-by-step pictures unless the user asks for one.
3. Never invent a size. Every number on the drawing must be used somewhere. A size that has
   no number must be DERIVED (sums, differences, symmetry, tangency, trigonometry) and you must
   write down how. Pixel measuring is the last resort and must be said in the final reply.
4. Small scripts: 1-4 features per script. Read every printed line before the next script.
5. A line containing `!!`, a wrong dV, or a failed probe means STOP and fix it
   (`fz.rollback(step)`) before you build anything else.
6. Never say "done" before every check in Step 4 has passed. If something is uncertain, say so.
7. Never put try/except in a script. An error message is how you learn what went wrong.

## 1. Tools - exact call shapes

If the `mcp__fusion__*` tools are not loaded yet, first call ToolSearch with query
`select:mcp__fusion__fusion_mcp_execute,mcp__fusion__fusion_mcp_read,mcp__fusion__fusion_mcp_update`.

Check that Fusion answers: `mcp__fusion__fusion_mcp_read` with
`{"queryType": "document", "operation": "open"}`. If that fails, tell the user to start Fusion and
switch on Preferences > General > API > "Fusion MCP Server" (基本設定 > 一般 > API).

Run a script - `mcp__fusion__fusion_mcp_execute`:
```json
{"featureType": "script", "object": {"script": "<the python text>"}}
```
Add `"readOnly": true` inside `object` for scripts that only look (report/probe/timeline).

Screenshot - `mcp__fusion__fusion_mcp_read`:
```json
{"queryType": "screenshot", "direction": "current", "width": 1000, "height": 700}
```
Always aim the camera with `fz.view(...)` first, then use `"direction": "current"`.

EVERY script has this exact shape (copy it):
```python
import sys, importlib
sys.path.insert(0, r'C:\Users\2263171\.claude\skills\skillfusion')
import fz; importlib.reload(fz)

def run(_context):
    fz.box(0, 0, 0, 40, 30, 20, name='base')
```

Facts about scripts:
- If a script raises an error, Fusion undoes EVERYTHING that script did in the active design.
  Fix the script and run it again. (Exception: a new tab from `fz.new_design()` stays - that is
  why new_design runs alone.)
- Output = what the script prints. fz prints one line per feature:
  `[steps 3-5] extrude 'slot' cut dV=-512.000 V=23488.000 mm3 bodies=1`
  `steps` are timeline numbers (for `fz.rollback`), `dV` = volume change of this feature.

## 2. Workflow

### Step 1 - READ (write it in your reply text, before any Fusion modelling)
1. Read `C:\Users\2263171\.claude\skills\skillfusion\reference\drawings.md` and
   `C:\Users\2263171\.claude\skills\skillfusion\examples\example_3d_161.md` (shows exactly what your
   ledger, plan and scripts should look like).
2. Look at the image (Read tool). If any number or small feature is hard to read, zoom:
   `python "C:\Users\2263171\.claude\skills\skillfusion\drawtool.py" crop IMG x0 y0 x1 y1 OUT.png 3`
   then Read OUT.png. (`grid IMG OUT.png 100` puts pixel coordinates over the whole sheet.)
   Save OUT files in your scratchpad directory.
3. Write the VIEWS line: which view is front / top / right / section, the projection
   (Japanese/Korean school drawings = third angle: top view ABOVE front, right view RIGHT of front),
   and the scale notes (a section can have its own SCALE).
4. Choose the world origin and write it (e.g. "x=0 left face, y=0 front face, z=0 bottom";
   round parts: main axis on a world axis through 0).
5. Write the LEDGER - one row for EVERY number on the sheet:

   | # | text | view | what it measures (from -> to) | world value | used by |
   |---|------|------|--------------------------------|-------------|---------|
   | 1 | 64 | top | overall width | x -32..32 | F1 |
   | 2 | 2 X 45° | section | chamfer on both ends of bore | 2 mm | F7 |
   | 3 | (12) | top | reference = 50-38 (check only) | - | check |

6. Under the table, write DERIVED sizes with their arithmetic, e.g.
   `slot centre x = 10 + 7.5/2 = 13.75` ; `edge run = 20 / tan60 = 11.547`.
7. Match features between views (front<->top share x, front<->right share z, top<->right share y).
   Every visible line, hidden (dashed) line and circle in every view must be explained by some
   feature. Write one line per feature: what it is and in which views you see it.

### Step 2 - PLAN
1. Read `C:\Users\2263171\.claude\skills\skillfusion\reference\recipes.md`.
2. Feature list, in build order. Normally: overall block or main cylinder first, then joins, then
   cuts, then holes, then fillets/chamfers last. For each feature write: the fz call (plane, points,
   at/to) and the EXPECTED dV (compute with python in Bash: area x length, pi r^2 h, ...).
   Leave expected dV as "?" only for fillets/lofts where no formula is easy.
3. Write the expected final volume (sum) and the overall size (x, y, z extents).
4. Write 6-10 PROBE points: points that must be material and points that must be empty
   (inside holes, slots, cut-off corners). Keep each point at least 0.5 mm away from any face.

### Step 3 - BUILD
1. Script 1: only `fz.new_design()`.
2. Then scripts with 1-4 features each (template above). After each script compare every printed
   dV with your plan. Same within 0.1% -> continue. Different -> the feature is in the wrong place,
   wrong size or wrong direction: `fz.rollback(first_step_of_that_feature)` in a new script, fix,
   rebuild. dV=0 on a cut/join = it missed the body completely.
3. Use world coordinates exactly as in your ledger. Cutting tools must stick out at least 1 mm past
   the faces they cut through (e.g. a through hole from y=-1 to y=depth+1).

### Step 4 - CHECK (all must pass)
1. `fz.report(expect_volume=..., expect_size=(dx, dy, dz))` -> must print `VOLUME OK` and
   `SIZE OK`, and no `TIMELINE PROBLEM` / `TIMELINE ROLLED BACK` line. Check the cylinder list: every diameter on the drawing appears,
   at the right position. Check the flat-face levels against your ledger.
2. `fz.probe(inside=[...], outside=[...])` -> `probe: 0 failed`.
3. Screenshots: for each drawing view run `fz.view('front')` (then 'top', 'right', ...) and take the
   screenshot. Compare with that view on the drawing, line by line: outline, steps, slopes, holes,
   positions. Hidden (dashed) features will not show - check them with probes instead.
4. If the volume is wrong but the shape looks right, your hand calculation may be wrong: re-check
   BOTH, feature by feature (the dV lines tell you which feature differs). Do not "adjust" sizes to
   force a match - every size must come from the ledger.
5. Lofts (and other freeform faces): Fusion's volume of such a body is only exact to about 0.01%,
   so `report` then uses a 0.01% tolerance (it says so on the VOLUME line). For a loft joined to
   other solids, the expected volume needs the overlap - compute it by numerical integration of the
   cross-section areas in python (Simpson's rule), as recipes.md section H describes.

### Step 5 - FINISH
1. Colour: if the sheet has a coloured picture of the part, copy its colour:
   `python "C:\Users\2263171\.claude\skills\skillfusion\drawtool.py" color IMG X Y` on a mid-tone
   area of the part, then `fz.color((r, g, b))`.
   No coloured picture -> leave the default.
2. `fz.view('iso')` (or 'iso-left' if the drawing's picture is seen from the left) + screenshot.
3. FINAL CHECK = the very last Fusion call: a script with `fz.report(expect_volume=..., expect_size=...)`.
   Copy its `VOLUME` and `SIZE` lines into the reply exactly as printed (never retype numbers from
   earlier output). If it prints `TIMELINE ROLLED BACK`, run `fz.timeline_end()` and report again.
4. Reply to the user: what you built (feature list), the checks (volume, size, probes, views),
   every assumption or pixel-measured value, and that the design tab is unsaved.

## 3. fz reference (mm, degrees, world coordinates, Z up)

Planes and their 2D coordinates (u, v):

| plane | u | v | normal axis (`at`, `to`) | drawing view that shows true shapes |
|-------|---|---|--------------------------|-------------------------------------|
| `'xy'` | x | y | z | TOP view |
| `'xz'` | x | z | y | FRONT view |
| `'yz'` | y | z | x | RIGHT (side) view |

Shapes (2D, in plane coordinates):
- `fz.rect(u0, v0, u1, v1)` - rectangle by two corners
- `fz.circle(cu, cv, r=..)` or `d=..`
- `fz.slot(u0, v0, u1, v1, r)` - stadium/U-slot; (u0,v0),(u1,v1) = centres of the two end arcs
- `fz.ellipse(cu, cv, ru, rv)` - semi-axis ru along u, rv along v
- `fz.poly([(u, v), (u, v), ('arc', (u_mid, v_mid), (u_end, v_end)), ...])` - closed outline;
  an `'arc'` item goes from the previous point through mid to end. Closes itself.
- `fz.polar((cu, cv), r, angle_deg)` -> point on a circle (handy for arc mid points)

Solids (op = `'new'` | `'join'` | `'cut'` | `'intersect'`; `name=` labels the feature/body):
- `fz.box(x0, y0, z0, x1, y1, z1, op)` - block between two corners
- `fz.cyl((x, y, z), axis, d=, h=, op=)` - cylinder; base centre (x,y,z), runs h along +axis (h<0: -axis)
- `fz.extrude(shapes, plane, at, to, op)` - prism of the shape(s) from `at` to `to` on the normal axis.
  A list of shapes is extruded together (their union).
- `fz.revolve(shapes, plane, axis, angle=360, op=)` - axis = `'x'|'y'|'z'` lying in the plane,
  or two plane points `((u0, v0), (u1, v1))` for an axis that is not a world axis
- `fz.loft([(shape, plane, at), (shape, plane, at)], op)` - ruled solid between outlines
- `fz.pyramid(shape, plane, at, (x, y, z), op='cut')` - from an outline to one apex point
  (oblique corner cuts, tetrahedra)
- `fz.holes_on_circle((x, y, z), axis, pcd=, n=, d=, h=, start=0)` - bolt circle holes (cut)
- `fz.fillet([(x, y, z), ...], r)` / `fz.chamfer([(x, y, z), ...], d)` - each point lies ON an edge
  (e.g. the middle of a straight edge, or `(cx + r, cy, z_top)` for a hole's top edge)

Checks and tools:
- `fz.report(expect_volume=None, expect_size=None)` - volume, size, cylinders, flat-face levels, problems
- `fz.probe(inside=[pts], outside=[pts])`
- `fz.timeline()`, `fz.rollback(step)` - list steps / delete step `step` and everything after it
- `fz.timeline_end()` - if the timeline marker was dragged back (report says ROLLED BACK), make all steps active again
- `fz.volume()`, `fz.body(name)`, `fz.color((r, g, b), body_name=None)`
- `fz.view(name)` - 'front', 'top', 'right', 'left', 'back', 'bottom', 'iso', 'iso-left', 'iso-back'
- 2D sketches with dimensions: `fz.sketch(...)`, `fz.bodies_to_sketch(...)` - see section 5

## 4. The five mistakes small models make (check yourself)

1. Wrong view axis. In the RIGHT view the paper's left edge is the FRONT face (y=0) and paper-right
   is +y (toward the back). In the TOP view paper-up is +y (toward the back); the edge next to the
   front view is the front face. Write u, v for every point from these rules.
2. A feature placed from one view only. Every feature needs its size/position from at least two
   views (e.g. a slot: shape in the top view, depth in the front or side view).
3. Unused or guessed numbers. Every ledger row must end with a "used by". An unused number means a
   missing or wrong feature.
4. Ignoring a dV mismatch "because the picture looks right". A mismatch is always a real error.
5. Section views: hatched = solid material cut by the plane; white inside the outline = holes or
   cavities. Read bores, counterbores and internal pockets from the section, not from guesses.

## 5. 2D exercises (outline drawings, logos, "color it like pic")

- Default output: ONE sketch at the origin on the XY plane with the finished outline only (no text),
  plus sketch dimensions placed like the drawing, every one reading back exactly (`s.dims()`).
- Direct sketch: `s = fz.sketch('Name')`, then `s.draw(fz.poly([...]))`, `s.line(a, b)`,
  `s.circle(c, r=)`, `s.arc3(a, mid, b)`, construction lines with `construction=True`.
  Points with the same coordinates are joined automatically.
- Dimensions (points are (u, v) in mm; `text` = where the number goes):
  `s.dim(a, b, 'h'|'v'|'a', text)` distance (h = along x, v = along y, a = aligned) between sketch points;
  `s.dim_d(on, text)` diameter, `s.dim_r(on, text)` radius of the circle/arc through point `on`;
  `s.dim_angle(on1, on2, text)` angle between lines through on1 and on2 (text picks which angle);
  `s.dim_offset(on1, on2, text)` distance between parallel lines; `s.dims()` prints all values.
- Outlines made of overlapping shapes (logos, rings, letters): build thin bodies (extrude 1 mm with
  `op='new'`, then `'join'`/`'cut'` other 1 mm shapes), then `c = fz.bodies_to_sketch('Name')` makes a
  clean sketch of the final outline and deletes the helper bodies; dimension it with `c.dim...`.
  Overlap joined pieces by 1 mm (touching only along an edge leaves a seam line).
- "Colour it like the picture": keep separate bodies per colour (`op='new'`, thin, stacked 0.1 mm
  apart if they overlap) and `fz.color((r, g, b), body_name)` each one.
- Outline drawings with a thick line (e.g. mascot outlines): radii are to the OUTER edge of the line;
  the line thickness goes inward.
- See `examples/example_2d_sketch_dims.py`.

## 6. Troubleshooting

| symptom | cause / fix |
|---------|-------------|
| `name 'run' is not defined` | the script has no `def run(_context):` |
| `No active Fusion design` | run `fz.new_design()` first (alone) |
| `design this job made ... is not open any more` | the user closed your tab: ask them, or `fz.use_active()` on the right tab |
| `the shape made no closed area` | outline does not close or crosses itself; check point order |
| `dV=0` on cut/join | tool is not touching the body: wrong `at`/`to`, wrong plane, wrong sign |
| dV too big / too small | tool too long, wrong side, overlaps another feature - re-derive points |
| `no edge passes through` | the fillet/chamfer point is not exactly on an edge; compute it again |
| revolve error | profile crosses the axis, or the axis is not in the plane |
| `!! FEATURE PROBLEM` | read the message; usually zero-thickness or self-touching geometry: move tools 1 mm |
| screenshot shows nothing useful | run `fz.view('iso')` (it fits the view) and screenshot again |
| a probe says ON-SURFACE | move that probe point 0.5 mm off the face |
