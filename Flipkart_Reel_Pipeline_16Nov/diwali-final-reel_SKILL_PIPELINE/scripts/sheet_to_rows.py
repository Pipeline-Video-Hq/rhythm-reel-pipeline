"""Turn the Rhythm sheet CSV into the files pipeline.py addrows needs (16-Nov).

    python3 sheet_to_rows.py "<path to Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv>" [rows...|from-to]

Writes 02_BAU_DATA/sheet_rows_csv_<vertical>.json (one per vertical: persona_links + rows with name, vertical, 5 pids) and adds
each row's "Text for the Film" to 02_BAU_DATA/film_titles.json (existing titles are kept). Then run:
    FK_MODE=BAU python3 pipeline.py addrows 02_BAU_DATA/sheet_rows_csv_<vertical>.json
Rows whose product links have no pid are listed and left out (fix the sheet first).
"""
import csv, json, os, re, sys

DATA = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "02_BAU_DATA"))


def want(args):
    s = set()
    for a in args:
        if "-" in a:
            x, y = a.split("-"); s.update(range(int(x), int(y) + 1))
        else:
            s.add(int(a))
    return s


def main():
    src, pick = sys.argv[1], want(sys.argv[2:])
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig")))
    tp = os.path.join(DATA, "film_titles.json")
    titles = json.load(open(tp)) if os.path.exists(tp) else {}
    links, by, bad = {}, {}, []
    for i, x in enumerate(rows):
        n = i + 2                                   # sheet row number (row 1 = header)
        if pick and n not in pick:
            continue
        m = re.search(r"/d/([^/]+)", x["Persona Link"])
        if m:
            links.setdefault(x["Name"], m.group(1))
        pids = [(re.search(r"pid=([A-Za-z0-9]+)", x[f"Product {k}"]) or [None, ""])[1][:16] for k in range(1, 6)]
        if not all(pids):
            bad.append(f"row {n} ({x['Vertical']}): empty pid in slot(s) {[k + 1 for k, p in enumerate(pids) if not p]}")
            continue
        by.setdefault(x["Vertical"], []).append(dict(row=n, name=x["Name"], vertical=x["Vertical"], pids=pids))
        if titles.get(str(n)) not in (None, x["Text for the Film"]):   # 23-Nov: the sheet is the source - a corrected title replaces the old one
            print(f"row {n}: film title updated from the sheet: {titles[str(n)]!r} -> {x['Text for the Film']!r}")
        titles[str(n)] = x["Text for the Film"]
    for vert, rs in by.items():
        out = os.path.join(DATA, "sheet_rows_csv_" + re.sub(r"[^A-Za-z]", "", vert) + ".json")
        json.dump(dict(persona_links=links, rows=rs), open(out, "w"), indent=1)
        print(f"{len(rs):4d} rows -> {out}")
    json.dump(titles, open(tp, "w"), indent=1, ensure_ascii=False)
    for b in bad:
        print("SKIPPED", b)


if __name__ == "__main__":
    main()
