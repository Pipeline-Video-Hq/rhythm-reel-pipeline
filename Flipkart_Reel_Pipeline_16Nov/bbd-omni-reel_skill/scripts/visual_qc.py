"""Mandatory visual QC gate for every clip (user rule 27-Oct-2026 after row 79 shipped with 3 legs at 14 s:
"dobara kisi videos main ye galtiyan na ho").

    python3 visual_qc.py <row>            -> qc/vqc_sN_full.jpg + qc/vqc_sN_limbs.jpg per clip (4 fps), and
                                             qc/visual_checklist.json (all items false) if it does not exist yet
Then LOOK at every sheet (full + the zoomed lower-body "limbs" sheet) and set each item to true only if it is true
for EVERY frame. assemble.py refuses to build the master until every item of every clip is true.
A false item = regenerate that clip (fix the plate first if the plate caused it). Never tick an item without looking.
"""
import glob, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

ITEMS = [
    "hand_count_ok",        # hands sheet (6 fps): exactly 2 hands in EVERY frame, never a 3rd (row 73), no selfie arm
    "limb_count_ok",        # exactly 2 arms, 2 hands x 5 fingers, 2 legs, 2 feet in EVERY frame; nothing extra/merged
    "face_same_person",     # same face as the persona and the other clips (no drift, no new moles/jewellery)
    "product_matches",      # product identical to the listing in every frame (shape, straps, toe-post, print, colour)
    "product_big_visible",  # the product is large and fully in frame for most of the clip
    "outfit_continuity",    # the persona's own outfit/shoes/jewellery same as the other clips; fits the campaign
    "room_continuity",      # no objects appearing/disappearing (pictures, idols, furniture), rangoli/diyas stay put
    "actions_plausible",    # no fire handled (matches, lighters, diya on cloth), no impossible motion, no glitches
    "no_text_logos_people", # no gibberish text, no stray logos, no extra people
    "looks_real",           # handheld phone look, not glossy/CGI/model-posed
    "lips_not_moving",      # music-only reels: mouth closed/smiling, never mouthing words (user 28-Oct)
    "apparel_worn",         # clothing products are WORN by the avatar for the whole shot - never held up, on a hanger, folded or laid on a bed (user 28-Oct, rows 10/12/13). Non-apparel rows: tick true.
]


def sheets(row):
    d = row_dir(row)
    os.makedirs(os.path.join(d, "qc"), exist_ok=True)
    clips = sorted(glob.glob(os.path.join(d, "clips", "s[0-9]*.mp4")))
    clips = [c for c in clips if "_take" not in c]
    for c in clips:
        n = os.path.splitext(os.path.basename(c))[0]
        full = os.path.join(d, "qc", f"vqc_{n}_full.jpg")
        limbs = os.path.join(d, "qc", f"vqc_{n}_limbs.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c, "-vf",
                        "fps=4,scale=180:-2,tile=8x3:padding=4", "-frames:v", "1", full])
        # lower 55 % of the frame, bigger: legs, feet, hands, the product
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c, "-vf",
                        "fps=4,crop=iw:ih*0.55:0:ih*0.45,scale=240:-2,tile=8x3:padding=4", "-frames:v", "1", limbs])
        # upper 65 %, 6 fps: count HANDS in every frame (row 73: a third hand appeared at 5 s for ~1 s and the
        # lower-body sheet could not see it)
        hands = os.path.join(d, "qc", f"vqc_{n}_hands.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c, "-vf",
                        "fps=6,crop=iw:ih*0.65:0:ih*0.1,scale=220:-2,tile=9x4:padding=4", "-frames:v", "1", hands])
        print(n, full, limbs, hands)
    ck = os.path.join(d, "qc", "visual_checklist.json")
    # 2-Nov: merge instead of create-once - re-runs keep earlier ticks, and clips added later get their own false items
    cur = load(ck) or {}
    for c in clips:
        k0, mt = os.path.splitext(os.path.basename(c))[0], int(os.path.getmtime(c))
        if k0 not in cur or cur[k0].get("_mtime", mt) != mt:      # new or re-generated clip -> must be looked at again
            cur[k0] = {k: False for k in ITEMS}
        cur[k0]["_mtime"] = mt
    save(cur, ck)
    print("checklist:", ck)


def gate(row):
    """Return list of problems; empty = OK to assemble."""
    d = row_dir(row)
    ck = load(os.path.join(d, "qc", "visual_checklist.json"))
    if not ck:
        return ["qc/visual_checklist.json missing - run visual_qc.py <row> and check every sheet"]
    bad = [f"{clip}: {k}" for clip, items in ck.items() for k in ITEMS if not items.get(k)]
    return bad


if __name__ == "__main__":
    sheets(int(sys.argv[1]))
