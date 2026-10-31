# Worked example - 3D DRAWING EXERCISE 161 (verified: V = 86485.20 mm3)

Sheet: top view (upper left), front view (lower left), SECTION A-A (lower right, SCALE 2:1.6),
green isometric picture (upper right). Part: square base with a groove underneath, a round boss
with a flange on top, a stepped bore through the middle.

## Step 1 - READ

VIEWS: front = lower-left, top = above it (third angle), SECTION A-A = cut through the centre seen
from the front, drawn at its own scale (do not compare its pixel sizes with the other views).

ORIGIN: boss axis = z axis, base centred on it: x -32..32, y -32..32, base bottom z = 0.

LEDGER

| # | text | view | what it measures | world value | used by |
|---|------|------|------------------|-------------|---------|
| 1 | 64 | top | base width | x -32..32 | F1 |
| 2 | 64 | top | base depth | y -32..32 | F1 |
| 3 | 32 | top | boss centre from left edge | x = 0 | F3, F4 |
| 4 | 32 | top | boss centre from back edge | y = 0 | F3, F4 |
| 5 | ⌀12 | top | through hole | r 6 | F4 |
| 6 | ⌀42 | top + front | flange | r 21 | F3 |
| 7 | 18 | front | base height | z 0..18 | F1 |
| 8 | 20, 20 | front | groove: 20 from each side at the bottom | x -12..12 at z 0 | F2 |
| 9 | 15 | front | groove top width | x -7.5..7.5 at z 5 | F2 |
| 10 | 13 | front | groove top to base top | groove depth 18-13 = 5 | F2 |
| 11 | 35 | front | boss height above base | z 18..53 | F3 |
| 12 | 5 | front | flange thickness | z 53..58 | F3 |
| 13 | ⌀30 | section | boss outside | r 15 | F3 |
| 14 | ⌀22 | section | pocket inside the boss | r 11 | F4 |
| 15 | 25 | section | pocket depth from boss top (flange underside) | z 28..53 | F4 |
| 16 | ⌀12 | section | hole below the pocket and through the flange | r 6 | F4 |
| 17 | 15 | section | flange edge to hole edge: 21 - 6 = 15 (check) | - | check OK |
| 18 | 17 | section | boss to base edge: 32 - 15 = 17 (check) | - | check OK |
| 19 | 35, 18, 5, 5 | section | same as front view (check) | - | check OK |

DERIVED: groove slope = (12 - 7.5) / 5 = 0.9 per mm, so extended to z = -1 the bottom half-width
is 12.9. Hole through the flange = ⌀12 because in the section the hole edges above the pocket are
on the same vertical lines as the ⌀12 hole below it.

FEATURES (views where each one is seen):
- F1 base block (front, top)
- F2 trapezoid groove along y under the base (front: trapezoid; iso: notch; section: line at z 5)
- F3 boss ⌀30 + flange ⌀42 (front, top, section)
- F4 stepped bore ⌀12 / ⌀22 pocket / ⌀12 (top circle, section)

## Step 2 - PLAN

| F | call | expected dV |
|---|------|-------------|
| F1 | `fz.box(-32, -32, 0, 32, 32, 18)` | 64*64*18 = +73728 |
| F2 | `fz.extrude(fz.poly([(-12.9,-1),(12.9,-1),(7.5,5),(-7.5,5)]), 'xz', -33, 33, 'cut')` | -(24+15)/2*5*64 = -6240 |
| F3 | `fz.revolve(fz.poly([(0,17),(15,17),(15,53),(21,53),(21,58),(0,58)]), 'xz', 'z', op='join')` | pi*15^2*35 + pi*21^2*5 = +31667.25 (z 17..18 overlaps the base) |
| F4 | `fz.revolve(fz.poly([(0,-1),(6,-1),(6,28),(11,28),(11,53),(6,53),(6,59),(0,59)]), 'xz', 'z', op='cut')` | -(pi*36*23 + pi*121*25 + pi*36*5) = -12670.05 (below z 5 is already groove) |

Expected V = 86485.20, size 64 x 64 x 58.
PROBES inside: (20, 20, 9) base, (13, 0, 40) boss wall, (18, 0, 55) flange.
PROBES outside: (0, 0, 40) pocket, (0, 0, 10) hole, (0, 20, 2) groove, (25, 25, 30) beside the boss.

## Step 3 - BUILD (two scripts)

Script 1:
```python
import sys, importlib
sys.path.insert(0, r'C:\Users\2263171\.claude\skills\skillfusion')
import fz; importlib.reload(fz)

def run(_context):
    fz.new_design()
```

Script 2:
```python
import sys, importlib
sys.path.insert(0, r'C:\Users\2263171\.claude\skills\skillfusion')
import fz; importlib.reload(fz)

def run(_context):
    fz.box(-32, -32, 0, 32, 32, 18, name='161')
    fz.extrude(fz.poly([(-12.9, -1), (12.9, -1), (7.5, 5), (-7.5, 5)]), 'xz', -33, 33, 'cut', name='groove')
    fz.revolve(fz.poly([(0, 17), (15, 17), (15, 53), (21, 53), (21, 58), (0, 58)]), 'xz', 'z', op='join', name='boss + flange')
    fz.revolve(fz.poly([(0, -1), (6, -1), (6, 28), (11, 28), (11, 53), (6, 53), (6, 59), (0, 59)]), 'xz', 'z', op='cut', name='bore')
```
Printed dV values: +73728.000, -6240.000, +31667.254, -12670.043 -> all as planned (0.1%).

## Step 4 - CHECK
```python
def run(_context):
    fz.report(expect_volume=86485.20, expect_size=(64, 64, 58))
    fz.probe(inside=[(20, 20, 9), (13, 0, 40), (18, 0, 55)],
             outside=[(0, 0, 40), (0, 0, 10), (0, 20, 2), (25, 25, 30)])
```
(with the same three header lines). Then `fz.view('front')` + screenshot, `fz.view('top')` +
screenshot, compared with the drawing.

## Step 5 - FINISH
`python drawtool.py color IMG 1400 380` on the green picture -> `fz.color((40, 175, 75))`,
`fz.view('iso')`, screenshot, reply with the feature list, checks and "unsaved tab".
