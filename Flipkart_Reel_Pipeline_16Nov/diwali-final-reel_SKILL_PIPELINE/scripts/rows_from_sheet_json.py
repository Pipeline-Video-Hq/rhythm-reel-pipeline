import json,sys,collections,os
# 23-Nov: LEGACY one-off of 30-Oct (hardcoded paths of another Mac, overwrites film_titles.json). Use sheet_to_rows.py.
if "--legacy-30oct" not in sys.argv:
    raise SystemExit("rows_from_sheet_json.py is a retired 30-Oct one-off - use sheet_to_rows.py")
raw=json.loads(sys.stdin.read())
for r in raw["rows"]:
    r["pids"]=[p.split("&")[0][:16] for p in r["pids"]]
raw["_note"]="Today's 100 (30-Oct) col Q - the 68 rows beyond the first 2 per category. pids fixed (upto->AT, query strings cut)."
json.dump({"_note":raw["_note"],"persona_links":raw["persona_links"],"rows":raw["rows"]},open("sheet_rows_today100_rest.json","w"),indent=1)
ft=json.load(open("film_titles.json")); ft.update({k:v for k,v in raw["titles"].items()}); json.dump(ft,open("film_titles.json","w"),indent=1,ensure_ascii=False)
order=[2,3,4,5,6,7,8,9,64,65,66,67,68,69,70,126,127,128,129,130,131,132,188,189,190,191,192,193,194,195,250,251,252,253,254,255,256,312,313,314,315,316,317,318,374,375,376,377,378,379,380,437,438,439,440,441,442,443,523,524,525,526,527,528,529,613,614,615,616,617,653,654,655,656,657,698,699,700,701,702,748,749,750,751,752,768,769,770,771,772,808,809,810,811,812,848,849,850,851,852]
MD="~/Desktop/Flipkart Fashion with Music/Musics/"
M=["flipkart_jeans_music.mp3","home_line_bed_src.wav","penny_compounding_bed60.wav","shirt_haul_skill_bed.mp3","shreya_v1_music.mp3","unboxing_skill_bed.mp3"]
plan=json.load(open("music_plan.json")); cnt=collections.Counter(os.path.basename(plan[str(r)]) for r in order if str(r) in plan)
prev=None
for r in order:
    if str(r) not in plan:
        nxt=None
        cand=sorted([m for m in M if m!=prev], key=lambda m:(cnt[m], M.index(m)))
        plan[str(r)]=MD+cand[0]; cnt[cand[0]]+=1
    prev=os.path.basename(plan[str(r)])
json.dump(plan,open("music_plan.json","w"),indent=1)
seq=[os.path.basename(plan[str(r)]) for r in order]
print(len(raw["rows"]), "rows;", "back-to-back:", sum(a==b for a,b in zip(seq,seq[1:])), dict(collections.Counter(seq)))
