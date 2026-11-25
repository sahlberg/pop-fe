"""Helpers for writing GAR layouts: lettered red/blue circle headings."""
COLS = [[226, 34, 46], [38, 146, 214]]


def circles(word, x0, pitch, cy, r=10.3, size=14.5, start=0):
    """One flat red/blue disc per letter (alternating, starting red) plus the letter."""
    out = []
    for i, ch in enumerate(word):
        cx = x0 + pitch * i
        if ch != ' ':
            out.append({"type": "erase", "box": [cx - r, cy - r, cx + r, cy + r],
                        "fill": COLS[(i + start) % 2], "shape": "ellipse"})
            out.append({"type": "text", "box": [cx - 10, cy - 11, cx + 10, cy + 11], "erase": False,
                        "size": size, "text": ch, "font": "Bold", "color": [255, 255, 255],
                        "align": "center", "valign": "middle"})
    return out
