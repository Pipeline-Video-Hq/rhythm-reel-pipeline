"""Client-approved title look (user 29-Oct-2026, board assets/refs/title_fonts_board_29oct.jpg):
8 real fonts, one per video, rotating; each font has its board style; two lines = big headline + small subline.
NO price, NO % in either line (user: "jo pahele feedback diye the unhi pe strict rehna").

plan.json super:  {"board": 0-7, "head": "Big Diwali Deals", "sub": "Home Decor · Diwali Sale LIVE",
                   "start": 0, "end": 17.4, "y": 0.1}
supers.render() hands any super with a "board" key to render() here.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts", "board")
# (name, file, variable-font instance, board style) - pairing exactly as on the board
FONTS = [
    ("Baloo 2 ExtraBold", "Baloo2.ttf", b"ExtraBold", "shadow"),
    ("Poppins ExtraBold", "Poppins-ExtraBold.otf", None, "sticker"),
    ("Bebas Neue", "BebasNeue.ttf", None, "bar"),
    ("Lobster", "Lobster.ttf", None, "shadow"),
    ("Pacifico", "Pacifico.ttf", None, "sticker"),
    ("Rozha One", "RozhaOne.ttf", None, "typed"),
    ("Kalam Bold", "KalamBold.ttf", None, "note"),
    ("Caveat Bold", "Caveat.ttf", b"Bold", "note"),
]
RED, YELLOW, CREAM, INK = (200, 22, 40, 255), (255, 214, 64, 255), (255, 244, 200, 250), (35, 30, 30, 255)


def _font(i, size):
    name, f, inst, _ = FONTS[i]
    ft = ImageFont.truetype(os.path.join(FD, f), size)
    if inst:
        try:
            ft.set_variation_by_name(inst)
        except Exception:
            pass
    return ft


def _fit(i, text, size, max_w):
    while size > 20:
        ft = _font(i, size)
        if ft.getbbox(text)[2] <= max_w:
            return ft
        size -= 2
    return _font(i, size)


def _text(txt, ft, fill):
    l, t, r, b = ft.getbbox(txt)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), txt, font=ft, fill=fill)
    return im


def _shadowed(im, blur=6, off=(3, 5), alpha=0.75):
    pad = blur * 3
    out = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
    sh = Image.new("RGBA", im.size, (0, 0, 0, 255)); sh.putalpha(im.split()[3].point(lambda a: int(a * alpha)))
    out.paste(sh, (pad + off[0], pad + off[1]), sh)
    out = out.filter(ImageFilter.GaussianBlur(blur))
    out.alpha_composite(im, (pad, pad))
    return out


def _stack(imgs, gap, align="center"):
    w = max(i.width for i in imgs); h = sum(i.height for i in imgs) + gap * (len(imgs) - 1)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0)); y = 0
    for i in imgs:
        x = (w - i.width) // 2 if align == "center" else 0
        out.alpha_composite(i, (x, y)); y += i.height + gap
    return out


def _panel(content, fill, pad, radius):
    out = Image.new("RGBA", (content.width + 2 * pad[0], content.height + 2 * pad[1]), (0, 0, 0, 0))
    ImageDraw.Draw(out).rounded_rectangle([0, 0, out.width - 1, out.height - 1], radius=radius, fill=fill)
    out.alpha_composite(content, pad)
    return out


def _stack_s(items, gap):          # 30-Oct: drop an empty subline (title = sheet "Text for the Film" only)
    items = [x for x in items if x is not None]
    return items[0] if len(items) == 1 else _stack(items, gap)


def block(i, head, sub, max_w=900):
    style = FONTS[i][3]
    if len(head) > 22 and not sub:      # long sheet text: split into two lines (30-Oct: >22 chars, one line got too small at 480p) (at ":" if there is one, else mid-word)
        if ":" in head:
            head, sub = head.split(":", 1)[0] + ":", head.split(":", 1)[1].strip()
        else:
            w = head.split(); k = len(w) // 2 + (len(w) % 2)
            head, sub = " ".join(w[:k]), " ".join(w[k:])
        two_big = True
    else:
        two_big = False
    caps = style == "bar"
    head, sub = (head.upper(), sub.upper()) if caps else (head, sub)
    hs = {"shadow": 92, "sticker": 74, "bar": 104, "typed": 80, "note": 84}[style]
    hft = _fit(i, head, hs, max_w - 80)
    sft = _fit(i if style != "bar" else i, sub, int(hs * (0.85 if two_big else 0.5)), max_w - 80) if sub else None
    T = lambda txt, ft, col: _text(txt, ft, col) if txt else None
    if style == "shadow":
        b = _stack_s([T(head, hft, (255, 255, 255, 255)), T(sub, sft, (255, 255, 255, 255))], 8)
        return _shadowed(b)
    if style == "sticker":
        b = _stack_s([T(head, hft, RED), T(sub, sft, INK)], 10)
        return _shadowed(_panel(b, YELLOW, (34, 20), 30), blur=5, off=(2, 4), alpha=0.45)
    if style == "bar":
        b = _stack_s([T(head, hft, (255, 255, 255, 255)), T(sub, sft, YELLOW)], 10)
        return _panel(b, (25, 25, 25, 225), (30, 18), 6)
    if style == "typed":
        h = _panel(_text(head, hft, (20, 20, 20, 255)), (255, 255, 255, 250), (22, 10), 4)
        s = _panel(_text(sub, sft, (20, 20, 20, 255)), (255, 255, 255, 250), (16, 6), 4) if sub else None
        return _shadowed(_stack_s([h, s], 6), blur=4, off=(2, 3), alpha=0.35)
    # note: cream card, red handwriting, slight tilt
    b = _stack_s([T(head, hft, RED), T(sub, sft, (110, 30, 30, 255))], 6)
    card = _shadowed(_panel(b, CREAM, (30, 16), 6), blur=5, off=(2, 4), alpha=0.4)
    return card.rotate(2.0, resample=Image.BICUBIC, expand=True)


def render(s, out_png):
    i = int(s["board"]) % len(FONTS)
    b = block(i, s["head"], s.get("sub", ""), int(W * s.get("max_w", 0.86)))
    frame = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx, cy = int(W * s.get("x", 0.5)), int(H * s.get("y", 0.1))
    x0 = min(max(cx - b.width // 2, 0), W - b.width); y0 = min(max(cy - b.height // 2, 44), H - b.height)   # 30-Oct: 44 px top margin (two-line titles touched the edge)
    frame.alpha_composite(b, (x0, y0))
    frame.save(out_png)
    return out_png, [x0, y0, x0 + b.width, y0 + b.height]


if __name__ == "__main__":   # preview sheet of all 8: python3 board_title.py out.jpg
    import sys
    sheet = Image.new("RGB", (4 * 540, 2 * 300), (90, 80, 70))
    for i in range(8):
        t = block(i, "Big Diwali Deals", "Home Decor · Diwali Sale LIVE", 500)
        t.thumbnail((520, 280))
        sheet.paste(t, ((i % 4) * 540 + (540 - t.width) // 2, (i // 4) * 300 + (300 - t.height) // 2), t)
    sheet.save(sys.argv[1])
