"""Write row_NNN/plan.json from shots.json + clips/s<N>.check.json + products.json. No hand timing.

    python3 autoplan.py <row>

Segments: each shot's verified keep spans (clipcheck.py), in order; the 2nd+ span of a shot is a 1.06 punch-in so the
jump cut reads as an edit. Refuses if a shot has no PASS/FIX check.
Supers (learned placement rules):
  * hook (shots.json "hook", else brief film_text): outline, top-left of the badge, first 3.2 s
  * one product-name pill per product (no prices - user rule), shown during the shot that names it, TOP of frame (y 0.11) - products and hands live
    mid/bottom frame, so bottom pills covered shoes twice; ends 0.1 s before the shot ends (product moves at cuts)
  * end super (shots.json "end_super", else "Flipkart Big Billion Days") over the closing shot
  * nothing in the badge corner (x > 0.74, y < 0.16)
Override any super by editing plan.json afterwards; re-run assemble.py + qc.py.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

GENERIC = {"shoes", "shoe", "running", "sports", "sport", "men", "women", "for", "sneakers", "casual", "the", "and",
           "with", "kids", "boys", "girls", "pack", "set", "of", "lace", "up", "walking"}
NUMW = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "seven": "7", "eight": "8",
        "nine": "9", "ten": "10", "thirteen": "13"}


def toks(t):
    t = re.sub(r"[^a-z0-9 ]", " ", t.lower().replace("-", " "))
    return [NUMW.get(w, w) for w in t.split() if w not in GENERIC and len(w) >= 2]


def money(v):
    v = int(float(str(v).replace(",", "")))
    s = str(v)
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        head = re.sub(r"(\d)(?=(\d\d)+$)", r"\1,", head)
        s = head + "," + tail
    return "₹" + s


def short_name(title):
    words = [w for w in re.split(r"\s+", title) if w.lower() not in GENERIC]
    return " ".join(words[:3]).title()


def main(row):
    d = row_dir(row)
    b = load(os.path.join(d, "brief.json"))
    sp = load(os.path.join(d, "shots.json"))
    prods = load(os.path.join(d, "products.json"), [])
    segs, shot_t = [], []
    t = 0.0
    for s in sp["shots"]:
        chk = load(os.path.join(d, os.path.splitext(s["clip"])[0] + ".check.json"))
        if not chk or chk.get("verdict") not in ("PASS", "FIX"):
            sys.exit(f"s{s['n']}: no passing clipcheck - run clipcheck.py {row} {s['n']} (RETAKE = regenerate)")
        t0 = t
        for i, (a, e) in enumerate(chk["keep"]):
            seg = {"clip": s["clip"], "in": a, "out": e}
            if i:
                seg["zoom"] = 1.06
            segs.append(seg); t += e - a
        shot_t.append((t0, t, s))
    supers = []
    hook = sp.get("hook") or b.get("film_text") or ""
    if hook:
        supers.append(dict(text=hook, start=0.05, end=round(min(3.2, shot_t[0][1] - 0.1), 2), style="outline",
                           x=0.41, y=0.07, size=44, max_w=0.62))
    hook_end = supers[0]["end"] if supers else 0
    # product -> shot that names it (token overlap with the spoken line)
    names = sp.get("pill_names", {})
    # one pill per product actually shown: shots.json "products" (1-based indices into products.json) if set,
    # else the first of any near-identical listings (the sheet often has the same shoe at 2-3 prices)
    if sp.get("products"):
        prods = [prods[i - 1] for i in sp["products"]]
    else:
        seen, uniq = [], []
        for q in prods:
            qt = set(toks(q.get("title", "")))
            if not any(len(qt & u) >= max(1, len(qt | u) - 1) for u in seen):
                seen.append(qt); uniq.append(q)
        prods = uniq
    alltoks = [set(toks(q.get("title", ""))) for q in prods]
    for k, p in enumerate(prods):
        # distinguishing words only (shared brand words like "Abros" can't tell two products apart)
        pt = alltoks[k] - set().union(*[t for i, t in enumerate(alltoks) if i != k]) or alltoks[k]
        best = max(range(len(shot_t)), key=lambda i: len(pt & set(toks(shot_t[i][2]["line"]))))
        if not pt & set(toks(shot_t[best][2]["line"])):
            continue                                            # product not spoken in this reel
        t0, t1, s = shot_t[best]
        # two products in one shot: split the shot at the second name's position in the line
        others = [i for i, q in enumerate(prods) if i != k and
                  (alltoks[i] - alltoks[k]) & set(toks(s["line"]))]
        if others:
            words = toks(s["line"]); pos = [i for i, w in enumerate(words) if w in pt]
            opos = [j for i in others for j, w in enumerate(words) if w in (alltoks[i] - alltoks[k])]
            if pos and opos:
                mid = t0 + (t1 - t0) * (min(max(pos), max(opos)) + 1) / max(1, len(words))
                (t0, t1) = (t0, mid) if min(pos) < min(opos) else (mid, t1)
        start = max(t0 + 0.3, hook_end + 0.1)
        end = t1 - 0.1
        if end - start < 1.2:
            continue
        name = names.get(str(k + 1)) or short_name(p.get("title", ""))
        supers.append(dict(text=name, start=round(start, 2), end=round(end, 2), style="pill",     # name only - no prices (user rule)
                           x=0.45, y=0.11, size=42))
    c0, c1, cs = shot_t[-1]
    if re.search(r"big billion|bbd|flipkart", cs["line"], re.I):
        supers.append(dict(text=sp.get("end_super") or "Flipkart Big Billion Days", start=round(c0 + 0.1, 2),
                           end=round(c1 - 0.05, 2), style="box", x=0.41, y=0.08, size=40, max_w=0.64))
    supers.sort(key=lambda x: x["start"])
    for a_, b_ in zip(supers, supers[1:]):                   # no two supers in the same top zone at once
        if b_["start"] < a_["end"]:
            a_["end"] = round(b_["start"] - 0.05, 2)
    supers = [x for x in supers if x["end"] - x["start"] >= 1.0]
    plan = dict(segments=segs, audio={"mode": "speech"}, supers=supers, logo=True, endslate=True)
    save(plan, os.path.join(d, "plan.json"))
    print(f"plan.json: {len(segs)} segments, {round(t, 2)} s + end card; supers:")
    for x in supers:
        print(f"  {x['start']:5.2f}-{x['end']:5.2f}  {x['style']:7s} {x['text'][:50]!r}")


if __name__ == "__main__":
    main(int(sys.argv[1]))
