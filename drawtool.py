"""drawtool - read engineering-drawing images precisely (needs Pillow).

  python drawtool.py info  IMG
  python drawtool.py grid  IMG OUT.png [step]                 labelled pixel grid over the whole image (default step 100)
  python drawtool.py crop  IMG x0 y0 x1 y1 OUT.png [zoom] [step]
                                                              enlarge a region (default zoom 3); grid labels are ORIGINAL pixels
  python drawtool.py scan  IMG row Y [x0 x1]                  dark-pixel runs along row Y   -> x positions of lines
  python drawtool.py scan  IMG col X [y0 y1]                  dark-pixel runs along column X -> y positions of lines
  python drawtool.py scale PX1 PX2 MM                         pixels per mm from a known dimension (PX1, PX2 = positions)
  python drawtool.py mm    PX1 PX2 PX_PER_MM                  pixel distance -> mm
  python drawtool.py color IMG X Y                            average RGB of a 7x7 patch (to copy a part's colour)

Pixel coordinates are always ORIGINAL image pixels (x to the right, y down).
Read the OUT.png with the Read tool to look at it.
"""
import sys
from PIL import Image, ImageDraw, ImageFont


def _font(size):
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _open(path):
    return Image.open(path).convert('RGB')


def info(img):
    im = _open(img)
    print('size %d x %d px' % im.size)


def _grid(draw, x0, y0, x1, y1, step, zoom, font):
    gx = (x0 // step) * step
    while gx <= x1:
        if gx >= x0:
            X = (gx - x0) * zoom
            draw.line([(X, 0), (X, (y1 - y0) * zoom)], fill=(255, 0, 0), width=1)
            draw.text((X + 2, 2), str(gx), fill=(255, 0, 0), font=font)
        gx += step
    gy = (y0 // step) * step
    while gy <= y1:
        if gy >= y0:
            Y = (gy - y0) * zoom
            draw.line([(0, Y), ((x1 - x0) * zoom, Y)], fill=(0, 0, 255), width=1)
            draw.text((2, Y + 2), str(gy), fill=(0, 0, 255), font=font)
        gy += step


def grid(img, out, step=100):
    im = _open(img)
    d = ImageDraw.Draw(im)
    _grid(d, 0, 0, im.size[0], im.size[1], int(step), 1, _font(18))
    im.save(out)
    print('saved %s (%d x %d), grid every %s px' % (out, im.size[0], im.size[1], step))


def crop(img, x0, y0, x1, y1, out, zoom=3, step=None):
    im = _open(img)
    x0, y0, x1, y1 = (int(v) for v in (x0, y0, x1, y1))
    zoom = float(zoom)
    c = im.crop((x0, y0, x1, y1))
    c = c.resize((int((x1 - x0) * zoom), int((y1 - y0) * zoom)), Image.LANCZOS)
    if step is None:
        span = max(x1 - x0, y1 - y0)
        step = 10 if span <= 200 else 20 if span <= 500 else 50
    d = ImageDraw.Draw(c)
    _grid(d, x0, y0, x1, y1, int(step), zoom, _font(14))
    c.save(out)
    print('saved %s: original region (%d,%d)-(%d,%d) at zoom %g, grid every %s px' % (out, x0, y0, x1, y1, zoom, step))


def scan(img, mode, n, a=None, b=None, dark=160):
    im = _open(img)
    W, H = im.size
    n = int(n)
    if mode == 'row':
        a = 0 if a is None else int(a)
        b = W - 1 if b is None else int(b)
        px = [im.getpixel((x, n)) for x in range(a, b + 1)]
    else:
        a = 0 if a is None else int(a)
        b = H - 1 if b is None else int(b)
        px = [im.getpixel((n, y)) for y in range(a, b + 1)]
    runs, start = [], None
    for i, p in enumerate(px):
        isdark = sum(p) / 3.0 < dark
        if isdark and start is None:
            start = i
        if not isdark and start is not None:
            runs.append((a + start, a + i - 1))
            start = None
    if start is not None:
        runs.append((a + start, a + len(px) - 1))
    what = 'x' if mode == 'row' else 'y'
    print('%s %d: %d dark runs (%s from-to, centre):' % (mode, n, len(runs), what))
    for s, e in runs:
        print('  %d-%d  centre %.1f' % (s, e, (s + e) / 2.0))


def scale(p1, p2, mm):
    k = abs(float(p2) - float(p1)) / float(mm)
    print('%.4f px per mm  (%.5f mm per px)' % (k, 1.0 / k))


def to_mm(p1, p2, k):
    print('%.3f mm' % (abs(float(p2) - float(p1)) / float(k)))


def color(img, x, y):
    im = _open(img)
    x, y = int(x), int(y)
    px = [im.getpixel((i, j)) for i in range(x - 3, x + 4) for j in range(y - 3, y + 4)
          if 0 <= i < im.size[0] and 0 <= j < im.size[1]]
    r, g, b = (int(round(sum(p[k] for p in px) / float(len(px)))) for k in range(3))
    print('rgb (%d, %d, %d)  -> fz.color((%d, %d, %d))' % (r, g, b, r, g, b))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return
    cmd, args = argv[1], argv[2:]
    if cmd == 'info':
        info(*args)
    elif cmd == 'grid':
        grid(*args)
    elif cmd == 'crop':
        crop(*args)
    elif cmd == 'scan':
        scan(args[0], args[1], *args[2:])
    elif cmd == 'scale':
        scale(*args)
    elif cmd == 'mm':
        to_mm(*args)
    elif cmd == 'color':
        color(*args)
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv)
