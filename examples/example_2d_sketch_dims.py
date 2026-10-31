# Worked example - 2D exercise "Shape A" (verified: every dimension reads back exactly)
#
# Drawing: base 24 (point A at the left end), left edge rises at 50 deg to a height of 7,
# top-left edge is an arc: chord 20, sweep 40 deg (curving in toward the part),
# a diagonal 24 long runs from the top corner T back to the base's right end C,
# the right edge leaves C at 106 deg and meets a horizontal top line through T at Q.
#
# LEDGER
# | text | meaning                                  | used by              |
# | 24   | base A..C                                | C = (24, 0)          |
# | 7    | height of the arc's lower end P1         | P1.y = 7             |
# | 50°  | left edge angle to the base              | P1.x = -7/tan50      |
# | 20   | arc chord P1..T                          | T (circle-circle)    |
# | 40°  | arc sweep                                | R = 10/sin20         |
# | 24   | diagonal T..C                            | T (circle-circle)    |
# | 106° | right edge angle at C                    | Q                    |
#
# Run as ONE script after a separate fz.new_design() script.
import sys, importlib, math
sys.path.insert(0, r'C:\Users\2263171\.claude\skills\skillfusion')
import fz; importlib.reload(fz)


def run(_context):
    # ---- derived points (write the arithmetic, never guess)
    A, C = (0.0, 0.0), (24.0, 0.0)
    P1 = (-7 / math.tan(math.radians(50)), 7.0)
    dx, dy = C[0] - P1[0], C[1] - P1[1]                  # T is 20 from P1 and 24 from C
    d = math.hypot(dx, dy)
    a = (20 ** 2 - 24 ** 2 + d * d) / (2 * d)
    h = math.sqrt(20 ** 2 - a * a)
    T = (P1[0] + a * dx / d - h * dy / d, P1[1] + a * dy / d + h * dx / d)   # the upper intersection
    Q = (24 + T[1] / math.tan(math.radians(106)), T[1])
    R = 10 / math.sin(math.radians(20))                  # chord 20, sweep 40 -> R = 29.238
    ux, uy = (T[0] - P1[0]) / 20, (T[1] - P1[1]) / 20     # unit vector P1 -> T
    nx, ny = -uy, ux                                     # normal pointing away from the part
    mid = ((P1[0] + T[0]) / 2, (P1[1] + T[1]) / 2)
    cen = (mid[0] + R * math.cos(math.radians(20)) * nx, mid[1] + R * math.cos(math.radians(20)) * ny)
    arc_mid = (cen[0] - R * nx, cen[1] - R * ny)         # the arc curves in toward the part

    # ---- geometry (points with equal coordinates join automatically)
    s = fz.sketch('Shape A')
    s.line(A, C)
    s.line(C, Q)
    s.line(Q, T)
    s.line(T, C)
    s.line(A, P1)
    s.arc3(P1, arc_mid, T)
    s.line(A, (-9, 0), construction=True)                # extension line for the 50 deg angle
    s.line(C, (33, 0), construction=True)                # extension line for the 106 deg angle
    s.line(cen, P1, construction=True)                   # radii for the 40 deg sweep
    s.line(cen, T, construction=True)

    # ---- dimensions placed like the drawing
    s.dim(A, C, 'h', (12, -4))
    s.dim(P1, A, 'v', (-9, 3.5))
    s.dim_angle((-5, 0), ((A[0] + P1[0]) / 2, (A[1] + P1[1]) / 2), (-5.5, 2.2))
    s.dim(P1, T, 'a', (mid[0] + 7.5 * nx, mid[1] + 7.5 * ny))
    s.dim_angle(((cen[0] + P1[0]) / 2, (cen[1] + P1[1]) / 2), ((cen[0] + T[0]) / 2, (cen[1] + T[1]) / 2),
                (mid[0] + 1.2 * nx, mid[1] + 1.2 * ny))
    s.dim(T, C, 'a', ((T[0] + 24) / 2 + 8 * T[1] / 24, T[1] / 2 + 8 * (24 - T[0]) / 24))
    s.dim_angle((30, 0), ((C[0] + Q[0]) / 2, (C[1] + Q[1]) / 2),
                (24 + 5 * math.cos(math.radians(50)), 5 * math.sin(math.radians(50))))
    s.dims()          # expect 24, 7, 50, 20, 40, 24, 106
    print('profiles:', s.sk.profiles.count, '(expect 2: area A and the white triangle)')
    fz.view('top')
