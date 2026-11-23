"""Automatic speech gate for one generated clip.

    python3 clipcheck.py <row> <shot>                 # line comes from row_NNN/shots.json
    python3 clipcheck.py <row> <shot> --clip clips/s3.mp4 --line "Aur ye ..."   # ad hoc

Transcribes (whisper turbo; a failing result is re-heard with large-v3 before it counts), compares with the
scripted romanised line (lines.compare), and writes row_NNN/clips/s<shot>.check.json:
  verdict PASS | FIX (fixable in the edit: repeat / ad-lib inside or after the line) | RETAKE (scripted words missing)
  keep: [[in, out], ...]  - the spans to use in plan.json (repeat copies and ad-libs already cut out)
Prints one line per clip. Use the keep spans as the plan segments; a RETAKE needs a new generation.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from lines import compare
import qc

PAD_IN, PAD_OUT = 0.12, 0.22


def clip_dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout.strip() or 0)


def energy(src):
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    a = np.frombuffer(raw, np.int16).astype(float) / 32768
    w = 320                                                  # 20 ms frames
    return [float(20 * np.log10(np.sqrt(np.mean(a[i:i + w] ** 2)) + 1e-9)) for i in range(0, max(0, len(a) - w), w)]


def snap(t, env, lo, hi):
    """Move a cut to the quietest 20 ms frame in [t+lo, t+hi] (Whisper word times are +-0.15 s)."""
    if not env:
        return t
    i0, i1 = max(0, int((t + lo) / 0.02)), min(len(env) - 1, int((t + hi) / 0.02))
    if i1 <= i0:
        return t
    i = min(range(i0, i1 + 1), key=lambda k: env[k])
    return round(i * 0.02 + 0.01, 2)


def agreed_extras(res):
    """Ad-libs only count when BOTH models hear extra speech at the same time (one model mishearing a real
    word as 'extra' must never cut it)."""
    rs = list(res.values())
    if len(rs) < 2:
        return []
    out = []
    for text, a, b in rs[0]["extra"]:
        if any(a < e2 and a2 < b for _, a2, e2 in rs[1]["extra"]):
            out.append((text, a, b))
    return out


def keep_spans(base, cut_sources, dur, env=None, extras=()):
    t0 = max(0.0, (base["first"] or 0) - PAD_IN)
    t1 = min(dur, snap((base["last"] or dur) + 0.05, env, 0.0, 0.3) + 0.05)
    cuts = []
    for r in cut_sources:
        for text, a, b, c in r["repeats"]:          # keep first copy, drop the second
            cuts.append((snap(b, env, -0.2, 0.1), snap(c, env, -0.15, 0.2)))
    for text, a, b in extras:                       # ad-lib inside the line (both models agree)
        if t0 + 0.2 < a and b < t1 - 0.2 and (len(text.split()) >= 2 or len(text) >= 4):
            cuts.append((snap(a, env, -0.2, 0.05), snap(b, env, -0.05, 0.2)))
    spans, cur = [], t0
    for a, b in sorted(cuts):
        if a > cur + 0.3:
            spans.append([round(cur, 2), round(a, 2)])
        cur = max(cur, b)
    if t1 > cur + 0.3:
        spans.append([round(cur, 2), round(t1, 2)])
    return spans


def render(src, spans, wav):
    fc = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(spans))
    fc += "".join(f"[a{i}]" for i in range(len(spans))) + f"concat=n={len(spans)}:v=0:a=1,aresample=16000[o]"
    run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-filter_complex", fc, "-map", "[o]", "-ac", "1", wav])


def verify(src, spans, line, need_cov, tmp):
    wav = os.path.join(tmp, f"v{abs(hash(str(spans)))}.wav")
    render(src, spans, wav)
    rs = [compare(line, qc.words(wav, tmp, m) or []) for m in (qc.WHISPER_MODEL, qc.CONFIRM_MODEL)]
    cov = max(r["coverage"] for r in rs)
    clean = not any(r["repeats"] for r in rs) and not any(len(e[0].split()) >= 2 for r in rs for e in r["extra"])
    return cov >= need_cov - 0.05 and clean, cov, rs


def check(row, shot, clip=None, line=None):
    import tempfile
    d = row_dir(row)
    if line is None:
        sh = load(os.path.join(d, "shots.json"))["shots"][shot - 1]
        line, clip = sh["line"], clip or sh.get("clip", f"clips/s{shot}.mp4")
    clip = clip or f"clips/s{shot}.mp4"
    src = os.path.join(d, clip)
    tmp = tempfile.mkdtemp()
    heard = {m: qc.words(src, tmp, m) or [] for m in (qc.WHISPER_MODEL, qc.CONFIRM_MODEL)}
    res = {m: compare(line, w) for m, w in heard.items()}
    base_m = max(res, key=lambda m: (res[m]["coverage"], m == qc.CONFIRM_MODEL))
    base = res[base_m]
    dur = clip_dur(src)
    env = energy(src)
    # brand words (Capitalised) are often misheard by Whisper - tolerated; any other content word missing, or two
    # scripted words missing in a row ("lace up"), means Omni dropped part of the line -> RETAKE
    real_missing = [m for m in base["missing"] if len(re.sub(r"\W", "", m)) >= 4 and not m[:1].isupper()]
    verdict, keep, vcov = "RETAKE", [], None
    if not real_missing and base.get("max_run", 0) < 2:
        others = [r for m, r in res.items() if m != base_m]
        ex = agreed_extras(res)
        tries = [keep_spans(base, [base], dur, env, ex), keep_spans(base, list(res.values()), dur, env, ex),
                 keep_spans(base, others, dur, env, ex), keep_spans(base, [], dur, env, ex),
                 keep_spans(base, [], dur, env)]
        for spans in [t for i, t in enumerate(tries) if t and t not in tries[:i]]:
            ok, vcov, _ = verify(src, spans, line, base["coverage"], tmp)
            if ok:
                keep = spans
                verdict = "PASS" if len(spans) == 1 else "FIX"     # one span = plain trim
                break
    out = dict(clip=clip, line=line, verdict=verdict, base_model=base_m.split("/")[-1],
               transcripts={m.split("/")[-1]: " ".join(w for w, _, _ in ws) for m, ws in heard.items()},
               missing=base["missing"], extra=[e for r in res.values() for e in r["extra"]],
               repeats=[x for r in res.values() for x in r["repeats"]], coverage=base["coverage"],
               verified_coverage=vcov, keep=keep, duration=round(dur, 2))
    save(out, os.path.join(d, os.path.splitext(clip)[0] + ".check.json"))
    print(f"row {row} s{shot}: {verdict}  cover {base['coverage']}  missing {base['missing']}  "
          f"repeats {[x[0] for x in out['repeats']]}  keep {keep}")
    return out


if __name__ == "__main__":
    a = sys.argv[1:]
    kw = {}
    for flag in ("--clip", "--line"):
        if flag in a:
            i = a.index(flag); kw[flag[2:]] = a[i + 1]; del a[i:i + 2]
    check(int(a[0]), int(a[1]), **kw)
