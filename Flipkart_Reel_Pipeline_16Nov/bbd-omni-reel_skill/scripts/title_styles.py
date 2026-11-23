"""The user's 13 title text styles (27-Oct-2026; memory: diwali-title-fonts). style(text, n) converts plain text.
Rotate n across videos so every video has a different look. Rendered by supers.py (per-glyph font fallback)."""
import string
U, L, D = string.ascii_uppercase, string.ascii_lowercase, string.digits

def _math(text, up, lo, exc=None):
    exc = exc or {}
    out = []
    for c in text:
        if c in exc: out.append(exc[c])
        elif c in U: out.append(chr(up + U.index(c)))
        elif c in L: out.append(chr(lo + L.index(c)))
        else: out.append(c)
    return "".join(out)

SC = dict(zip(L, "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"))
SUP = dict(zip(U + L, "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾQᴿˢᵀᵁⱽᵂˣʸᶻ" + "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖqʳˢᵗᵘᵛʷˣʸᶻ"))
GRK = dict(zip(L, "αв¢∂єƒgнιנкℓмησρqяѕтυνωχуz"))

def _sc(t, first_cap=True):
    out, start = [], True
    for c in t:
        if c.isalpha():
            out.append(c.upper() if (first_cap and start) else SC.get(c.lower(), c)); start = False
        else:
            out.append(c); start = c in " \n-|:"
    return "".join(out)

STYLES = [
    ("bold script",      lambda t: _math(t, 0x1D4D0, 0x1D4EA)),
    ("fraktur",          lambda t: _math(t, 0x1D504, 0x1D51E, {"C": "ℭ", "H": "ℌ", "I": "ℑ", "R": "ℜ", "Z": "ℨ"})),
    ("bold fraktur",     lambda t: _math(t, 0x1D56C, 0x1D586)),
    ("sans bold italic", lambda t: _math(t, 0x1D63C, 0x1D656)),
    ("sans italic",      lambda t: _math(t, 0x1D608, 0x1D622)),
    ("sans",             lambda t: _math(t, 0x1D5A0, 0x1D5BA)),
    ("sans bold",        lambda t: _math(t, 0x1D5D4, 0x1D5EE)),
    ("monospace",        lambda t: _math(t, 0x1D670, 0x1D68A)),
    ("small caps",       lambda t: _sc(t, True)),
    ("greek look",       lambda t: "".join(GRK.get(c, c) if c.islower() else c for c in t)),
    ("superscript",      lambda t: "".join(SUP.get(c, c) for c in t)),
    ("all small caps",   lambda t: _sc(t.lower(), False)),
    ("syllabics F",      lambda t: _sc(t, True).replace("F", "ᖴ")),
]

SIZE_MULT = {"superscript": 1.8}   # superscript glyphs are tiny; render the super bigger so it stays readable


def size_for(name, size):
    return int(size * SIZE_MULT.get(name, 1.0))


BANNED = {"bold fraktur", "fraktur", "superscript"}   # user 27-Oct (row 423) bold fraktur; fraktur 28-Oct "LIVE" reads "LJVE"; superscript 28-Oct (row 12): letters jump up and down because many letters have no superscript glyph


def style(text, n):
    name, fn = STYLES[n % len(STYLES)]
    while name in BANNED:
        n += 1; name, fn = STYLES[n % len(STYLES)]
    return fn(text), name

if __name__ == "__main__":
    for i in range(len(STYLES)):
        print(i, *style("Flipkart Diwali Sale Is Live", i))
