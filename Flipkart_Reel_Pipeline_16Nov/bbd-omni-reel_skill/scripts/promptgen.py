"""Build the Omni prompts for a row from shots.json, with every learned guard built in. Refuses on any gap.

    python3 promptgen.py <row>       -> row_NNN/prompts.json  {"s1": {image_asset_ids, duration_seconds, prompt}, ...}

Checks before writing (each one is a failure we actually paid for):
  * dialogue_dev is Devanagari for Hindi words; no romanised Hindi function words left (Omni said "mat" like English)
  * dialogue_dev still says the whole romanised line (lines.compare) - no word lost in translation ("lace up")
  * voice, wardrobe, setting are set once per row and reused word for word (voice drift, outfit/shoe changes)
  * every shot has a plate (asset id) and an action
  * the words microphone/mic/lav never appear (naming them made Omni add one); wardrobe is described positively
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from lines import compare, skel, words_of
from realism import CLIP_CAMERA, CLIP_REALISM, CLIP_GUARD, CLIP_NO_TALK, CLIP_HANDS

ROMAN_HINDI = r"\b(hai|hain|ke|ki|ka|ko|liye|mein|aur|ye|yeh|karo|kar|se|par|pe|bhi|toh|nahi|mat|ek|dekho|lo|wala|wali|wale|abhi|bas|jaye|gaye|hoon|tha)\b"
BANNED = r"\b(microphone|mic|lav|lavalier|clip-on)\b"

PRON = ("The Hindi words of the dialogue are written in Devanagari: pronounce them as natural spoken Hindi "
        "(e.g. मत = \"mut\", not the English word \"mat\"); the words in Latin letters (English words and brand "
        "names) are said the way an Indian speaker says them in English. Say every word exactly once, in this order; "
        "never repeat a word or phrase and add nothing else. When the line is finished, stop talking and just smile at the camera.")


def build(row):
    d = row_dir(row)
    b = load(os.path.join(d, "brief.json"))
    sp = load(os.path.join(d, "shots.json"))
    he = "she" if str(b.get("gender", "")).lower().startswith("f") else "he"
    person = "woman" if he == "she" else "man"
    errs = []
    for f in ("voice", "wardrobe", "setting"):
        if not sp.get(f):
            errs.append(f"row field '{f}' is empty")
    out = {}
    for s in sp["shots"]:
        k = f"s{s['n']}"
        dev = s.get("dialogue_dev", "").strip()
        if not dev:
            errs.append(f"{k}: dialogue_dev empty"); continue
        if not re.search(r"[ऀ-ॿ]", dev):
            errs.append(f"{k}: dialogue_dev has no Devanagari")
        if re.search(r"₹|\b[Rr]s\.?\s*\d|rupe|रुपय|रुपए", dev):
            errs.append(f"{k}: dialogue mentions a price - no prices (user rule)")
        left = re.findall(ROMAN_HINDI, dev, re.I)
        if left:
            errs.append(f"{k}: romanised Hindi left in dialogue_dev: {sorted(set(left))} - write them in Devanagari")
        r = compare(s["line"], [(w, 0, 0) for w in words_of(dev)])
        lost = [m for m in r["missing"] if skel(m) != "v"]      # strict: we wrote both sides
        if lost:
            errs.append(f"{k}: dialogue_dev drops script words {lost}")
        for f in ("plate", "action"):
            if not s.get(f):
                errs.append(f"{k}: {f} empty")
        end = s["duration"] - 0.5
        prompt = (
            f"<FIRST_FRAME> is the starting frame of this shot; continue from it exactly - same {person}, same face, "
            f"{sp['wardrobe']}, {sp['setting']}. {CLIP_CAMERA}, "
            f"{s.get('framing') or 'waist-up'}. {s.get('action', '')}\n"
            f"Dialogue ({he} speaks to camera, lips in perfect sync, natural everyday Hinglish, clear Indian accent, "
            f"native Hindi speaker, {sp['voice']}): \"{dev}\"\n"
            f"Speech starts within the first 0.5 s and ends by {end:g} s; no talking before or after the line. "
            f"Quiet natural room tone only, no music.\n"
            f"Keep every product identical to the first frame in every frame: same colours, print, shape and logo. "
            f"No text on screen, no extra people, natural hands with five fingers.\n{PRON}\n"
            f"Wardrobe stays exactly as in the first frame for the whole shot: {sp['wardrobe']}; nothing new appears on "
            f"the clothes, body or face.\n{CLIP_GUARD}\n{CLIP_HANDS}\n{CLIP_NO_TALK}\n{CLIP_REALISM}"
        )
        if re.search(BANNED, prompt, re.I):
            errs.append(f"{k}: prompt names a microphone/lav - describe the clothes positively instead")
        out[k] = dict(image_asset_ids=[s.get("plate", "")], duration_seconds=s["duration"], prompt=prompt,
                      model="gemini-omni-1.2-flash", resolution="720p", aspect_ratio="9:16")
    if errs:
        print("NOT READY:\n  " + "\n  ".join(errs)); sys.exit(1)
    save(out, os.path.join(d, "prompts.json"))
    print(f"prompts.json: {len(out)} shots, total {sum(v['duration_seconds'] for v in out.values())} s of Omni")


if __name__ == "__main__":
    build(int(sys.argv[1]))
