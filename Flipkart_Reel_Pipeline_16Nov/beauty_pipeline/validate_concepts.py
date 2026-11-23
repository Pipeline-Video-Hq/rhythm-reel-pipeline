"""Fail if concepts repeat a set / wardrobe colour / archetype / light / hook device / palette from the registry or the batch,
or if the structure is serial one-by-one.   Usage: python3 validate_concepts.py concepts_batch.json"""
import json, sys, re
if len(sys.argv) != 2: sys.exit("Usage: python3 validate_concepts.py concepts_batch.json")
REG = json.load(open("concept_registry.json")); NEW = json.load(open(sys.argv[1]))
BANNED_SET_WORDS = ['kitchen']  # user 2026-11-05: never a kitchen
UPBEAT_PACKS = ["rhythm_bgm_approved", "upbeat-bright", "upbeat-fashion", "fashion-upbeat", "happy", "groovy", "funky-groovy", "playful", "cool-beat", "fashion-shoot", "indian-festive", "stylish", "diwali-music", "diwali"]  # user 2026-11-06: music is ALWAYS upbeat
FIELDS = ["set", "archetype", "light", "hook_device", "palette", "bgm"]
norm = lambda s: re.sub(r"[^a-z ]", "", str(s).lower()).strip()
colour = lambda w: norm(w).split()[0] if norm(w) else ""
bad = []
for c in NEW:
    if not c.get('skin_tone'):
        bad.append(f"{c['row']}: missing skin_tone (hands must match the avatar, lock 14)")
    if any(w in str(c.get('set','')).lower() for w in BANNED_SET_WORDS):
        bad.append(f"{c['row']}: set must never be a kitchen (user rule)")
    if c.get('application_count') != 1:
        bad.append(f"{c['row']}: application_count must be exactly 1 (she applies ONE product once; all other beats only show products)")
    sd=c.get('show_devices') or []
    if not sd or len(set(map(str.lower,sd.values() if isinstance(sd,dict) else sd)))!=len(sd): bad.append(f"{c['row']}: show_devices missing or not all different (each product must be shown a different way)")
    if not c.get('apply_product'): bad.append(f"{c['row']}: missing apply_product")
    if not c.get('set'): bad.append(f"{c['row']}: missing set (a room setting must always be selected)")
    if c.get('bgm_pack') not in UPBEAT_PACKS: bad.append(f"{c['row']}: bgm_pack must be one of the upbeat packs {UPBEAT_PACKS} (music is always upbeat)")
    if not c.get('bgm'): bad.append(f"{c['row']}: missing bgm (a different track every run)")
for i, c in enumerate(NEW):
    if norm(c.get("structure", "")) == "serial" or "one by one" in norm(c.get("product_interaction", "")):
        bad.append(f"{c['row']}: serial one-by-one showing is not allowed")
    others = REG + [n for j, n in enumerate(NEW) if j != i]
    for f in FIELDS:
        if f == "bgm" and c.get("bgm_pack") == "rhythm_bgm_approved":
            continue   # 16-Nov: Rhythm BGM is a 22-track round robin (bgm_rotation.py) - repeats after 22 are intended
        for o in others:
            if norm(c.get(f)) == norm(o.get(f)) and c.get(f):
                bad.append(f"{c['row']}: same {f} as {o.get('id', o.get('row'))}: {c[f]}")
    for o in others:
        if colour(c.get("wardrobe", "")) == colour(o.get("wardrobe", "")) and c.get("wardrobe"):
            bad.append(f"{c['row']}: same wardrobe colour as {o.get('id', o.get('row'))}: {c['wardrobe']}")
print("\n".join(bad) if bad else "OK: all concepts are distinct from the registry and each other")
sys.exit(1 if bad else 0)
