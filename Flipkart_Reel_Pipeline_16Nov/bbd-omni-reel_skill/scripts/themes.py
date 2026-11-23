"""ALL VIDEOS INDOORS AT HOME (user 28-Oct-2026: "saare videos ghar ke andar hon, canteen wagera mein nahi") - every place = "home".
Per-video THEMES for the Diwali Phase_1 batches (client feedback 28-Oct-2026):
  1. "Different themes must be used in every video."
  2. "Use different background music in each video."  (music_pool.py)
  3. Camera tilt "shouldn't be this evident in every video, keep it as one of the themes" -> camera "tilt" ONLY on vlog.
  4. Rangoli/lights are NOT mandatory: decor only for ethnic / home decor / home furnishing / festive kids / puja GRWM.
  5. "The FSNs and callouts should be Diwali-sale specific" -> the Diwali message lives in the products + title.

    python3 themes.py rows_100.json > assignment.json
"""
import json, random, sys

# vertical (sheet col F) -> category key
CAT = {"Women's Ethnic Wear": "ethnic", "WomenFW": "women_fw", "Men Footwear": "men_fw", "WomenWesternCore": "western",
       "KidClothing": "kids_cloth", "KidsFootwear": "kids_fw", "FashionWearables": "wearables", "Home Decor": "decor",
       "HomeFurnishing": "furnishing"}
DECOR_CATS = {"ethnic", "decor"}  # 29-Oct user: Diwali decor ONLY Ethnic + Home Decor
WEAR = {"ethnic", "women_fw", "western", "kids_cloth"}
FOOT = {"men_fw", "kids_fw"}
ALL_PEOPLE = WEAR | FOOT | {"wearables"}
HOME = {"decor", "furnishing"}

# shots: list of beats; {P} = the product of that beat. "close" beats are tight product close-ups (footwear/wearables).
THEMES = {
    "tryon_haul": dict(name="Try-on haul", cats=WEAR | FOOT, place="home", decor=None, camera="steady",
        beats=["already wearing {P1} (clothing worn, footwear on her feet), a small turn", "now in {P2}, walks two steps toward the phone",
               "now in {P3}, a confident final pose"]),
    "unboxing": dict(name="Parcel unboxing, then wear/use", cats=ALL_PEOPLE | HOME, place="home", decor=None, camera="steady",
        beats=["opens a plain brown courier parcel (no logo) on a table and takes out {P1}, pleased",
               "close-up of {P1} in her/his hands, turning it to show details", "is using / wearing {P2}, happy"]),
    "mirror_check": dict(name="Mirror fit-check", cats=WEAR | {"wearables"}, place="home", decor=None, camera="steady",
        beats=["checks {P1} in a full-length wardrobe mirror, adjusts it", "turns sideways at the mirror in {P2}",
               "steps back from the mirror in {P3}, smiles at the phone"]),
    "puja_grwm": dict(name="Diwali puja get-ready", cats={"ethnic", "kids_cloth", "wearables"}, place="home", decor=True,
        camera="steady", beats=["getting ready for the evening puja, already wearing {P1}", "ready in {P2}, adjusts it near a small puja corner (lamp unlit)",
                                "final look in {P3}, folds hands in a namaste"]),
    "office_party": dict(name="Office Diwali party look", cats={"western", "men_fw", "wearables", "women_fw"}, place="home",
        decor=False, camera="steady", beats=["at home, getting ready for the office Diwali party in {P1}",
                                             "close-up of {P1} as she/he walks across the room", "ready to leave, poses near the door in {P2}"]),
    "park_walk": dict(name="Walk-through at home", cats={"men_fw", "kids_fw", "women_fw"}, place="home",
        decor=False, camera="steady", beats=["walks across the living room toward the phone in {P1}", "close-up of {P1} on the floor, feet stepping",
                                             "sits upright on a sofa edge, shows {P2}, feet flat"]),
    "terrace_workout": dict(name="Home workout corner", cats={"men_fw", "kids_fw"}, place="home", decor=False, camera="steady",
        beats=["stretches in a cleared corner of the living room in {P1}", "jogs on the spot, close-up of {P1}", "ties the laces of {P2}, standing, foot on a step"]),
    "cafe_hangout": dict(name="Friends coming over at home", cats={"western", "wearables", "women_fw"}, place="home", decor=False,
        camera="steady", beats=["opens the front door from inside, dressed in {P1}", "sits upright on a chair at the dining table, shows {P2}", "stands up and does a small turn in {P1}"]),
    "gift_reveal": dict(name="Bhai Dooj gift reveal", cats={"wearables", "kids_cloth", "kids_fw", "decor"}, place="home", decor=None,
        camera="steady", beats=["holds a wrapped gift box toward the phone, opens it: {P1}", "close-up of {P1} in her/his hands",
                                "is wearing / showing {P2}, delighted"]),
    "makeover": dict(name="Room before/after makeover", cats=HOME, place="home", decor=True, camera="steady",
        beats=["a plain corner of the room, she/he brings in {P1}", "places / spreads {P1}, adjusts it neatly",
                "the finished corner with {P2}, she/he sits on the edge and smiles"]),
    "balcony_play": dict(name="Kids play in the living room", cats={"kids_cloth", "kids_fw"}, place="home", decor=False, camera="steady",
        beats=["twirls happily in the living room in {P1}", "hops in place, close-up of {P1}", "waves at the parent filming, in {P2}"]),
    # "shopping_list" REMOVED 28-Oct-2026 (user, row 64): no notebook / list / paper prop in any video.
    "step_out": dict(name="Getting ready to step out (home entrance)", cats={"men_fw", "women_fw", "western", "kids_fw"}, place="home",
        decor=False, camera="steady", beats=["picks {P1} from the shoe rack near the front door and wears it, standing", "close-up of {P1} on the floor tiles",
                                             "walks to the door in {P2}, ready to go"]),
    "detail_showcase": dict(name="Detail close-up showcase", cats={"wearables", "women_fw", "men_fw", "kids_fw", "decor", "furnishing"},
        place="home", decor=None, camera="steady", beats=["tight close-up of {P1}: texture, stitching, hardware",
                                                          "wears / places {P1}, medium shot", "tight close-up of {P2}"]),
    "vlog": dict(name="Handheld vlog (lively tilt camera)", cats=WEAR | {"wearables", "men_fw"}, place="home", decor=False,
        camera="tilt", beats=["a friend films her/him on the go: holds {P1} up with BOTH hands toward the friend, smiling", "spins in {P2}, arms relaxed", "close-up of {P2}"]),
}
HOME_VARIANTS_N = 6


def decor_for(theme, cat):
    return cat in DECOR_CATS   # 29-Oct user: decor by category only (Ethnic + Home Decor), never by theme


def assign(rows, seed=2810):
    """rows: [{row, vertical, ...}] in sheet order. Returns {row: {theme, decor, camera, place, home_variant}}."""
    r = random.Random(seed)
    out, prev, used_by_cat, n_tilt = {}, None, {}, 0
    for i, row in enumerate(rows):
        cat = CAT[row["vertical"]]
        pool = [t for t, v in THEMES.items() if cat in v["cats"] and t != prev]
        if n_tilt >= max(1, (i + 1) // 10):
            pool = [t for t in pool if THEMES[t]["camera"] != "tilt"] or pool
        used = used_by_cat.setdefault(cat, [])
        fresh = [t for t in pool if t not in used] or pool
        if not [t for t in pool if t not in used]:
            used.clear()
        t = r.choice(fresh)
        used.append(t)
        n_tilt += THEMES[t]["camera"] == "tilt"
        out[row["row"]] = dict(theme=t, theme_name=THEMES[t]["name"], cat=cat, decor=decor_for(t, cat),
                               camera=THEMES[t]["camera"], place=THEMES[t]["place"], home_variant=i % HOME_VARIANTS_N,
                               beats=THEMES[t]["beats"])
        prev = t
    return out


if __name__ == "__main__":
    rows = json.load(open(sys.argv[1]))
    print(json.dumps(assign(rows), indent=1))
