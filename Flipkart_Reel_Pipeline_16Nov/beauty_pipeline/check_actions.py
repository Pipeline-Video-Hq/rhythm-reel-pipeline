"""Fail on unnatural gestures in a run's storyboard / action files.   Usage: python3 check_actions.py <run folder>"""
import sys, glob, json, re
BAD = [r"above (her|his) head", r"over (her|his) head", r"on (her|his) head", r"raised above", r"overhead", r"arm'?s length", r"behind (her|his) head", r"upside", r"contort"]
run = sys.argv[1]; bad = []
files = glob.glob(f"{run}/04_actions/*.json") + glob.glob(f"{run}/04_storyboard*.md")
for f in files:
    t = open(f, encoding="utf-8").read().lower()
    for b in BAD:
        for m in re.finditer(b, t):
            bad.append(f"{f.split('/')[-1]}: unnatural gesture phrase '{m.group(0)}' ... {t[max(0,m.start()-40):m.end()+40].strip()!r}")
import os
types = []
for f in sorted(glob.glob(f"{run}/04_actions/*.json")):
    d = json.load(open(f, encoding="utf-8")); bt = d.get("beat_type")
    if bt not in ("show", "apply"):
        if d.get("scene_id", "").upper().startswith("BR"): continue
        bad.append(f"{os.path.basename(f)}: missing beat_type ('show' or 'apply')")
    else: types.append(bt)
devs=[]
for f in sorted(glob.glob(f"{run}/04_actions/*.json")):
    d=json.load(open(f,encoding='utf-8'))
    if d.get('beat_type')=='show':
        sd=d.get('show_device')
        if not sd: bad.append(os.path.basename(f)+': show clip missing show_device')
        else: devs.append(sd.strip().lower())
for f in sorted(glob.glob(f"{run}/04_actions/*.json")):
    d=json.load(open(f,encoding='utf-8'))
    if d.get('opens') and not d.get('open_state_ref'):
        bad.append(os.path.basename(f)+': opens something but has no open_state_ref (open-state asset)')
if len(devs)!=len(set(devs)): bad.append('two show clips use the same show_device; each product must be shown in a different way')
if types and types.count("apply") != 1:
    bad.append(f"run has {types.count('apply')} apply clips; exactly ONE is required")
for f in sorted(glob.glob(f"{run}/04_actions/*.json")):
    t=open(f,encoding='utf-8').read().lower()
    if ('eye' in t or 'lash' in t) and ('apply' in t) and not any(k in t for k in ('stable','still','gaze fixed')):
        bad.append(os.path.basename(f)+': eye application lacks stability wording (lock 8)')
if not os.path.exists(os.path.join(run,"product_text.json")):
    bad.append("missing product_text.json (exact front-of-pack text per product; see product_text.py)")
else:
    import subprocess,sys as _s
    r=subprocess.run([_s.executable,os.path.join(os.path.dirname(os.path.abspath(__file__)),"product_text.py"),run,"check"],capture_output=True,text=True)
    if r.returncode: bad.append("product_text.json incomplete: "+r.stdout.strip())
for f in sorted(glob.glob(f"{run}/04_actions/*.json")):
    d=json.load(open(f,encoding='utf-8'))
    if d.get('beat_type')=='show' and 'hands' not in str(d.get('hands_clause','')).lower():
        bad.append(os.path.basename(f)+': show clip missing hands_clause (paste the output of hands_prompt.py; lock 18)')
print("\n".join(bad) if bad else "OK: no unnatural gesture phrases, application budget respected")
sys.exit(1 if bad else 0)
