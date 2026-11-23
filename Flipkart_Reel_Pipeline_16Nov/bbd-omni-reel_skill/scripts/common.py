"""Shared paths and helpers for the BBD Omni reel skill. Everything is relative to the skill folder, so the kit
runs wherever it is unzipped. Output goes to $BBD_OUT (default ~/bbd_reels)."""
import json, os, re, subprocess

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(SKILL, "data")               # sheet snapshot, reference per row, column-L scripts, ref images
ASSETS = os.path.join(SKILL, "assets")
PERSONAS = os.path.join(SKILL, "personas")       # <name lowercase>.jpg, one per persona (column C)
# 23-Nov: no machine-specific default (was one person's Downloads folder); pipeline.py always sets BBD_OUT
OUT = os.path.abspath(os.path.expanduser(os.environ.get("BBD_OUT") or "~/bbd_reels"))
LOGO = os.path.join(ASSETS, "brand", "bbd_logo_overlay.png")      # client BBD badge, on every frame
ENDSLATE = os.path.join(ASSETS, "brand", "bbd_endslate.mp4")       # BBD lockup end card
MUSIC = os.path.join(ASSETS, "music", "bed_instrumental.mp3")
FONT_BOLD = os.path.join(ASSETS, "fonts", "Inter-Bold.otf")
FONT_SEMI = os.path.join(ASSETS, "fonts", "Inter-SemiBold.otf")
FONT_DEVA = os.path.join(ASSETS, "fonts", "NotoSansDevanagari-Bold.ttf")
EMOJI_FONT = "/System/Library/Fonts/Apple Color Emoji.ttc"
WHISPER = os.environ.get("WHISPER_BIN") or "mlx_whisper"   # optional, only for listening checks
SHEET_ID = "1zfBPuJbX-Xw9gY8Ve7Pmav9oMKz2x8erj3PuOeI263Y"
SHEET_GID = 1110512177   # BBD tab

MALE = {"Arjun", "Kabir", "Aarav", "Rohan", "Aditya", "Vihaan", "Ishaan", "Laksh", "Omkar", "Dev", "Advik", "Aarush", "Reyansh", "Vivaan"}
KIDS = {"Advik", "Aarush", "Reyansh", "Vivaan", "Diya", "Navya", "Myra", "Ira"}


def row_dir(row):
    return os.path.join(OUT, f"row_{int(row):03d}")


def load(path, default=None):
    if not os.path.exists(path):
        return default
    return json.load(open(path))


def save(obj, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def gender(name):
    return "male" if name in MALE else "female"


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "", s.replace("'", "").title())[:24]


def dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("FAILED: " + " ".join(cmd[:6]) + " ...\n" + r.stderr[-2500:])
    return r
