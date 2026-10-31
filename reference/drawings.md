# Reading engineering drawings (for skillfusion)

## 1. Which view is which

Japanese (JIS), Korean (KS) and US school drawings use THIRD-ANGLE projection:

```
            +-----------+
            |  TOP view |        <- looking down on the part
            +-----------+
+---------+ +-----------+ +-----------+
|  LEFT   | |   FRONT   | |   RIGHT   |
+---------+ +-----------+ +-----------+
            +-----------+
            |  BOTTOM   |        <- looking up at the part
            +-----------+
```
Each side view shows the side of the part that faces it. First-angle (ISO-E) drawings swap them
(top view below the front, right view on the left). If unsure, check one distinctive feature in
both views.

The FRONT view is the view with the most dimensions, usually lower-left. A pictorial
(isometric, often coloured) picture is for understanding only - never measure on it.

## 2. View -> world axes (fz uses Z up, y = 0 at the FRONT face)

| drawing view | paper -> (right) | paper ^ (up) | depth (into the paper) | fz plane, (u, v) |
|--------------|------------------|--------------|------------------------|------------------|
| FRONT  | +x | +z | +y (front face is nearest) | `'xz'`, (x, z) |
| TOP    | +x | +y (toward the BACK; the edge next to the front view is the front face y=0) | -z | `'xy'`, (x, y) |
| RIGHT  | +y (the paper's LEFT edge is the front face y=0) | +z | -x | `'yz'`, (y, z) |
| LEFT   | -y (the paper's RIGHT edge is the front face) | +z | +x | `'yz'`, (y, z) |
| BOTTOM | +x | -y (the edge next to the front view is the front face) | +z | `'xy'`, (x, y) |
| BACK   | -x | +z | -y | `'xz'`, (x, z) |

To turn a point on the paper into (u, v): measure it from the view's reference edges in mm (using
the dimensions), then apply the table. Example, RIGHT view: u = y = distance from the paper-left edge,
v = z = height above the bottom edge.

Sharing rule: FRONT and TOP have the same x; FRONT and RIGHT have the same z; TOP and RIGHT have the
same y. A line at height z in the front view and a line at the same height in the right view are
usually the same edge/face. Use this to find where a feature is when only one view dimensions it.

Rotated views: a view may be turned 90 degrees to fit the sheet (the tee 163 shows its side view lying
down). Find a feature you know (a flange, a hole) to see how it is turned.

## 3. Lines

| line | meaning |
|------|---------|
| thick solid | visible edge or outline |
| dashed (hidden) | edge behind material: holes, slots, pockets, back faces |
| dash-dot (thin) | centre line / axis of a hole or cylinder / symmetry line; cutting plane in other views |
| thin solid with arrows | dimension line; the thin lines it ends on are extension lines from the feature |
| hatching (parallel thin lines) | in a SECTION: the solid material that the cutting plane cut through |

A cylinder seen from the side is a rectangle with a centre line; its diameter is written on the
rectangle (⌀). A hole seen from the side is two dashed lines with a centre line.

## 4. Symbols

| symbol | meaning |
|--------|---------|
| ⌀30 | diameter 30 (r = 15) |
| R8 | radius 8 (fillet, rounded end, arc) |
| SR | sphere radius |
| C2, 2 X 45° | 45-degree chamfer 2 mm (a "2 X 45°" leader pointing at a bore edge = chamfer that edge) |
| 4X ⌀15, 4-⌀15 | four holes ⌀15 |
| PCD 120, ⌀120 dash-dot circle | pitch (bolt) circle: holes are centred on it |
| (9.5) | reference dimension: it follows from other numbers. Use it as a CHECK |
| □20 | square 20 x 20 |
| t5 | thickness 5 |
| THRU | through all |
| ⌴ / ⌵ | counterbore / countersink |
| 60° with an arc | angle between the two lines the arc ends on (measure which lines carefully) |
| SECTION A-A | view of the part cut along the line A-A (marked with arrows in another view) |
| SCALE 2:1.6 | this view is drawn at a different scale - never compare its pixel sizes with other views |

## 5. Sections

- The cutting line (dash-dot with letters and arrows) shows where the cut is; the arrows show the
  viewing direction.
- Hatched area = material in the cutting plane. White area inside the outline = empty (bore, pocket,
  groove) or a surface behind the plane.
- Sections are the place to read internal steps: counterbores, pockets wider than the hole above
  them, wall thickness, chamfers on bore edges.
- A small section drawn elsewhere (e.g. "SECTION B-B" showing an ellipse) gives the cross-section of
  an arm/rib at that place; its size there is a check for your loft.

## 6. When a size has no number

Derive it, in this order, and write the arithmetic in the ledger:
1. chain arithmetic: total minus the other parts (64 - 20 - 20 = 24);
2. symmetry about a centre line (a feature centred on the axis);
3. alignment with another view (same x/y/z as a feature that is dimensioned there);
4. tangency: a line tangent to a circle, an arc tangent to two lines; tangent lines between two
   circles r1, r2 at distance d touch at angle asin((r2 - r1) / d);
5. trigonometry: an edge at angle a rising h -> horizontal run h / tan(a);
6. radius from a chord and sweep: R = (chord / 2) / sin(sweep / 2);
7. LAST resort, pixels: `drawtool.py scan` to find exact line positions, `drawtool.py scale` from the
   longest dimension in the SAME view, then `drawtool.py mm`. Round to the drawing's style
   (0.5, 0.25 or 0.1 mm) and say in the reply that it was measured.

## 7. Consistency checks before you model

- Front width = top width; front height = right height; top depth = right width.
- Every dashed line in a view is explained by a hole/slot/pocket/back face you can name.
- Every arc / circle in a view is a cylinder, hole, fillet or rounded end you can name, and you know
  its axis direction (a circle in the TOP view = axis z; FRONT view = axis y; RIGHT view = axis x).
- Every sloped line in a view is either an inclined face (seen edge-on: it is a line in this view and
  an area in the others) or an edge of an inclined face.
- A triangle-shaped face that is sloped in two views is an oblique plane through 3 corners:
  build it with `fz.pyramid` (see recipes).
