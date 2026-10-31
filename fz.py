"""fz - small, tested helper layer over the Autodesk Fusion API (skillfusion skill).

Start EVERY Fusion MCP script with these lines:

    import sys, importlib
    sys.path.insert(0, r'C:\\Users\\2263171\\.claude\\skills\\skillfusion')
    import fz; importlib.reload(fz)

    def run(_context):
        ...fz calls...

Conventions
- Millimetres and degrees. WORLD coordinates. Z is up.
- A shape is drawn on a plane; its 2D points are (u, v):
      'xy' -> (u, v) = (x, y)    normal axis z   (drawing TOP view)
      'xz' -> (u, v) = (x, z)    normal axis y   (drawing FRONT view)
      'yz' -> (u, v) = (y, z)    normal axis x   (drawing RIGHT view)
  `at` / `to` are world positions on the normal axis.
- Every modelling call prints one line:
      [steps a-b] kind 'name' op  dV=change  V=total mm3  bodies=n
  dV=0 on a cut/join means it missed the body - fix it before going on.
"""
import math
import os
import time
import adsk.core
import adsk.fusion

MM = 0.1  # Fusion's internal length unit is the centimetre
PLANES = {'xy': ('x', 'y', 'z'), 'xz': ('x', 'z', 'y'), 'yz': ('y', 'z', 'x')}
_I = {'x': 0, 'y': 1, 'z': 2}
# The design this job works on is tagged with an attribute; its tag is kept in this file, so a
# user clicking another tab between scripts cannot make fz edit the wrong document.
_JOB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.current_job')


# ----------------------------------------------------------------- basics
def app():
    return adsk.core.Application.get()


def _tag_of(doc):
    if doc is None:
        return None
    des = adsk.fusion.Design.cast(doc.products.itemByProductType('DesignProductType'))
    if des is None:
        return None
    a = des.attributes.itemByName('skillfusion', 'job')
    return a.value if a else None


def _job_tag():
    try:
        with open(_JOB_FILE, encoding='utf-8') as f:
            return f.read().strip() or None
    except OSError:
        return None


def _set_job(des):
    tag = 'job-%d' % int(time.time() * 1000)
    des.attributes.add('skillfusion', 'job', tag)
    with open(_JOB_FILE, 'w', encoding='utf-8') as f:
        f.write(tag)


def _ensure_job():
    tag = _job_tag()
    a = app()
    if not tag or _tag_of(a.activeDocument) == tag:
        return
    for i in range(a.documents.count):
        doc = a.documents.item(i)
        if _tag_of(doc) == tag:
            doc.activate()
            print("!! another tab was active - switched back to this job's design")
            return
    raise RuntimeError("the design this job made with fz.new_design() is not open any more. "
                       "To work on the design that is active now, run fz.use_active() first.")


def design():
    _ensure_job()
    d = adsk.fusion.Design.cast(app().activeProduct)
    if d is None:
        raise RuntimeError('No active Fusion design. Call fz.new_design() first.')
    return d


def use_active():
    """Make the ACTIVE design the one fz works on (use it before changing an existing design
    that you did not create with fz.new_design in this job)."""
    d = adsk.fusion.Design.cast(app().activeProduct)
    if d is None:
        raise RuntimeError('the active document is not a Fusion design')
    _set_job(d)
    print('fz now works on the active design %r' % app().activeDocument.name)


def root():
    return design().rootComponent


def P(x, y, z=0.0):
    """World point in mm -> Fusion Point3D (cm)."""
    return adsk.core.Point3D.create(x * MM, y * MM, z * MM)


def V(mm):
    """Length in mm -> ValueInput."""
    return adsk.core.ValueInput.createByReal(mm * MM)


def deg(a):
    return adsk.core.ValueInput.createByString('%r deg' % float(a))


def xyz(plane, u, v, w=0.0):
    """(u, v) on `plane`, at position w on its normal axis -> world (x, y, z)."""
    a, b, c = PLANES[plane]
    d = {a: u, b: v, c: w}
    return (d['x'], d['y'], d['z'])


def polar(c, r, a_deg):
    """Point (u, v) at angle a_deg (0 = +u, 90 = +v) on a circle of radius r around c."""
    a = math.radians(a_deg)
    return (c[0] + r * math.cos(a), c[1] + r * math.sin(a))


def _bvol(b):
    # body.volume uses low accuracy: on lofted bodies it was 0.02% off; VeryHigh was within 1e-6.
    return b.getPhysicalProperties(adsk.fusion.CalculationAccuracy.VeryHighCalculationAccuracy).volume * 1000.0


def volume():
    """Total volume of all bodies in mm^3 (very high accuracy)."""
    return sum(_bvol(b) for b in root().bRepBodies)


def new_design():
    """Open a NEW empty design tab (unsaved) and make it active."""
    a = app()
    a.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    d = adsk.fusion.Design.cast(a.activeProduct)
    d.designType = adsk.fusion.DesignTypes.ParametricDesignType
    _set_job(d)
    zup = (a.preferences.generalPreferences.defaultModelingOrientation ==
           adsk.core.DefaultModelingOrientations.ZUpModelingOrientation)
    print('new design ready (unsaved tab), %s' % ('Z-up' if zup else 'Y-up preference (fz still uses world axes)'))


def body(name=None):
    """Body by name, or the first body when name is None."""
    bs = root().bRepBodies
    if bs.count == 0:
        raise RuntimeError('there is no body yet - the first solid needs op="new"')
    if name is None:
        return bs.item(0)
    b = bs.itemByName(name)
    if b is None:
        raise RuntimeError('no body named %r; bodies are %s' % (name, [x.name for x in bs]))
    return b


def _op(op):
    F = adsk.fusion.FeatureOperations
    ops = {'new': F.NewBodyFeatureOperation, 'join': F.JoinFeatureOperation,
           'cut': F.CutFeatureOperation, 'intersect': F.IntersectFeatureOperation}
    if op not in ops:
        raise RuntimeError("op must be 'new', 'join', 'cut' or 'intersect', not %r" % (op,))
    if op == 'join' and root().bRepBodies.count == 0:
        op = 'new'
    return ops[op]


def _participants(inp, op, body_name):
    if body_name is not None and op != 'new':
        inp.participantBodies = [body(body_name)]


def _tl():
    """Timeline length; first moves a rolled-back timeline marker to the end (new features would
    otherwise be inserted in the middle and the later ones stay inactive)."""
    tl = design().timeline
    if tl.markerPosition != tl.count:
        print('!! timeline marker was at %d of %d (rolled back) - moved to the end' % (tl.markerPosition, tl.count))
        tl.moveToEnd()
    return tl.count


def timeline_end():
    """Move a rolled-back timeline marker to the end so every feature is active."""
    tl = design().timeline
    print('timeline marker %d of %d -> end' % (tl.markerPosition, tl.count))
    tl.moveToEnd()


def _done(kind, feat, v0, t0, name=None, op=''):
    if name:
        feat.name = name
        if op == 'new' and feat.bodies.count:
            feat.bodies.item(0).name = name
    v1 = volume()
    msg = '[steps %d-%d] %s %r %s dV=%+.3f V=%.3f mm3 bodies=%d' % (
        t0 + 1, _tl(), kind, name or '', op, v1 - v0, v1, root().bRepBodies.count)
    if feat.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
        msg += '  !! FEATURE PROBLEM: %s' % feat.errorOrWarningMessage
    if op in ('join', 'cut', 'intersect') and abs(v1 - v0) < 1e-6:
        msg += '  !! dV=0: the tool did not touch the body (wrong position/direction?)'
    print(msg)
    return feat


# ----------------------------------------------------------------- sketches
def _plane(plane, at):
    if plane not in PLANES:
        raise RuntimeError("plane must be 'xy', 'xz' or 'yz', not %r" % (plane,))
    r = root()
    base = {'xy': r.xYConstructionPlane, 'xz': r.xZConstructionPlane, 'yz': r.yZConstructionPlane}[plane]
    if abs(at) < 1e-9:
        return base
    n = base.geometry.normal
    s = 1.0 if [n.x, n.y, n.z][_I[PLANES[plane][2]]] > 0 else -1.0
    inp = r.constructionPlanes.createInput()
    inp.setByOffset(base, V(at * s))
    pl = r.constructionPlanes.add(inp)
    pl.isLightBulbOn = False
    return pl


def _sketch(plane, at=0.0, name=None):
    sk = root().sketches.add(_plane(plane, at))
    if name:
        sk.name = name
    return sk


def _sp(sk, plane, at, uv):
    x, y, z = xyz(plane, uv[0], uv[1], at)
    return sk.modelToSketchSpace(P(x, y, z))


def _normal_sign(sk, plane):
    n = sk.xDirection.crossProduct(sk.yDirection)
    return 1.0 if [n.x, n.y, n.z][_I[PLANES[plane][2]]] > 0 else -1.0


def _profiles(sk):
    col = adsk.core.ObjectCollection.create()
    for i in range(sk.profiles.count):
        col.add(sk.profiles.item(i))
    if col.count == 0:
        raise RuntimeError('the shape made no closed area - check that the outline closes and does not cross itself')
    return col


# ----------------------------------------------------------------- shapes
class Shape(object):
    def __init__(self, kind, **kw):
        self.kind = kind
        self.kw = kw

    def draw(self, sk, plane, at):
        return _DRAW[self.kind](sk, plane, at, **self.kw)


def poly(pts):
    """Closed outline. pts = list of (u, v) points. An item ('arc', mid, end) draws an
    arc from the previous point through mid=(u, v) to end=(u, v). Closes itself."""
    return Shape('poly', pts=list(pts))


def rect(u0, v0, u1, v1):
    """Axis-aligned rectangle with opposite corners (u0, v0) and (u1, v1)."""
    return poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


def circle(cu, cv, r=None, d=None):
    """Circle with centre (cu, cv); give r= or d=."""
    if r is None:
        if d is None:
            raise RuntimeError('circle needs r= or d=')
        r = d / 2.0
    return Shape('circle', c=(cu, cv), r=r)


def ellipse(cu, cv, ru, rv):
    """Ellipse with centre (cu, cv), semi-axis ru along u and rv along v."""
    return Shape('ellipse', c=(cu, cv), ru=ru, rv=rv)


def slot(u0, v0, u1, v1, r):
    """Stadium/U-slot: straight slot whose end-arc centres are (u0, v0) and (u1, v1), radius r."""
    du, dv = u1 - u0, v1 - v0
    L = math.hypot(du, dv)
    if L < 1e-9:
        return circle(u0, v0, r)
    eu, ev = du / L, dv / L
    nu, nv = -ev, eu
    return poly([(u0 + r * nu, v0 + r * nv), (u1 + r * nu, v1 + r * nv),
                 ('arc', (u1 + r * eu, v1 + r * ev), (u1 - r * nu, v1 - r * nv)),
                 (u0 - r * nu, v0 - r * nv),
                 ('arc', (u0 - r * eu, v0 - r * ev), (u0 + r * nu, v0 + r * nv))])


def _draw_poly(sk, plane, at, pts):
    L = sk.sketchCurves.sketchLines
    A = sk.sketchCurves.sketchArcs
    if not pts or isinstance(pts[0][0], str):
        raise RuntimeError('poly must start with a point (u, v)')
    start = tuple(pts[0])
    segs, cur = [], start
    for it in pts[1:]:
        if isinstance(it[0], str):
            if it[0] != 'arc' or len(it) != 3:
                raise RuntimeError("arc item must be ('arc', (u_mid, v_mid), (u_end, v_end)), not %r" % (it,))
            segs.append(('arc', cur, tuple(it[1]), tuple(it[2])))
            cur = tuple(it[2])
        else:
            segs.append(('line', cur, None, tuple(it)))
            cur = tuple(it)
    if math.hypot(cur[0] - start[0], cur[1] - start[1]) > 1e-6:
        segs.append(('line', cur, None, start))
    if len(segs) < 2:
        raise RuntimeError('poly needs at least 3 points (or arcs)')
    first, last, curves = None, None, []
    for i, (kind, a, m, b) in enumerate(segs):
        closing = i == len(segs) - 1
        if kind == 'line':
            p0 = last if last is not None else _sp(sk, plane, at, a)
            p1 = first if (closing and first is not None) else _sp(sk, plane, at, b)
            ln = L.addByTwoPoints(p0, p1)
            if first is None:
                first = ln.startSketchPoint
            last = ln.endSketchPoint
            curves.append(ln)
        else:
            pa, pm, pb = (_sp(sk, plane, at, q) for q in (a, m, b))
            arc = A.addByThreePoints(pa, pm, pb)
            s, e = arc.startSketchPoint, arc.endSketchPoint
            if s.geometry.distanceTo(pa) > e.geometry.distanceTo(pa):
                s, e = e, s
            if last is not None:
                last.merge(s)
            else:
                first = s
            if closing:
                first.merge(e)
                last = first
            else:
                last = e
            curves.append(arc)
    return curves


def _draw_circle(sk, plane, at, c, r):
    return [sk.sketchCurves.sketchCircles.addByCenterRadius(_sp(sk, plane, at, c), r * MM)]


def _draw_ellipse(sk, plane, at, c, ru, rv):
    if abs(ru - rv) < 1e-9:
        return _draw_circle(sk, plane, at, c, ru)
    cp = _sp(sk, plane, at, c)
    if ru > rv:
        maj, pt = (c[0] + ru, c[1]), (c[0], c[1] + rv)
    else:
        maj, pt = (c[0], c[1] + rv), (c[0] + ru, c[1])
    return [sk.sketchCurves.sketchEllipses.add(cp, _sp(sk, plane, at, maj), _sp(sk, plane, at, pt))]


_DRAW = {'poly': _draw_poly, 'circle': _draw_circle, 'ellipse': _draw_ellipse}


def _shapes(s):
    return list(s) if isinstance(s, (list, tuple)) else [s]


# ----------------------------------------------------------------- solids
def extrude(shapes, plane='xy', at=0.0, to=10.0, op='new', name=None, body=None):
    """Draw shape(s) on `plane` at normal position `at` and extrude them to position `to`.
    Several shapes in one call are extruded together (their union)."""
    if abs(to - at) < 1e-9:
        raise RuntimeError('at == to: zero thickness')
    t0 = _tl(); v0 = volume()
    sk = _sketch(plane, at, (name or 'extrude') + ' sketch')
    for s in _shapes(shapes):
        s.draw(sk, plane, at)
    ext = root().features.extrudeFeatures
    inp = ext.createInput(_profiles(sk), _op(op))
    d = (to - at) * _normal_sign(sk, plane)
    E = adsk.fusion.ExtentDirections
    inp.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V(abs(d))),
                         E.PositiveExtentDirection if d > 0 else E.NegativeExtentDirection)
    _participants(inp, op, body)
    f = ext.add(inp)
    sk.isVisible = False
    return _done('extrude', f, v0, t0, name, op)


def revolve(shapes, plane='xz', axis='z', angle=360.0, op='new', name=None, body=None, at=0.0):
    """Revolve shape(s) drawn on `plane` around `axis`.
    axis = 'x' / 'y' / 'z' (a world axis lying in the plane), or two (u, v) points
    ((u0, v0), (u1, v1)) giving an axis line inside the plane."""
    t0 = _tl(); v0 = volume()
    sk = _sketch(plane, at, (name or 'revolve') + ' sketch')
    for s in _shapes(shapes):
        s.draw(sk, plane, at)
    r = root()
    if isinstance(axis, str):
        if axis not in PLANES[plane][:2]:
            raise RuntimeError('axis %r does not lie in plane %r; use %r or %r, or give two (u, v) points'
                               % (axis, plane, PLANES[plane][0], PLANES[plane][1]))
        if abs(at) > 1e-9:
            raise RuntimeError('a world axis needs at=0; give the axis as two (u, v) points instead')
        ax = {'x': r.xConstructionAxis, 'y': r.yConstructionAxis, 'z': r.zConstructionAxis}[axis]
    else:
        a, b = axis
        ax = sk.sketchCurves.sketchLines.addByTwoPoints(_sp(sk, plane, at, a), _sp(sk, plane, at, b))
        ax.isConstruction = True
    rev = r.features.revolveFeatures
    inp = rev.createInput(_profiles(sk), ax, _op(op))
    inp.setAngleExtent(False, deg(angle))
    _participants(inp, op, body)
    f = rev.add(inp)
    sk.isVisible = False
    return _done('revolve', f, v0, t0, name, op)


def loft(sections, op='new', name=None, body=None):
    """Loft through sections in order. sections = list of (shape, plane, at); each shape
    must be ONE closed outline. The last item may be a world point (x, y, z) = apex."""
    t0 = _tl(); v0 = volume()
    lf = root().features.loftFeatures
    inp = lf.createInput(_op(op))
    for i, sec in enumerate(sections):
        if isinstance(sec[0], (int, float)):
            x, y, z = sec
            sk = _sketch('xy', z, '%s apex' % (name or 'loft'))
            inp.loftSections.add(sk.sketchPoints.add(sk.modelToSketchSpace(P(x, y, z))))
        else:
            shape, plane, at = sec
            sk = _sketch(plane, at, '%s section %d' % (name or 'loft', i + 1))
            shape.draw(sk, plane, at)
            if sk.profiles.count != 1:
                raise RuntimeError('loft section %d must be one closed outline (got %d areas)' % (i + 1, sk.profiles.count))
            inp.loftSections.add(sk.profiles.item(0))
        sk.isVisible = False
    inp.isSolid = True
    _participants(inp, op, body)
    f = lf.add(inp)
    return _done('loft', f, v0, t0, name, op)


def pyramid(shape, plane, at, apex, op='cut', name=None, body=None):
    """Solid from a closed outline (on plane at `at`) to a single world point apex=(x, y, z).
    Use it for oblique corner cuts (tetrahedra) and pyramids."""
    return loft([(shape, plane, at), tuple(apex)], op, name, body)


def box(x0, y0, z0, x1, y1, z1, op='new', name=None, body=None):
    """Axis-aligned block between corners (x0, y0, z0) and (x1, y1, z1)."""
    return extrude(rect(x0, y0, x1, y1), 'xy', z0, z1, op, name, body)


_CYL = {'z': ('xy', lambda c: (c[0], c[1]), 2),
        'y': ('xz', lambda c: (c[0], c[2]), 1),
        'x': ('yz', lambda c: (c[1], c[2]), 0)}


def cyl(c, axis='z', d=10.0, h=10.0, op='new', name=None, body=None):
    """Cylinder of diameter d. Base centre = world point c=(x, y, z); it runs h mm along
    +axis (negative h runs along -axis). Use op='cut' for holes."""
    plane, uv, i = _CYL[axis]
    u, v = uv(c)
    return extrude(circle(u, v, d=d), plane, c[i], c[i] + h, op, name, body)


def holes_on_circle(c, axis='z', pcd=100.0, n=4, d=10.0, h=10.0, start=0.0, op='cut', name=None, body=None):
    """n holes of diameter d equally spaced on a pitch circle of diameter pcd around world
    point c, running h mm along +axis from c. start = angle (deg) of the first hole, measured
    in the plane normal to `axis` from +u toward +v (axis z: u=x v=y; y: u=x v=z; x: u=y v=z)."""
    plane, uv, i = _CYL[axis]
    cu, cv = uv(c)
    shapes = [circle(*polar((cu, cv), pcd / 2.0, start + k * 360.0 / n), d=d) for k in range(n)]
    return extrude(shapes, plane, c[i], c[i] + h, op, name, body)


# ----------------------------------------------------------------- edges
def edges_at(points, body_name=None, tol=0.05):
    """Edges of a body that pass through the given world points (one point ON each edge)."""
    # measureMinimumDistance measures to the edge's infinite carrier line/circle, so only
    # edges whose bounding box contains the point are candidates.
    mm = app().measureManager
    bodies = [body(body_name)] if body_name else list(root().bRepBodies)
    col = adsk.core.ObjectCollection.create()
    t = tol * MM
    for p in points:
        best, bd = None, 1e9
        q = P(*p)
        for b in bodies:
            for e in b.edges:
                bb = e.boundingBox
                if not (bb.minPoint.x - t <= q.x <= bb.maxPoint.x + t and bb.minPoint.y - t <= q.y <= bb.maxPoint.y + t
                        and bb.minPoint.z - t <= q.z <= bb.maxPoint.z + t):
                    continue
                dd = mm.measureMinimumDistance(e, q).value * 10.0
                if dd < bd:
                    best, bd = e, dd
        if bd > tol:
            raise RuntimeError('no edge passes through %r (nearest edge is %.3f mm away) - give a point that lies ON the edge'
                               % (tuple(p), bd))
        col.add(best)
    return col


def fillet(points, r, name=None, body=None, chain=True):
    """Round the edges through `points` (one world point on each edge) with radius r."""
    t0 = _tl(); v0 = volume()
    edges = edges_at(points, body)
    ff = root().features.filletFeatures
    inp = ff.createInput()
    inp.edgeSetInputs.addConstantRadiusEdgeSet(edges, V(r), chain)
    f = ff.add(inp)
    return _done('fillet R%g' % r, f, v0, t0, name)


def chamfer(points, d, name=None, body=None, chain=True):
    """Equal-distance chamfer d (a 'd X 45deg' chamfer) on the edges through `points`."""
    t0 = _tl(); v0 = volume()
    edges = edges_at(points, body)
    cf = root().features.chamferFeatures
    inp = cf.createInput2()
    inp.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(d), chain)
    f = cf.add(inp)
    return _done('chamfer %g' % d, f, v0, t0, name)


# ----------------------------------------------------------------- checks
def _axis_name(v):
    for nm, k in (('x', v.x), ('y', v.y), ('z', v.z)):
        if abs(abs(k) - 1.0) < 1e-6:
            return nm
    return 'oblique(%.3f,%.3f,%.3f)' % (v.x, v.y, v.z)


def report(expect_volume=None, expect_size=None, tol=0.01):
    """Print bodies, volume, size, cylinder diameters/positions and flat-face levels.
    expect_volume (mm^3) and expect_size (dx, dy, dz) are compared when given.
    Returns the number of failed comparisons."""
    S = adsk.core.SurfaceTypes
    bs = root().bRepBodies
    fails = 0
    tl0 = design().timeline
    if tl0.markerPosition != tl0.count:
        fails += 1
        print('!! TIMELINE ROLLED BACK: marker at %d of %d - steps after it are NOT in the model. '
              'Run fz.timeline_end() in a normal (not readOnly) script, then report again.'
              % (tl0.markerPosition, tl0.count))
    print('bodies: %d   total V=%.3f mm3' % (bs.count, volume()))
    tot = [1e9, 1e9, 1e9, -1e9, -1e9, -1e9]
    free = 0
    for b in bs:
        bb = b.boundingBox
        mn = (bb.minPoint.x * 10, bb.minPoint.y * 10, bb.minPoint.z * 10)
        mx = (bb.maxPoint.x * 10, bb.maxPoint.y * 10, bb.maxPoint.z * 10)
        for k in range(3):
            tot[k] = min(tot[k], mn[k])
            tot[3 + k] = max(tot[3 + k], mx[k])
        print(' body %r V=%.3f mm3 size %.3f x %.3f x %.3f  from (%.3f, %.3f, %.3f) to (%.3f, %.3f, %.3f)  faces=%d'
              % ((b.name, _bvol(b)) + tuple(mx[k] - mn[k] for k in range(3)) + mn + mx + (b.faces.count,)))
        cyls, levels, other = {}, {'x': set(), 'y': set(), 'z': set()}, {}
        for f in b.faces:
            g = f.geometry
            t = g.surfaceType
            if t == S.CylinderSurfaceType:
                a = _axis_name(g.axis)
                o = (g.origin.x * 10, g.origin.y * 10, g.origin.z * 10)
                pos = {'x': (o[1], o[2]), 'y': (o[0], o[2]), 'z': (o[0], o[1])}.get(a, o)
                key = 'D%.3f axis %s at (%s)' % (g.radius * 20, a, ', '.join('%.3f' % (q + 0.0) for q in pos))
                cyls[key] = cyls.get(key, 0) + 1
            elif t == S.PlaneSurfaceType:
                a = _axis_name(g.normal)
                if a in levels:
                    levels[a].add(round([g.origin.x, g.origin.y, g.origin.z][_I[a]] * 10, 3))
                else:
                    other['sloped flat'] = other.get('sloped flat', 0) + 1
            else:
                nm = {S.ConeSurfaceType: 'cone (chamfer/countersink)', S.TorusSurfaceType: 'torus (fillet)',
                      S.SphereSurfaceType: 'sphere'}.get(t, 'freeform (loft/fillet)')
                other[nm] = other.get(nm, 0) + 1
                free += nm.startswith('freeform')
        for k in sorted(cyls):
            print('   cylinder %s%s' % (k, '' if cyls[k] == 1 else '  x%d faces' % cyls[k]))
        for a in 'xyz':
            if levels[a]:
                print('   flat faces at %s = %s' % (a, ', '.join('%g' % q for q in sorted(levels[a]))))
        if other:
            print('   other faces: %s' % ', '.join('%s x%d' % kv for kv in sorted(other.items())))
    if bs.count:
        size = tuple(tot[3 + k] - tot[k] for k in range(3))
        print('overall size %.3f x %.3f x %.3f' % size)
        if expect_size is not None:
            ok = all(abs(size[k] - expect_size[k]) <= tol for k in range(3))
            fails += not ok
            print('SIZE %s: expected %s' % ('OK' if ok else 'MISMATCH', tuple(expect_size)))
    if expect_volume is not None:
        v = volume()
        rel = 1e-4 if free else 1e-5   # Fusion's volume of freeform (loft) faces is only ~1e-5..1e-4 exact
        ok = abs(v - expect_volume) <= max(tol, abs(expect_volume) * rel)
        fails += not ok
        print('VOLUME %s: model %.3f, expected %.3f, diff %+.3f mm3 (tolerance %g%%%s)'
              % ('OK' if ok else 'MISMATCH', v, expect_volume, v - expect_volume, rel * 100,
                 ', freeform faces present' if free else ''))
    tl = design().timeline
    for i in range(tl.count):
        it = tl.item(i)
        if it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState:
            fails += 1
            print('TIMELINE PROBLEM step %d %r: %s' % (i + 1, it.name, it.errorOrWarningMessage))
    return fails


def probe(inside=(), outside=(), body_name=None):
    """Check world points: `inside` must be in material, `outside` must be empty space.
    Returns the number of failures."""
    PC = adsk.fusion.PointContainment
    bodies = [body(body_name)] if body_name else list(root().bRepBodies)
    fails = 0
    for want, pts in (('inside', inside), ('outside', outside)):
        for p in pts:
            st = [b.pointContainment(P(*p)) for b in bodies]
            if any(s == PC.PointInsidePointContainment for s in st):
                got = 'inside'
            elif any(s == PC.PointOnPointContainment for s in st):
                got = 'ON-SURFACE (move the probe point off the face)'
            else:
                got = 'outside'
            ok = got == want
            fails += not ok
            print('  %s %r expected %s, got %s' % ('ok  ' if ok else 'FAIL', tuple(p), want, got))
    print('probe: %d failed' % fails)
    return fails


def timeline():
    """Print every timeline step (1-based numbers, as used by rollback)."""
    tl = design().timeline
    for i in range(tl.count):
        it = tl.item(i)
        bad = it.healthState != adsk.fusion.FeatureHealthStates.HealthyFeatureHealthState
        print('%3d %s %s' % (i + 1, it.name, ('!! ' + it.errorOrWarningMessage) if bad else ''))


def rollback(step):
    """Delete timeline step `step` (1-based, from the [steps a-b] lines) and everything after it."""
    tl = design().timeline
    n = tl.count
    for i in range(n - 1, step - 2, -1):
        tl.item(i).entity.deleteMe()
    print('deleted steps %d-%d; V=%.3f mm3 bodies=%d' % (step, n, volume(), root().bRepBodies.count))


# ----------------------------------------------------------------- looks
def _base_appearance():
    for i in range(app().materialLibraries.count):
        lib = app().materialLibraries.item(i)
        for j in range(lib.appearances.count):
            a = lib.appearances.item(j)
            if a.id.startswith('PrismMaterial-078'):
                return a
    raise RuntimeError('base appearance PrismMaterial-078 (plastic matte white) not found')


def color(rgb, body_name=None, name=None):
    """Give body `body_name` (default: all bodies) a flat colour rgb=(r, g, b), 0-255."""
    d = design()
    nm = name or 'fz %d,%d,%d' % tuple(int(c) for c in rgb)
    ap = d.appearances.itemByName(nm)
    if ap is None:
        ap = d.appearances.addByCopy(_base_appearance(), nm)
        for pid in ('opaque_albedo', 'surface_albedo'):
            cp = adsk.core.ColorProperty.cast(ap.appearanceProperties.itemById(pid))
            if cp:
                cp.value = adsk.core.Color.create(int(rgb[0]), int(rgb[1]), int(rgb[2]), 255)
    targets = [body(body_name)] if body_name else list(root().bRepBodies)
    for b in targets:
        b.appearance = ap
    print('colour %s on %s' % (nm, [b.name for b in targets]))


_VIEWS = {'front': ((0, -1, 0), (0, 0, 1)), 'back': ((0, 1, 0), (0, 0, 1)),
          'top': ((0, 0, 1), (0, 1, 0)), 'bottom': ((0, 0, -1), (0, -1, 0)),
          'right': ((1, 0, 0), (0, 0, 1)), 'left': ((-1, 0, 0), (0, 0, 1)),
          'iso': ((1, -1, 1), (0, 0, 1)), 'iso-left': ((-1, -1, 1), (0, 0, 1)),
          'iso-back': ((1, 1, 1), (0, 0, 1))}


def view(name='iso', sketches=None):
    """Aim the camera like a drawing view, then screenshot with direction 'current'.
    front: X right, Z up | top: X right, Y up | right: Y right, Z up | bottom: X right, -Y up
    iso: from front-right-top | iso-left: from front-left-top | iso-back: from back-right-top.
    sketches=None hides sketches when bodies exist; True/False forces it."""
    if name not in _VIEWS:
        raise RuntimeError('view must be one of %s' % sorted(_VIEWS))
    r = root()
    show = (r.bRepBodies.count == 0) if sketches is None else sketches
    for i in range(r.sketches.count):
        r.sketches.item(i).isVisible = show
    for i in range(r.constructionPlanes.count):
        r.constructionPlanes.item(i).isLightBulbOn = False
    vp = app().activeViewport
    cam = vp.camera
    cam.isSmoothTransition = False
    cam.cameraType = adsk.core.CameraTypes.OrthographicCameraType
    (dx, dy, dz), (ux, uy, uz) = _VIEWS[name]
    bb = None
    for b in r.bRepBodies:
        if bb is None:
            bb = b.boundingBox.copy()
        else:
            bb.combine(b.boundingBox)
    if bb is None:
        c = adsk.core.Point3D.create(0, 0, 0)
    else:
        c = adsk.core.Point3D.create((bb.minPoint.x + bb.maxPoint.x) / 2, (bb.minPoint.y + bb.maxPoint.y) / 2,
                                     (bb.minPoint.z + bb.maxPoint.z) / 2)
    cam.target = c
    cam.eye = adsk.core.Point3D.create(c.x + dx * 100, c.y + dy * 100, c.z + dz * 100)
    cam.upVector = adsk.core.Vector3D.create(ux, uy, uz)
    vp.camera = cam
    vp.fit()
    print('camera: %s view - now take mcp__fusion__fusion_mcp_read screenshot with direction "current"' % name)


# ----------------------------------------------------------------- 2D sketches with dimensions
def _curve_dist(c, q):
    """Exact distance (cm, sketch space) from point q to a sketch line, circle or arc."""
    t = c.objectType.split('::')[-1]
    if t == 'SketchLine':
        a, b = c.startSketchPoint.geometry, c.endSketchPoint.geometry
        dx, dy = b.x - a.x, b.y - a.y
        L2 = dx * dx + dy * dy
        s = 0.0 if L2 == 0 else max(0.0, min(1.0, ((q.x - a.x) * dx + (q.y - a.y) * dy) / L2))
        return math.hypot(q.x - (a.x + s * dx), q.y - (a.y + s * dy))
    if t == 'SketchCircle':
        g = c.geometry
        return abs(math.hypot(q.x - g.center.x, q.y - g.center.y) - g.radius)
    if t == 'SketchArc':
        g = c.geometry
        rx, ry = g.referenceVector.x, g.referenceVector.y
        sgn = 1.0 if g.normal.z >= 0 else -1.0
        px, py = q.x - g.center.x, q.y - g.center.y
        th = math.atan2(sgn * (rx * py - ry * px), rx * px + ry * py)
        rel = (th - g.startAngle) % (2 * math.pi)
        if rel <= (g.endAngle - g.startAngle) + 1e-9:
            return abs(math.hypot(px, py) - g.radius)
        return min(c.startSketchPoint.geometry.distanceTo(q), c.endSketchPoint.geometry.distanceTo(q))
    return app().measureManager.measureMinimumDistance(c, q).value


class sketch(object):
    """A 2D sketch you can draw on and dimension, all in plane coordinates (u, v) in mm.
    s = fz.sketch('Name')            # on the XY plane: u = x, v = y
    s.draw(fz.poly([...])); s.line(a, b); s.circle(c, r=5); s.arc3(a, mid, b)
    s.dim(a, b, 'h'|'v'|'a', text=(u, v));  s.dim_d(on, text);  s.dim_r(on, text)
    s.dim_angle(on1, on2, text);  s.dim_offset(on1, on2, text);  s.dims()"""

    def __init__(self, name='Sketch', plane='xy', at=0.0, existing=None):
        self.plane, self.at = plane, at
        self.sk = existing if existing is not None else _sketch(plane, at, name)
        self.sk.areDimensionsShown = True
        self.sk.isVisible = True

    def p(self, uv):
        return _sp(self.sk, self.plane, self.at, uv)

    def _w(self, uv):
        return P(*xyz(self.plane, uv[0], uv[1], self.at))

    def point_near(self, uv, tol=None):
        q = self.p(uv)
        best, bd = None, 1e9
        pts = self.sk.sketchPoints
        for i in range(pts.count):
            s = pts.item(i)
            dd = s.geometry.distanceTo(q) * 10
            if dd < bd:
                best, bd = s, dd
        if tol is not None and bd > tol:
            return None
        if best is None or bd > 0.05:
            raise RuntimeError('no sketch point at %r (nearest is %.3f mm away)' % (tuple(uv), bd))
        return best

    def _pt(self, uv):
        sp = self.point_near(uv, tol=1e-3)
        return sp if sp is not None else self.p(uv)

    def curve_near(self, uv, kinds=None):
        q = self.p(uv)
        best, bd = None, 1e9
        cs = self.sk.sketchCurves
        for i in range(cs.count):
            c = cs.item(i)
            if kinds and c.objectType.split('::')[-1] not in kinds:
                continue
            dd = _curve_dist(c, q) * 10
            if dd < bd:
                best, bd = c, dd
        if best is None or bd > 0.05:
            raise RuntimeError('no %s passes through %r (nearest %.3f mm away)' % (kinds or 'curve', tuple(uv), bd))
        return best

    def draw(self, shape):
        return shape.draw(self.sk, self.plane, self.at)

    def line(self, a, b, construction=False):
        ln = self.sk.sketchCurves.sketchLines.addByTwoPoints(self._pt(a), self._pt(b))
        ln.isConstruction = construction
        return ln

    def circle(self, c, r=None, d=None, construction=False):
        if r is None:
            r = d / 2.0
        ci = self.sk.sketchCurves.sketchCircles.addByCenterRadius(self._pt(c), r * MM)
        ci.isConstruction = construction
        return ci

    def arc3(self, a, mid, b, construction=False):
        """Arc from a through mid to b; joins existing sketch points at a and b."""
        old = [self.point_near(a, tol=1e-3), self.point_near(b, tol=1e-3)]
        ar = self.sk.sketchCurves.sketchArcs.addByThreePoints(self.p(a), self.p(mid), self.p(b))
        s, e = ar.startSketchPoint, ar.endSketchPoint
        if s.geometry.distanceTo(self.p(a)) > e.geometry.distanceTo(self.p(a)):
            s, e = e, s
        for o, mine in zip(old, (s, e)):
            if o is not None:
                o.merge(mine)
        ar.isConstruction = construction
        return ar

    def _text(self, text):
        return self.p(text)

    def dim(self, a, b, kind='a', text=(0, 0)):
        """Distance between the sketch points at a and b. kind: 'h' along u, 'v' along v, 'a' aligned."""
        O = adsk.fusion.DimensionOrientations
        o = {'a': O.AlignedDimensionOrientation, 'h': O.HorizontalDimensionOrientation,
             'v': O.VerticalDimensionOrientation}[kind]
        return self.sk.sketchDimensions.addDistanceDimension(self.point_near(a), self.point_near(b), o, self._text(text))

    def dim_d(self, on, text):
        """Diameter of the circle/arc passing through point `on`."""
        c = self.curve_near(on, ('SketchCircle', 'SketchArc'))
        return self.sk.sketchDimensions.addDiameterDimension(c, self._text(text))

    def dim_r(self, on, text):
        """Radius of the arc/circle passing through point `on`."""
        c = self.curve_near(on, ('SketchArc', 'SketchCircle'))
        return self.sk.sketchDimensions.addRadialDimension(c, self._text(text))

    def dim_angle(self, on1, on2, text):
        """Angle between the two lines through on1 and on2; `text` picks which of the 4 angles."""
        l1 = self.curve_near(on1, ('SketchLine',))
        l2 = self.curve_near(on2, ('SketchLine',))
        return self.sk.sketchDimensions.addAngularDimension(l1, l2, self._text(text))

    def dim_offset(self, on1, on2, text):
        """Distance between two parallel lines through on1 and on2."""
        l1 = self.curve_near(on1, ('SketchLine',))
        l2 = self.curve_near(on2, ('SketchLine',))
        return self.sk.sketchDimensions.addOffsetDimension(l1, l2, self._text(text))

    def dims(self):
        """Print every dimension value (mm or deg) so you can compare with the drawing."""
        ds = self.sk.sketchDimensions
        for i in range(ds.count):
            dd = ds.item(i)
            t = dd.objectType.split('::')[-1].replace('Sketch', '').replace('Dimension', '')
            v = dd.parameter.value
            txt = '%.3f deg' % math.degrees(v) if 'Angular' in t else '%.3f mm' % (v * 10)
            print('  dim %d %s = %s' % (i, t, txt))
        print('sketch fully constrained: %s' % self.sk.isFullyConstrained)


def bodies_to_sketch(name='Sketch', delete_history=True):
    """Project the top flat faces of all bodies into a new XY sketch (unlinked) and, by default,
    delete everything before it in the timeline. Returns an fz.sketch for dimensioning.
    Use it to make a clean 2D outline from overlapping simple shapes built as thin bodies."""
    r = root()
    zmax = max(b.boundingBox.maxPoint.z for b in r.bRepBodies)
    faces = []
    for b in r.bRepBodies:
        for f in b.faces:
            g = f.geometry
            if (g.surfaceType == adsk.core.SurfaceTypes.PlaneSurfaceType and g.normal.z > 0.999
                    and abs(f.boundingBox.maxPoint.z - zmax) < 1e-6):
                faces.append(f)
    sk = r.sketches.add(r.xYConstructionPlane)
    sk.name = name
    sk.project2(faces, False)
    if delete_history:
        tl = design().timeline
        for i in range(tl.count - 2, -1, -1):
            tl.item(i).entity.deleteMe()
    print('projected %d faces into sketch %r' % (len(faces), name))
    return sketch(name, existing=sk)
