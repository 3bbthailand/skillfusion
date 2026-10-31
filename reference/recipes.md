# fz recipes (all tested patterns)

Origin: prismatic parts -> x = 0 left face, y = 0 FRONT face, z = 0 bottom face.
Round parts -> the main axis on a world axis through (0, 0, 0) (vertical: z; horizontal: x).
L = length in x, W = depth in y, H = height in z.

## A. Blocks and steps

```python
fz.box(0, 0, 0, L, W, H, name='base')                                   # base block
fz.box(x0, y0, z0, x1, y1, z1, op='join', name='rib')                    # add a block
fz.extrude(fz.rect(x0, z0, x1, H + 1), 'xz', -1, W + 1, 'cut', name='notch')   # notch seen in FRONT view, through y
fz.extrude(fz.rect(x0, y0, x1, y1), 'xy', z0, H + 1, 'cut', name='pocket')    # pocket seen in TOP view, from z0 up
fz.extrude(fz.rect(y0, z0, y1, H + 1), 'yz', -1, L + 1, 'cut', name='step')   # step seen in RIGHT view, through x
fz.extrude(fz.poly([(0, 0), (10, 0), (30, 40), (0, 40)]), 'xy', 10, 20, 'join', name='raised part')  # any top-view outline raised from z=10 to 20
```

## B. Inclined faces (a straight line in one view, an area in the others)

Cut everything on one side of the line with a polygon in THAT view's plane. Extend the line 1 mm
past the part with the same slope, then close the polygon around the waste side:
```python
# RIGHT view: line from (y=0, z=8) to (y=30, z=24) on a block H=24; material above it removed for x 0..15
m = (24 - 8) / 30
fz.extrude(fz.poly([(-1, 8 - m), (30, 24), (30, 25), (-1, 25)]), 'yz', -1, 15, 'cut', name='slope')
# FRONT view 45-degree chamfer of the top-left edge, size 5, through the whole depth
fz.extrude(fz.poly([(-1, H - 6), (6, H + 1), (-1, H + 1)]), 'xz', -1, W + 1, 'cut', name='C5')
```
A 45-degree chamfer of one straight edge can also be `fz.chamfer([point_in_middle_of_edge], d)`.

## C. Oblique corner cut (a triangle face that looks sloped in two views)

The cut-off piece is a tetrahedron: a corner K of the block plus one point on each of the three
edges that meet at K (P1, P2 on the face that holds K, P3 on the third edge). Use the triangle
K-P1-P2 on its face plane and P3 as the apex:
```python
# block corner K = (60, 40, 15) on the top face z = 15; P1 = (40, 40, 15), P2 = (60, 0, 15); P3 = (60, 40, 0)
fz.pyramid(fz.poly([(60, 40), (40, 40), (60, 0)]), 'xy', 15, (60, 40, 0), op='cut', name='corner cut')
```
Expected dV = -(triangle area x height) / 3.

## D. Holes

```python
fz.cyl((x, y, -1), 'z', d=D, h=H + 2, op='cut', name='hole')      # through, along z (circle in TOP view)
fz.cyl((x, -1, z), 'y', d=D, h=W + 2, op='cut', name='hole')      # through, along y (circle in FRONT view)
fz.cyl((-1, y, z), 'x', d=D, h=L + 2, op='cut', name='hole')      # through, along x (circle in RIGHT view)
fz.cyl((x, y, H + 1), 'z', d=D, h=-(t + 1), op='cut', name='blind hole t deep')
# counterbore: big shallow cut + small through cut
fz.cyl((x, y, H + 1), 'z', d=D2, h=-(t2 + 1), op='cut', name='counterbore')
fz.cyl((x, y, -1), 'z', d=D1, h=H + 2, op='cut', name='hole')
# countersink to diameter Dc on a hole of diameter D: chamfer its top edge by (Dc - D) / 2
fz.chamfer([(x + D / 2, y, H)], (Dc - D) / 2, name='countersink')
# bolt circle: 4 holes d15 on pitch circle 120, through a flange 10 thick lying in z 0..10
fz.holes_on_circle((cx, cy, -1), 'z', pcd=120, n=4, d=15, h=12, start=0, name='bolt holes')
#   start = angle of the first hole from +u toward +v (axis z: u=x v=y; axis x: u=y v=z; axis y: u=x v=z)
# U-slot open to the back face y = W, round end centre at (xc, yc), radius r, floor at z0
fz.extrude(fz.slot(xc, yc, xc, W + 10, r), 'xy', z0, H + 1, 'cut', name='U slot')
```

## E. Round parts: revolve the HALF section

Trace one side of the axis as a closed outline. u = radius (>= 0), v = position along the axis.
Start and end on the axis. Bores the same way with op='cut', 1 mm past both ends.
```python
fz.revolve(fz.poly([(0, 17), (15, 17), (15, 53), (21, 53), (21, 58), (0, 58)]), 'xz', 'z', op='join', name='boss + flange')
fz.revolve(fz.poly([(0, -1), (6, -1), (6, 28), (11, 28), (11, 53), (6, 53), (6, 59), (0, 59)]), 'xz', 'z', op='cut', name='bore')
# a shaft lying along x: points (x, r) on plane 'xz', axis 'x'
fz.revolve(fz.poly([(0, 0), (0, 10), (40, 10), (40, 6), (60, 6), (60, 0)]), 'xz', 'x', name='shaft')
```

## F. Fillets, rounded corners, chamfers (do these LAST)

```python
fz.fillet([(0, 0, H / 2)], 8, name='R8')                  # vertical edge at the front-left corner (an R in the TOP view)
fz.fillet([(L / 2, 0, H)], 3, name='R3 top front edge')   # edge along x
fz.chamfer([(xc + D / 2, yc, H), (xc + D / 2, yc, 0)], 2, name='2x45 both ends')   # both circular edges of a hole
```
The point must lie exactly ON the edge (on a circle edge: centre + radius along one axis, at the
face height). Several points = several edges in one feature.

## G. Pipes, tees, crossing cylinders, flanges

```python
fz.cyl((-92, 0, 0), 'x', d=60, h=184, name='main pipe')           # OD along x, between the flanges
fz.cyl((-100, 0, 0), 'x', d=110, h=8, op='join', name='flange L') # flanges at the ends (x -100..-92)
fz.cyl((0, 0, 0), 'z', d=60, h=-112, op='join', name='branch')    # branch from the main AXIS downward
fz.cyl((-101, 0, 0), 'x', d=44, h=202, op='cut', name='main bore')
fz.cyl((0, 0, 0), 'z', d=44, h=-121, op='cut', name='branch bore')
```
A branch length dimensioned from the main pipe's SURFACE must be converted to the axis: + OD/2.
Joins of equal crossing cylinders overlap by 8 r^3 / 3 (see formulas) - use it in the expected dV.

## H. Arms between two bosses (levers, links)

Bosses first (`fz.cyl`, join). The arm is usually a loft between two cross-sections perpendicular
to the arm (ellipse if a section view shows an ellipse, rectangle if it shows a rectangle):
```python
fz.loft([(fz.ellipse(0, 0, w1, h1), 'yz', x1), (fz.ellipse(0, 0, w2, h2), 'yz', x2)], op='join', name='arm')
```
- w = half width (from the TOP view), h = half height (from the FRONT/section view), at planes x1, x2.
- If the top-view outline lines are TANGENT to the boss circles (radius r1 at x = 0, r2 at x = d):
  s = (r2 - r1) / d; the tangent points are at x1 = -r1 * s and x2 = d - r2 * s, with half widths
  w1 = r1 * sqrt(1 - s^2), w2 = r2 * sqrt(1 - s^2). Put the loft sections there.
- Heights are often dimensioned where the arm meets the boss faces (x = r1 and x = d - r2):
  interpolate/extrapolate linearly to x1 and x2.
- Then cut the bores, then chamfer the bore edges. Probe the arm at the section-view position.
- Expected dV of the arm join = arm volume minus its overlap with each boss. Arm volume (ellipse
  half-axes a, b changing linearly over length L): `pi*L*(a1*b1 + (a1*(b2-b1) + b1*(a2-a1))/2 + (a2-a1)*(b2-b1)/3)`.
  Overlap with a vertical boss (radius R, centre cx, taller than the arm there) by Simpson's rule:
```python
import math
def strip_area(A, B, c):            # area of ellipse y^2/A^2 + z^2/B^2 <= 1 with |y| <= c
    if c >= A: return math.pi * A * B
    if c <= 0: return 0.0
    return (B / A) * 2 * (c * math.sqrt(A * A - c * c) + A * A * math.asin(c / A))
def overlap(xa, xb, cx, R, a, b, n=20000):   # a(x), b(x) = half width / half height functions
    h = (xb - xa) / n; s = 0.0
    for i in range(n + 1):
        x = xa + i * h
        c = math.sqrt(max(0.0, R * R - (x - cx) ** 2))
        s += (1 if i in (0, n) else 4 if i % 2 else 2) * strip_area(a(x), b(x), c)
    return s * h / 3
# small boss: overlap(x1, cx1 + R1, cx1, R1, a, b); big boss: overlap(cx2 - R2, x2, cx2, R2, a, b)
```

## I. 2D outline from overlapping shapes (logos, rings, letters)

```python
fz.extrude(fz.circle(0, 0, r=50), 'xy', 0, 1, name='disk')
fz.extrude(fz.circle(0, 0, r=41.5), 'xy', -1, 2, 'cut', name='inner')
fz.extrude(fz.poly([(-20, -5), (20, -5), (0, 46)]), 'xy', 0, 1, 'join', name='triangle')   # tip overlaps the ring -> one body
c = fz.bodies_to_sketch('Logo')          # clean outline sketch; helper bodies are deleted
c.dim_d((50, 0), (60, 45)); c.dims()
```

## J. Expected-volume formulas (python in Bash)

```python
import math
pi = math.pi
area = lambda p: abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(p, p[1:] + p[:1]))) / 2   # polygon (shoelace)
prism    = area(pts) * length
cylinder = pi * r**2 * h
ring     = pi * (R**2 - r**2) * h
slot     = (2 * r * c + pi * r**2) * h            # c = distance between the two end centres
frustum  = pi * h / 3 * (R**2 + R * r + r**2)
pyramid  = base_area * h / 3                      # also a tetrahedron corner cut
edge_chamfer_straight = d**2 / 2 * L
edge_fillet_straight  = (1 - pi / 4) * r**2 * L    # 90-degree edge
bore_edge_chamfer     = pi * d**2 * (r + d / 3)    # d x 45 chamfer on a hole of radius r
tee_overlap           = 8 * r**3 / 3                # two equal cylinders radius r, branch ending on the main axis
circle_segment        = r**2 / 2 * (th - math.sin(th))   # th = sweep in radians
```
When a cut overlaps an earlier cut, only the NEW material counts - subtract the overlap or leave
the expected dV as "?" and rely on probes for that feature.
