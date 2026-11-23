"""TEMPLATE per-run assembler: copy this file into the run folder as assemble.py and edit the CLIPS list, CHIPS, header text (base_png) and OUT.
Omni 360p clips (audio stripped) -> 1080x1920 with header, Flipkart logo, product chips and the CTA ONLY in the last 2 s -> Flipkart end slate -> music only
(fade-in/out, loudnorm) -> master + 480p. HARD CUTS only (XF = 0, no crossfades). Run: python3 assemble.py
Needs: ffmpeg, Pillow, brand assets in <pipeline folder>/assets/brand_beauty (FK_PIPE, set by pipeline.py finish) (Flipkart_End_Slate.mp4, logo_overlay.png, fonts/Poppins-ExtraBold.ttf, fonts/Inter-Bold.ttf)
and the run's music in <run>/assets/bgm/ (a different track every run, see PIPELINE_CONCEPT_LAB.md)."""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
PIPE = os.environ.get("FK_PIPE")  # the one pipeline folder (set by pipeline.py finish)
if not PIPE:   # 23-Nov: no guessed ~/Downloads path - run it through `pipeline.py finish <row>` or set FK_PIPE
    raise SystemExit("FK_PIPE is not set - run `pipeline.py finish <row>` (or export FK_PIPE=<Flipkart_Reel_Pipeline_16Nov folder>)")
ASSETS = os.path.join(PIPE, "assets", "brand_beauty")
FF = __import__("shutil").which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
W, H, FPS = 1080, 1920, 24
TRIM = 0                                   # drop the last 3 frames of every Omni clip (the forced last frame snaps/jumps); no regeneration
CLIPS = [("S1_hook", 3), ("S2_apply", 6), ("S3_show_minara", 4), ("S4_show_huda", 4), ("S5_show_teenteen", 4), ("S6_show_hdpro", 4)]
XF = 0.0                                   # crossfade between clips to soften cuts
FOOT = sum(d for _, d in CLIPS) - XF * (len(CLIPS) - 1)
START = {}; _t = 0.0
for _n, _d in CLIPS: START[_n] = _t; _t += _d - XF
SLATE = os.path.join(ASSETS, "Flipkart_End_Slate.mp4"); SLATE_D = 1.583333
MUSIC = os.path.join(ROOT, "assets", "bgm", "Upbeat Fashion Full.mp3")
WORK = os.path.join(ROOT, "assets", "_work"); os.makedirs(WORK, exist_ok=True)
OUT = os.path.join(ROOT, "exports", "Mehak_ID45")
PB = os.path.join(ASSETS, "fonts", "Poppins-ExtraBold.ttf"); IB = os.path.join(ASSETS, "fonts", "Inter-Bold.ttf")
CHIPS = [("Sultry Eyeshadow Palette", START["S2_apply"] + 0.8, START["S2_apply"] + 5.0), ("Minara Palette Duo", START["S3_show_minara"] + 0.8, START["S3_show_minara"] + 3.4),
         ("Huda Beauty Duo", START["S4_show_huda"] + 0.8, START["S4_show_huda"] + 3.4), ("Teen Teen Palette", START["S5_show_teenteen"] + 0.8, START["S5_show_teenteen"] + 3.4),
         ("HD Pro Palette", START["S6_show_hdpro"] + 0.8, START["S6_show_hdpro"] + 3.4)]
CTA = (FOOT - 2.0, FOOT)                      # "Shop Now" only in the last 2 s before the end slate


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def base_png(path):
    im = Image.open(os.path.join(ASSETS, "logo_overlay.png")).convert("RGBA")
    d = ImageDraw.Draw(im)
    hf = ImageFont.truetype(PB, 58)
    l1, l2 = "Flipkart beauty", "essentials"
    tw = max(d.textlength(l1, font=hf), d.textlength(l2, font=hf))
    x0, y0 = 54, 92
    d.rounded_rectangle([x0, y0, x0 + tw + 64, y0 + 176], radius=26, fill=(255, 246, 222, 240))
    d.text((x0 + 32, y0 + 14), l1, font=hf, fill=(176, 24, 24))
    d.text((x0 + 32, y0 + 88), l2, font=hf, fill=(176, 24, 24))
    im.save(path)


def chip_png(text, path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(IB, 46); tw = d.textlength(text, font=f)
    x0, y0 = (W - tw) // 2 - 40, H - 330
    d.rounded_rectangle([x0, y0, x0 + tw + 80, y0 + 96], radius=48, fill=(255, 255, 255, 235))
    d.text((x0 + 40, y0 + 20), text, font=f, fill=(110, 20, 40)); im.save(path)


def cta_png(path):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(IB, 62); t = "Shop Now on Flipkart"; tw = d.textlength(t, font=f)
    x0, y0 = (W - tw) // 2 - 56, 1560
    d.rounded_rectangle([x0, y0, x0 + tw + 112, y0 + 124], radius=62, fill=(40, 116, 240, 255))
    d.text((x0 + 56, y0 + 24), t, font=f, fill="white"); im.save(path)


norm = []
for name, dur in CLIPS:
    o = os.path.join(WORK, name + "_n.mp4")
    run([FF, "-y", "-i", os.path.join(ROOT, "assets", "video_clips", name + ".mp4"), "-an", "-t", f"{dur:.4f}",
         "-vf", f"scale={W}:{H}:flags=lanczos,fps={FPS},setsar=1", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", o])
    norm.append(o)
xf = os.path.join(WORK, "xf.mp4")
cl = os.path.join(WORK, "concat.txt"); open(cl, "w").write("".join(f"file '{p}'\n" for p in norm))
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", cl, "-c", "copy", xf])   # hard cuts, no crossfades
lst = xf

ov = []
p = os.path.join(WORK, "base.png"); base_png(p); ov.append((p, 0, FOOT))
for i, (t, a, b) in enumerate(CHIPS):
    p = os.path.join(WORK, f"chip{i}.png"); chip_png(t, p); ov.append((p, a, b))
p = os.path.join(WORK, "cta.png"); cta_png(p); ov.append((p, CTA[0], CTA[1]))

cmd = [FF, "-y", "-i", xf]
for p, _, _ in ov: cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{FOOT + 1:.3f}", "-i", p]
fc = "[0:v]null[v0];"
for i, (_, a, b) in enumerate(ov):
    fc += f"[v{i}][{i+1}:v]overlay=0:0:eof_action=pass:enable='between(t,{a:.2f},{b:.2f})'[v{i+1}];"
main = os.path.join(WORK, "main.mp4")
cmd += ["-filter_complex", fc.rstrip(";"), "-map", f"[v{len(ov)}]", "-an", "-t", f"{FOOT:.4f}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), main]
run(cmd)

slate = os.path.join(WORK, "slate_n.mp4")
run([FF, "-y", "-i", SLATE, "-an", "-vf", f"scale={W}:{H},fps={FPS},setsar=1", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", slate])
lst2 = os.path.join(WORK, "concat2.txt"); open(lst2, "w").write(f"file '{main}'\nfile '{slate}'\n")
joined = os.path.join(WORK, "joined.mp4")
run([FF, "-y", "-f", "concat", "-safe", "0", "-i", lst2, "-c", "copy", joined])
total = FOOT + SLATE_D
run([FF, "-y", "-i", joined, "-i", MUSIC,
     "-filter_complex", f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:st=0:d=0.3,afade=t=out:st={total-2:.3f}:d=2,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
     "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT + "_master.mp4"])
run([FF, "-y", "-i", OUT + "_master.mp4", "-vf", "scale=480:-2", "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-b:a", "96k", OUT + "_480p.mp4"])
print("done", OUT + "_master.mp4", round(total, 2), "s")
