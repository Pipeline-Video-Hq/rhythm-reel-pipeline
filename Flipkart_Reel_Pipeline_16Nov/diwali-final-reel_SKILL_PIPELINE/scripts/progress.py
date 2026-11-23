"""Write 03_WORK/PROGRESS.md for batch 4: one line per row (stage, final 480p, Drive link)."""
import json, os, glob
B = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
d = json.load(open(f"{B}/04_DATA/sheet_rows_batch4.json")); links = json.load(open(f"{B}/04_DATA/drive_links_final.json"))
rows = [666] + [x["row"] for x in d["rows"]]
out = ["# PROGRESS - Diwali batch 4 (Drive only, no sheet links)", ""]
cnt = {"DRIVE": 0, "FINAL": 0, "WORKING": 0, "PENDING": 0}
for r in rows:
    w = f"{B}/03_WORK/row_{r:03d}"; fin = glob.glob(f"{B}/01_LATEST_FINAL/*/Diwali_row{r:03d}_*_480p.mp4")
    clips = len(glob.glob(f"{w}/clips/*.mp4")); plates = len(glob.glob(f"{w}/plates/*"))
    if str(r) in links: st, info = "DRIVE", links[str(r)]["link"]
    elif fin: st, info = "FINAL", fin[0]
    elif clips or plates: st, info = "WORKING", f"{plates} plates, {clips} clips"
    else: st, info = "PENDING", ""
    cnt[st] += 1
    out.append(f"| {r} | {st} | {info} |")
out[1:1] = [f"Drive {cnt['DRIVE']}/100 · final not uploaded {cnt['FINAL']} · working {cnt['WORKING']} · pending {cnt['PENDING']}", "", "| Row | Stage | Asset / link |", "|---|---|---|"]
open(f"{B}/03_WORK/PROGRESS.md", "w").write("\n".join(out) + "\n")
print(out[1])
