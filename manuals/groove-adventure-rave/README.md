# Groove Adventure Rave - Yuukyuu no Kizuna (SLPM-87011): English manual

An in-place English translation of the Japanese manual, made with
`mtrans.py` in the pop-fe top directory. The `.pdf` is the finished manual.

`layouts/NNN.json` describes the translation of scan `NNN.jpg` (printed page
NNN-3; 002 is the front cover, 029 the back cover, 003 the untranslated inside
cover). The scans are not included. They are available as two-page spreads at

    https://psinstructionmanual.com/raveyukyunokizuna/

(files RAVEYukyuNoKizuna001.jpg ... 014.jpg, 1400x697; 000 is a box photo and
is not needed). Spread 001 is back cover | front cover; spread k (2-14) is
pages 2k-1 | 2k. Split them into the NNN.jpg names the layouts expect with

    python3 - <<'PY'
    from PIL import Image
    for k in range(1, 15):
        im = Image.open(f'RAVEYukyuNoKizuna{k:03d}.jpg')
        w, h = im.size
        left, right = (29, 2) if k == 1 else (2 * k - 1, 2 * k)
        im.crop((0, 0, w // 2, h)).save(f'{left:03d}.jpg', quality=95)
        im.crop((w // 2, 0, w, h)).save(f'{right:03d}.jpg', quality=95)
    PY

To re-render a page, put the scans in this directory and run

    python3 ../../mtrans.py layouts/014.json      # writes 014-en.png

`layouts/glossary.md` lists the names and terms used, and `layouts/circles.py`
generates the red/blue lettered-circle headings.

See `.claude/skills/manual-translate/SKILL.md` for the method.
