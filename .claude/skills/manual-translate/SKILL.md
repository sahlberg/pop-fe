---
name: manual-translate
description: Translate scanned game-manual pages (Japanese PS1/PS2 manuals, jpg/png scans) to English in place, keeping the original layout, artwork and colours and replacing only the text. Use when the user asks to translate a manual, a manual page, or scans in a folder like tmp/GPM or tmp/GAR.
---

# Translating scanned manual pages in place

The result should look like an official English printing of the same manual.
Keep the page and change only the words:
- Keep the artwork, screenshots, bullets, tree lines, page numbers, logos and paper shading exactly as they are.
- Erase only the Japanese, and draw English in the same position, weight and colour.

The user compared a "redraw everything" version against this approach and
chose this one, so don't redraw whole pages.

Worked example in the repo: `manuals/groove-adventure-rave/`, with all
page layouts (`layouts/*.json`), the glossary, the circle-heading helper and
the finished English PDF. It has colourful pages with manga bubbles, white
outlined lettering over art, rotated text and lettered-circle headings. The
scans themselves are not committed: put them next to `layouts/` as `NNN.jpg`
to re-render. Copy from these layouts when starting a new manual.

Assemble the finished manual as a PDF: front cover, the `*-en.png` pages in
order, back cover, with the cover scans upscaled 3x to the same size (PIL
`save(..., save_all=True, append_images=..., resolution=300, quality=92)`).

## The tool: `mtrans.py` (pop-fe top level)

Every page is described by a JSON layout, and the tool renders it:

```
python3 mtrans.py <manual>/layouts/NNN.json          # render
python3 mtrans.py <manual>/layouts/NNN.json --grid   # also write <out>-grid.png with a coordinate grid
python3 mtrans.py draft <manual>/NNN.jpg             # Tesseract OCR -> starting layouts/NNN.json + NNN-draft.png
```

The module docstring at the top of `mtrans.py` is the full reference for the
layout format. Read it before writing layouts. In brief:

- The page is upscaled 3x with LANCZOS. **All coordinates and font sizes are in original scan pixels.** Measure them on the source scan.
- Layout fields:
  - `"src"` and `"out"` are paths relative to the layout file. The convention is `"../NNN.jpg"` → `"../NNN-en.png"`.
  - `"styles"` defines named font/size/colour/leading styles.
  - `"items"` lists the items.
- Fonts are Noto Sans in Regular, Medium, SemiBold and Bold. When text doesn't fit, the tool shrinks it to 70% and then switches to the Condensed face. A `warning: text does not fit` message means the box or the size needs fixing.
- Glyphs Noto Sans lacks (○ △ □ ↑ ↓ ★) fall back to DejaVu Sans automatically.
- Text items with an empty `"text"` are skipped, so a page can be done a piece at a time.
- Extra keys such as `"ja"` and `"note"` are ignored. Use `"note"` on the page to record what was left untranslated and why.

### Item types

- `erase`: removes what is in the box. Pick the fill mode by background:
  - **default (blend)**: plain paper or a gradient. Interpolates between the clean rows above and below the box. A flat fill would show as patches.
  - **`"fill": "light"` / `"dark"` (inpaint)**: light or dark text over pictures, screenshots or gradient pills. Removes only the text pixels and fills them in from their surroundings.
    - `"size"` is the glyph height in original px.
    - `"thresh"` (default 18) is the contrast that counts as text. Raise it to 25–50 for faint leftovers, or lower it to keep artwork lines.
  - **`"white": N` + `"grow": px`**, used with `"light"`: white lettering with a dark outline or glow over busy art. Only pixels whose darkest channel is above N count as text (around 225 works). `grow` then widens the mask, by about 3–4.5 px, to take the outline as well.
  - **`"fill": "median"`**: text on a solid coloured bar.
  - **`"fill": [r,g,b]`**: an exact flat colour. Add `"shape": "ellipse"` to blank a disc.
- `text`: erases the box (or `"erase": [box]`, or `"erase": false`), then draws wrapped text.
  - Options: `align`, `valign`, `size`, `font`, `color` and `leading`.
  - `"angle"` rotates the text counter-clockwise about the box centre.
  - `"stroke": [w, [r,g,b]]` draws outlined lettering.
  - `\n` forces a line break; a blank line starts a new paragraph.
- `toc`: a contents column. Keeps the original bullets, tree lines and page numbers, and redraws the labels and dot leaders.

## Workflow per manual

1. **Survey.** Look at every page:
   - Work out the file-number to printed-page offset. GPM `NNN.png` is page NNN-1; GAR `NNN.jpg` is page NNN-3.
   - Decide which pages to do. Ask in prose about the covers. On GPM the user left the front and back covers untranslated.
2. **Glossary first.** Create `<manual>/layouts/glossary.md` and fill it as you go. It holds:
   - character names, place names, items, skills and menu terms
   - re-spelled headings
   - any spelling you were not able to verify, marked UNVERIFIED

   Spelling sources:
   - The manual's own printed English and the official localisation (for example *Rave Master* names for GAR) come first.
   - A fan patch can also help. If an xdelta won't apply to the user's BIN, applying it to a zero-filled source can still recover its text (this worked for GPM staff names).

   Keep terms consistent across all pages.
3. **Per page:**
   1. Optionally run `draft` for rough boxes. Its `"ja"` OCR is unreliable and it misses text in screenshots. **Always translate from the image itself**, reading zoomed crops (PIL crop + resize). Draft never replaces a layout that already has English; never use `--force` on a hand-made layout.
   2. Measure the boxes on zoomed crops and grid renders. Find the row positions, the text hierarchy, and each level's colour and weight. Sample colours from the scan with numpy.
   3. Write `layouts/NNN.json`, render it, and **look at the output**. Check:
      - the whole page;
      - zoomed crops of every changed area, side by side with the original;
      - leftover Japanese, including ruby (furigana) above kanji;
      - halos, blotches and patchy fills;
      - text overflowing its box;
      - artwork damaged by the erase.
   4. Iterate. Fix leftovers with small extra erase boxes, often with a higher `thresh`.
   5. Never overwrite an existing `*-en.png` without asking. While experimenting, write to scratch files.
4. **Report** to the user:
   - the pages done;
   - judgement calls, such as invented romanisations or re-spelled headings;
   - what was left in Japanese (usually small in-game screenshots), and why.

## Style decisions the user approved

- Match each hierarchy level's weight and grey or colour: titles Bold, headings Bold or SemiBold, body Regular or Medium.
- For long labels use condensed glyphs, not smaller text.
- Keep the original bullets, numbering, page numbers, tree lines and decorative leaders.
- English text that was printed as English (logos, the contents page) stays. Only remove the ruby printed above it.
- Translate the larger in-game screenshots' menus when they're legible. Tiny item lists can stay, recorded in the layout `"note"`.
- Manga speech bubbles: erase the inside of the bubble and set centred text, sized to fill the bubble.
- Decorative lettered headings, one glyph per shape (GAR's alternating red and blue circles): re-spell them in English with one letter per disc. Choose a word or phrase that fits the number of circles; you may add or drop circles. `manuals/groove-adventure-rave/layouts/circles.py` generates the erase and letter items (`circles(word, x0, pitch, cy)`). A layout can be generated by a small Python script that writes the JSON.
- Legal or health notices (the Sony notice): translate fully, and keep the region and "for sale in Japan" logos with the English flowing around them.

## Changing the tool

`mtrans.py` (pop-fe top level) is shared by every manual:
- Keep changes backward-compatible: new behaviour only through new optional keys.
- After a change, re-render a few GPM layouts (for example 007, 030, 064, 090) to the scratchpad and check they are **pixel-identical** to the existing outputs (numpy maxdiff 0).
- Test risky changes on copies in the scratchpad, never in a manual's folder. A `--force` draft once destroyed a hand-made GPM layout.
- Document every new key in the module docstring.
