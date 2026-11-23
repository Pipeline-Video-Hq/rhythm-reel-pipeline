"""QC material for a built master (or one clip): contact sheets, loudness, super boxes.

    python3 qc.py <row>                 -> row_NNN/qc/master_sheet_*.png + qc/report.json
    python3 qc.py <row> clips/s2.mp4    -> qc sheet for one clip (check BEFORE assembling)

Sheets: 4 frames per second, 6 per row, each tile stamped with its time; super boxes drawn in red so a
reviewer can see at a glance whether text ever touches the product or the face.

Speech check (master and clips): word-timed transcript (whisper large-v3-turbo, Hindi) -> qc/words_<name>.txt and
repeats: the same 1-4 words said twice in a row (Omni often says a phrase twice, e.g. "ek dum ready, ek dum ready").
Turbo transcribes; any section where it hears a repeat is re-transcribed with large-v3 and only a repeat that
large-v3 also hears counts (turbo alone invents repeats). A repeated phrase of 2+ words = FAIL (re-trim to keep one copy, or re-take); a single repeated word = WARN (could be
natural reduplication like "jaldi jaldi" - check it against the script). Clip mode prints the word times so the trim
can drop the second copy and any ad-lib after the script's last line.
"""
import json, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *


def frames(src, fps, tmp):
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-vf", f"fps={fps},scale=270:480", os.path.join(tmp, "f%04d.jpg")])
    return sorted(os.path.join(tmp, f) for f in os.listdir(tmp) if f.endswith(".jpg"))


def sheet(src, out_prefix, boxes=None, fps=4, per_sheet=48):
    tmp = tempfile.mkdtemp()
    fs = frames(src, fps, tmp)
    outs = []
    for k in range(0, len(fs), per_sheet):
        chunk = fs[k:k + per_sheet]
        rows = (len(chunk) + 5) // 6
        S = Image.new("RGB", (6 * 274, rows * 484), (16, 16, 16))
        for i, f in enumerate(chunk):
            t = (k + i) / fps
            im = Image.open(f).convert("RGB"); d = ImageDraw.Draw(im)
            for b in boxes or []:
                if b["start"] <= t <= b["end"]:
                    x0, y0, x1, y1 = [v / 4 for v in b["bbox"]]
                    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 0), width=2)
            d.rectangle([0, 0, 58, 16], fill=(0, 0, 0)); d.text((3, 2), f"{t:5.2f}s", fill=(255, 255, 0))
            S.paste(im, ((i % 6) * 274, (i // 6) * 484))
        o = f"{out_prefix}_{k // per_sheet + 1}.png"; S.save(o); outs.append(o)
    return outs


WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "mlx-community/whisper-large-v3-turbo")
CONFIRM_MODEL = os.environ.get("WHISPER_CONFIRM_MODEL", "mlx-community/whisper-large-v3-mlx")


def words(src, tmp=None, model=None):
    """[(word, start, end)] from whisper, Hindi, word timestamps. Drops zero-length hallucination tokens."""
    import shutil
    wb = WHISPER if shutil.which(WHISPER) else next((p for p in (
        os.path.expanduser("~/Downloads/FLipkart/Flipkart/creator-research/tracker/.venv/bin/mlx_whisper"),) if os.path.exists(p)), None)
    if not wb:
        return None
    tmp = tmp or tempfile.mkdtemp()
    subprocess.run([wb, src, "--model", model or WHISPER_MODEL, "--language", "hi", "--word-timestamps", "True",
                    "--output-format", "json", "--output-dir", tmp], capture_output=True)
    j = os.path.join(tmp, os.path.splitext(os.path.basename(src))[0] + ".json")
    if not os.path.exists(j) or os.path.getmtime(j) < os.path.getmtime(src):
        return None
    out = []
    for seg in load(j)["segments"]:
        for w in seg.get("words", []):
            if w["end"] - w["start"] >= 0.04:
                out.append((w["word"].strip(), round(w["start"], 2), round(w["end"], 2)))
    return out


def _norm(w):
    return re.sub(r"[^\w]", "", w.lower())


def repeats(ws, max_gap=2.5):
    """Back-to-back repeated n-grams (n=4..1). Returns [{n, text, t1, t2, level}]."""
    if not ws:
        return []
    n_ = [_norm(w) for w, _, _ in ws]; hits = []; used = set()
    for n in (4, 3, 2, 1):
        for i in range(len(ws) - 2 * n + 1):
            a, b = n_[i:i + n], n_[i + n:i + 2 * n]
            if a == b and all(a) and i not in used and ws[i + n][1] - ws[i + n - 1][2] <= max_gap:
                hits.append(dict(n=n, text=" ".join(w for w, _, _ in ws[i:i + n]), t1=ws[i][1], t2=ws[i + n][1],
                                 level="FAIL" if n >= 2 else "WARN"))
                used.update(range(i, i + 2 * n))
    return sorted(hits, key=lambda h: h["t1"])


def words_chunked(src, bounds):
    """Transcribe each [t0, t1] section separately (whisper drops words on a long master with a music bed)."""
    out, tmp = [], tempfile.mkdtemp()
    for k, (t0, t1) in enumerate(bounds):
        wav = os.path.join(tmp, f"c{k}.wav")
        run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t0:.2f}", "-to", f"{t1:.2f}", "-i", src, "-vn", "-ac", "1", "-ar", "16000", wav])
        ws = words(wav, tmp)
        if ws is None:
            return None
        if repeats(ws):   # turbo sometimes hears a phrase twice: a repeat counts only if large-v3 hears it too
            os.remove(os.path.join(tmp, f"c{k}.json"))
            ws = words(wav, tmp, CONFIRM_MODEL) or ws
        out += [(w, round(a + t0, 2), round(b + t0, 2)) for w, a, b in ws]
    return out


def speech_check(src, out_txt, bounds=None):
    ws = words_chunked(src, bounds) if bounds else words(src)
    if ws is not None and not bounds and repeats(ws):
        ws = words(src, None, CONFIRM_MODEL) or ws
    if ws is None:
        print("speech check skipped: no whisper (set WHISPER_BIN)"); return None
    open(out_txt, "w").write("\n".join(f"{s:6.2f}-{e:6.2f}  {w}" for w, s, e in ws) + "\n")
    reps = repeats(ws)
    for h in reps:
        print(f"REPEAT {h['level']}: '{h['text']}' at {h['t1']:.2f}s and again at {h['t2']:.2f}s")
    return dict(transcript=" ".join(w for w, _, _ in ws), words_file=out_txt, repeats=reps)


def loudness(src):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", src, "-filter_complex", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r); TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)
    return dict(lufs=float(I[-1]) if I else None, true_peak=float(TP[-1]) if TP else None)


def main():
    row = int(sys.argv[1]); d = row_dir(row); os.makedirs(os.path.join(d, "qc"), exist_ok=True)
    if len(sys.argv) > 2:
        src = os.path.join(d, sys.argv[2]); name = os.path.splitext(os.path.basename(src))[0]
        print("\n".join(sheet(src, os.path.join(d, "qc", f"clip_{name}"), fps=4)))
        sp = speech_check(src, os.path.join(d, "qc", f"words_{name}.txt"))
        if sp:
            print("words:", sp["words_file"]); print(sp["transcript"])
        return
    brief = load(os.path.join(d, "brief.json"))
    src = os.path.join(d, "final", brief["out_name"])
    boxes = load(os.path.join(d, "work", "super_boxes.json"), [])
    outs = sheet(src, os.path.join(d, "qc", "master_sheet"), boxes, fps=4)
    rep = dict(master=src, duration=round(dur(src), 2), **loudness(src), sheets=outs, supers=boxes)
    rep["checks"] = dict(duration_ok=15 <= rep["duration"] <= 35,
                         loudness_ok=rep["lufs"] is not None and -16 <= rep["lufs"] <= -12,
                         peak_ok=rep["true_peak"] is not None and rep["true_peak"] <= -1.0)
    if brief.get("music_only") is not True:
        plan = load(os.path.join(d, "plan.json"), {})
        t, bounds = 0.0, []
        for seg in plan.get("segments", []):
            L = (seg["out"] - seg["in"]) / seg.get("speed", 1.0); bounds.append((t, t + L)); t += L
        sp = speech_check(src, os.path.join(d, "qc", "words_master.txt"), bounds or None)
        if sp:
            rep["speech"] = sp
            rep["checks"]["no_repeats"] = not any(h["level"] == "FAIL" for h in sp["repeats"])
    save(rep, os.path.join(d, "qc", "report.json"))
    print(json.dumps({k: rep[k] for k in ("duration", "lufs", "true_peak", "checks")}), "\n" + "\n".join(outs))
    if rep.get("speech"):
        print("transcript:", rep["speech"]["transcript"])


if __name__ == "__main__":
    main()
