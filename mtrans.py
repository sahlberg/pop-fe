#!/usr/bin/env python3
"""Replace the Japanese text on a scanned manual page with English.

    python3 mtrans.py LAYOUT.json            # writes the output named in the layout
    python3 mtrans.py LAYOUT.json --grid     # also writes <out>-grid.png with a
                                             # coordinate grid, for measuring boxes
    python3 mtrans.py draft 009.png [...]    # OCR the page and write a starting
                                             # layouts/009.json + layouts/009-draft.png
                                             # (--force replaces an untranslated draft;
                                             # a layout with any English is never replaced)

Draft layouts contain one "text" item per detected text block, with "ja" (what
Tesseract read; often imperfect, so check against the image), "text": "" to
fill in, and guessed box/size/font/color/leading/align/fill. Items whose
"text" is still empty are skipped when rendering, so a page can be done
piecemeal. Extra keys such as "ja" and "note" are ignored by the renderer.

The page is upscaled (default 3x). Every coordinate in the layout is in
ORIGINAL page pixels, so you can measure it on the source scan.

Layout file (JSON):

{
  "src": "006.png",
  "out": "006-en.png",
  "scale": 3,                       # optional
  "styles": {                       # optional, merged over DEFAULT_STYLES
    "caption": {"font": "Medium", "size": 9, "color": [60, 60, 70]}
  },
  "items": [ ... ]
}

Item types:

  {"type": "erase", "box": [x0, y0, x1, y1]}
      Remove whatever is in the box, blending in the background.
      "fill": [r, g, b] uses a flat colour instead, or "median" for the box's
      own dominant colour (for text on a solid coloured bar), or "light" / "dark"
      to remove only light (or dark) text pixels and fill them in from the
      surrounding picture (for text printed over photos or screenshots).
      "thresh" (default 18) is how much lighter/darker than its surroundings a
      pixel must be to count as text; raise it to keep faint artwork lines.
      "white": N (with "light") treats only pixels whose darkest channel is > N
      as text, for white lettering over busy artwork; "grow": px (orig) widens
      the text mask, e.g. to also remove a dark outline round the letters.
      "key": [[r0, g0, b0], [r1, g1, b1]] (with "light"/"dark") treats only pixels
      whose colour lies inside that range as text, for coloured lettering over
      artwork of a similar brightness (yellow letters on an orange brush stroke).
      "shape": "ellipse" fills the ellipse inscribed in the box instead (only
      with a flat colour or "median"), e.g. to blank a lettered circle.

  {"type": "text", "box": [x0, y0, x1, y1], "text": "...", "style": "body"}
      Erase the box, then draw the text wrapped to fit it.
      "erase": [x0, y0, x1, y1] to erase a different area than the text box
               (or false to erase nothing), "fill" as for erase.
      "align": "left" | "center" | "right"    (default left)
      "valign": "top" | "middle" | "bottom"   (default top)
      "size", "font", "color", "leading" override the style.
      "angle": degrees counter-clockwise; the text is laid out in the box as
               usual, then rotated about the box centre (for slanted text).
      "stroke": [width, [r, g, b]] outlines the glyphs (width in orig px).
      The text shrinks (then switches to the condensed face) until it fits.
      "\\n" forces a line break; a blank line starts a new paragraph.

  {"type": "toc", "rows": [[level, "label", page], ...],
   "y0": 122.7, "dy": 15.2,            # centre of first row, row pitch
   "x": {"1": 68.3, "2": 76.7, "3": 85},  # where the label text starts
   "num": [270, 305]}                  # x range holding the page numbers
      Table of contents column: erases each label and its dot leaders, keeps the
      original bullets/tree lines/page numbers, draws English plus new leaders.
      A row may be [level, "label", page, {"y": 200.5}] to override its centre.
      Styles used: "toc1", "toc2", "toc3".

Sizes in styles are in ORIGINAL pixels too (font size, i.e. em height).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = '/usr/share/fonts/google-noto/NotoSans-%s.ttf'
# glyphs Noto Sans lacks (button symbols, arrows, stars) come from DejaVu Sans
FALLBACK = {'Bold': '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf',
            'Regular': '/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf'}
CONDENSED = {'Bold': 'CondensedBold', 'SemiBold': 'CondensedSemiBold',
             'Medium': 'CondensedMedium', 'Regular': 'Condensed'}

DEFAULT_STYLES = {
    'toc1': {'font': 'Bold', 'size': 10.3, 'color': [28, 28, 34]},
    'toc2': {'font': 'Medium', 'size': 10.3, 'color': [72, 72, 78]},
    'toc3': {'font': 'Regular', 'size': 10.3, 'color': [125, 125, 130]},
    'title': {'font': 'Bold', 'size': 27, 'color': [20, 20, 24]},
    'heading': {'font': 'Bold', 'size': 11, 'color': [28, 28, 34]},
    'body': {'font': 'Regular', 'size': 9, 'color': [40, 40, 45], 'leading': 1.45},
    'small': {'font': 'Regular', 'size': 7.5, 'color': [40, 40, 45], 'leading': 1.35},
}


class Page:
    def __init__(self, layout, base):
        self.base = base
        self.K = layout.get('scale', 3)
        src = Image.open(os.path.join(base, layout['src'])).convert('RGB')
        self.O = np.asarray(src).astype(int)
        self.im = src.resize((src.width * self.K, src.height * self.K), Image.LANCZOS)
        self.A = np.asarray(self.im).astype(int)
        self.d = ImageDraw.Draw(self.im)
        self.styles = {k: dict(v) for k, v in DEFAULT_STYLES.items()}
        for k, v in layout.get('styles', {}).items():
            self.styles.setdefault(k, {}).update(v)

    # ---- helpers -------------------------------------------------------
    def font(self, face, size_orig):
        return ImageFont.truetype(FONT_DIR % face, max(4, round(size_orig * self.K)))

    _cover = {}

    def has_glyph(self, f, ch):
        """True if font f has a real glyph for ch (compared against its .notdef box)."""
        key = (f.path, ch)
        if key not in self._cover:
            if ch.isspace() or ord(ch) < 0x2000 and ch != '\u00a0':
                self._cover[key] = True
            else:
                def shape(c):
                    im = Image.new('L', (f.size * 2, f.size * 2))
                    ImageDraw.Draw(im).text((0, 0), c, font=f, fill=255)
                    return im.tobytes()
                self._cover[key] = shape(ch) != shape('\U0010fffd')
        return self._cover[key]

    def runs(self, text, f):
        """Split text into (string, font) runs, using DejaVu for missing glyphs."""
        out = []
        for ch in text:
            g = f
            if not self.has_glyph(f, ch):
                bold = any(w in f.path for w in ('Bold', 'Black', 'SemiBold', 'Medium'))
                g = ImageFont.truetype(FALLBACK['Bold' if bold else 'Regular'], f.size)
            if out and out[-1][1].path == g.path:
                out[-1][0] += ch
            else:
                out.append([ch, g])
        return out

    def tlen(self, text, f):
        return sum(self.d.textlength(t, font=g) for t, g in self.runs(text, f))

    def draw_text(self, d, xy, text, f, **kw):
        x, y = xy
        for t, g in self.runs(text, f):
            d.text((x, y), t, font=g, anchor='ls', **kw)
            x += d.textlength(t, font=g)

    def style(self, item, default):
        st = dict(self.styles[item.get('style', default)])
        for k in ('font', 'size', 'color', 'leading'):
            if k in item:
                st[k] = item[k]
        return st

    def erase(self, box, fill=None, gh=9, thresh=18, ellipse=False, white=None, grow=None, key=None):
        """Erase an ORIGINAL-pixel box on the upscaled page."""
        K = self.K
        x0, y0 = int(box[0] * K), int(box[1] * K)
        x1, y1 = int(box[2] * K), int(box[3] * K)
        if fill in ('light', 'dark'):
            self.inpaint(x0, y0, x1, y1, fill, gh, thresh, white, grow, key)
            return
        if fill == 'median':  # solid panel: its most common colour, ignoring the text
            fill = np.median(self.A[y0:y1, x0:x1].reshape(-1, 3), 0).astype(int)
        if fill is not None:
            shape = self.d.ellipse if ellipse else self.d.rectangle
            shape((x0, y0, x1, y1), fill=tuple(int(v) for v in fill))
            return
        H = self.A.shape[0]
        k = np.ones(21) / 21

        def edge(y):
            y = min(max(y, 0), H - 1)
            row = np.pad(self.A[y].astype(float), ((10, 10), (0, 0)), mode='edge')
            r = row[x0:x1 + 21]  # = original x0-10 .. x1+10
            return np.stack([np.convolve(r[:, c], k, 'valid') for c in range(3)], 1)

        top, bot = edge(y0 - 2), edge(y1 + 2)
        t = np.linspace(0, 1, y1 - y0 + 1)[:, None, None]
        patch = (top[None] * (1 - t) + bot[None] * t).clip(0, 255).astype(np.uint8)
        self.im.paste(Image.fromarray(patch), (x0, y0))

    @staticmethod
    def box_blur(a, r):
        """Mean over a (2r+1)^2 window, edges clamped. a is HxW or HxWxC."""
        for axis in (0, 1):
            pad = [(0, 0)] * a.ndim
            pad[axis] = (r + 1, r)
            c = np.cumsum(np.pad(a, pad, mode='edge'), axis=axis)
            hi = np.take(c, range(2 * r + 1, c.shape[axis]), axis=axis)
            lo = np.take(c, range(0, c.shape[axis] - 2 * r - 1), axis=axis)
            a = (hi - lo) / (2 * r + 1)
        return a

    def inpaint(self, x0, y0, x1, y1, kind, gh=9, thresh=18, white=None, grow_px=None, key=None):
        """Replace only the text pixels (lighter or darker than their surroundings)
        with the surrounding picture. gh = glyph height in original px: the
        background estimate must look further than one glyph, or the strokes of big
        characters count as their own background and leave a ghost."""
        K = self.K
        rw = max(4 * K, int(1.5 * gh * K))
        m = 2 * rw
        H, W = self.A.shape[:2]
        ox0, oy0, ox1, oy1 = max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, W), min(y1 + m, H)
        R = self.A[oy0:oy1, ox0:ox1].astype(float)
        lum = R.mean(2)
        sign = 1 if kind == 'light' else -1

        def text_mask(bg):
            return sign * (lum - bg) > thresh

        # background = local mean of the non-text pixels (two passes, so the text
        # itself doesn't darken/lighten the estimate)
        mask = text_mask(self.box_blur(lum, rw))
        keep = (~mask).astype(float)
        bg = self.box_blur(lum * keep, rw) / np.maximum(self.box_blur(keep, rw), 1e-3)
        mask = text_mask(bg)
        if white is not None:  # absolute: only near-white pixels are text (busy artwork)
            mask = R.min(2) > white
        if key is not None:  # absolute colour range
            lo, hi = np.array(key[0], float), np.array(key[1], float)
            mask = ((R >= lo) & (R <= hi)).all(2)
        grow = max(K, int(0.15 * gh * K))  # cover antialiased edges
        if grow_px is not None:  # e.g. to swallow a dark outline round the letters
            grow = max(1, int(grow_px * K))
        mask = self.box_blur(mask.astype(float), grow) > 0
        # fill only from background: never from text-like pixels anywhere nearby
        # (a rule under a title would otherwise smear into the gap)
        known = (~mask).astype(float)
        inside = np.zeros_like(mask)
        inside[y0 - oy0:y1 - oy0, x0 - ox0:x1 - ox0] = True
        mask &= inside
        out = R.copy()
        r = 2 * K
        while mask.any() and r < 4 * m:
            num = self.box_blur(out * known[..., None], r)
            den = self.box_blur(known, r)
            fillable = mask & (den > 0.05)
            out[fillable] = num[fillable] / den[fillable][:, None]
            known[fillable] = 1
            mask &= ~fillable
            r *= 2
        patch = out[y0 - oy0:y1 - oy0, x0 - ox0:x1 - ox0].clip(0, 255).astype(np.uint8)
        self.im.paste(Image.fromarray(patch), (x0, y0))

    def wrap(self, text, f, width):
        lines = []
        for para_i, para in enumerate(text.split('\n\n')):
            if para_i:
                lines.append(None)  # paragraph gap
            for hard in para.split('\n'):
                cur = ''
                for word in hard.split(' '):
                    trial = word if not cur else cur + ' ' + word
                    if self.tlen(trial, f) <= width or not cur:
                        cur = trial
                    else:
                        lines.append(cur)
                        cur = word
                lines.append(cur)
        return lines

    # ---- item types ----------------------------------------------------
    def do_erase(self, it):
        self.erase(it['box'], it.get('fill'), it.get('size', 9), it.get('thresh', 18),
                   it.get('shape') == 'ellipse', it.get('white'), it.get('grow'), it.get('key'))

    def do_text(self, it):
        K = self.K
        box = it['box']
        er = it.get('erase', box)
        st = self.style(it, 'body')
        if er:
            self.erase(er, it.get('fill'), st['size'], it.get('thresh', 18),
                       it.get('shape') == 'ellipse', it.get('white'), it.get('grow'), it.get('key'))
        x0, y0, x1, y1 = (v * K for v in box)
        W, H = x1 - x0, y1 - y0
        lead = st.get('leading', 1.25)
        faces = [st['font'], CONDENSED.get(st['font'], st['font'])]
        best = None
        for face in faces:
            size = st['size']
            while size >= st['size'] * 0.7:
                f = self.font(face, size)
                lines = self.wrap(it['text'], f, W)
                lh = f.size * lead
                height = sum(lh * (0.5 if l is None else 1) for l in lines) - lh + f.size * 1.15
                widest = max(self.tlen(l, f) for l in lines if l is not None)
                if height <= H + 1 and widest <= W + 1:
                    best = (f, lines, lh, height)
                    break
                size -= 0.25
            if best:
                break
        if not best:
            print(f'warning: text does not fit {box}: {it["text"][:40]!r}', file=sys.stderr)
            best = (f, lines, lh, height)
        f, lines, lh, height = best
        va = it.get('valign', 'top')
        y = y0 + {'top': 0, 'middle': (H - height) / 2, 'bottom': H - height}[va]
        y += f.size * 0.92  # first baseline
        align = it.get('align', 'left')
        angle = it.get('angle', 0)
        stroke = it.get('stroke')  # [width in orig px, [r, g, b]]
        sw = int(round(stroke[0] * K)) if stroke else 0
        sf = tuple(stroke[1]) if stroke else None
        if angle:
            # draw on a transparent layer in the box's own frame, then rotate it
            # about the box centre (degrees, counter-clockwise)
            pad = int(0.1 * max(W, H)) + sw + 4
            layer = Image.new('RGBA', (int(W) + 2 * pad, int(H) + 2 * pad), (0, 0, 0, 0))
            dd, ox, oy = ImageDraw.Draw(layer), x0 - pad, y0 - pad
        else:
            dd, ox, oy = self.d, 0, 0
        for l in lines:
            if l is None:
                y += lh * 0.5
                continue
            w = self.tlen(l, f)
            x = {'left': x0, 'center': x0 + (W - w) / 2, 'right': x1 - w}[align]
            self.draw_text(dd, (x - ox, y - oy), l, f, fill=tuple(st['color']),
                           stroke_width=sw, stroke_fill=sf)
            y += lh
        if angle:
            r = layer.rotate(angle, resample=Image.BICUBIC, expand=True)
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            self.im.paste(r, (int(round(cx - r.width / 2)), int(round(cy - r.height / 2))), r)

    def number_left(self, yc, xlo, xhi):
        """Left edge (orig px) of the page number printed in [xlo, xhi) on row yc."""
        yc = int(round(yc))
        lum = self.O[yc - 6:yc + 7, xlo:xhi].sum(2)
        dark = lum < np.percentile(lum, 90) - 120
        tall = [x for x in range(dark.shape[1]) if dark[:, x].sum() >= 4]
        if not tall:
            return None
        left = tall[-1]
        for c in reversed(tall):
            if left - c > 7:
                break
            left = c
        return xlo + left

    def do_toc(self, it):
        K = self.K
        rows = []
        for i, r in enumerate(it['rows']):
            extra = r[3] if len(r) > 3 else {}
            yc = extra.get('y', it['y0'] + it['dy'] * i)
            rows.append((yc, r[0], r[1], r[2], extra))
        xlo, xhi = it['num']
        found = [(self.number_left(yc, xlo, xhi), len(str(p))) for yc, _, _, p, _ in rows]
        two = [n for n, digits in found if n is not None and digits >= 2]
        ref2 = float(np.median(two)) if two else None
        half = it.get('half', 6.5)
        for (yc, lv, label, page, extra), (nl, digits) in zip(rows, found):
            if 'numleft' in extra:
                nl = extra['numleft']
            elif nl is None:
                nl = xhi - 8 * digits
            elif digits >= 2 and ref2 is not None:
                nl = min(nl, ref2)
            xt = it['x'][str(lv)]
            x0, x1 = int(xt * K), int(nl * K) - 4
            self.erase((xt, yc - half, nl - 4 / K, yc + half))
            st = self.style({'style': f'toc{lv}'}, f'toc{lv}')
            colour = tuple(st['color'])
            f = None
            for face in (st['font'], CONDENSED[st['font']]):
                for s in np.arange(st['size'], st['size'] * 0.8, -0.25):
                    f = self.font(face, s)
                    if self.d.textlength(label, font=f) <= (x1 - x0) - 30:
                        break
                else:
                    continue
                break
            base = int(yc * K) + int(round(3.7 * K))
            self.d.text((x0 + 3, base), label, font=f, fill=colour, anchor='ls')
            x = x0 + 3 + self.d.textlength(label, font=f) + 10
            while x < x1 - 10:
                self.d.ellipse((x - 1.6, base - 3.2, x + 1.6, base), fill=colour)
                x += 9

    def grid(self, path):
        g = Image.fromarray(self.O.astype(np.uint8)).resize(self.im.size, Image.NEAREST)
        d = ImageDraw.Draw(g)
        f = ImageFont.truetype(FONT_DIR % 'Regular', 18)
        K = self.K
        for v in range(0, max(g.size) // K, 10):
            c = (255, 0, 0) if v % 50 == 0 else (255, 170, 170)
            if v % 50 == 0:
                d.line((v * K, 0, v * K, g.height), fill=c)
                d.line((0, v * K, g.width, v * K), fill=c)
                d.text((v * K + 2, 2), str(v), font=f, fill=(255, 0, 0))
                d.text((2, v * K + 2), str(v), font=f, fill=(255, 0, 0))
            else:
                for p in range(0, g.width, 6):
                    d.point((v * K, p), fill=c)
                    d.point((p, v * K), fill=c)
        g.save(path)


# ---------------------------------------------------------------------------
# draft: find the Japanese text with Tesseract and write a starting layout
# ---------------------------------------------------------------------------
JA = re.compile(r'[぀-ヿ㐀-鿿ｦ-ﾟ々〆ヵヶ]')
USEFUL = re.compile(r'[぀-ヿ㐀-鿿＀-￯A-Za-z0-9]')
DASHES = re.compile(r'[ー一ｰ\-_―─]+')
LEADER = re.compile(r'(\.{3,}|…|‥|・{3,}|-{4,})|\d+\s*$')


def is_gutter(O, xa, xb, cy, h):
    """True if some column between xa and xb is blank paper from 2.5 lines above
    to 2.5 lines below cy: a gap between columns rather than inside a sentence."""
    H, W = O.shape[:2]
    xa, xb = int(max(xa + 1, 0)), int(min(xb, W))
    if xb - xa < 1:
        return False
    y0, y1 = int(max(cy - 2.5 * h, 0)), int(min(cy + 2.5 * h, H))
    strip = O[y0:y1, xa:xb].mean(2)
    blank = (np.abs(strip - np.median(strip)) < 35).all(0)
    # Japanese is set on a grid, so 1-2px spaces between glyphs line up from line
    # to line; a gutter is a blank strip at least one character wide
    run = best = 0
    for v in blank:
        run = run + 1 if v else 0
        best = max(best, run)
    return best >= max(4, 0.7 * h)


def ocr_lines(gray_up, K, tag, psm=3, min_h=3.5, min_conf=40, O=None):
    """Run Tesseract on an upscaled grayscale image; return text lines in orig px."""
    with tempfile.NamedTemporaryFile(suffix='.png') as tf:
        gray_up.save(tf.name)
        tsv = subprocess.run(['tesseract', tf.name, '-', '-l', 'jpn', '--psm', str(psm), 'tsv'],
                             capture_output=True, text=True, check=True).stdout
    raw = {}
    for row in tsv.splitlines()[1:]:
        f = row.split('\t')
        if len(f) < 12 or f[0] != '5':
            continue
        conf, text = float(f[10]), f[11].strip()
        x, y, w, h = (int(v) / K for v in f[6:10])
        # keep low-confidence words for geometry (they bridge gaps such as
        # "(->P.20)"); only confident words contribute text
        if conf < 0 or not USEFUL.search(text) or not (min_h <= h <= 80):
            continue
        if conf < min_conf:
            text = ''
        raw.setdefault((f[2], f[3], f[4]), []).append((x, y, x + w, y + h, text, conf))
    out = []
    for ws in raw.values():
        ws.sort()
        # typical glyph height of this line; ー, 「 etc. get odd boxes, so ignore outliers
        hs = np.array([w[3] - w[1] for w in ws if w[4]] or [w[3] - w[1] for w in ws])
        h = float(np.median(hs))
        good = [w for w in ws if 0.6 * h <= w[3] - w[1] <= 1.3 * h]
        cy = float(np.median([(w[1] + w[3]) / 2 for w in good])) if good else None
        # split where Tesseract joined text across a wide horizontal gap
        segs, cur = [], [ws[0]]
        for w in ws[1:]:
            gap = w[0] - cur[-1][2]
            # gaps inside a sentence (「」, low-confidence "(->P.20)") can be wider than a
            # column gutter, so split only where the paper is blank above and below
            if gap > 5 * h or (gap > 0.8 * h and O is not None
                               and is_gutter(O, cur[-1][2], w[0], cy if cy else w[1], h)):
                segs.append(cur)
                cur = []
            cur.append(w)
        segs.append(cur)
        for seg in segs:
            # drop a lone low-confidence glyph at either end (usually an icon)
            def junk(w):  # an icon or a decoration bar read as a glyph or a dash run
                return ((len(w[4]) <= 1 and w[5] < 85) or (DASHES.fullmatch(w[4]) and w[5] < 95)
                        or (not JA.search(w[4]) and w[5] < 80))
            while len(seg) > 1 and junk(seg[0]):
                seg = seg[1:]
            while len(seg) > 1 and junk(seg[-1]):
                seg = seg[:-1]
            text = ''.join(w[4] for w in seg)
            nja = len(JA.findall(text))
            confs = [w[5] for w in seg if w[4]]
            if nja < 2 or nja < 0.4 * len(text):
                continue  # English, page numbers, footer: leave alone
            if nja < 3 and np.mean(confs) < 85:
                continue  # two shaky characters: usually artwork read as text
            out.append({'x0': min(w[0] for w in seg), 'x1': max(w[2] for w in seg),
                        'y0': cy - h / 2 if cy is not None else min(w[1] for w in seg),
                        'y1': cy + h / 2 if cy is not None else max(w[3] for w in seg),
                        'h': h, 'text': text, 'tag': tag})
    return out


def overlap(a, b):
    ix = min(a['x1'], b['x1']) - max(a['x0'], b['x0'])
    iy = min(a['y1'], b['y1']) - max(a['y0'], b['y0'])
    return max(ix, 0) * max(iy, 0)


def merge_rows(lines, O):
    """Join pieces of one printed line that Tesseract reported separately."""
    lines = sorted(lines, key=lambda l: l['x0'])
    out = []
    for ln in lines:
        for o in out:
            h = max(o['h'], ln['h'])
            cy_o, cy_l = (o['y0'] + o['y1']) / 2, (ln['y0'] + ln['y1']) / 2
            if (abs(cy_o - cy_l) < 0.3 * h
                    and max(o['h'], ln['h']) / max(min(o['h'], ln['h']), 1) < 1.25
                    and -0.5 * h < ln['x0'] - o['x1'] < 5 * h
                    and not is_gutter(O, o['x1'], ln['x0'], cy_o, h)):
                o['text'] += ln['text']
                o['x1'] = max(o['x1'], ln['x1'])
                o['y0'], o['y1'] = min(o['y0'], ln['y0']), max(o['y1'], ln['y1'])
                break
        else:
            out.append(dict(ln))
    return out


def group_blocks(lines):
    """Merge vertically adjacent lines of the same size and column into blocks."""
    blocks = []
    for ln in sorted(lines, key=lambda l: (l['y0'], l['x0'])):
        for b in blocks:
            last = b[-1]
            h = max(ln['h'], last['h'])
            gap = ln['y0'] - last['y1']
            same_size = max(ln['h'], last['h']) / max(min(ln['h'], last['h']), 1) < 1.4
            ov = min(ln['x1'], last['x1']) - max(ln['x0'], last['x0'])
            same_col = ov > 0.5 * min(ln['x1'] - ln['x0'], last['x1'] - last['x0']) \
                or abs(ln['x0'] - last['x0']) < 1.5 * h
            if -2 <= gap <= 1.8 * h and same_size and same_col:
                b.append(ln)
                break
        else:
            blocks.append([ln])
    return blocks


def snap_line(O, ln):
    """Grow a line sideways over adjacent ink that OCR left out (e.g. a missed
    first character), stopping at a gap wider than one glyph or at a rule or
    border (a run of ink much longer than a glyph)."""
    H, W = O.shape[:2]
    if ln['h'] >= 14:
        # Tesseract's boxes for big text vary by up to half a glyph; tighten to the
        # longest run of rows that look like text (some ink, but not a solid band)
        y0, y1 = int(max(ln['y0'] - 2, 0)), int(min(ln['y1'] + 3, H))
        reg = O[y0:y1, int(ln['x0']):int(ln['x1']) + 1].mean(2)
        paper = np.percentile(reg, 90)
        frac = (np.abs(reg - paper) > 60).mean(1)
        textrow = (frac > 0.03) & (frac < 0.8)
        best, run, start = (0, 0), 0, 0
        for i, v in enumerate(textrow):
            if v:
                if run == 0:
                    start = i
                run += 1
                if run > best[1] - best[0]:
                    best = (start, i + 1)
            else:
                run = 0
        if best[1] - best[0] >= 0.5 * ln['h']:
            ln['y0'], ln['y1'] = y0 + best[0], y0 + best[1]
            ln['h'] = float(best[1] - best[0])
    h = ln['h']
    cy = (ln['y0'] + ln['y1']) / 2
    y0, y1 = int(max(cy - 0.3 * h, 0)), int(min(cy + 0.3 * h + 1, H))  # middle of the line only
    band = O[y0:y1].mean(2)
    inside = band[:, int(ln['x0']):int(ln['x1']) + 1]
    bg = np.median(inside)
    # ink = at least half as contrasty as this line's own text, so faint
    # show-through from the other side of the paper doesn't count
    contrast = np.percentile(np.abs(inside - bg), 97)
    inkcol = (np.abs(band - bg) > max(40, 0.5 * contrast)).sum(0) >= max(1, int(0.15 * (y1 - y0)))
    reach = max(2, int(h * 0.9))
    maxrun = int(3 * h)   # small Japanese glyphs touch, so a run can span a few
    limit = 2.5 * h if h < 14 else 1.2 * h  # at most ~2 small / 1 large character

    # a vertical rule or frame edge: ink right through and well beyond the line
    ty0, ty1 = int(max(ln['y0'] - 0.25 * h, 0)), int(min(ln['y1'] + 0.25 * h + 1, H))
    tall = O[ty0:ty1].mean(2)
    rule = (np.abs(tall - bg) > max(40, 0.5 * contrast)).mean(0) > 0.9
    if h >= 14:  # big titles sit next to framed decorations; stop at any frame edge
        own = O[int(max(ln['y0'], 0)):int(min(ln['y1'] + 1, H))].mean(2)
        rule |= (np.abs(own - bg) > max(40, 0.5 * contrast)).mean(0) > 0.75

    iy0, iy1 = int(max(ln['y0'], 0)), int(min(ln['y1'] + 1, H))
    mpad = max(2, int(0.4 * h))
    outside_rows = list(range(max(iy0 - mpad, 0), iy0)) + list(range(iy1, min(iy1 + mpad, H)))

    def spill(xa, xb):
        """Share of the rows just above/below the line that carry ink in columns xa..xb."""
        if not outside_rows or xb <= xa:
            return 0.0
        reg = O[outside_rows, xa:xb].mean(2)
        return float((np.abs(reg - bg) > max(40, 0.5 * contrast)).mean())

    own_spill = spill(int(ln['x0']), int(ln['x1']) + 1)

    def grow(x, step):
        while True:
            nxt = range(x + step, x + step * (reach + 1), step)
            hits = [c for c in nxt if 0 <= c < W and inkcol[c]]
            if not hits:
                return x
            c = hits[0]
            if rule[max(c - 1, 0):c + 2].any():
                return x
            run = c
            while 0 <= run + step < W and inkcol[run + step]:
                run += step
            if abs(run - c) > maxrun:
                return x  # a rule or picture edge, not a glyph
            # a missed glyph sits inside the line's band; decorations, frames and
            # artwork spill above or below it. Compare against the spill under the
            # line's own text, since a rule running under the whole line is normal.
            lo, hi = sorted((c, run))
            if spill(lo, hi + 1) - own_spill > (0.25 if h >= 14 else 0.15):
                return x
            x = run

    ln['x0'] = min(ln['x0'], max(grow(int(ln['x0']), -1), ln['x0'] - limit))
    ln['x1'] = max(ln['x1'], min(grow(int(ln['x1']), +1) + 1, ln['x1'] + limit))
    return ln


def measure_block(O, b):
    """Style guesses for a block, from the original pixels."""
    x0 = min(l['x0'] for l in b); x1 = max(l['x1'] for l in b)
    y0 = min(l['y0'] for l in b); y1 = max(l['y1'] for l in b)
    H, W = O.shape[:2]
    X0, Y0, X1, Y1 = int(max(x0 - 1, 0)), int(max(y0 - 1, 0)), int(min(x1 + 2, W)), int(min(y1 + 2, H))
    # the paper (or picture) colour comes from a ring just outside the box: big
    # bold titles can cover half their own box, so the box median isn't paper
    rY0, rY1, rX0, rX1 = max(Y0 - 4, 0), min(Y1 + 4, H), max(X0 - 4, 0), min(X1 + 4, W)
    ring = O[rY0:rY1, rX0:rX1].astype(float).mean(2)
    m = np.ones_like(ring, bool)
    m[Y0 - rY0:Y1 - rY0, X0 - rX0:X1 - rX0] = False
    rv = ring[m]
    bg = float(np.median(rv))
    busy = float((np.abs(rv - bg) > 40).mean())  # share of non-paper pixels
    reg = O[Y0:Y1, X0:X1].reshape(-1, 3)
    dev = reg.mean(1) - bg
    light = bg < 170 and (dev > 40).sum() > (dev < -40).sum()  # never on pale paper
    # thin strokes are blurred on the scan, so the true ink colour is the extreme end
    ink = reg[dev > 40] if light else reg[dev < -40]
    if len(ink):
        k = ink.mean(1)
        sel = k >= np.percentile(k, 90) if light else k <= np.percentile(k, 10)
        colour = np.median(ink[sel], 0).astype(int)
    else:
        colour = np.array([40, 40, 45])
    h = float(np.median([l['h'] for l in b]))
    item = {'type': 'text', 'ja': '\n'.join(l['text'] for l in b), 'text': '',
            'box': [round(x0 - 1, 1), round(y0 - 1, 1), round(x1 + 1, 1), round(y1 + 1, 1)],
            'size': round(h * 1.05, 1),
            # weight can't be told reliably from the scan; big text is usually bold
            'font': 'Bold' if h >= 14 else 'Regular',
            'color': [int(v) for v in colour]}
    if len(b) > 1:
        pitch = float(np.median(np.diff([l['y0'] for l in b])))
        # Japanese is set looser than English reads well; the agent may tune this
        item['leading'] = round(min(pitch / item['size'], 1.7), 2)
        lefts = [l['x0'] for l in b]
        rights = [l['x1'] for l in b[:-1]] or [b[0]['x1']]
        if np.ptp(lefts) > 2 * h and np.ptp(rights) <= 3:
            item['align'] = 'right'
    # text-only removal keeps whatever the text is printed over (illustrations,
    # frames, screenshots); plain blending is only for text on clean paper
    if light or busy > 0.05:
        item['fill'] = 'light' if light else 'dark'
    if any(LEADER.search(l['text']) for l in b) and len(b) == 1 and h < 14:
        item['note'] = 'looks like a contents row - consider a "toc" item'
    return item


def draft(src, force=False):
    src = os.path.abspath(src)
    base = os.path.dirname(src)
    stem = os.path.splitext(os.path.basename(src))[0]
    ldir = os.path.join(base, 'layouts')
    os.makedirs(ldir, exist_ok=True)
    lpath = os.path.join(ldir, stem + '.json')
    if os.path.exists(lpath):
        if not force:
            print(f'{lpath} exists, not overwriting (use --force)')
            return
        try:
            old = json.load(open(lpath))
            done = any(it.get('text') or it['type'] != 'text' for it in old.get('items', []))
        except Exception:
            done = True
        if done:  # --force only replaces untouched drafts, never translation work
            print(f'{lpath} already has English in it; refusing to overwrite it even '
                  f'with --force. Move it away first if you really mean it.')
            return
    K = 3
    img = Image.open(src).convert('RGB')
    O = np.asarray(img).astype(int)
    gray = img.convert('L').resize((img.width * K, img.height * K), Image.LANCZOS)
    lines = ocr_lines(gray, K, 'dark', O=O)
    # second pass on the inverted page, for light text on dark pictures, and a
    # sparse-text pass for big titles that the normal mode treats as artwork
    # Each Tesseract mode misses different things; extra passes only add lines
    # that don't overlap what is already found:
    #   inverted page    - light text on dark pictures
    #   sparse, 3x and 1x - big titles the normal mode takes for artwork
    #   block mode       - headings and menu labels inside screenshots
    extra = ocr_lines(Image.eval(gray, lambda v: 255 - v), K, 'light', O=O) \
        + ocr_lines(gray, K, 'dark', psm=11, min_h=13, min_conf=30, O=O) \
        + ocr_lines(img.convert('L'), 1, 'dark', psm=11, min_h=13, min_conf=30, O=O) \
        + ocr_lines(gray, K, 'dark', psm=6, min_conf=60, O=O)
    for ln in extra:
        area = (ln['x1'] - ln['x0']) * (ln['y1'] - ln['y0'])
        if sum(overlap(ln, o) for o in lines) < 0.1 * area:
            lines.append(ln)
    lines = [snap_line(O, ln) for ln in merge_rows(lines, O)]
    # growing must never run into another line on the same row
    for a in lines:
        for b in lines:
            if a is b or abs((a['y0'] + a['y1']) / 2 - (b['y0'] + b['y1']) / 2) > 0.5 * max(a['h'], b['h']):
                continue
            if b['x0'] >= a['x0'] and a['x1'] > b['x0'] - 2 and b['x0'] > a['x0'] + a['h']:
                a['x1'] = max(a['x0'] + 1, b['x0'] - 2)
    items = [measure_block(O, b) for b in group_blocks(lines)]
    items.sort(key=lambda it: (it['box'][1], it['box'][0]))
    layout = {'src': '../' + os.path.basename(src), 'out': f'../{stem}-en.png', 'items': items}
    # one item per line keeps the file easy to edit
    body = ',\n'.join('    ' + json.dumps(it, ensure_ascii=False) for it in items)
    with open(lpath, 'w') as f:
        f.write('{\n  "src": %s,\n  "out": %s,\n  "items": [\n%s\n  ]\n}\n'
                % (json.dumps(layout['src']), json.dumps(layout['out']), body))
    # preview: numbered boxes over the page
    pv = img.resize((img.width * K, img.height * K), Image.LANCZOS)
    d = ImageDraw.Draw(pv)
    f = ImageFont.truetype(FONT_DIR % 'Bold', 22)
    for i, it in enumerate(items):
        x0, y0, x1, y1 = (v * K for v in it['box'])
        c = (230, 0, 0) if 'fill' not in it else (0, 160, 0)
        d.rectangle((x0, y0, x1, y1), outline=c, width=3)
        d.text((x0, y0 - 2), str(i), font=f, fill=c, anchor='lb')
    ppath = os.path.join(ldir, stem + '-draft.png')
    pv.save(ppath)
    print(f'wrote {lpath} ({len(items)} text blocks) and {ppath}')


def main():
    if sys.argv[1] == 'draft':
        for src in [a for a in sys.argv[2:] if not a.startswith('--')]:
            draft(src, force='--force' in sys.argv)
        return
    path = sys.argv[1]
    base = os.path.dirname(os.path.abspath(path))
    layout = json.load(open(path))
    pg = Page(layout, base)
    out = os.path.join(base, layout['out'])
    if '--grid' in sys.argv:
        stem, ext = os.path.splitext(out)
        pg.grid(stem + '-grid' + ext)
    todo = 0
    for it in layout['items']:
        if it['type'] == 'text' and not it.get('text'):
            todo += 1  # draft item not translated yet: leave the page untouched there
            continue
        getattr(pg, 'do_' + it['type'])(it)
    if todo:
        print(f'note: {todo} text item(s) have no English yet and were skipped')
    pg.im.save(out)
    print('wrote', out)


if __name__ == '__main__':
    main()
