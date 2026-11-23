"""REEL PLANNER (user 21-Nov): turns the 5 product plans of a row into ONE consistent reel - no code calls, no cost.

- ROOM: the fewest rooms (1, at most 2) that fit all 5 products' real use. Each room is a fixed BACKGROUND BIBLE: walls, floor,
  light, every piece of furniture and every background prop with its real size and exact place. The bible is pasted into
  every image and clip prompt, and every image of the room is an edit of the room's master image, so the background and the
  background props never change. Items of a product's own category are removed (a rug product -> no other rug) or, for things
  a room always has (bedsheet, curtains, cushions, towel), kept PLAIN and replaced by the product only in its own slot.
- CAMERA: fixed positions per framing, always facing the same back wall.
- PERSON: one persona lock for the reel - height in cm against the room (door, seat, counter), build, outfit, hair.
- ORDER: products are ordered so the person's state stays logical (beard before the razor, never after) and same-room
  products stay together; the sheet's slot numbers are kept (the plan.json order follows reel_plan.json).
- MOVEMENT: each product has 3 shot variants; the planner picks one per product so no two products repeat a movement.
"""
import json, os, re
from product_planner import shots_of

PIPE = os.environ.get("FK_PIPE") or os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
PERSONAS = os.path.join(PIPE, "02_BAU_DATA", "personas_body.json")

ROOMS = {
 "living_room": dict(
    walls="warm off-white painted walls", floor="light-grey vitrified floor tiles, 60 x 60 cm", back="the sofa wall",
    light="soft daylight from the window on the right wall, even and warm, no harsh shadows",
    items=[("a cream fabric three-seater sofa", "sofa", "200 wide, seat 45 high, backrest 85 high", "against the back wall, centred"),
           ("two plain beige cushions", "cushion", "40 x 40", "one at each end of the sofa"),
           ("a low teak coffee table", "table", "100 x 50, 42 high", "in front of the sofa, 60 cm from it"),
           ("a woven cotton rug in muted beige", "floor_textile", "160 x 230", "under the coffee table"),
           ("a potted areca palm in a white ceramic pot", "plant", "150 high", "in the back-left corner"),
           ("a wooden side table with a small white table lamp", "side_table", "45 x 45, 55 high (lamp 40 high)", "at the right end of the sofa"),
           ("a window with plain sheer white curtains", "curtain", "window 150 x 150, curtains to the floor", "on the right wall"),
           ("a wooden door frame", "door", "90 wide, 210 high", "on the left wall near the back corner"),
           ("one framed abstract print in soft colours", "wall_art", "60 x 90", "on the back wall above the sofa")]),
 "bedroom": dict(
    walls="soft pale-sage painted walls", floor="light oak laminate floor, planks 20 cm wide", back="the bed wall",
    light="soft morning daylight from the window on the right wall, even, no harsh shadows",
    items=[("a queen bed with a grey upholstered headboard", "bed", "160 x 200, mattress top 50 high, headboard 110 high", "against the back wall, centred"),
           ("a plain white bedsheet, neatly spread", "bed_cover", "fits the 160 x 200 bed", "on the bed"),
           ("two plain white pillows", "pillow", "45 x 70", "at the head of the bed"),
           ("two walnut bedside tables, each with a small lamp", "side_table", "45 x 40, 55 high", "one on each side of the bed"),
           ("a small upholstered bench", "seat", "100 x 40, seat 45 high", "at the foot of the bed"),
           ("a white sliding-door wardrobe (no mirror)", "wardrobe", "180 wide, 210 high", "on the left wall"),
           ("a window with plain light-grey curtains", "curtain", "window 150 x 150, curtains to the floor", "on the right wall"),
           ("a small potted snake plant", "plant", "60 high", "on the floor by the window"),
           ("a wooden door frame", "door", "90 wide, 210 high", "on the left wall, beside the wardrobe")]),
 "bathroom": dict(
    walls="light-grey ceramic wall tiles, 30 x 60 cm", floor="matte grey anti-skid floor tiles, 30 x 30 cm",
    back="the wall behind the person (towel rail and frosted window); the camera is where the mirror would be, so NO mirror is ever in frame",
    light="bright, even, slightly cool daylight from the frosted window plus a ceiling light, no harsh shadows",
    items=[("a white stone vanity counter with a white wash basin and a chrome tap", "counter", "100 wide, 55 deep, 85 high", "in front of the person (its edge at the bottom of the frame)"),
           ("a chrome towel rail with one folded white hand towel", "towel", "rail 60 wide; towel 40 x 60", "on the back wall at shoulder height"),
           ("a frosted glass window", "window", "60 x 60", "on the back wall, upper left"),
           ("a small potted money plant", "plant", "25 high", "on the window sill"),
           ("a plain white ceramic soap dispenser (no label)", "toiletry", "15 high", "on the counter, left of the basin")]),
 "kitchen": dict(
    walls="white subway-tile backsplash, pale-grey painted walls above", floor="beige vitrified floor tiles, 60 x 60 cm",
    back="the counter wall",
    light="bright daylight from the window on the right plus under-cabinet lights, even",
    items=[("a black granite kitchen counter", "counter", "240 long, 60 deep, 90 high", "along the back wall"),
           ("pale-grey upper cabinets", "cabinet", "60 high, bottom edge 150 from the floor", "above the counter"),
           ("a steel sink with a chrome tap", "sink", "60 x 45", "in the counter, right side"),
           ("a two-burner glass hob (switched off)", "hob", "70 x 40", "in the counter, left side"),
           ("a small potted basil plant", "plant", "25 high", "on the counter near the window"),
           ("a window with a plain white roller blind", "window", "90 x 90", "on the right wall above the sink")]),
 "dining_area": dict(
    walls="warm white painted walls", floor="light-grey vitrified tiles, 60 x 60 cm", back="the sideboard wall",
    light="soft daylight from the left, warm pendant light above the table",
    items=[("a six-seat sheesham-wood dining table", "table", "180 x 90, 75 high", "centre of the frame"),
           ("upholstered dining chairs", "seat", "seat 45 high", "around the table"),
           ("a low wooden sideboard", "cabinet", "160 x 45, 80 high", "against the back wall"),
           ("a woven rattan pendant lamp", "lamp", "45 wide", "above the table"),
           ("a potted rubber plant", "plant", "120 high", "in the back-right corner")]),
 "entrance_foyer": dict(
    walls="warm off-white walls", floor="light-grey vitrified tiles, 60 x 60 cm", back="the shoe-cabinet wall",
    light="soft daylight from the side window, even",
    items=[("a closed white shoe cabinet (doors shut, no shoes visible anywhere)", "cabinet", "100 wide, 35 deep, 100 high", "against the back wall"),
           ("a small cushioned wooden bench", "seat", "90 x 35, seat 45 high", "beside the shoe cabinet"),
           ("a wooden main door, closed", "door", "100 wide, 210 high", "on the left wall"),
           ("a small ceramic key bowl", "decor", "15 wide", "on top of the shoe cabinet"),
           ("a potted areca palm", "plant", "120 high", "in the corner by the door")]),
 "balcony": dict(
    walls="light-beige exterior walls", floor="terracotta-coloured anti-skid tiles", back="the railing with the city view (soft, out of focus)",
    light="soft daylight, open sky, even",
    items=[("a black metal railing", "railing", "100 high", "along the back"),
           ("potted plants in terracotta pots", "plant", "30-60 high", "along the railing"),
           ("one cane chair", "seat", "seat 42 high", "on the left")]),
 "study": dict(
    walls="pale-blue painted walls", floor="light oak laminate floor", back="the bookshelf wall",
    light="daylight from the left window, a desk lamp off",
    items=[("a wooden study desk", "table", "120 x 60, 75 high", "against the back wall"),
           ("a grey office chair", "seat", "seat 46 high", "at the desk"),
           ("an open bookshelf with neatly arranged books (no readable titles)", "shelf", "80 wide, 180 high", "on the back wall, right"),
           ("a small potted plant", "plant", "30 high", "on the desk corner")]),
 "dressing_area": dict(
    walls="soft blush-white painted walls", floor="light oak laminate floor", back="the dresser wall",
    light="soft daylight from the right, warm and even",
    items=[("a white wooden dresser with drawers (no mirror in frame)", "dresser", "100 wide, 45 deep, 75 high", "against the back wall"),
           ("a cushioned dressing stool", "seat", "seat 45 high", "in front of the dresser"),
           ("a small ceramic tray (empty)", "decor", "20 x 12", "on the dresser, left"),
           ("a potted peace lily", "plant", "50 high", "on the floor beside the dresser"),
           ("a white sliding-door wardrobe (no mirror)", "wardrobe", "180 wide, 210 high", "on the left wall")]),
 "nursery": dict(
    walls="pale-yellow painted walls", floor="light oak laminate floor", back="the crib wall",
    light="soft daylight, gentle and even",
    items=[("a white wooden crib (empty)", "crib", "125 x 65, rail 90 high", "against the back wall"),
           ("a white changing table with drawers", "table", "80 x 50, 90 high", "on the right"),
           ("a grey rocking chair", "seat", "seat 42 high", "on the left"),
           ("two soft plush toys", "toy", "25 high", "on the changing table")]),
 "utility_area": dict(
    walls="white tiles to shoulder height, pale-grey paint above", floor="grey anti-skid tiles", back="the appliance wall",
    light="even daylight from a small window",
    items=[("a white front-load washing machine (closed)", "appliance", "60 x 60, 85 high", "against the back wall, left"),
           ("a white wall shelf with plain unlabelled containers", "shelf", "80 wide", "above the washing machine"),
           ("a steel drying rack, folded against the wall", "rack", "150 high", "on the right")]),
}

KIND_WORDS = {
 "floor_textile": ["rug", "carpet", "mat", "doormat", "runner", "dhurrie"],
 "bed_cover": ["bedsheet", "bed sheet", "bedspread", "bed cover", "comforter", "quilt", "dohar", "blanket", "duvet"],
 "pillow": ["pillow"], "cushion": ["cushion"], "curtain": ["curtain", "drape", "blind"],
 "sofa_cover": ["sofa cover"], "table_cover": ["table cover", "table runner", "tablecloth", "table mat", "placemat"],
 "towel": ["towel"], "plant": ["plant", "planter"], "wall_art": ["wall art", "painting", "photo frame", "wall decor", "clock"],
 "lamp": ["lamp"], "toiletry": ["soap", "dispenser"], "decor": ["bowl", "tray", "showpiece", "figurine", "vase"],
 "seat": ["stool", "bench", "chair"], "shelf": ["shelf", "rack"],
}
SWAP_KINDS = {"bed_cover", "pillow", "cushion", "curtain", "sofa_cover", "table_cover", "towel", "wall_art", "lamp", "plant", "seat"}

FAMILY_EXCLUDE = {
 "ethnic": "any other garment on display (no clothes on hangers, chairs or the bed)",
 "everyday_clothing": "any other garment on display (no clothes on hangers, chairs or the bed)",
 "footwear": "any other footwear anywhere in the room (the shoe cabinet stays shut)",
 "fashion_wearables": "any other bag, watch, sunglasses, belt or jewellery on display",
 "fragrance": "any other perfume, deodorant or cosmetic bottle",
 "grooming": "any other grooming product, razor, trimmer or bottle on display",
 "kitchen": "any other cookware, utensil or appliance of the same type on the counter",
 "household_utility": "any other cleaning or utility product on display",
 "baby_care": "any other baby product of the same type; no baby",
 "home_decor": "any other decor piece of the same type",
 "home_furnishing": "a second item of the same textile type",
}
DISPLAY_LETTERS = "KLMNOPQRSTUV"   # footwear display approaches (22-Nov)
ALWAYS_EXCLUDE = ["a mirror or any reflective surface showing the person", "festive decor (no diya, rangoli, marigold, fairy lights)",
                  "other people or pets", "brand logos or readable text on any prop", "clutter"]

CAMERA = {
 "full_body": "camera at chest height (about 130 cm), 2.6 m from the person, level, normal phone lens (no wide-angle distortion); framing from a little above the head to just below the feet",
 "knee_up": "camera at chest height, 1.8 m from the person, level; framing from above the head to the knees",
 "waist_up": "camera at chest height, 1.2 m from the person, level; framing from above the head to the waist",
 "knee_down": "camera at knee height (about 50 cm), 1.0 m away, tilted 15 degrees down; framing from mid-thigh to 20 cm of floor in front of the feet (the knees always in frame)",
 "shoulders_up": "camera at face height, 0.8 m away, level; framing from just above the head to the upper chest, the whole face in frame",
 "wall_close": "camera at shoulder height (about 130 cm), 1.0 m from the wall, level, facing the wall straight on; about 95 cm of wall fills the frame width; the wall item fills the right two-thirds of the frame and the person stands at the left edge in profile BESIDE it, never in front of it",
 "feet_close": "camera at ankle height (about 25 cm), 0.6 m away, slightly down; framing the shins, both feet and the floor around them",
 "hands_close": "camera 0.5 m from the hands at their height; both hands and the product big, forearms visible to the elbows",
 "product_close": "camera 0.4 m from the product; the product fills about half the frame with the hand holding it",
 "macro": "camera 15-20 cm from the push-in target; the detail fills the frame",
}

OUTFIT = {
 ("footwear", "women"): "a plain dusty-rose cotton kurta to mid-thigh and ankle-length off-white cotton trousers (ankles and feet fully visible)",
 ("footwear", "men"): "a plain navy crew-neck T-shirt and stone-coloured chinos ending just above the ankle (feet fully visible)",
 ("fashion_wearables", "women"): "a plain black round-neck top and light-blue straight jeans",
 ("fashion_wearables", "men"): "a plain white Oxford shirt with sleeves rolled once, and charcoal chinos",
 ("fragrance", "women"): "a plain powder-blue shirt dress with elbow-length sleeves",
 ("fragrance", "men"): "a plain light-grey polo T-shirt and dark-navy chinos",
 ("grooming", "men"): "a plain white crew-neck T-shirt",
 ("grooming", "women"): "a plain white crew-neck T-shirt",
}
HOME_OUTFIT = {"women": "plain home clothes: a solid sage cotton kurta and off-white leggings",
               "men": "plain home clothes: a solid grey crew-neck T-shirt and navy track pants"}
CLOTHING_FAMILIES = {"ethnic", "everyday_clothing"}
STOP = set("the a an and or of to in on at with her his their its it is are as by for from into onto then that this one two "
           "slowly gently slightly about cm s while over under up down back toward towards side front".split())


def kinds_of(text):
    t = (text or "").lower()
    return {k for k, words in KIND_WORDS.items() if any(re.search(rf"\b{re.escape(w)}(s|es)?\b", t) for w in words)}


def persona(name, gender_hint=None):
    db = json.load(open(PERSONAS)) if os.path.exists(PERSONAS) else {}
    p = dict(db.get((name or "").lower(), {}))
    if not p:   # 23-Nov: never guess a person (a silent default gave every unknown name a 160 cm woman)
        raise SystemExit(f"persona '{name}' is not in {PERSONAS} - add her/his height, gender and photo first")
    g = p.get("gender") or gender_hint or "women"
    p.setdefault("gender", g)
    p.setdefault("height_cm", 173 if g == "men" else 160)
    p["name"] = name
    return p


def person_lock(p, outfit, hair):
    h = int(p["height_cm"]); man = p["gender"] == "men"
    she, her = ("he", "his") if man else ("she", "her")
    return (f"PERSON LOCK: {p['name']}, the same {'man' if man else 'woman'} as the persona sheet in every frame - same face, skin "
            f"tone, hair and build, about {p.get('age', 25)} years old. Real height {h} cm: the top of the 210 cm door frame is "
            f"about {210 - h} cm above {her} head, a 45 cm seat reaches {her} knee, an 85-90 cm counter reaches {her} hip; "
            f"{her} head is about one-seventh of {her} height. {she.capitalize()} keeps this exact size against the room in "
            f"every shot. Outfit: {outfit}. Hair: {hair}. No other accessories unless a product is one.")


def _words(s):
    return {w for w in re.findall(r"[a-z]{3,}", (s or "").lower()) if w not in STOP}


def similarity(a, b):
    A, B = _words(a), _words(b)
    return len(A & B) / max(1, len(A | B))


def movement_text(shot):
    ae = float(shot.get("action_end_s", 2.5))
    return shot.get("action_summary", "") + " " + " ".join(
        str(b.get("moves", "")) + " " + str(b.get("movement", "")) for b in shot.get("beats", []) if float(b.get("t_start", 0)) < ae)


def choose_rooms(plans):
    """Fewest rooms (max 2) covering every product's acceptable rooms; preferred rooms win ties."""
    acc = {s: [p["scene"]["room"]] + [r for r in p["scene"]["acceptable_rooms"] if r != p["scene"]["room"]] for s, p in plans.items()}
    pref = {}
    for s, p in plans.items():
        pref[p["scene"]["room"]] = pref.get(p["scene"]["room"], 0) + 1
    left, chosen = set(plans), []
    while left:
        cand = {r for s in left for r in acc[s]}
        best = max(cand, key=lambda r: (sum(1 for s in left if r in acc[s]), pref.get(r, 0)))
        chosen.append(best)
        left -= {s for s in left if best in acc[s]}
    assign = {s: next(r for r in acc[s] if r in chosen) for s in plans}
    return chosen, assign


POSE_KEY = re.compile(r"angle|yaw|pitch|pose|posit|hand|gaze|stance|display|direction|rotation|orient|weight|lean|tilt|"
                      r"expression|smile|look|parallel")
TYPES = [("heel_lift", r"heel (lifts?|raises?|rises?)|(lifts?|raises?) (the |her |his )?(right |left )?heel|onto the ball"),
         ("toe_raise", r"toes? (lift|lifts|raise|raises|rise|rises|point|points)|(lifts?|raises?) (the |her |his )?(right |left )?toes"),
         ("weight_shift", r"shift(s|ing)? (her |his )?weight|weight shift"),
         ("slide", r"\bslid(e|es|ing)\b|\bglid(e|es|ing)\b"), ("step", r"\bsteps?\b"), ("tap", r"\btaps?\b"),
         ("turn", r"turn|rotat|pivot|swivel|angle|\broll"), ("spray", r"spray|mist|spritz"), ("apply", r"apply|dab|rub|massage"),
         ("smooth", r"smooth|stroke"), ("label_turn", r"label"), ("lift_and_show", r"\blift|\braise|hold(s)? up"),
         ("place", r"\bplace|set(s)? down|puts? down"), ("pour", r"\bpour"), ("open", r"\bopen")]


def movement_type(shot):
    """The kind of movement of a shot variant (planner's movement_type, else read from its first moving beat)."""
    if shot.get("no_person"):
        return "photo"
    mt = str(shot.get("movement_type", "")).strip().lower()
    if mt and mt != "other":
        return mt
    ae = float(shot.get("action_end_s", 2.5))
    for b in shot.get("beats", []):
        if float(b.get("t_start", 0)) < ae and str(b.get("moves", "")).lower() not in ("nothing", "none", "camera", ""):
            txt = str(b.get("movement", "")).lower()
            for name, rx in TYPES:
                if re.search(rx, txt):
                    return name
            return "other"
    return "other"


def order_slots(plans, assign, rooms):
    """Topological order: a product that NEEDS a state (beard) comes before one that CHANGES it; then room, then slot."""
    before = {s: set() for s in plans}   # before[x] = slots that must come before x
    for a, pa in plans.items():
        ch = {k.lower(): str(v).lower().strip() for k, v in (pa["person"].get("state_changes") or {}).items()
              if not POSE_KEY.search(k.lower())}   # poses/angles reset at the cut between products - only lasting states count
        for b, pb in plans.items():
            if a == b:
                continue
            rq = {k.lower(): str(v).lower().strip() for k, v in (pb["person"].get("state_requires") or {}).items()
                  if not POSE_KEY.search(k.lower())}
            if any(k in rq and rq[k] != v for k, v in ch.items()):
                before[a].add(b)
    order, done = [], set()
    while len(order) < len(plans):
        ready = [s for s in plans if s not in done and before[s] <= done]
        if not ready:
            return None
        s = min(ready, key=lambda x: (rooms.index(assign[x]), x))
        order.append(s); done.add(s)
    return order


_SUPPORT = re.compile(r"\b(table|counter|countertop|tray|shelf|dresser|desk|stool|mat|bed|sofa|floor|cabinet|top|surface|chair|rack|sill|"
                      r"stand|basket|caddy|bin|organi[sz]er|box|cloth|towel|lap|changing table|crib|cot)\b", re.I)
_FURNITURE = re.compile(r"\b(sofa|couch|desk|table|chair|stool|bed|cabinet|dresser|shelf|rack|bench|crib|cot|wardrobe|console)\b", re.I)


def _supported(p):
    """A prop is drawn only if its placement says what holds it up (furniture may simply stand against a wall / on the floor)."""
    pl = str(p.get("placement", ""))
    if _FURNITURE.search(str(p.get("item", ""))) and re.search(r"\b(wall|floor|corner|room)\b", pl, re.I):
        return True
    return bool(_SUPPORT.search(pl))


_PROP_CLASSES = [("cloth", r"\b(cloth|muslin|napkin|towel|blanket|swaddle|wrap)\b"),
                 ("container", r"\b(tray|caddy|bin|organi[sz]er|basket|box|crate)\b")]


def _prop_class(text):
    t = str(text).lower()
    for n, rx in _PROP_CLASSES:
        if re.search(rx, t):
            return n
    return None


def build(row, family, variant, persona_name, plans, specs):
    """plans/specs: {slot: dict}. Returns (reel dict, errors, warnings)."""
    E, W = [], []
    rooms, assign = choose_rooms(plans)
    if len(rooms) > 2:
        E.append(f"the 5 products need {len(rooms)} rooms {rooms} (max 2) - re-plan a product or change the row's approach")
    order = order_slots(plans, assign, rooms)
    if order is None:
        E.append("the products' person states contradict each other in every order (e.g. two products both need and remove the beard)")
        order = sorted(plans)
    # one shot variant per product: every product a DIFFERENT movement type (user 20-Nov rule), then the least similar wording
    import itertools
    opts = {}
    for s in order:
        vs = shots_of(plans[s]); good = plans[s].get("_meta", {}).get("valid_variants")
        good = [i for i in (good if good is not None else range(len(vs))) if i < len(vs)]
        if not good:
            E.append(f"slot {s}: no usable shot variant")
        opts[s] = good or [0]
    display = family == "footwear" and any(plans[s].get("_meta", {}).get("letter", "") in DISPLAY_LETTERS for s in order)   # 22-Nov: same movement by design
    FACE = {"full_body", "knee_up", "waist_up", "shoulders_up", "wall_close"}
    best, best_key, best_cmp = None, None, None
    for combo in itertools.product(*[opts[s] for s in order]):
        shots = [shots_of(plans[s])[i] for s, i in zip(order, combo)]
        types = [movement_type(x) for x in shots]
        texts = [movement_text(x) for x in shots]
        sim = max([similarity(a, b) for a, b in itertools.combinations(texts, 2)] or [0])
        over = 0 if display else sum(max(0, types.count(t) - 2) for t in set(types) if t != "photo")       # user 21-Nov: a movement may appear in at most 2 products
        face = any(x.get("framing_start") in FACE and not x.get("no_person") for x in shots)          # user 21-Nov: the face is seen at least once per reel
        same_cut = sum(1 for x, y in zip(shots, shots[1:]) if x.get("framing_end") == y.get("framing_start"))
        key = (-over, face, len(set(types)), -same_cut, -sim)
        pc = sum(1 for x in shots if x.get("no_person"))
        cmp_key = (face, pc <= 3, (pc if family == "home_decor" else -pc), key[0], key[2], key[3], key[4])   # 22-Nov: the face is shown; at most 3 photo shots; decor prefers them
        if best_key is None or cmp_key > best_cmp:
            best, best_key, best_cmp = combo, key, cmp_key
    chosen = dict(zip(order, best))
    types = {s: movement_type(shots_of(plans[s])[chosen[s]]) for s in order}
    count = {}
    for s, ty in types.items():
        count.setdefault(ty, []).append(s)
    over = {} if display else {k: v for k, v in count.items() if len(v) > 2 and k != "photo"}
    if over:
        E.append("more than 2 products would repeat the same movement (" + "; ".join(f"{k}: slots {v}" for k, v in over.items())
                 + ") - re-plan one of them after the user's yes: pipeline.py plan <row> --confirmed --replan=<slots>")
    if not best_key[1]:
        E.append("no product shows the person's face (every variant starts below the face) - re-plan one slot after the "
                 "user's yes: pipeline.py plan <row> --confirmed --replan=<slot> (the rule book now asks for a face variant)")
    if best_key[3] < 0:
        W.append("two consecutive products cut between the same framing - the cut may look like a jump")
    # person
    gender = "men" if variant == "men" else "women" if variant == "women" else None
    per = persona(persona_name, gender)
    reqs = []
    for s in order:
        reqs += [r for r in (plans[s]["person"].get("requirements") or []) if r not in reqs]
    if family in CLOTHING_FAMILIES:
        outfit = ("in each product's shot the person wears THAT product exactly (its reference sheet); everything that is not part "
                  "of the listing stays the same plain neutral pieces in every product: " +
                  ("plain off-white straight trousers if a listing has no bottom, plain tan flat sandals" if per["gender"] != "men"
                   else "plain beige trousers if a listing has no bottom, plain brown leather sandals"))
    else:
        outfit = OUTFIT.get((family, per["gender"])) or HOME_OUTFIT[per["gender"] if per["gender"] in HOME_OUTFIT else "women"]
    if reqs:
        outfit += "; for these products: " + "; ".join(reqs)
    hair = ("short, neatly combed" if per["gender"] == "men" else "tied in a neat low bun, a few loose strands")
    # rooms -> background bibles
    prod_kinds = {s: kinds_of(plans[s]["product"].get("category_item", "") + " " + plans[s]["product"].get("type", "")) for s in plans}
    bibles = {}
    for r in rooms:
        t = ROOMS[r]; here = [s for s in order if assign[s] == r]
        swap, items = {}, []
        for item, kind, size, place in t["items"]:
            owners = [s for s in here if kind in prod_kinds[s]]
            if owners and kind not in SWAP_KINDS:
                continue                                     # the product category is not in the room at all (no 2nd rug)
            if owners:
                swap[kind] = owners
                item = item + f" - in slot {', '.join(map(str, owners))} this is REPLACED by that product (never both at once)"
            items.append(dict(item=item, kind=kind, size_cm=size, placement=place))
        for s in here:                                       # props the real uses need: life-size, fixed, there all reel long
            for p in plans[s]["scene"].get("props") or []:
                if not any(p["item"].lower() in x["item"].lower() for x in items):
                    if not _supported(p):
                        W.append(f"slot {s}: prop '{p['item']}' is dropped - its placement names nothing it rests on (it would float)")
                        continue
                    cl_ = _prop_class(p["item"])             # 22-Nov: one cloth and one container per room - 4 muslin cloths on one table cannot be drawn consistently
                    if cl_ and any(x["kind"] == "prop" and _prop_class(x["item"]) == cl_ for x in items):
                        W.append(f"slot {s}: prop '{p['item']}' is dropped - the room already has a {cl_} prop (clutter is redrawn differently in every frame)")
                        continue
                    items.append(dict(item=p["item"], kind="prop", size_cm=p["size_cm"], placement=p["placement"]))
        exclude = list(ALWAYS_EXCLUDE)
        if FAMILY_EXCLUDE.get(family):
            exclude.append(FAMILY_EXCLUDE[family])
        for s in here:
            exclude += [x for x in (plans[s]["scene"].get("exclude") or []) if x not in exclude]
        bibles[r] = dict(room=r, walls=t["walls"], floor=t["floor"], back=t["back"], light=t["light"], items=items,
                         exclude=exclude, swap=swap)
        anchors, surfaces = {}, {}
        for s in here:   # user 21-Nov: the product's surface is furniture of the room bible, so the ROOM MASTER already contains it
            sc_ = plans[s]["scene"]; sf = sc_.get("surface") if isinstance(sc_.get("surface"), dict) else {}
            k = sf.get("kind")
            if k == "floor":
                anchors[s] = surfaces[s] = f"the floor ({bibles[r]['floor']})"
            elif k == "wall":
                anchors[s] = surfaces[s] = f"{bibles[r]['back']} - the plain {bibles[r]['walls']}; ONLY this product is on it"
            elif k == "lap":
                anchors[s] = surfaces[s] = "her lap"
            elif k == "none_held":
                anchors[s] = surfaces[s] = "no surface: the product stays in one hand the whole time"
            elif k in SURFACE_KIND_MAP:
                hit = next((x for kd in SURFACE_KIND_MAP[k] for x in bibles[r]["items"] if x["kind"] == kd), None)
                if hit:
                    txt = f"{hit['item'].split(' - in slot')[0]} ({hit['size_cm']}), {hit['placement']}"
                else:
                    bibles[r]["items"].append(dict(item=f"a {sf.get('name', k)}", kind="surface", size_cm=sf.get("size_cm", ""),
                                                   placement=sf.get("placement", "")))
                    txt = f"a {sf.get('name', k)} ({sf.get('size_cm', '')}), {sf.get('placement', '')}"
                    W.append(f"slot {s}: its surface '{sf.get('name')}' is not in the {r} template - added to the room bible "
                             "(it is in the room master from the first image)")
                anchors[s] = surfaces[s] = txt
            else:
                a_, ok = room_anchor(bibles[r], sc_["anchor"]); anchors[s] = surfaces[s] = a_
                if not ok:
                    W.append(f"slot {s}: its anchor '{sc_['anchor']}' is not furniture of the {r} bible - check the shot")
        bibles[r]["anchors"] = anchors; bibles[r]["surfaces"] = surfaces
    reel = dict(display=bool(display), row=int(row), family=family, variant=variant, persona=per, outfit=outfit, hair=hair,
                person_lock=person_lock(per, outfit, hair), rooms=rooms, room_of={str(s): assign[s] for s in plans},
                order=order, variant_of={str(s): chosen.get(s, 0) for s in plans},
                movement_of={str(s): types.get(s, "other") for s in plans}, bibles=bibles, camera=CAMERA)
    return reel, E, W


SURFACE_KIND_MAP = {"table": ("table", "side_table", "counter"), "counter": ("counter", "table"),
                    "dresser": ("dresser", "side_table", "cabinet", "table"), "bed": ("bed",), "sofa": ("sofa", "seat"),
                    "shelf": ("shelf", "cabinet"), "stool": ("seat",), "desk": ("table",), "cabinet_top": ("cabinet", "dresser")}
ANCHOR_KINDS = [(r"sofa|couch|chair|bench|stool|seat|ottoman", ("sofa", "seat")), (r"counter|sink|basin|vanity counter", ("counter",)),
                (r"\bbed\b|mattress", ("bed",)), (r"dresser|vanity|dressing table", ("dresser",)), (r"table|desk", ("table",)),
                (r"crib|cot", ("crib",)), (r"washing machine", ("appliance",))]


def room_anchor(b, text):
    """The plan's anchor mapped to the room's OWN furniture (so no new chair/sofa is ever added - background stays fixed)."""
    t = (text or "").lower()
    for rx, kinds in ANCHOR_KINDS:
        if re.search(rx, t):
            for x in b["items"]:
                if x["kind"] in kinds:
                    return f"{x['item'].split(' - in slot')[0]} ({x['size_cm']}), {x['placement']}", True
    if re.search(r"floor|rug|tile", t):
        return f"the floor ({b['floor']})", True
    return text, False


def background_text(b):
    lines = [f"BACKGROUND BIBLE - {b['room'].replace('_', ' ')} (identical in EVERY frame of this room; the camera always faces "
             f"{b['back']}): walls {b['walls']}; floor {b['floor']}; light {b['light']}. Furniture and background props, real "
             f"sizes in cm, never moved, added or removed:"]
    lines += [f"  - {x['item']} ({x['size_cm']}) - {x['placement']}" for x in b["items"]]
    lines.append("  SUPPORT CHAIN (user 23-Nov: a cloth hovered with things on it): every item above rests ON the furniture or floor its "
                 "placement names, touching it with a contact shadow; a cloth, towel, mat, napkin or tray lies flat ON a table, counter, "
                 "bed or shelf (its whole underside on it), and only then can anything rest on it; nothing hangs, floats or is propped in the air.")
    lines.append("  NOT in the room: " + "; ".join(b["exclude"]) + ".")
    return "\n".join(lines)
