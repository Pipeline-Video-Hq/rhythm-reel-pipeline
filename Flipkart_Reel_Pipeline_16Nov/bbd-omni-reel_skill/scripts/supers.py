"""Render one on-screen super as a full-frame 1080x1920 RGBA PNG, in a creator-native style.

Styles (copy the reference reel's own text look; never design a nicer one):
  outline  white bold text with a hard black outline (default Reels look)
  pill     white text on Instagram's translucent black rounded pill
  box      black text on a white box (CapCut "classic")
  bar      white bold text on a solid black rectangle (quoted top bar)
  plain    text with soft shadow only
Emoji are drawn with Apple Color Emoji. x/y are the CENTRE of the text block as fractions of the frame.
Returns the PNG path and the pixel bbox (for the text-never-on-product QC).
"""
import os, re, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FONT_BOLD, FONT_DEVA, EMOJI_FONT

W, H = 1080, 1920
EMOJI_RE = re.compile("([\U0001F300-\U0001FAFF☀-➿⭐❤\U0001F000-\U0001F2FF][️‍\U0001F3FB-\U0001F3FF\U0001F300-\U0001FAFF♀♂]*)")


def _hex(c):
    if isinstance(c, (list, tuple)):
        return tuple(c)
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _font(size, text):
    return ImageFont.truetype(FONT_DEVA if re.search(r"[ऀ-ॿ]", text) else FONT_BOLD, size)


# Fallback fonts for the user's "fancy" title styles (27-Oct-2026: 𝓕𝓵𝓲𝓹𝓴𝓪𝓻𝓽, 𝔉𝔩𝔦𝔭𝔨𝔞𝔯𝔱, Fʟɪᴘᴋᴀʀᴛ, ᶠˡⁱᵖᵏᵃʳᵗ, ᖴ ...).
# Inter has none of these glyphs; each character is drawn with the first font that has it.
_FALLBACK = [("/System/Library/Fonts/Supplemental/STIXTwoMath.otf", 0), ("/System/Library/Fonts/SFNS.ttf", 0),
             ("/System/Library/Fonts/Geneva.ttf", 0), ("/System/Library/Fonts/Menlo.ttc", 1),
             ("/System/Library/Fonts/Supplemental/EuphemiaCAS.ttc", 1),
             ("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 0)]
_CMAPS = {}


def _cmap(path, idx):
    k = (path, idx)
    if k not in _CMAPS:
        try:
            from fontTools.ttLib import TTFont, TTCollection
            t = TTCollection(path).fonts[idx] if path.endswith(".ttc") else TTFont(path)
            _CMAPS[k] = set(t.getBestCmap().keys())
        except Exception:
            _CMAPS[k] = set()
    return _CMAPS[k]


def _runs(text):
    """Split text into (substring, (path, index)) runs; None font = the normal Inter/Devanagari font."""
    base = (FONT_DEVA if re.search(r"[ऀ-ॿ]", text) else FONT_BOLD, 0)
    need = {ord(c) for c in text if not c.isspace()}
    # one font for the whole run when any single font covers every glyph (keeps weight/size consistent)
    sup = any(0x1D2C <= ord(c) <= 0x1DBF or 0x02B0 <= ord(c) <= 0x02FF or ord(c) in (0x2071, 0x207F) for c in text)
    for fb in ([] if sup else [base]) + _FALLBACK:      # superscript style: never let Inter fake it at full size
        if os.path.exists(fb[0]) and need <= _cmap(*fb):
            return [[text, fb]]
    out = []
    for ch in text:
        f = base
        if ch != " " and ord(ch) not in _cmap(*base):
            f = next((fb for fb in _FALLBACK if os.path.exists(fb[0]) and ord(ch) in _cmap(*fb)), base)
        if out and (out[-1][1] == f or ch == " "):
            out[-1][0] += ch
        else:
            out.append([ch, f])
    return out


def _tfont(fp, size):
    return ImageFont.truetype(fp[0], size, index=fp[1])


def _textlen(t, size):
    return sum(_tfont(f, size).getlength(r) for r, f in _runs(t)) if t else 0


def _emoji(ch, h):
    # PIL cannot shape skin-tone / ZWJ sequences without raqm: draw the base emoji only
    ch = re.sub("[\U0001F3FB-\U0001F3FF\u200d\u2640\u2642]", "", ch)
    ch = ch[:2] if len(ch) > 1 and ch[1] == "\ufe0f" else ch[:1]
    try:
        f = ImageFont.truetype(EMOJI_FONT, 160)
        im = Image.new("RGBA", (220, 220), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
        im = im.crop(im.getbbox() or (0, 0, 1, 1))
        return im.resize((max(1, int(im.width * h / im.height)), h), Image.LANCZOS)
    except Exception:
        return None


def _line_img(text, size, fill, stroke, stroke_col):
    """One line: text runs + emoji runs side by side."""
    # ~~text~~ = struck-through run (MRP next to the sale price)
    parts = [p for p in re.split(r"(~~[^~]+~~)", text) if p]
    parts = [q for p in parts for q in ([p] if p.startswith("~~") else [x for x in EMOJI_RE.split(p) if x])]
    imgs = []
    asc = int(size * 1.25)
    for p in parts:
        if p.startswith("~~") and p.endswith("~~"):
            t = p[2:-2]; f = _font(int(size * 0.8), t)
            bb = f.getbbox(t, stroke_width=stroke)
            im = Image.new("RGBA", (bb[2] - bb[0] + 4, asc + stroke * 2), (0, 0, 0, 0))
            d = ImageDraw.Draw(im)
            d.text((-bb[0] + 2, stroke + int(size * 0.12)), t, font=f, fill=fill + (255,), stroke_width=stroke, stroke_fill=stroke_col + (255,))
            y = stroke + int(size * 0.12) + (bb[1] + bb[3]) // 2 - 2
            d.line([(2, y), (im.width - 2, y)], fill=fill + (255,), width=max(3, size // 14))
            imgs.append(("t", im)); continue
        if EMOJI_RE.fullmatch(p):
            e = _emoji(p, int(size * 0.95))
            if e:
                imgs.append(("e", e))
            continue
        for r, fp in _runs(p):
            f = _tfont(fp, size)
            bb = f.getbbox(r, stroke_width=stroke)
            # baseline-aligned: draw at the same y for every run, keep the advance width
            w = max(int(f.getlength(r)) + stroke * 2 + 4, bb[2] + 4)
            im = Image.new("RGBA", (w, asc + stroke * 2 + int(size * 0.3)), (0, 0, 0, 0))
            ImageDraw.Draw(im).text((2, stroke + int(size * 1.0)), r, font=f, anchor="ls", fill=fill + (255,),
                                    stroke_width=stroke, stroke_fill=stroke_col + (255,))
            imgs.append(("r", im))
    if not imgs:
        return Image.new("RGBA", (1, asc), (0, 0, 0, 0))
    hgt = max(i.height for _, i in imgs)
    wid = sum(i.width for _, i in imgs) + sum(0 if k == "r" else 6 for k, _ in imgs)
    out = Image.new("RGBA", (wid, hgt), (0, 0, 0, 0))
    x = 0
    for k, i in imgs:
        y = (hgt - i.height) // 2 if k == "e" else 0
        out.paste(i, (x, y), i); x += i.width + (0 if k == "r" else 6)
    return out


def _wrap(text, size, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _textlen(EMOJI_RE.sub("MM", t.replace("~~", "")), size) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def render(s, out_png):
    if "board" in s:      # 29-Oct-2026 client-approved title board (board_title.py)
        import board_title
        return board_title.render(s, out_png)
    text = s["text"].replace("\\n", "\n")
    style = s.get("style", "outline")
    size = int(s.get("size", 58))
    max_w = int(W * s.get("max_w", 0.84))
    fill = _hex(s.get("color", "#ffffff" if style != "box" else "#000000"))
    lines = []
    for para in text.split("\n"):
        lines += _wrap(para, size, max_w)
    stroke = max(3, size // 10) if style == "outline" else 0
    limgs = [_line_img(l, size, fill, stroke, (0, 0, 0)) for l in lines]
    gap = int(size * float(s.get("line_gap", 0.18)))       # negative allowed: tighter lines
    for k, li in enumerate(limgs):                            # trim empty rows above/below each line's ink
        bb = li.getbbox()
        if bb:
            limgs[k] = li.crop((0, max(0, bb[1] - 2), li.width, min(li.height, bb[3] + 2)))
    bw = max(i.width for i in limgs)
    bh = sum(i.height for i in limgs) + gap * (len(limgs) - 1)
    bg = s.get("bg")          # optional translucent panel behind ANY style, e.g. [0, 0, 0, 110]
    pad_x, pad_y = (int(size * 0.55), int(size * 0.32)) if (style in ("pill", "box", "bar") or bg) else (0, 0)
    block = Image.new("RGBA", (bw + 2 * pad_x, bh + 2 * pad_y), (0, 0, 0, 0))
    d = ImageDraw.Draw(block)
    if bg:
        d.rounded_rectangle([0, 0, block.width - 1, block.height - 1], radius=int(size * 0.3), fill=tuple(bg))
    elif style == "pill":
        d.rounded_rectangle([0, 0, block.width - 1, block.height - 1], radius=int(size * 0.45), fill=(0, 0, 0, 150))
    elif style == "box":
        d.rounded_rectangle([0, 0, block.width - 1, block.height - 1], radius=int(size * 0.18), fill=(255, 255, 255, 255))
    elif style == "bar":
        d.rounded_rectangle([0, 0, block.width - 1, block.height - 1], radius=int(size * 0.12), fill=(0, 0, 0, 255))
    y = pad_y
    align = s.get("align", "center")
    for li in limgs:
        x = pad_x + ((bw - li.width) // 2 if align == "center" else 0 if align == "left" else bw - li.width)
        block.paste(li, (x, y), li); y += li.height + gap
    if style == "plain":
        sh = Image.new("RGBA", block.size, (0, 0, 0, 0)); sh.putalpha(block.split()[3].point(lambda a: int(a * 0.6)))
        sh = sh.filter(ImageFilter.GaussianBlur(4))
        base = Image.new("RGBA", block.size, (0, 0, 0, 0)); base.paste(sh, (3, 4), sh); base.alpha_composite(block); block = base
    if s.get("tilt"):
        block = block.rotate(float(s["tilt"]), resample=Image.BICUBIC, expand=True)
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = int(W * s.get("x", 0.5)), int(H * s.get("y", 0.2))
    x0 = min(max(cx - block.width // 2, 0), W - block.width)
    y0 = min(max(cy - block.height // 2, 0), H - block.height)
    frame.paste(block, (x0, y0), block)
    frame.save(out_png)
    return out_png, [x0, y0, x0 + block.width, y0 + block.height]


if __name__ == "__main__":
    import json
    p, bb = render(json.loads(sys.argv[1]), sys.argv[2])
    print(p, bb)
