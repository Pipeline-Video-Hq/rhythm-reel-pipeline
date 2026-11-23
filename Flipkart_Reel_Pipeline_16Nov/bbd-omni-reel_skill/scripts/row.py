"""Build bbd_reels/row_NNN/brief.json for BBD tab rows.

    python3 row.py 2            -> one row
    python3 row.py 2-51         -> a range
    python3 row.py 2 --sheet live.csv   -> use a fresh CSV export of the BBD tab (columns A-U)

BBD tab columns: A Status, B Persona (Drive link), C Name, D Voice ("Voice" / "Bacground music"), E BU, F Vertical,
G Type, H CTA, I Text for the Film, J client beat brief (HOOK/PRODUCTS/CLOSE/TONE), K Script by Truefan ai (ours),
L-Q Product 1-6 links, R Delivery Url (ours), T Reference (ours, optional), U what the video copies (ours).
The persona is resolved by its Drive file id (data/persona_ids.json) because names in C have typos.
"""
import csv, glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *


def rows_arg(a):
    out = []
    for part in a.split(","):
        if "-" in part:
            s, e = part.split("-"); out += list(range(int(s), int(e) + 1))
        else:
            out.append(int(part))
    return out


def main():
    args = sys.argv[1:]
    src = os.path.join(DATA, "bbd.csv")
    if "--sheet" in args:
        i = args.index("--sheet"); src = args[i + 1]; del args[i:i + 2]
    sheet = list(csv.reader(open(src)))
    scripts = {}
    for f in sorted(glob.glob(os.path.join(DATA, "scripts_out", "out_B*.json"))):
        scripts.update({int(k): v for k, v in json.load(open(f)).items()})
    refs = load(os.path.join(DATA, "refs.json"), {})
    pid = load(os.path.join(DATA, "persona_ids.json"), {})
    built, skipped = [], []
    for r in args and rows_arg(args[0]) or []:
        if r - 1 >= len(sheet) or not any(sheet[r - 1]):
            skipped.append((r, "empty row")); continue
        x = sheet[r - 1] + [""] * 26
        m = re.search(r"/d/([\w-]+)", x[1])
        name = pid.get(m.group(1), x[2].strip()) if m else x[2].strip()
        script = (x[10].strip() if src != os.path.join(DATA, "bbd.csv") else "") or scripts.get(r) or x[10].strip()
        if not script:
            skipped.append((r, "no column-K script yet")); continue
        ref = refs.get(str(r)) or {}
        brief = dict(
            row=r, tab="BBD", name=name, gender=gender(name), child=name in KIDS,
            voice="Background music" if x[3].lower().startswith("bac") else "Voice",
            music_only=x[3].lower().startswith("bac"), bu=x[4], vertical=x[5], cta=x[7],
            film_text=x[8].strip(), offer=x[8].strip(), client_brief=x[9], script=script,
            product_urls=[u for u in x[11:17] if u.startswith("http")],
            persona=dict(name=name, drive_id=m.group(1) if m else None,
                         image=os.path.join(PERSONAS, name.lower() + ".jpg")),
            reference=dict(code=ref.get("code"), url=ref.get("url"), shows=ref.get("shows"),
                           image=os.path.join(DATA, "refs", os.path.basename(ref["image"])) if ref.get("image") else None,
                           format=ref.get("format"), talks=ref.get("talks")),
            out_name=f"BBD_row{r:03d}_{name}_{slug(x[5])}.mp4",
        )
        save(brief, os.path.join(row_dir(r), "brief.json"))
        built.append(r)
        if not os.path.exists(brief["persona"]["image"]):
            print("PERSONA IMAGE MISSING:", name, brief["persona"]["drive_id"], "-> Drive download + b64save.py")
    print("built", len(built), "briefs:", built)
    for r, why in skipped:
        print("SKIP row", r, "-", why)


if __name__ == "__main__":
    main()
