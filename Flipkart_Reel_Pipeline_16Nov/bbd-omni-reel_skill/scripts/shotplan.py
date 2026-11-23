"""Split the column-K script into spoken shots - every word covered, clip length sized to the line.

    python3 shotplan.py <row> [--shots 3|4]

Why: Omni fills spare seconds by repeating the last phrase or ad-libbing ("ek dum ready, ek dum ready",
"bas ab shuru karo" x2), and hand-split scripts dropped lines ("Dono pehli nazar mein..."). So:
  * sentences are packed in order into shots of <= 20 words; the closing Big Billion Days line stays whole;
  * duration_seconds = ceil(words / 2.7 + 0.9), clamped 4..10 (clean takes speak ~2.7 words/s);
  * the joined shot lines must equal the script word-for-word (asserted).
Writes row_NNN/shots.json. Then fill per shot: "dialogue_dev" (Hindi words in Devanagari, English/brands in Latin),
"action" (0-x s beats), "plate" (asset id), and once per row "voice" - promptgen.py refuses until they are filled.
"""
import json, math, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

MAX_WORDS, RATE = 20, 2.7


def sentences(text):
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    out = []
    for p in parts:                       # very long sentences split at commas
        if len(p.split()) > MAX_WORDS:
            chunks, cur = [], []
            for c in re.split(r"(?<=,)\s+", p):
                if cur and len(" ".join(cur + [c]).split()) > MAX_WORDS:
                    chunks.append(" ".join(cur)); cur = []
                cur.append(c)
            chunks.append(" ".join(cur)); out += chunks
        else:
            out.append(p)
    return [s for s in out if s]


INTRO = re.compile(r"^(ye|yeh|aur ye|aur yeh|phir|pehle|pehla|doosra|doosri|teesra|teesri|and|next|this)\b", re.I)


def pack(sents, n_target):
    """New shot when the line would pass MAX_WORDS, or when a sentence introduces the next product
    ('Ye ...', 'Aur ye ...', 'Phir ...') - one product per shot keeps each plate to one product."""
    shots, cur = [], []
    for i, s in enumerate(sents):
        intro = bool(INTRO.match(s)) and len(" ".join(cur).split()) >= 6
        if cur and (intro or len(" ".join(cur + [s]).split()) > MAX_WORDS):
            shots.append(" ".join(cur)); cur = []
        cur.append(s)
    if cur:
        shots.append(" ".join(cur))
    while len(shots) < n_target:            # split the longest shot at a sentence/comma boundary
        i = max(range(len(shots)), key=lambda k: len(shots[k].split()))
        sub = sentences(shots[i]) if len(sentences(shots[i])) > 1 else re.split(r"(?<=,)\s+", shots[i])
        if len(sub) < 2:
            break
        h = max(1, len(sub) // 2)
        shots[i:i + 1] = [" ".join(sub[:h]), " ".join(sub[h:])]
    return shots


def duration(words):
    return max(4, min(10, math.ceil(words / RATE + 0.9)))


def norm(t):
    return re.sub(r"[^\w]+", " ", t.lower()).split()


def main():
    a = sys.argv[1:]
    n_target = 3
    if "--shots" in a:
        i = a.index("--shots"); n_target = int(a[i + 1]); del a[i:i + 2]
    row = int(a[0]); d = row_dir(row)
    b = load(os.path.join(d, "brief.json"))
    script = b["script"]
    if str(b.get("music_only")) == "True" or script.startswith("[Music"):
        print("music-only row: no spoken shots (model rule: Kling, no lip-sync)"); return
    lines = pack(sentences(script), n_target)
    assert norm(" ".join(lines)) == norm(script), "coverage check failed - a script word was lost"
    old = load(os.path.join(d, "shots.json"), {})
    shots = []
    for k, ln in enumerate(lines, 1):
        w = len(ln.split())
        prev = (old.get("shots") or [{}] * 99)[k - 1] if old.get("shots") and len(old["shots"]) >= k else {}
        keep = {f: prev.get(f, "") for f in ("dialogue_dev", "action", "plate", "framing")} if prev.get("line") == ln else {}
        shots.append(dict(n=k, line=ln, words=w, duration=duration(w), clip=f"clips/s{k}.mp4",
                          dialogue_dev=keep.get("dialogue_dev", ""), action=keep.get("action", ""),
                          plate=keep.get("plate", ""), framing=keep.get("framing", "")))
    out = dict(row=row, voice=old.get("voice", ""), wardrobe=old.get("wardrobe", ""), setting=old.get("setting", ""),
               hook=old.get("hook", ""), shots=shots)
    save(out, os.path.join(d, "shots.json"))
    for s in shots:
        print(f"s{s['n']}  {s['words']:2d} words -> {s['duration']} s   {s['line']}")
    print("coverage OK (all script words are in a shot). Fill dialogue_dev/action/plate/voice/wardrobe/setting, then promptgen.py")


if __name__ == "__main__":
    main()
