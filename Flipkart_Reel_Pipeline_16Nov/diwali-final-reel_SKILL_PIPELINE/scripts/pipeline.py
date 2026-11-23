"""FINAL Diwali pipeline helper (user 30-Oct-2026: "gesture wala final usi ko continue karna hai").

    /usr/bin/python3 pipeline.py new <row> [<row> ...]   set up 03_WORK/row_NNN (brief.json, products/, folders)
    /usr/bin/python3 pipeline.py prompt <row>            print the worker prompt (category template, title, music, decor)
                                                         vertical "Makeup" -> Beauty pipeline prompt (../../beauty_pipeline)
    /usr/bin/python3 pipeline.py prompt <row> [A-E]      BAU: presentation approach = the row's letter in 02_BAU_DATA/row_approaches.csv
    /usr/bin/python3 pipeline.py setapproach <A-E|HOLD> <rows...|from-to>   choose the approach per row (HOLD = do not run)
    /usr/bin/python3 pipeline.py setslot <1-5> <rows...>  Makeup: which slot is the ONE applied product (others only shown)
    /usr/bin/python3 pipeline.py approaches [<letter>]   per vertical: rows per letter + on hold (and the rows set to <letter>)
    /usr/bin/python3 pipeline.py finish <row>            assemble_fk -> 480p -> 01_LATEST_FINAL/ (no QC)
    /usr/bin/python3 pipeline.py status                  which batch rows are in 01_LATEST_FINAL, which are open
    /usr/bin/python3 pipeline.py addrows <sheet_rows.json> add sheet rows (data + products) to 04_DATA
    /usr/bin/python3 pipeline.py musicplan <rows...>     6-track rotation in row order -> 04_DATA/music_plan.json
    /usr/bin/python3 pipeline.py upload <rows...>        480p -> Drive category folder, links -> 04_DATA/drive_links_final.json

Work root = 01_DIWALI_REELS/03_WORK (BBD_OUT). Row data = 04_DATA/batch_100.json + 04_DATA/rows/row_NNN/.
Finals = 01_LATEST_FINAL/<Category>/ (+ 1080p_masters/).
"""
import json, os, re, shutil, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import makeup_approaches   # 16-Nov: Makeup = 5 apply approaches per product type, one product applied per reel
import product_spec   # 17-Nov: per-product spec sheets sent as the generation reference (not Makeup)
import approaches   # 16-Nov: presentation approaches A-E per vertical (REEL_PRESENTATION_IMPLEMENTATION_SPEC.md)
LAX = os.environ.get("FK_LAX") == "1"


def strict(msg):
    """22-Nov (user: checks must not stop a paid run): with FK_LAX=1 a failed check is printed and logged, never raised, so the
    reel is always finished and filed. Without FK_LAX it raises as before."""
    if LAX:
        print("WARNING (not blocking): " + msg, flush=True)
        try:
            open(os.path.join(os.environ.get("FK_CHECKS_LOG", "/private/tmp/fk_checks.log")), "a").write(msg + "\n")
        except OSError:
            pass
        return
    raise SystemExit(msg)


def block(msg):
    """23-Nov (Garvit): structural and before-payment checks ALWAYS stop the row. FK_LAX never turns these into warnings:
    a wrong plan must not be paid for, and a broken reel must not be filed or uploaded."""
    raise SystemExit(msg)


import product_planner, reel_planner, shot_builder   # 21-Nov: OpenAI product plans -> one consistent, planned reel

# 13-Nov: FK_MODE=BAU switches to the BAU job (sheet tab "1500_1", user: "ek alag se folder bana dena") - its own root, so
# its row numbers never clash with the Diwali 03_WORK/row_NNN folders. Without FK_MODE everything is exactly as before.
BAU = os.environ.get("FK_MODE", "").upper() == "BAU"
# 16-Nov: ONE pipeline folder - everything (both pipelines, assets, music, data, runs) lives under PIPE (this export's root).
PIPE = os.environ.get("FK_PIPE") or os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
KL = os.environ.get("FK_WORK_ROOT") or os.path.join(PIPE, "runs", "BAU_1500_1" if BAU else "DIWALI")
PREFIX = "BAU1500" if BAU else "Diwali"
TAB = "1500_1" if BAU else "Diwali Phase_1"
WORK = os.path.join(KL, "03_WORK")
DATA = os.path.join(PIPE, "02_BAU_DATA") if BAU else os.path.join(KL, "04_DATA")
LATEST = os.path.join(KL, "01_LATEST_FINAL")
SKILL = os.path.join(PIPE, "diwali-final-reel_SKILL_PIPELINE")
OMNI = os.path.join(PIPE, "bbd-omni-reel_skill")          # was {OMNI}
ASM_FK = os.path.join(SKILL, "scripts", "assemble_fk.py")
PY = sys.executable
_BP = os.path.join(DATA, "batch_100.json")
BATCH = json.load(open(_BP)) if os.path.exists(_BP) else {}

# category -> (template key, example row folder in 02_SKILL_PIPELINE/examples, decor)
CATS = {
    "Women's Ethnic Wear": ("apparel", "row_006", True),
    "WomenWesternCore": ("apparel", "row_195", False),
    "KidClothing": ("apparel_kid", "row_256", False),
    "WomenFW": ("footwear", "row_065", False),
    "Men Footwear": ("footwear", "row_065", False),
    "KidsFootwear": ("footwear_kid", "row_065", False),
    "FashionWearables": ("wearable", "row_195", False),
    "Home Decor": ("decor", "row_444", True),
    "HomeFurnishing": ("furnishing", "row_444", False),
    # 30-Oct: the 7 non-fashion categories of the Diwali sheet (Fragrance excluded by the user) - not sampled yet
    "House Hold Kitchen": ("kitchen", "row_444", False),
    "Household suppliers": ("household", "row_444", False),
    "Makeup": ("makeup", "row_444", False),
    "Grooming Men": ("grooming", "row_444", False),
    "BabyCare": ("babycare", "row_444", False),
    "ToysAndSS": ("toys", "row_444", False),
    "Pets": ("pets", "row_444", False),
    # 4-Nov: Fragrance sample (row 875, user picked it) - style C hands-only
    "Fragrance": ("fragrance", "row_444", False),
    # 13-Nov BAU tab 1500_1: Men Ethnic (new category)
    "Men Ethnic": ("apparel_men", "row_006", False),
    # 14-Nov BAU tab 1500_1 Day 2: Fashion Wearables split by gender (sunglasses, watches, belts, bags, jewellery)
    "FashionWearables _Women": ("wearable", "row_195", False),
    "FashionWearables _Men": ("wearable_men", "row_195", False),
    # 16-Nov BAU tab 1500_1 Day 2: Women Footwear (sheet col Q "DAY 2", rows 122-141)
    "women Footwear": ("footwear_bau", "row_065", False),
    # 16-Nov: exact Rhythm CSV labels (shot grammar comes from approaches.py A-E; key only picks room/notes)
    "Women western": ("apparel", "row_195", False), "Men casual": ("apparel_men", "row_006", False),
    "Home Decore": ("decor", "row_444", False), "household kitchen": ("kitchen", "row_444", False),
    "baby care": ("babycare", "row_444", False), "women fragrance": ("fragrance", "row_444", False),
    "Men fragrance": ("fragrance", "row_444", False),
}
# vertical -> folder name (01_LATEST_FINAL/<code> and the Drive category folder)
FOLDERS = {"Women's Ethnic Wear": "Women's Ethnic Wear", "WomenWesternCore": "Women's Western Wear", "KidClothing": "Kids Clothing",
           "WomenFW": "Women's Footwear", "Men Footwear": "Men's Footwear", "KidsFootwear": "Kids Footwear",
           "FashionWearables": "Fashion Wearables", "Home Decor": "Home Decor", "HomeFurnishing": "Home Furnishing",
           "House Hold Kitchen": "Household Kitchen", "Household suppliers": "Household Supplies", "Makeup": "Makeup",
           "Grooming Men": "Men's Grooming", "BabyCare": "Baby Care", "ToysAndSS": "Toys and School Supplies", "Pets": "Pets",
           "Fragrance": "Fragrance", "Men Ethnic": "Men's Ethnic Wear",
           "FashionWearables _Women": "Women's Fashion Wearables", "FashionWearables _Men": "Men's Fashion Wearables",
           "women Footwear": "Women's Footwear",
           "Women western": "Women's Western Wear", "Men casual": "Men's Casual Wear", "Home Decore": "Home Decor",
           "household kitchen": "Household Kitchen", "baby care": "Baby Care", "women fragrance": "Women's Fragrance",
           "Men fragrance": "Men's Fragrance"}
TITLE_HEAD = {"apparel": "Diwali Try-On Haul", "apparel_kid": "Kids' Diwali Looks", "footwear": "Diwali Footwear Edit",
              "footwear_kid": "Diwali Kids' Footwear", "wearable": "Diwali Accessory Edit", "decor": "Diwali Decor Edit",
              "furnishing": "Diwali Home Refresh", "kitchen": "Diwali Kitchen Picks", "household": "Diwali Home Essentials",
              "makeup": "Diwali Beauty Picks", "grooming": "Diwali Grooming Kit", "babycare": "Diwali Baby Care Picks",
              "toys": "Diwali Toy Box", "pets": "Diwali Pet Picks",
              "fragrance": "Diwali Fragrance Picks", "apparel_men": "Ethnic Try-On Haul", "wearable_men": "Accessory Edit"}
# room override for categories whose products belong in another room of the same v2-class home
ROOMS = {
    "kitchen": "a bright, modern, tidy Indian apartment KITCHEN of the same class as the style reference: light quartz or granite "
               "counter, white or pastel modular cabinets, a window with daylight, a few real things (a steel bottle, a fruit basket, "
               "a hand towel), gas hob OFF - no flame anywhere",
    "household": "the same v2-class flat: a utility/laundry corner or living room as fits the products (ironing, cleaning, storage), "
                 "bright and tidy, real",
    "makeup": "a bright bedroom DRESSING-TABLE corner of the same class: a wooden vanity with a mirror (the mirror shows only her back "
              "/ the room, never a phone or a second person), soft window daylight, a few cosmetics neatly placed",
    "grooming": "a clean modern BATHROOM vanity or bedroom mirror corner of the same class (white tiles, a mirror cabinet, a towel), "
                "daylight; the mirror never shows a phone or a second person",
    "fragrance": "a bright bedroom DRESSING-TABLE corner of the same class: a light wooden vanity top with a small tray, a folded "
                 "dupatta or a jewellery dish, soft window daylight; the mirror (if visible) shows only the room, never a phone or a person",
    "babycare": "a bright bedroom/nursery corner of the same class: a wooden crib with soft white bedding, a changing table, a soft toy",
    "toys": "a bright living room or kids' room corner of the same class, a play mat on the floor",
    "pets": "OUTDOORS - the LAWN of the same v2-class home (user 1-Nov: 'pet wala ghar ke lawn main hona chahiye'): a neat green "
            "grass lawn of an Indian independent house / villa garden, the house wall and a glass door or verandah behind, potted "
            "plants, a garden bench or cane chair, soft natural daylight (no harsh sun), a pet bed or mat on the grass. NOT indoors",
}

TEMPLATES = {
    "apparel": """APPAREL (approved: rows 6 / 195): 5 outfits, all WORN, ~22-24 s. Mix per outfit (never the same pattern twice in a row):
  BEFORE -> WORN pairs (user 30-Oct night: "kuch hanger pe kuch packing open karte huye, taki ek jaise na lage", "hanger pe kam
  dikhana"), mixed so no two videos look alike:
    PACKET OPEN (~2 s, hands only, on the bed or a table): two hands tear open / unzip a plain Flipkart-style courier pouch and
      slide out the exact folded outfit, its print visible -> cut to it WORN with a REF_GESTURES gesture;
    HANGER (~2 s, one hand at the hook, hands only) -> WORN - AT MOST ONE hanger shot per video (many videos use none).
  WORN + zoom punch-in on the cloth (same clip continued, zoom 1.8, zoom_y >= 0.7, face never cut);
  WORN -> CLOSE-UP of the worn detail (print / embroidery / border), her hand showing it, no face.
  Use 2 before->worn pairs (at least 1 PACKET OPEN, at most 1 HANGER), 2-3 zoom punch-ins, 2 close-ups. The outfit is never
  shown held up or lying alone as a shot of its own - the packet/hanger moment is only the ~2 s before it is worn.
  Gestures all different (turn, dupatta, smooth, waist, look_down, flare).""",
    "apparel_kid": """KIDS APPAREL (approved: row 256): as APPAREL, the child WEARS every set; packet opened / hanger held by the MOTHER's hands; CLIP_REALISM_CHILD
  (playful, filmed by a parent); child-friendly gestures (twirl/flare, turn, dupatta lift, look_down, hand on waist).""",
    "footwear": """FOOTWEAR (approved: row 65): EVERY distinct pair = SHOWN first (two hands turning ONE shoe, hands only, short product-only
  prompt) -> WORN (full body wide -> zoom punch-in on the feet zoom 2.1-2.4 zoom_y 1.0, and/or knees-down "phone held very low,
  about 40 cm from her feet"). realism.FOOTWEAR_BEAUTY on every plate (attractive, groomed, pedicured feet). Outfit with ankles
  visible, same in every shot. Gesture foot_show / step / heel turn / toe tap.""",
    "footwear_kid": """KIDS FOOTWEAR: as FOOTWEAR, the child WEARS each pair; the SHOWN shot is the mother's two hands turning one shoe;
  CLIP_REALISM_CHILD; playful steps/jumps on the spot; no FOOTWEAR_BEAUTY adult wording - "clean, neat, cute" instead.""",
    "wearable": """FASHION WEARABLES (watches / bags / accessories - not sampled yet, built from the approved grammar): each product
  SHOWN first in her hands (turning it, hands only) -> WORN/CARRIED (watch on her wrist, bag on her shoulder or in her hand)
  with a gesture (look_down at the wrist, adjust the strap, turn) -> zoom punch-in on the product (zoom 1.7-2.0, zoom_y where it
  sits) and 1-2 close-ups (dial, clasp, texture). Her outfit stays the same and suits the product.""",
    "decor": """HOME DECOR (approved: row 444): calm reveal - she carries each product in with both hands and PLACES it (before -> after),
  then the same clip continues as a zoom punch-in on the product (zoom ~1.7, zoom_y 0.85-0.9; keep the product centred in the
  plate). 2 close-ups of product detail. Diwali decor ON. NOTHING LIT - no flames on diyas/candles/tealights, ever.""",
    "furnishing": """HOME FURNISHING (bedsheets / cushion covers / curtains - not sampled yet, built from the approved grammar): each
  product SHOWN first folded in her hands -> cut to it ALREADY laid on the bed, bed made (cushion placed, curtain drawn) and her hand
  smoothing it -> zoom punch-in on the print, + 1-2 close-ups of fabric texture with her hand. User 31-Oct: NEVER shake / unfold /
  spread a bedsheet in the air (it looks tiny) - only FOLDED IN HANDS -> LAID ON THE BED. On the bed the sheet must look full-size:
  it covers the WHOLE mattress edge to edge and hangs over both sides and the foot of the bed, matching pillow covers on the pillows,
  wide enough to show the full bed (never a narrow strip that reads like a towel or throw). No Diwali decor. Same home, same outfit.""",
    "kitchen": """HOUSEHOLD KITCHEN (new 30-Oct, built from the approved grammar): each product SHOWN first in her two hands (turning it,
  hands-only or waist-up) -> IN USE / PLACED in the kitchen (she sets the container/cookware on the counter, opens a lid, stacks
  it, pours water from a bottle) -> zoom punch-in on the product (zoom ~1.7, zoom_y where it sits) + 1-2 close-ups (lid, handle,
  finish). Gas OFF, no flame, no food cooking on fire. Everyday nice home clothes.""",
    "household": """HOUSEHOLD SUPPLIES (new 30-Oct): each product SHOWN in her hands -> USED naturally (iron moves over a shirt on an
  ironing board - unplugged look, no steam drama; organiser filled; cleaning tool used on a table) -> zoom punch-in + close-up.
  Check every listing first and pick a plausible action per product.""",
    "makeup": """MAKEUP (new 30-Oct): each product SHOWN to the camera in one hand (turning it to show the shade/label side) -> APPLIED
  at the dressing table (lipstick swiped on the lips, kajal, compact dabbed) - her lips may move ONLY as part of applying
  lipstick, never talking -> zoom punch-in on the product or the applied look (face allowed here, zoom_y ~0.3-0.4) + 1 close-up
  swatch on the back of her hand. Exactly 2 hands; mirror never shows a phone.""",
    "grooming": """MEN'S GROOMING (new 30-Oct): the man SHOWS each product (trimmer/shaver/kit) in his hands -> USES it at the mirror
  (trimmer moving along the beard line, no cuts, no blood) -> zoom punch-in on the product in hand + 1 close-up of the blade/head.
  Handsome, groomed, real skin. Exactly 2 hands.""",
    "fragrance": """FRAGRANCE (new 4-Nov, style C hands-only, built from the approved grammar): every distinct listing gets >= 2 shots.
  SHOWN: two hands pick the bottle up from the vanity and turn it slowly so the front label reads clearly -> USED: one hand lifts the
  cap off and sets it down, then a light spritz onto the inner wrist of the other hand (a fine soft mist, no liquid dripping) ->
  zoom punch-in on the label/cap (zoom ~1.6-1.8, zoom_y where it sits) + 1 close-up (cap, glass ribs, box art). Gift sets are
  shown ALREADY OPEN on the vanity (no lid opening, no unboxing): a hand lifts one bottle out of its slot and puts it back.
  The product box stands next to its bottle. Exactly 2 hands from the bottom edge, plain sleeves, no face, no rings changing.
  Bottle shape, cap colour (gold / rose-gold / silver) and printed names must match the listing exactly.""",
    "babycare": """BABY CARE (new 30-Oct): the mother SHOWS each product in her hands (turning it) -> USES / PLACES it calmly (lotion
  on her palm, a soft blanket folded into the crib, a baby item set on the changing table). A baby may lie asleep in the crib in
  the background, still and safe - never held up, never handled roughly, face mostly turned away. Zoom punch-in on each product
  + 1 close-up. Gentle, warm.""",
    "toys": """TOYS & SCHOOL SUPPLIES (new 30-Oct): she SHOWS each product (unboxed, in her hands) -> a child (~7 y, same child in
  every shot) PLAYS with it / uses it on the play mat or a table, delighted (closed-mouth smile), she watches -> zoom punch-in on
  the product + 1 close-up. CLIP_REALISM_CHILD for shots with the child.""",
    "pets": """PETS (new 30-Oct): he SHOWS each pet product in his hands -> his pet (ONE friendly dog, same dog in every shot, calm
  natural movement) USES it (eats from the bowl, lies on the bed, plays with the toy, wears the collar) -> zoom punch-in on the
  product + 1 close-up. Exactly one dog, four legs, no extra animals.
  LOCATION (user 1-Nov): EVERY shot is OUTSIDE on the home's LAWN (green grass, house wall/verandah behind), never a living room -
  ignore the indoor HOME_V2_ROOMS room; keep only the v2 class / phone-look. Same lawn spot in every shot. Bathing (shampoos) =
  on the grass with a tub or towel, lather on the dog.""",
}

# User 30-Oct night: "is tarah sari categories main kar dena, mtlb same na lage" - every category mixes several ways of bringing a
# product in (like packet-open vs hanger for apparel), and neighbouring videos open differently.
INTROS = {
    "footwear": ["SHOE-BOX OPEN: two hands lift the lid, the pair sits in tissue, one shoe is taken out",
                 "SHOWN: two hands turning one shoe", "PACKET OPEN: hands slide the pair out of a courier pouch"],
    "wearable": ["BOX OPEN: hands open the watch/accessory box and lift the product out",
                 "SHOWN: she turns the product in her hands", "PACKET OPEN: hands slide it out of a courier pouch"],
    "decor": ["CARRY IN: she carries it in with both hands and places it",
              "UNBOX: she lifts it out of an opened carton on the floor/table, then places it",
              "FINISHING TOUCH: it is already in place, her hand straightens/turns it"],
    # user 31-Oct: no SPREAD/shake-open intro for bedsheets (looks tiny) - folded in hands, then already laid on the bed
    "furnishing": ["FOLDED: shown folded in her hands", "PACKET OPEN: hands open the pack and slide the folded set out",
                   "PICK UP: she picks the folded set up from the bench/bed end"],
    "default": ["SHOWN: shown in the presenter's hands, turning it", "PACKET/BOX OPEN: hands open a courier pouch or the product box and take it out",
                "PICK UP: the presenter picks it up from the shelf/counter where it already sits"],
}
INTRO_KEY = {"footwear": "footwear", "footwear_kid": "footwear", "wearable": "wearable", "decor": "decor", "furnishing": "furnishing"}


def variety(key, row):
    if key in ("apparel", "apparel_kid"):
        return ""   # apparel has its own packet-open / hanger mix in the template
    if key in ("footwear", "footwear_kid"):
        # user 31-Oct: "footwear ko aise hi hath main dikhao jaise pahele dikhate the, packet se nahi nikalo"
        # 31-Oct: rows 73/74 and 135/136 came out in the same outfit -> rotate the outfit by row
        women = ["mustard-yellow kurta with white cropped palazzo", "teal straight kurta with cream cropped pants",
                 "rust-orange co-ord set (short kurta + ankle-length pants)", "soft-pink printed kurta with white cigarette pants",
                 "olive-green kurta with beige cropped pants", "white chikankari kurta with blue cropped denim",
                 "maroon short kurti with off-white ankle pants", "navy-blue kurta with white cropped pants"]
        men = ["olive-green half-sleeve shirt with cream chinos", "black polo T-shirt with grey chinos",
               "mustard short kurta with white pyjama pants", "light-grey linen shirt with dark-brown chinos",
               "beige linen shirt with olive chinos", "rust-orange polo with navy chinos",
               "white short kurta with beige chinos", "denim-blue shirt with khaki chinos"]
        fol = BATCH[str(row)]["folder"]
        outfits = men if "Men" in fol and "Women" not in fol else women
        return ("FOOTWEAR INTRO (user 31-Oct): every pair is SHOWN in two hands exactly as in the approved row 65 - NO packet "
                "opening and NO shoe-box opening.\nOUTFIT for THIS video (rotated per row so neighbouring videos never match; "
                f"kids: a child-size version): {outfits[int(row) % len(outfits)]}, ankles visible, the same in every shot.")
    opts = INTROS[INTRO_KEY.get(key, "default")]
    first = opts[int(row) % len(opts)]
    return ("VARIETY (user: \"same na lage\"): bring the products in with a MIX of these intros - " + " | ".join(opts) +
            f". Open THIS video with: {first}. Use at least 2 different intro types and at least 1 packet/box opening; never the "
            "same intro 3 times in a row. Do NOT change the approved shot framing (user: \"shot mat badlna\") - only the way each product is brought in varies. The SHOWN -> USED/WORN beat stays.")


BOARDS = [1, 4, 5, 6, 7]   # 30-Oct: board 2 (Bebas, ALL CAPS) dropped - sheet titles must keep their exact case; 0/3 white shadow unreadable on light walls


def rdir(row):
    return os.path.join(WORK, f"row_{int(row):03d}")


def cat_code(v):
    return re.sub(r"[^A-Za-z]", "", v["folder"])


# 16-Nov: BEAUTY ROUTE - rows whose vertical is in BEAUTY_VERTICALS are made with the Beauty pipeline (Omni 360p, concept card,
# product_text.json, hands_prompt, check_actions, generate_clips, per-run assemble.py) instead of the apparel templates above.
# new / prompt / finish / upload / status keep working the same way: same row folder, same out_name, same 01_LATEST_FINAL layout.
BEAUTY_VERTICALS = {"Makeup"}
BEAUTY = os.environ.get("FK_BEAUTY_DIR") or os.path.join(PIPE, "beauty_pipeline")
BEAUTY_SUBDIRS = ("04_actions", "assets/anchor", "assets/plates", "assets/product_refs", "assets/keyframes",
                  "assets/video_clips", "assets/bgm", "exports", "final", "qc", "work")


def is_beauty(row):
    return BATCH[str(row)]["vertical"] in BEAUTY_VERTICALS


def new_beauty(row, d):
    """Lay out the Beauty run folder inside the normal row folder (row_NNN = the Beauty pipeline's ID_<row>)."""
    v = BATCH[str(row)]
    for sub in BEAUTY_SUBDIRS:
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    mf = os.path.join(d, "01_product_manifest.md")
    if not os.path.exists(mf):
        open(mf, "w").write(f"# Row {row} {v['name']} - {v['vertical']} - product manifest (fill from the listings)\n\n"
                            + "".join(f"{i}. {u}\n" for i, u in enumerate(v["products"], 1)))
    log = os.path.join(d, "08_run_log.md")
    if not os.path.exists(log):
        open(log, "w").write(f"# Row {row} {v['name']} - {v['vertical']} - BEAUTY pipeline run log\n")


def makeup_choice(row, letter=None):
    """Row's makeup approach letter + applied slot from row_approaches.csv (empty/HOLD = on hold)."""
    r = approaches.load_sheet(DATA).get(int(row), {})
    if not (letter or os.environ.get("FK_APPROACH")) and (r.get("approach") or "").strip().upper() not in ("", "HOLD"):
        approaches.check_rotation(DATA, row, r["approach"].strip().upper())   # 21-Nov: >= 5 approaches before one repeats
    letter = (letter or os.environ.get("FK_APPROACH") or r.get("approach") or "").strip().upper()
    if not letter or letter == "HOLD":
        raise SystemExit(f"row {row}: ON HOLD - no makeup approach in row_approaches.csv (pipeline.py setapproach <A-E> {row})")
    pids = [re.sub(r".*pid=", "", u).split("&")[0] if "pid=" in u else "" for u in BATCH[str(row)]["products"]]
    slot = int(os.environ.get("FK_APPLY_SLOT") or r.get("apply_slot") or makeup_approaches.default_slot(pids))
    return letter, slot, pids


def prompt_beauty(row, letter=None):
    v = BATCH[str(row)]; d = rdir(row)
    letter, slot, pids = makeup_choice(row, letter)
    mk = makeup_approaches.block(pids, slot, letter, endslate_s())
    sd = product_spec.for_row(d, v["products"])   # 21-Nov: product spec per slot, pasted into that product's prompts
    mk += ("\nPRODUCT SPECS (paste slot N's block VERBATIM into every image and clip prompt of slot N):\n"
           + "\n".join(open(os.path.join(sd, f"slot_{i}.txt")).read().rstrip() for i in range(1, 6)) + "\n")
    import bgm_rotation
    bgm = bgm_rotation.get(row)   # 16-Nov: 22-track round robin across all reels
    json.dump(dict(row=int(row), family="makeup", letter=letter, apply_slot=slot,
                   applied_type=makeup_approaches.ptype(pids[slot - 1])["name"]), open(os.path.join(d, "approach.json"), "w"), indent=1)
    film = json.load(open(os.path.join(DATA, "film_titles.json"))).get(str(int(row)))
    if not film:
        raise SystemExit(f"row {row}: no sheet title in film_titles.json - add the col I text first")
    b = json.load(open(os.path.join(d, "brief.json"))); stem = b["out_name"][:-4]
    prods = "\n".join(f"  {i}. {u}" for i, u in enumerate(v["products"], 1))
    bau = (f"\nBAU (not Diwali): {BAU_NO_DECOR}\n  Put at the end of every image and clip prompt: \"{BAU_NEGATIVE}\"\n"
           f"  {BAU_HOME_REAL}\n" if BAU else "")
    return f"""You are a worker making ONE Flipkart {'BAU ' if BAU else ''}MAKEUP reel with the BEAUTY pipeline: sheet tab "{TAB}" row {row}
({v['name']}, {v['folder']}). One run = this row = one reel: 4 s per product (20 s) + the end slate, music only.

READ FIRST, fully: {BEAUTY}/README.md (steps 0-9), {BEAUTY}/SKILL.md, {BEAUTY}/CATEGORY_RULES.md (Makeup row), {BEAUTY}/PROMPT_LOCKS.md,
{BEAUTY}/PIPELINE_CONCEPT_LAB.md, {BEAUTY}/REALISM_RULES.md, and copy the shape of {BEAUTY}/example_run_ID_4/.
Run every Beauty script from {BEAUTY} with the run folder as its argument.
NO QC STAGES (user 17-Nov): skip the frame gate, check_actions.py, validate_concepts.py and product_text.py check; one take per
image and per clip; never re-generate for review. Still write the action JSONs + clip_frames.json (generate_clips needs them).

RUN FOLDER: {d}  (already laid out: 04_actions/, assets/..., exports/, final/, 01_product_manifest.md, 08_run_log.md;
products/ holds the fetched listing photos - use them as product_refs).
PERSONA: {v['name']} - photo {OMNI}/personas/{v['name'].lower()}.jpg, avatar link {v['persona_link']}
PRODUCTS (all 5 must appear, exactly once each):
{prods}
HEADER (on-screen title for the whole film) = the sheet's "Text for the Film", EXACTLY as written, not translated or edited:
  {json.dumps(film, ensure_ascii=False)}
  (this replaces the template's "My top 5 beauty picks" lines in base_png; split it over 2 lines only at a natural break).
CTA: "Shop Now on Flipkart" in the last 2 s only (template default).
{bau}
{mk}
In the concept card set application_count 1 and apply_product = slot {slot}; this approach overrides the card's own choice.
SAME PRODUCT IN EVERY SHOT (user 17-Nov): each product's FIRST keyframe is made from its listing photo (+ product_text.json
PRODUCT TEXT block). Every other keyframe of that product (its detail clip, the applied/worn result, the opened or swatched
state) is an EDIT of that first keyframe - first keyframe as image 1, listing photo after it - with "the same <product>,
unchanged: same pack shape, colour, shade, label text and applicator" in the prompt. Every clip prompt adds "the product
stays exactly as in the starting frame; it never changes, morphs or swaps".
MUSIC (round robin, do not pick another): MUSIC = "{bgm}" in assemble.py; concept card bgm_pack "rhythm_bgm_approved",
bgm "{os.path.basename(bgm)}". Start at 0 s, fade out over the last 2 s.
ENGINE: Omni connector, folder "Flipkart_Fashion-Rhythm_AI_Profiles" on every call. Images: generate_nano_banana_image 1K 9:16. Clips:
generate_clips.py - model "gemini-omni-1.2-flash" (Omni 1.2, same as every other vertical), 360p, first frame only. Run generate_clips.py "{d}" --confirmed directly (no --dry / review round).
Record every generation id in 08_run_log.md as soon as you submit it. Never delete files: move unwanted ones into work/junk.

ASSEMBLY: copy {BEAUTY}/assemble_template.py to "{d}/assemble.py", edit CLIPS / CHIPS / header / music, and set
  OUT = os.path.join(ROOT, "final", "{stem}")
Then run: {'FK_MODE=BAU ' if BAU else ''}/usr/bin/python3 {os.path.realpath(__file__)} finish {row}
(it runs your assemble.py, renames final/{stem}_master.mp4 to final/{b['out_name']}, makes the 480p and files it in 01_LATEST_FINAL).
Report: final path, duration, shot list.
No Drive upload, no sheet edits."""


def finish_beauty(row, d, b):
    """Run the worker's per-run assemble.py; leave final/<out_name> as the master for the common finish steps."""
    asm = os.path.join(d, "assemble.py")
    if not os.path.exists(asm):
        raise SystemExit(f"row {row}: no {asm} - copy {BEAUTY}/assemble_template.py and edit it first")
    # 23-Nov: the product names on screen (CHIPS) must be this row's products (product_text.json), never the template's
    # example names left in by mistake
    src = open(asm).read(); ptp = os.path.join(d, "product_text.json")
    m = re.search(r"CHIPS\s*=\s*\[(.*?)\]\s*\n", src, re.S)
    chips = re.findall(r'\(\s*"([^"]+)"\s*,', m.group(1)) if m else []
    if not os.path.exists(ptp):
        raise SystemExit(f"row {row}: product_text.json missing - the on-screen product names cannot be checked")
    pt = json.load(open(ptp, encoding="utf-8"))
    words = {w for v in pt.values() for w in re.findall(r"[a-z0-9]{3,}", (str(v.get("brand", "")) + " " + str(v.get("name", ""))
                                                                         + " " + str(v.get("variant", ""))).lower())}
    TEMPLATE_NAMES = {"sultry eyeshadow palette", "minara palette duo", "huda beauty duo", "teen teen palette", "hd pro palette"}
    wrong = [c for c in chips if c.lower() in TEMPLATE_NAMES or not (set(re.findall(r"[a-z0-9]{3,}", c.lower())) & words)]
    if wrong:
        raise SystemExit(f"row {row}: on-screen product name(s) {wrong} do not match this row's products in product_text.json - "
                         f"fix CHIPS in {asm}")
    subprocess.run(["nice", "-n", "19", sys.executable, asm], check=True, cwd=d, env=dict(os.environ, FK_PIPE=PIPE))
    master = os.path.join(d, "final", b["out_name"])
    produced = master[:-4] + "_master.mp4"
    if os.path.exists(produced):
        os.replace(produced, master)
    junk = master[:-4] + "_480p.mp4"          # the template's own 480p - finish rebuilds it at 480x854
    if not os.path.exists(master):
        raise SystemExit(f"row {row}: assemble.py did not write {produced} - set OUT = os.path.join(ROOT, 'final', '{b['out_name'][:-4]}')")
    return junk


def new(row):
    v = BATCH[str(row)]; src = os.path.join(DATA, "rows", f"row_{int(row):03d}"); d = rdir(row)
    for sub in ("plates", "clips", "qc", "final", "work"):
        os.makedirs(os.path.join(d, sub), exist_ok=True)
    b = json.load(open(os.path.join(src, "brief.json")))
    b["name"] = v["name"]
    b.setdefault("persona", {})["name"] = v["name"]
    b["persona"]["image"] = os.path.join(OMNI, "personas", f"{v['name'].lower()}.jpg")
    b["out_name"] = f"{PREFIX}_row{int(row):03d}_{v['name']}_{cat_code(v)}.mp4"
    json.dump(b, open(os.path.join(d, "brief.json"), "w"), indent=1)
    # 23-Nov: refresh the listing photos when the sheet's products changed (they were copied only once, so a corrected
    # sheet kept the OLD product's photos and the wrong product was generated). The old folder is kept, never deleted.
    _sj, _dj = os.path.join(src, "products.json"), os.path.join(d, "products.json")
    _changed = os.path.exists(_sj) and os.path.exists(_dj) and open(_sj).read() != open(_dj).read()
    if _changed and os.path.isdir(os.path.join(d, "products")):
        shutil.move(os.path.join(d, "products"), os.path.join(d, "products_old_" + time.strftime("%Y%m%d-%H%M%S")))
    if os.path.isdir(os.path.join(src, "products")) and not os.path.isdir(os.path.join(d, "products")):
        shutil.copytree(os.path.join(src, "products"), os.path.join(d, "products"))
    if os.path.exists(os.path.join(src, "products.json")):
        shutil.copy(os.path.join(src, "products.json"), d)
    if is_beauty(row):
        new_beauty(row, d)
    elif BAU:   # 17-Nov user: product specs for every product on display (not the Beauty pipeline)
        product_spec.for_row(d, v["products"])
    if is_beauty(row) and BAU:   # 21-Nov: Makeup gets the product spec sheets too
        product_spec.for_row(d, v["products"])
    if not os.path.exists(os.path.join(d, "log.md")):
        open(os.path.join(d, "log.md"), "w").write(f"# Row {row} {v['name']} - {v['folder']} - FINAL pipeline\n")
    print("ready:", d, "| products:", len(os.listdir(os.path.join(d, "products"))) if os.path.isdir(os.path.join(d, "products")) else "MISSING (run products.py)")


# SHOOTING STYLES (user 3-Nov ~14:45): "pipeline me sirf shooting style badalna hai, baaki sab same. Saari videos music-only hai
# (koi bolta nahi), isliye har category ke 2 styles fix kar diye, row by row alternate karna taaki variety dikhe".
# One style per VIDEO; even row -> first style, odd row -> second style.
STYLE_TXT = {
 "A": "A = MIRROR SELFIE: she films herself in a full-length mirror, the phone held in front of her FACE (face hidden by the phone), "
      "the outfit WORN and fully visible in the mirror; slow poses, a gentle half-turn, one hand adjusting the outfit. The phone in "
      "the mirror is plain (no logo, no screen glow), held by one hand; the other hand is free. Exactly one person; the mirror shows "
      "only her and the room. (Overrides the old 'no mirror selfie' rule ONLY in this style - user 3-Nov product-in-frame rule.)",
 "B": "B = HEADLESS FIT CHECK: framing from the neck/chin down (no face), the product WORN and filling the frame; slow half-turns, "
      "smoothing the fabric, hands showing details. Footwear B: knee-down framing only (feet + shoes big, walking a step or two in "
      "place, toe/heel turns). Fashion wearables B: tight wrist / neck close-ups of the worn piece.",
 "C": "C = HANDS-ONLY PRODUCT DEMO: no face, no body above the forearms; two hands show and USE the product on a table/bed/counter "
      "in the same room (turn it, open it, demonstrate the key feature), the product big and sharp. Exactly two hands from the bottom "
      "edge (ARM TRACE).",
 "D": "D = RETIRED 3-Nov (user: no unboxing) - never use. Old text: COURIER POUCH UNBOXING: every product starts in a plain grey courier pouch / plain box (no printed logo) that two hands "
      "open, then the product is shown big (and for apparel/footwear, then worn: footwear knee-down, clothing headless or on the "
      "kid). Hands-only for the opening (ARM TRACE).",
 "E": "E = ROOM BEFORE/AFTER: the same room corner first plain/bare (before), then the same framing with the product placed/used "
      "(after) - same camera position, same light; then close-ups of the product in place. Hands may place it; no face needed.",
}
# 3-Nov ~16:00 user: "ab unboxing wala nahi dikhana" -> style D (courier pouch unboxing) is RETIRED; D replaced per category.
STYLES = {"Women's Ethnic Wear": "AB", "Women's Western Wear": "AB", "Women's Footwear": "BC", "Men's Footwear": "BC",
          "Kids Clothing": "BC", "Kids Footwear": "BC", "Household Kitchen": "CE", "Household Supplies": "CE", "Baby Care": "CC",
          "Toys and School Supplies": "CC", "Fragrance": "CC", "Fashion Wearables": "BC", "Home Decor": "EC",
          "Home Furnishing": "EC", "Makeup": "CC", "Men's Grooming": "CC", "Men's Ethnic Wear": "AB",
          "Women's Fashion Wearables": "BC", "Men's Fashion Wearables": "BC"}


def style_block(v, row):
    pair = STYLES.get(v["folder"])
    if not pair:
        return ""
    st = pair[int(row) % 2 == 1]
    return (f"SHOOTING STYLE (user 3-Nov - ONLY the shooting style changes, everything else in this pipeline stays the same; "
            f"music-only, nobody speaks): this video = style {st}. Category pair {pair[0]}/{pair[1]}, alternating row by row "
            f"(even row = {pair[0]}, odd row = {pair[1]}).\n{STYLE_TXT[st]}\nApply the style to EVERY shot of this video; keep the "
            f"products, all hard rules, title, music, logo, end slate. The product is always clearly in frame.\n")

def prompt(row):
    v = BATCH[str(row)]; key, ex, decor = CATS[v["vertical"]]
    board = BOARDS[int(row) % len(BOARDS)]
    title_head = TITLE_HEAD[key]
    ft = os.path.join(DATA, "film_titles.json")
    film = json.load(open(ft)).get(str(int(row))) if os.path.exists(ft) else None
    mp = os.path.join(DATA, "music_plan.json")
    music = json.load(open(mp)).get(str(row)) if os.path.exists(mp) else None
    music = music or v["music"]
    room = (f"ROOM for this category: {ROOMS[key]} (same v2 class as the style reference, nothing copied from it). "
            if key in ROOMS else "")
    persona = "Zoya (user's choice)" if int(row) == 65 else v["name"]
    return f"""You are a worker making ONE Diwali reel in the FINAL approved pipeline: row {row} ({persona}, {v['folder']}).
ENGINE (user 3-Nov, overrides any Kling/Higgsfield/720p text below): plates TrueFan Nano Banana 2 in BULK, clips TrueFan Omni 1.2 360p with the NEW PROMPT - follow {WORK}/NEWPROMPT_360.md and {WORK}/OMNI720_BRIEF.md (tools, folder, rate limits, bulk).

READ FIRST, fully: {SKILL}/SKILL.md, then {SKILL}/briefs/BRIEF.md, BRIEF2.md, BRIEF3.md, and {SKILL}/examples/{ex}/log.md + plan.json
(the approved example closest to this category). Realism constants: bottom of {OMNI}/scripts/realism.py
(feedback #3 + REF_GESTURES + CLIP_TRYON_BODY), pasted VERBATIM. Look at frames of the matching video in {LATEST}/ first.

Work folder: {rdir(row)} (brief.json + products/ ready). Run every skill script with BBD_OUT="{WORK}". Never touch other rows.
Persona photo: {OMNI}/personas/{('zoya' if int(row) == 65 else v['name'].lower())}.jpg (download from the
batch_100 persona_link if missing). Home (CLIENT-FINAL 30-Oct: row 195 v2 class, a DIFFERENT room per video): realism.HOME_BG + realism.HOME_V2 +
realism.HOME_V2_ROOMS[{(int(row) % 8) if (int(row) % 8 or int(row) == 64) else 1 + int(row) % 7}], and pass realism.HOME_V2_REF ({OMNI}/assets/refs/home_v2_style_FINAL_30oct.png)
as a STYLE reference for class/light/phone look ONLY - never copy its exact room. Same room in every shot of THIS video.
{room}
Decor: {'ON - realism.FESTIVE_EXTRAS (no lit diyas/flames)' if decor else 'OFF - realism.NO_DECOR'}.

{style_block(v, row)}SHOT TEMPLATE (base grammar; the SHOOTING STYLE above wins where they differ):
{TEMPLATES[key]}
{variety(key, row)}

PLATES (USER 2-Nov): TrueFan Nano Banana 2 = mcp__<omni-connector>__generate_nano_banana_image (load via ToolSearch), 9:16,
ALWAYS folder="Flipkart_Fashion-Rhythm_AI_Profiles" (user-confirmed; NEVER 'test-test_diwali'). User 3-Nov: EVERY TrueFan image AND video must sit in that folder - files you upload_media get no folder by themselves, so right after uploading call TrueFan move_to_folder(ids=[...], folder="Flipkart_Fashion-Rhythm_AI_Profiles"). Upload persona + listing photos with TrueFan upload_media; persona + listing photos; "no tripod or phone visible".
Only if TrueFan fails twice for a plate (error / rate limit), fall back to Higgsfield nano_banana_2_1 on account 1 and log it.
CLIPS: Higgsfield ACCOUNT 1 = tools mcp__higgsfield__* (load via ToolSearch; user 3-Nov: account 2 is empty, use account 1 (~649 cr) for the rest of batch 5; fallback plates also on account 1); a TrueFan plate goes to Kling by its URL (media_import_url); media ids do not cross accounts, so an asset logged from account 2 must be re-imported by its URL (or local file via media_upload). CREDIT GUARD: call mcp__higgsfield__balance before every clip submit; if it is below 60 credits, submit nothing more, log 'STOPPED: account 1 credits low' in log.md and end.
SPEED (2-Nov, same quality): make plate s1 first, then send the remaining plates in parallel calls (each with s1 as the same-home /
same-face reference). Clips: kling3_0_turbo 720p 9:16 sound off count 1, DURATION BY BEAT (2-Nov cost rule - Kling bills per second and 30% of
5 s footage was never used): SHOWN / hanger / packet-open / box-open / pick-up / close-up beats = 3 s (we use <= 2.8 s);
worn / used beat that gets a zoom punch-in = 4 s (we use <= 3.8 s); 5 s for a long finale, a full turn/walk, and any CARRY-IN / walk-in / place-down beat (pilot 467: a 4 s carry-in ended before she let go).
Same prompts. The FINALE is ALWAYS 5 s (pilot 790).
use_unlim false, decline presets, prompts < 2500 chars. SPEED: submit EVERY clip as soon as its plate arrives (no in-flight
cap; if the API refuses for concurrency, queue and resubmit as slots free), then wait with jobs_wait. Budget ~60 credits per
video, no unforced retakes - trim instead.
If the account runs out (insufficient credits), STOP cleanly: log the resume point in log.md (done plates/clips + pending ids) and report.

NO QC STAGES (user 17-Nov): no visual_qc.py, no checking sheets, no ARM TRACE / teeth crops, no retake rounds - one take each.
  Write INTO every plate and clip prompt: "the product stays clearly visible in frame the whole time", exactly two arms from the
  bottom edge (hands-only shots), lips closed, and {PHYSICS_BODY}
plan.json: zoom punch-ins per the template; ONE super {json.dumps(dict(board=board, head=film, sub="", start=0, end="<footage end>", x=0.42, y=0.05, max_w=0.66), ensure_ascii=False) if film else '{{"board":%d,"head":"%s","sub":"%s · Diwali Sale Live","start":0,"end":<footage end>,"x":0.42,"y":0.05,"max_w":0.66}}' % (board, title_head, v['folder'])}
  FRAMING (30-Oct): in every full-body plate keep the top of the head BELOW ~22% of the frame height (some floor/room above), so the 2-line title (top ~15%) never covers the face - never crop the face away instead.
  2-Nov (prevents the head-too-high redo): write it INTO every full-body plate prompt: "camera a little farther back, plain wall /
  room visible above her head, top of the head about 25-30% down from the top edge, feet fully in frame".
  ZOOM (2-Nov): assemble.py takes "zoom_x" (0 left, 0.5 centre, 1 right) next to "zoom_y" - aim punch-ins at off-centre
  products with zoom_x instead of making your own ffmpeg crops.
  TITLE = the sheet's "Text for the Film" for this row, EXACTLY as written (user 30-Oct: "jis row main jo likha hai wohi same ayega") - prices/% in it are allowed; do not edit or translate it. y 0.05 keeps it above the head.
music "{music}" from 0 s (music plan - do not change); camera steady; logo + endslate true. No price/% anywhere ELSE (plates, products) - the title above is the only text.
Then: /usr/bin/python3 {SKILL}/scripts/pipeline.py finish {row}  (assemble_fk + 480p + copy to 01_LATEST_FINAL/<Category>; no review step)

Log everything in {rdir(row)}/log.md. No Drive upload, no sheet edits. Final report (short): 480p path, duration, shot list,
credits."""


# =====================================================================================================================
# 13-Nov BAU job (tab 1500_1, Women's Ethnic + Men Ethnic). User's 3 changes for every NEW Ethnic video (decor part also for
# Home Decor); everything else unchanged (avatars, shots, title, music, phone look, 480p):
#  1) NO Diwali decor at all, 2) clothes look real, not catalogue-perfect, 3) upper-middle-class Indian home in every video.
# =====================================================================================================================
BAU_NO_DECOR = ("NO festive decoration of any kind: no diya, no rangoli, no marigold, no fairy lights, no lanterns, no torans, "
                "no festive lights, no puja items - an ordinary, plain, neat real home on a normal day.")
BAU_NEGATIVE = "AVOID: diya, rangoli, marigold, fairy lights, festive decoration, Diwali, lanterns, toran, string lights."
BAU_CLOTHES = ("The clothes look REAL, like a real garment just worn at home: small natural creases and soft folds where the "
               "body bends (waist, elbows, knees), real fabric weight and drape. Colour, print, embroidery, cut and fit stay "
               "EXACTLY as in the listing photos. Not crumpled, not torn, not dirty, not ill-fitting, no melting or warping "
               "fabric - and not stiff, plastic, catalogue-perfect or digitally smoothed either.")
BAU_HOME = ("The home is a spacious, clean, well-furnished UPPER-MIDDLE-CLASS Indian city flat (a comfortable salaried family's "
            "3 BHK): a good fabric sofa with cushions, a wooden wardrobe with a full-length mirror, proper curtains on the "
            "windows, one or two healthy indoor plants, light vitrified tiles or a wooden floor, soft warm natural daylight "
            "from a window. Real and lived-in but tidy (a cushion slightly tilted, a water bottle or a mug on a side table). "
            "NOT a hotel, NOT a showroom, NOT a mansion or villa: no chandelier, no marble palace look, no luxury staircase, "
            "no designer gallery wall. Every video of this batch is in the SAME CLASS of house; only the room/corner changes.")
BAU_ROOMS = [
    "living room: warm off-white wall, a beige three-seater fabric sofa with two printed cushions, a wooden centre table with a "
    "mug, cream curtains on a big window, a money plant on a wooden stand",
    "bedroom: light-grey wall, a wooden double bed with a plain cotton bedspread, a wooden wardrobe with a full-length mirror "
    "door, sheer white curtains, a potted plant by the window",
    "living room: pale-beige wall, a grey fabric sofa with a folded throw, a teak TV unit with a TV and a small plant, light-brown "
    "curtains, a cotton rug on light tiles",
    "bedroom corner: cream wall, a tall wooden wardrobe with a mirror, an upholstered bench, a side table with a lamp and a water "
    "bottle, soft daylight from a side window with linen curtains",
    "living-dining: warm white wall, a brown fabric sofa with cushions, a six-seater wooden dining table in the back with a fruit "
    "bowl, light curtains, a tall indoor plant in a ceramic pot",
    "living room by the balcony door: soft sage-green accent wall, a cream sofa, a glass balcony door with sheer curtains "
    "(daylight), a wooden side table with a mug, two potted plants",
]
BAU_TEMPLATES = {
    "apparel": """WOMEN'S ETHNIC (approved apparel grammar, BAU): every distinct outfit WORN by her, >= 2 shots per outfit (main worn
  shot + a separate close-up CLIP of the worn detail - print / embroidery / border / dupatta edge, her hand showing it). At most
  ONE hanger before-shot in the whole video (hand at the hook, ~2 s) -> cut to the same outfit worn; no packet/pouch/box opening.
  Slow gestures, each different: smooth the kurta front, lift the dupatta edge a little, gentle half-turn and back, hand lightly
  at the side of the waist, adjust the cuff. NO twirls/spins.""",
    "apparel_men": """MEN'S ETHNIC (new category, apparel grammar): the man WEARS every distinct outfit (kurta set / kurta-pyjama /
  Nehru-jacket set / sherwani as listed), >= 2 shots per outfit (main worn shot + a separate close-up CLIP of the worn detail -
  collar, placket buttons, embroidery, fabric weave, jacket pocket - his hand showing it). At most ONE hanger before-shot (~2 s)
  -> cut to it worn; no packet/pouch/box opening. Slow masculine gestures, each different: adjust the collar, straighten the
  kurta hem, fasten / touch a jacket button, roll or adjust a cuff, gentle half-turn and back, one hand relaxed in the pocket
  (if the outfit has one). Natural confident posture, not a stiff model pose. NO spins.""",
    # 14-Nov Day 2: Fashion Wearables (one product type per row: sunglasses / frames, watches, belts, bags, necklaces,
    # jewellery sets, earrings, anklets). Built from the delivered Diwali wearables grammar (rows 374-436, styles B/C).
    "wearable": """FASHION WEARABLES (BAU): every distinct listing gets >= 2 shots - a main shot + a separate DETAIL close-up CLIP of the
  same product (dial, buckle, lens/temple, clasp, stones, zip/logo) - about 10 clips. The product is the hero: BIG, sharp and
  centred in every frame (small items must fill a good part of the frame - 360p turns a tiny product into mush). Never an
  unboxing, packet or box opening. Product = listing EXACTLY (shape, colour, metal tone, stone colours, dial, strap, lens tint,
  logo placement). Identical / near-duplicate listings are shown once (log it). ONE plain outfit for the whole video, solid
  colours that suit the product (no busy print), and NO other jewellery, watch, belt, bag or glasses than the product in that shot.
  PER PRODUCT TYPE - style B (worn) framing / style C (hands-only) action:
  - SUNGLASSES / FRAMES: ALWAYS the EYEWEAR MIRROR SELFIE (user 14-Nov - see the SHOOTING STYLE block, it replaces B and C):
    the avatar WEARS the glasses and films the mirror with a phone in one hand. Never a hands-only eyewear shot.
  - WATCHES: B = worn on the wrist, forearm + wrist big (chest-down / waist-up framing, no face needed); gestures: turn the wrist
    to the camera, glance at the dial, adjust the strap. C = two hands hold the watch, turn the dial to the camera, fasten the strap.
  - BELTS: B = worn through the loops of plain trousers/jeans, framing from the chest to the thighs; gestures: adjust the buckle,
    tuck the shirt, hand resting on the belt at the side. C = hands thread the strap through the buckle, show the buckle and
    the leather grain.
  - BAGS: B = carried (shoulder bag / crossbody / handbag in hand / backpack on the back), framing from the chin down; gestures:
    adjust the strap, half-turn to show the side/back, open the zip a little to show the inside. C = hands on a table/bed: open
    the zip, show the compartments, the handle and the logo.
  - NECKLACES / PENDANTS / CHAINS / JEWELLERY SETS: B = worn on the neck, framing neck + collarbone (chin at the top edge, lips
    closed if visible), plain round- or V-neck top in a solid colour; gestures: fingers touch the pendant, smooth the chain,
    slight turn so it catches the light; a SET also shows its earrings (hair tucked behind the ear, three-quarter framing).
    C = two hands lift it by the chain so the pendant hangs, lay it on the palm / a plain tray.
  - EARRINGS: B = three-quarter head-and-neck close-up, hair tucked behind the ear, the earring BIG; gestures: slow head turn,
    tuck the hair, touch the earring. Lips closed. C = fingers hold the pair up, one on the palm.
  - ANKLETS: B = ankle close-up, bare groomed pedicured feet on a rug/floor (realism.FOOTWEAR_BEAUTY), plain cropped trousers or
    a long skirt lifted a little; gesture: a small step, turn the ankle. C = hands hold the anklet, lay it on the palm.
  Slow gestures, each different; NO spins, no twirls.""",
}
# 16-Nov Day 2: Women Footwear (sandals SND / flats-slippers SFF / shoes SHO). Built from the approved footwear grammar
# (row 65/66 look, every pair big, shown in hands -> worn, FOOTWEAR_BEAUTY) + no zoom + BAU home/physics.
BAU_TEMPLATES["footwear_bau"] = """WOMEN'S FOOTWEAR (BAU, approved footwear grammar - row 66 look): EVERY distinct pair gets >= 2 shots, the PAIR BIG
  (it fills a good part of the frame - a medium shot with tiny footwear does NOT count; 360p turns small shoes into mush):
  - SHOWN: two hands (hers, from the bottom edge, ARM TRACE) turn ONE shoe/sandal of the pair at chest height in front of the
    room - upper, side, sole, strap/buckle - short product-only prompt, no body words. NEVER a packet, pouch or shoe-box opening.
  - WORN: knee-down framing, "phone held very low, about 40 cm from her feet": she wears the PAIR (both feet, the same pair on
    both) on the floor (polished vitrified tiles / a cotton rug), a slow step or two in place, heel turn, toe point, ankle turn.
  Style B rows: per pair SHOWN (2-3 s) -> WORN knee-down (4-5 s), the worn shot is the main one.
  Style C rows: per pair a HANDS-ONLY demo (turn it, press the cushioned footbed, flex the sole, open/close the strap or buckle)
  -> then a WORN close-up where she sits on the bed edge / a chair and her hands slip the pair on or fasten the strap (hands +
  feet in frame, knee-down, no face). Hands-only + feet only in C.
  Product = listing EXACTLY (colour, strap layout, buckle, heel height/type, sole colour, toe shape - an open-toe sandal never
  becomes a closed shoe, a flat never grows a heel). Identical / near-duplicate listings shown once (log it). One pair at a time;
  other pairs never visible. Beautiful pedicured feet (realism.FOOTWEAR_BEAUTY): smooth skin, neat nude/soft polish, no cracked
  heels; exactly 2 feet, 5 toes each where visible. Slow, natural movement; NO spins, no running, no jumping."""
BAU_FW_WOMEN_NOTE = """PRODUCT NOTE (women's footwear): read every listing first - name each pair (sandal / flat / slipper / sneaker /
heel / juttis) in log.md. Plates: paste realism.FOOTWEAR_BEAUTY VERBATIM into every plate that shows her (feet or body); clip
prompts add "well-groomed, beautiful pedicured feet". Outfit: the OUTFIT line below, ankles visible, the same in every shot - the
hem never covers the footwear. Feet stay on the floor (physics: real weight, the sole flat on the floor, no floating or sliding
feet, no feet melting into the rug); the shoe keeps its shape and size between shots. Hands never rest on the stomach."""

BAU_TEMPLATES["wearable_men"] = BAU_TEMPLATES["wearable"]   # same grammar, the man wears/carries the product (see BAU_WEAR_MEN_NOTE)

# 14-Nov user (after the wearables samples): "chashme wala pipeline sahi kar do - background bahut zyada acha dikh raha hai,
# upper middle class home dikhna chahiye, abhi hotel dikh raha hai; chashma laga ke avatar mirror mein dekhta hai aur haath
# mein phone hai jisse vo record kar raha hai". Changes live here (code / prompt template), no separate MD file.
BAU_HOME_REAL = ("NOT A HOTEL (user 14-Nov: the sample rooms looked like a hotel - too perfect): the room must read as a real "
                 "family's OWN flat, not a hotel / Airbnb / showroom / catalogue set. AVOID: white hotel bedding with a bed runner, "
                 "matching twin bedside lamps, a padded headboard wall, perfectly empty surfaces, staged symmetry, glossy magazine "
                 "or studio light. ADD everyday family life: a printed Indian cotton bedsheet or a sofa throw, a framed family photo "
                 "or a wall clock, a few books / a phone charger / a steel water bottle / a small jewellery or cosmetics tray on the "
                 "dresser, a shirt or dupatta hung on a hook or a chair back, a slightly used, lived-in look. Ordinary window "
                 "daylight. Still clean and clearly UPPER-MIDDLE-CLASS - just a real, lived-in home.")
BAU_EYEWEAR_ROOMS = [
    "bedroom: light-grey wall, a tall wooden wardrobe with a full-length mirror door, a wooden double bed with a printed cotton "
    "bedsheet, a shirt hung on the wardrobe handle, a wall clock, sheer curtains on a window",
    "bedroom dressing corner: cream wall, a wooden dressing table with a big mirror (a comb, a deodorant, a watch tray on it), a "
    "stool, a framed family photo on the wall, a window with cotton curtains",
    "passage by the bedroom: warm off-white wall, a full-length wall mirror in a wooden frame, a shoe rack below with two pairs of "
    "shoes, a small plant, a key bowl on a ledge, the open bedroom door behind",
]


# 16-Nov user (row 277 s10: head too small for a wide, long torso): "never break basic physics laws and face and body
# ratio is not matching in the last clip, it must not happen in any video". PERMANENT for every row, every category.
PHYSICS_BODY = ("REAL PHYSICS + TRUE BODY PROPORTIONS: a normal adult body - head size natural for the shoulders and torso (the "
                "shoulders about 2 to 2.5 head-widths wide, the torso about 3 head-heights long), arms and hands normal length, "
                "the same body size and build in every shot as in the persona photo. No enlarged or shrunken head, no stretched "
                "or widened torso, no long arms. Real physics: gravity on cloth, hair and objects; nothing floats, melts, bends "
                "or passes through anything; hands really grip what they hold; a mirror shows a true reflection (same pose, "
                "phone back to the mirror, the camera viewpoint at the phone); objects keep their size and shape; feet on the floor.")
PHYSICS_QC = ("PHYSICS + PROPORTION QC (user 16-Nov, row 277 s10 shipped a head too small for the body - never again in ANY "
              "video): for every plate and every used clip range compare the head to the body - shoulders ~2-2.5 head-widths, "
              "torso ~3 head-heights, arms/hands normal, and the SAME size/build as the persona and the other shots of this "
              "video (put the frame next to plate s1 to check). Also check physics: nothing floating, merging, bending, "
              "passing through, a mirror reflection that matches the pose and the phone. Any doubt = remake the PLATE (a "
              "wrong-proportion plate always gives a wrong clip), not just a trim. Log \"PROPORTION+PHYSICS: PASS sN\".")


def is_eyewear(row):
    """Sunglasses / frames rows (pid prefixes SGL / FRA)."""
    return any(re.search(r"pid=(SGL|FRA)", u) for u in BATCH[str(row)]["products"])


def eyewear_style(who):
    he, his = ("he", "his") if who == "him" else ("she", "her")
    return (f"SHOOTING STYLE = EYEWEAR MIRROR SELFIE (user 14-Nov, replaces styles B and C for every sunglasses / frames video; "
            f"music-only, nobody speaks): {he} stands in front of the home's mirror WEARING the sunglasses and records {who}self with "
            f"a phone held in ONE hand at chest height - the phone is in {his} hand and visible in the mirror, back of the phone to "
            f"the mirror, plain, no logo, no screen glow. The phone NEVER covers the face or the glasses. Framing = the mirror "
            f"reflection, waist-up for the main shot and head-and-shoulders for the detail shot, the glasses BIG and sharp on the "
            f"face; lips closed, natural expression. The free hand pushes the glasses up the nose, touches the frame / temple, or "
            f"hangs relaxed at the side. Gestures (one per clip, all different): slow head turn to the side and back to show the "
            f"frame side-on, lower the glasses a little to look over them and push them back, slight chin tilt, adjust the temple "
            f"behind the ear. Every pair = main mirror shot + detail mirror shot (closer: lens tint, bridge, temple logo). One pair "
            f"at a time on the face; the other pairs are never visible. Same mirror, room, outfit and phone in every shot. Exactly one "
            f"person; the mirror shows only {who} and the room; exactly 2 hands (one holds the phone). NO hands-only shots, NO pair "
            f"held up or lying alone.\n")


def realism_beauty():
    import sys as _s
    _s.path.insert(0, os.path.join(OMNI, "scripts"))
    import realism
    return realism.FOOTWEAR_BEAUTY


def endslate_s():
    p = os.path.join(OMNI, "assets", "brand", "flipkart_endslate.mp4")
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout.strip())


def footwear_actions(spec, slot):
    """ALLOWED ACTIONS for one footwear product, read from its listing (Closure / Type / title). A worker may only show an
    action the product physically has: no lace tying without laces, no strap adjusting on a flip-flop/slide/clog."""
    sp = spec.get("specifications", {})
    keys = [k for k in sp if k.lower() in ("closure", "type", "type for flats", "type for sandals", "type for slippers")]
    txt = " ".join([spec.get("title", "")] + [sp[k] for k in keys]).lower()
    has = lambda *w: any(x in txt for x in w)
    if has("lace-up", "lace up", "laces", "lacing"):
        act = "LACES: may tie or tighten the laces (shown untied first, then tied)."
    elif has("velcro", "hook and loop", "hook & loop"):
        act = "VELCRO: may open and press the velcro strap closed (shown open first)."
    elif has("buckle", "ankle loop", "ankle strap"):
        act = "BUCKLE/STRAP: may fasten the buckle or strap (shown open first)."
    elif has("zip"):
        act = "ZIP: may pull the zip up."
    elif has("flip flop", "flip-flop", "slipper", "slide", "clog", "slip-on", "slip on", "mule", "thong"):
        act = ("SLIP-ON (no fastening): ALREADY WORN on BOTH feet from the first frame to the last; NEVER tie, buckle or adjust "
               "anything, never take it off, never put it on, never slide a foot in or out; any seated 'adjust' approach "
               "becomes: seated, both feet in the pair, one foot turns slightly to show it and back.")
    else:
        act = "FASTENING UNKNOWN: ALREADY WORN on both feet the whole clip; do not tie, buckle, adjust, remove or put it on."
    act += " In every clip the SAME pair stays on BOTH feet; no foot is ever bare, in another shoe, or changing shoes (user 20-Nov)."
    return f"ALLOWED ACTIONS (slot {slot}, from the listing; Closure = {sp.get('Closure', 'not listed')}): {act}"


def spec_block(row, planned=False):
    """All 5 PRODUCT SPEC blocks (made on demand) + how to use them as the generation reference."""
    d = rdir(row); sd = product_spec.for_row(d, BATCH[str(row)]["products"])
    blocks = "\n".join(open(os.path.join(sd, f"slot_{i}.txt")).read().rstrip() for i in range(1, 6))
    if "ootwear" in BATCH[str(row)].get("vertical", ""):   # user 20-Nov: Day 5 fake lace tying / adjusting flip-flops
        blocks += "\n" + "\n".join(footwear_actions(json.load(open(os.path.join(sd, f"slot_{i}.json"))), i) for i in range(1, 6))
    return f"""=== PRODUCT REFERENCE SHEETS + SPECS = THE REFERENCE FOR EVERY GENERATION (user 17-Nov) ===
STEP 0, before any plate - for EACH of the 5 slots, make a product reference sheet (6-angle image) exactly as in
{SKILL}/rules/PRODUCT_REFERENCE_SHEET.md:
  a) LOOK at Image 1 = {d}/products/p<N>_1.jpg (and the other p<N>_*.jpg photos) and write
     {sd}/slot_<N>/product_caption.json per {SKILL}/rules/PRODUCT_CAPTION_SCHEMA.md. List EVERY sticker, price/barcode label,
     badge, protective film, tag, wrap, overlay graphic, watermark, food/content and prop in unwanted_elements (with where it is
     and the clean surface that replaces it) - they are removed in the sheet. ONE PRODUCT PER SHEET: if the listing is a
     set / pack / combo with several pieces, pick ONE hero piece (the largest / most complete, with its lid or parts on),
     write it in selected_piece with its position in Image 1; the sheet shows only that piece in all 6 panels.
  b) Write {sd}/slot_<N>/sheet_prompt.json = {{"prompt": ..., "excluded_elements": [...]}} following that .md (never the brand,
     model or listing name in the prompt - "the <product type> in Image 1"), then run
     python3 {os.path.realpath(os.path.join(os.path.dirname(__file__), "product_spec.py"))} --check-sheet "{d}" <N>   (must print OK).
  c) Generate it: generate_nano_banana_image, aspect 3:2, Image 1 = p<N>_1.jpg uploaded as the reference, the prompt from (b),
     folder "Flipkart_Fashion-Rhythm_AI_Profiles", one take. Save it as {sd}/slot_<N>/reference_sheet.png and log its asset id.
  The 5 sheets can be generated in parallel.
  --check-sheet also writes {sd}/slot_<N>/identity_lock.txt (the exact visual details from the caption: cut, hem, pattern,
  trims, buttons, pieces).
SAME PRODUCT IN EVERY SHOT (user 17-Nov - a kurta changed between its main shot and its detail shot):
  1) MAIN plate of slot N: references = [slot N reference_sheet, slot N listing photo p<N>_1.jpg (+ persona, room plate)];
     prompt carries slot N's PRODUCT SPEC + IDENTITY LOCK verbatim.
  2) EVERY OTHER plate of slot N is NEVER a fresh generation - it is an EDIT of slot N's main plate, whatever the approach
     letter asks for: the detail close-up, the held-up / hanger / in-hand / folded view (held_to_worn, held_to_styled,
     folded_to_place), the before / empty-spot view (before_styled, before_furnished, task_before_after), the put-on / open /
     closed / lid-off / in-use state, the mirror or walk variant. image_asset_ids[0] = the main plate's image_asset_id, then the
     reference sheet, then the listing photo; prompt starts "Image 1 is the same <product> - <the change: move closer to X /
     he holds it on a hanger / the drawer is open / the spot before it is placed>; the <product> itself does not change in any
     way" + the IDENTITY LOCK. Same person, same outfit pieces, same room, same light. (For a "before" view the product is
     simply removed from the main plate; everything else stays.)
     Generate the main plate of each slot first, then queue all of that slot's other plates as edits of it.
  3) EVERY clip (Omni 1.2) of slot N starts from one of those plates and its prompt carries slot N's IDENTITY LOCK + "the
     <product> stays exactly as in the starting frame - same pattern, hem, buttons, trims and pieces; it never changes,
     morphs or swaps" (the clip may not 'improve' or restyle the garment).
  4) Clothing: the outfit worn in a main shot is the EXACT listing outfit (all its pieces, e.g. kurta + dhoti/pyjama if they
     are part of the listing; if the listing is only the top, the bottom is a plain neutral one and stays the same in that
     slot's main and detail shots).
  Never use one slot's sheet, spec or lock for another product.
{blocks}
""" if not planned else f"""=== STEP 0: PRODUCT REFERENCE SHEETS (user 17-Nov) - for EACH of the 5 slots, exactly as in
{SKILL}/rules/PRODUCT_REFERENCE_SHEET.md ===
  a) LOOK at Image 1 = {d}/products/p<N>_1.jpg (+ the other p<N>_*.jpg) and write {sd}/slot_<N>/product_caption.json per
     {SKILL}/rules/PRODUCT_CAPTION_SCHEMA.md (every sticker, label, film, tag, overlay, prop in unwanted_elements; ONE piece
     per sheet for a set, named in selected_piece).
  b) Write {sd}/slot_<N>/sheet_prompt.json (never the brand/model/listing name - "the <product type> in Image 1"), then run
     python3 {os.path.realpath(os.path.join(os.path.dirname(__file__), "product_spec.py"))} --check-sheet "{d}" <N>   (must print OK;
     it also writes slot_<N>/identity_lock.txt).
  c) generate_nano_banana_image, aspect 3:2, Image 1 = p<N>_1.jpg, the prompt from (b), one take; save
     {sd}/slot_<N>/reference_sheet.png and log its asset id. The 5 sheets can be generated in parallel.
PRODUCT SPECS (already pasted into the shot prompts):
{blocks}
"""


def prompt_bau(row, letter=None):
    v = BATCH[str(row)]; key = CATS[v["vertical"]][0]
    pids = [re.search(r"pid=([A-Za-z0-9]+)", u).group(1) for u in v.get("products", v.get("product_urls", [])) if re.search(r"pid=([A-Za-z0-9]+)", u)]
    dup = sorted({x for x in pids if pids.count(x) > 1})
    if dup:   # user 20-Nov (Day 5 'duplicate product'): never make a reel that shows the same product in two slots
        raise SystemExit(f"row {row}: the same product is in two slots ({', '.join(dup)}) - fix the sheet first")
    others = {p: sorted(int(r) for r, x in BATCH.items() if r != str(row) and any(p in y for y in x.get("products", x.get("product_urls", []))))
              for p in pids}
    others = {p: rs for p, rs in others.items() if rs}
    if others:   # user 20-Nov: a product repeated across reels must not look like a copy
        print("WARNING - products also used in other rows (make this reel's shots of them look different: other gesture, "
              "angle and room): " + "; ".join(f"{p} -> rows {rs[:8]}" for p, rs in others.items()), file=sys.stderr)
    fam = approaches.resolve(v["vertical"])
    if fam and not os.environ.get("FK_LEGACY"):   # 21-Nov: every non-Makeup row is made from its OpenAI product plans
        if not os.path.exists(os.path.join(rdir(row), "shots", "plan_skeleton.json")):
            raise SystemExit(f"row {row}: not planned yet. Run: pipeline.py plan {row}   (dry run: shows exactly what goes to OpenAI; "
                             f"then, after the user's yes, pipeline.py plan {row} --confirmed). Old prompt: FK_LEGACY=1.")
        shots_row(row, letter, quiet=True)   # re-checks every plan and rebuilds the prompts, so a prompt is never stale
        return prompt_planned(row, letter)
    board = BOARDS[int(row) % len(BOARDS)]
    ft = os.path.join(DATA, "film_titles.json")
    film = json.load(open(ft)).get(str(int(row))) if os.path.exists(ft) else None
    if not film:
        raise SystemExit(f"row {row}: no sheet title in {ft} - add the col I text first")
    room = BAU_ROOMS[int(row) % len(BAU_ROOMS)]
    eye = key.startswith("wearable") and is_eyewear(row)
    if eye:
        room = BAU_EYEWEAR_ROOMS[int(row) % len(BAU_EYEWEAR_ROOMS)]
    real = ("\n   " + BAU_HOME_REAL) if key.startswith("wearable") or key == "footwear_bau" else ""
    who = "him" if key in ("apparel_men", "wearable_men") or (fam and fam[1] == "men") else "her"
    kind = (fam[0].replace("_", " ") if fam else "fashion-wearables" if key.startswith("wearable")
            else "women's footwear" if key == "footwear_bau" else "ethnic")
    note = {"apparel_men": BAU_MEN_NOTE, "apparel": BAU_WOMEN_NOTE, "wearable": BAU_WEAR_WOMEN_NOTE,
            "wearable_men": BAU_WEAR_MEN_NOTE, "footwear_bau": BAU_FW_WOMEN_NOTE}.get(key, "")
    if fam:   # approach decides the shot grammar; product notes stay as product-identity help only
        shots = approaches.block(row, v["vertical"], v["products"], DATA, rdir(row), endslate_s(), letter)
        if note:
            note = "PRODUCT IDENTITY NOTE (where it conflicts with the APPROACH above, the APPROACH wins):\n" + note
    else:
        shots = (f"{eyewear_style(who) if eye else style_block(v, row)}SHOT TEMPLATE (the SHOOTING STYLE above wins where they differ):\n"
                 f"{BAU_TEMPLATES[key]}\nLength: final >= ~24 s (>= 22 s footage + end slate): about 8-10 clips of 3-5 s, every distinct outfit >= 2 shots, duplicates once.")
    if key == "footwear_bau":   # 31-Oct outfit rotation per row + FOOTWEAR_BEAUTY (permanent footwear rules)
        note += "\n" + variety("footwear", row) + "\nFOOTWEAR_BEAUTY (paste verbatim into every plate):" + realism_beauty()
    sup = json.dumps(dict(board=board, head=film, sub="", start=0, end="<footage end>", x=0.42, y=0.05, max_w=0.66), ensure_ascii=False)
    tf = "mcp__<omni-connector>"
    return f"""You are a worker making ONE Flipkart BAU {kind} reel for the client: sheet tab "{TAB}" row {row}
({v['name']}, {v['folder']}). It is NOT a Diwali video. Same approved pipeline as the Diwali reels EXCEPT the 3 BAU changes below.

READ FIRST: {SKILL}/SKILL.md (section 0-7 + the FINAL UPDATES / CURRENT PIPELINE sections), {SKILL}/rules/NEWPROMPT_360.md,
{SKILL}/rules/OMNI720_BRIEF.md (tools, bulk plates, folder), and {SKILL}/examples/row_006/plan.json for the plan.json format.
IGNORE every Diwali-decor instruction in those files (FESTIVE_EXTRAS, marigold, rangoli, fairy lights, "Diwali" titles) and
IGNORE the Higgsfield/Kling and 720p clip text - this job is TrueFan only, Omni 1.2 360p.

Work folder: {rdir(row)} (brief.json + products/ ready; look at EVERY listing photo first and list the distinct products in log.md).
Run every skill script with BBD_OUT="{WORK}" and FK_MODE=BAU. Never touch other rows or the Diwali folders.
Persona photo: {OMNI}/personas/{v['name'].lower()}.jpg (same face in every shot).

=== THE 3 BAU CHANGES (user 13-Nov) + PHYSICS (16-Nov) - paste these VERBATIM into EVERY plate prompt and EVERY clip prompt ===
1) {BAU_NO_DECOR}
   Put at the end of every prompt: "{BAU_NEGATIVE}"
2) {BAU_CLOTHES}
3) {BAU_HOME}{real}
4) {PHYSICS_BODY}
   ROOM for THIS video: {room}. Same room in every shot of this video (the master plate s1 is the same-home reference for all
   later plates). Do NOT pass the old HOME_V2_REF image and do NOT use realism.HOME_BG / HOME_V2 / FESTIVE_EXTRAS.
Never write "crease-free", "perfectly pressed", "flawless", "catalogue" (as a goal) or "festive" in any prompt.
Keep from realism.py only PLATE_REALISM (phone photo look, real skin) and CLIP_HANDS / CLIP_NO_TALK / CLIP_GUARD (+ FOOTWEAR_BEAUTY on footwear rows).

{shots}
{spec_block(row)}NO DIGITAL ZOOM (permanent): every plan.json segment zoom 1.0, never the same clip twice as a punch-in. The zoom-in of a
product is a camera push-in INSIDE its one 4 s clip (user 21-Nov: no cut inside a product).

ENGINE (TrueFan MCP only, tools {tf}__*, load via ToolSearch):
- folder="Flipkart_Fashion-Rhythm_AI_Profiles" on EVERY generate call (user's standing rule - the only Flipkart folder); every
  upload_media id -> move_to_folder into that folder right after uploading.
- PLATES: generate_nano_banana_image (Nano Banana 2, 9:16), persona + 2-3 listing photos as references (+ plate s1 from shot 2
  on). Master plate s1 first, then ALL other plates queued at once (wait_for_result:false) and collected
  with get_image_status - no checking stage, animate each plate as soon as it arrives. Write into each full-body plate: "camera a little farther back, wall visible above {who} head, top of
  the head about 25-30% down from the top edge" (style A: the phone covers the face in the mirror, the outfit fully visible).
- CLIPS: generate_video model "gemini-omni-1.2-flash", resolution "360p", aspect_ratio "9:16", duration 3-5 s by beat (finale
  5 s), image_asset_ids=[plate id]. Prompt = "The first image is the starting frame <FIRST_FRAME>." + the CAMERA/LIGHT/MOTION/
  FRAMING block from NEWPROMPT_360.md VERBATIM + the 3 BAU changes + "ACTION: <one slow gesture>" + "No speech, lips closed,
  no teeth. No on-screen text. Exactly two hands. Keep the product, face, outfit and room exactly as in the starting frame.
  One continuous take, no cuts. The person stays on the same spot." Submit all clips at once; poll get_generation_status.
- Rate limit / queued: ONE timed wait (5, then 10, then 15 min) and check once - never loop-poll. Blocked twice -> log
  BLOCKED + resume point and report.

NO QC STAGES (user 17-Nov - they slow everything down): do NOT run visual_qc.py, do NOT make vqc / mouth-crop / 1 fps sheets,
no visual_checklist.json, no ARM TRACE logging, no retake rounds. One take per plate and per clip. Every close-up / detail
plate is made from ITS OWN listing photos + its own main plate (never another product's plate).

plan.json: ONE super {sup}
  TITLE = the sheet's col I text EXACTLY as written (no edits). music: leave "default" (assemble_fk picks the category track);
  camera steady; logo true; endslate true.
Then: FK_MODE=BAU /usr/bin/python3 {SKILL}/scripts/pipeline.py finish {row}  (no review step after it)
Log everything in {rdir(row)}/log.md (top line "ENGINE: Omni 1.2 360p + BAU 13-Nov"). No Drive upload, no sheet edits.
Final report (short): 480p path, duration, shot list.
{note}
FACE (user 13-Nov after the samples): showing the face or not is NOT an issue - keep the row's style; no need to hide or show it.
DISK (user 13-Nov): before starting and before finish run `df -g /System/Volumes/Data`; if less than 2 GB is free, STOP, log
"PAUSED: disk" + resume point in log.md and report - never delete anything to make room.
MUSIC: never pick a track named Diwali (finish with FK_MODE=BAU does this automatically)."""


BAU_WOMEN_NOTE = """PRODUCT NOTE (women): look at the listings first.
- SAREES: she WEARS each saree properly draped (pleats in front, pallu over the left shoulder) with the listing's blouse. Gestures:
  lift the pallu edge a little to show its border/print, smooth the pleats, gentle half-turn so the pallu shows at the back, hold
  the pallu end at the waist. Close-up clips: border, pallu print, weave/zari with her fingers. Main shots show the whole drape down to the feet.
- SUITS / KURTA SETS / ETHNIC SETS: worn exactly as listed (kurta + bottom + dupatta if included). Gestures: smooth the kurta
  front, lift the dupatta edge, gentle half-turn, adjust the cuff. Close-ups: neckline/yoke work, print, dupatta border.
Hands never rest on the stomach (trim if a clip drifts there)."""
BAU_MEN_NOTE = """PRODUCT NOTE (men): this is a MAN (the persona) - read every "she/her" in the style text as "he/his". Style A mirror
selfie: he holds the phone in front of his face in the wardrobe's full-length mirror. Outfits are kurta sets / sherwanis - check
the listings for near-duplicates (same brand can be different colours; identical listings are shown once).
Hands never rest on the stomach (trim if a clip drifts there); hems never flare like a skirt (trim)."""
BAU_WEAR_WOMEN_NOTE = """PRODUCT NOTE (women's wearables): read the listings first - name the product type (sunglasses / watch / bag /
necklace / jewellery set / earrings / anklet) in log.md and follow its line in the SHOT TEMPLATE. Bags: a handbag is carried, never
worn as a backpack unless it is one. Jewellery: real metal shine, stones exactly the listing's colours, the piece sits naturally
(no floating, no melting into the skin); exactly 2 ears / 2 hands. Outfit idea: a plain solid-colour top or kurta that lets the
piece stand out (e.g. black, white, beige, navy), the same in every shot. Hands never rest on the stomach (trim if a clip drifts there)."""
BAU_WEAR_MEN_NOTE = """PRODUCT NOTE (men's wearables): this is a MAN (the persona) - read every "she/her" in the style text as "he/his".
Read the listings first - name the product type (sunglasses / frames / watch / belt / bag-backpack-messenger) in log.md and follow its
line in the SHOT TEMPLATE. Outfit: a plain shirt or polo/T-shirt + chinos/jeans in solid colours, the same in every shot (for belts:
shirt tucked in so the belt shows). Watch on the LEFT wrist unless the listing shows otherwise. Natural confident posture, no stiff
model pose. Hands never rest on the stomach (trim if a clip drifts there)."""


# ======================================================================== 21-Nov: PLANNED ROWS (OpenAI product plans)
def _approach_dict(fmt, variant):
    return dict(letter=fmt["letter"], name=fmt["name"], main=approaches._pick(fmt["main"], variant),
                detail=approaches._pick(fmt["detail"], variant))


def planned_inputs(row, letter=None):
    v = BATCH[str(row)]; d = rdir(row)
    family, variant, fmt = approaches.choose(row, v["vertical"], DATA, d, letter)
    pids = [(re.search(r"pid=([A-Za-z0-9]+)", u) or [None, None])[1] for u in v["products"]]
    if len(pids) != 5:
        block(f"row {row}: the sheet has {len(pids)} products - a reel needs exactly 5")
    dup = sorted({x for x in pids if x and pids.count(x) > 1})
    if dup:   # QC 11 'First 2 products are same' - 23-Nov: checked on every route, not only the worker prompt
        block(f"row {row}: the same product is in two slots ({', '.join(dup)}) - fix the sheet first")
    sd = product_spec.for_row(d, v["products"])
    items = []
    for i, u in enumerate(v["products"], 1):
        m = re.search(r"pid=([A-Za-z0-9]+)", u)
        if not m:
            raise SystemExit(f"row {row} slot {i}: no product id in the sheet - fix the sheet (the slot is never skipped)")
        items.append((i, m.group(1), json.load(open(os.path.join(sd, f"slot_{i}.json")))))
    return v, d, family, variant, fmt, items


def plan_row(row, confirmed=False, letter=None, replan=()):
    """pipeline.py plan <row> [--confirmed]: OpenAI plans for the 5 products (only product data is sent), then the reel plan
    and every prompt. Without --confirmed it only shows what would be sent (user rule: no paid call without approval)."""
    if is_beauty(row):
        raise SystemExit(f"row {row} is Makeup: it keeps the Beauty pipeline's tested application rules (no planner)")
    v, d, family, variant, fmt, items = planned_inputs(row, letter)
    plans, problems = product_planner.plan_products(d, items, family, variant, _approach_dict(fmt, variant), confirmed, replan)
    if problems:
        print("\n".join(problems))
    if len(plans) < 5 or any(not p.get("_meta", {}).get("valid") for p in plans.values()):
        raise SystemExit(f"row {row}: not all 5 products have a valid plan yet - nothing was built")
    shots_row(row, letter)


def shots_row(row, letter=None, quiet=False):
    """pipeline.py shots <row>: (re)build reel_plan.json + shots/ from the saved plans - no OpenAI call. Run it again after
    STEP 0 (it then adds the identity locks) or after editing a plan by hand."""
    v, d, family, variant, fmt, items = planned_inputs(row, letter)
    plans, specs = {}, {}
    for slot, pid, spec in items:
        p = product_planner.load(product_planner.key(pid, family, variant, fmt["letter"]))
        if p is None:
            raise SystemExit(f"row {row} slot {slot} {pid}: no plan yet - run: pipeline.py plan {row}")
        e, w = product_planner.validate(p, spec, family)
        if e:
            block(f"row {row} slot {slot} {pid}: the plan has errors:\n  - " + "\n  - ".join(e))
        plans[slot], specs[slot] = p, spec
    reel, E, W = reel_planner.build(row, family, variant, v["name"], plans, specs)
    for w in W:
        print("warning:", w, file=sys.stderr)
    if E:
        block(f"row {row}: reel plan problems:\n  - " + "\n  - ".join(E))
    json.dump(reel, open(os.path.join(d, "reel_plan.json"), "w"), indent=1, ensure_ascii=False)
    sp = os.path.join(d, "specs")
    txt = {s: open(os.path.join(sp, f"slot_{s}.txt")).read() for s in plans if os.path.exists(os.path.join(sp, f"slot_{s}.txt"))}
    ids = {s: open(os.path.join(sp, f"slot_{s}", "identity_lock.txt")).read() for s in plans
           if os.path.exists(os.path.join(sp, f"slot_{s}", "identity_lock.txt"))}
    out = shot_builder.write(d, reel, plans, txt, ids, family)
    if quiet:
        return
    print(open(os.path.join(out, "ORDER.md")).read() + f"shots: {out}")
    if len(ids) < 5:
        print(f"NOTE: identity locks for {5 - len(ids)} slot(s) are added after STEP 0 - run `pipeline.py shots {row}` again then.")


def prompt_planned(row, letter=None):
    v = BATCH[str(row)]; d = rdir(row); sd = os.path.join(d, "shots")
    reel = json.load(open(os.path.join(d, "reel_plan.json")))
    ft = os.path.join(DATA, "film_titles.json")
    film = json.load(open(ft)).get(str(int(row))) if os.path.exists(ft) else None
    if not film:
        raise SystemExit(f"row {row}: no sheet title in {ft} - add the col I text first")
    sup = json.dumps(dict(board=BOARDS[int(row) % len(BOARDS)], head=film, sub="", start=0, end="<footage end>", x=0.42, y=0.05,
                          max_w=0.66), ensure_ascii=False)
    rooms = ", ".join(f"{sd}/room_{r}.json" for r in reel["rooms"])
    return f"""You are a worker making ONE PLANNED Flipkart BAU reel: sheet tab "{TAB}" row {row} ({v['name']}, {v['folder']}).
Every image and clip prompt is already written in {sd}/ from the product plans - paste them VERBATIM, never write or change
a prompt yourself, never add a shot. Read {sd}/ORDER.md first. Work folder: {d}.
Persona sheet: {OMNI}/personas/{v['name'].lower()}.jpg. Listing photos: {d}/products/p<N>_*.jpg.

{spec_block(row, planned=True)}
STEP 1: when the 5 reference sheets exist and --check-sheet printed OK for each, run
   FK_MODE=BAU /usr/bin/python3 {os.path.realpath(__file__)} shots {row}
   (adds each product's identity lock to its prompts).
STEP 2 ROOM MASTER(S) ({rooms}): generate_nano_banana_image, aspect 9:16, 1K, image_asset_ids = the files' "refs" in that
   order (persona_sheet = the uploaded persona photo; room_master:<room> = that room master's asset id), prompt = "prompt"
   verbatim. Every other image of a room is an edit of its room master: it fixes the room, the background props, the light
   and the person's real size, so the background never changes.
STEP 3 STILLS, for every {sd}/slot_<N>.json: start_still (refs: its room master, the uploaded specs/slot_<N>/reference_sheet.png,
   the uploaded products/p<N>_1.jpg) then end_still (refs: the start still's id). Queue all start stills at once
   (wait_for_result false), collect them with get_image_status, then queue the end stills the same way.
STEP 4 CLIPS, for every slot: generate_video with model "gemini-omni-1.2-flash", resolution "360p", aspect_ratio "9:16",
   duration_seconds 4, image_asset_ids = [start still id, end still id] (first/last frame: exactly these two images), prompt =
   the clip "prompt" verbatim. Submit all 5, then download each to its "out" path (clips/slot_<N>.mp4).
STEP 5 plan.json = {sd}/plan_skeleton.json (5 segments: ONE continuous 4 s take per product, in the planned order) plus
   "supers": [{sup}], "logo": true, "endslate": true, "audio": {{"mode": "music", "music": "default"}}, "camera": "steady".
   TITLE = the sheet's col I text exactly. Never split a product's take, never add a segment, zoom stays 1.0 (the zoom-in is
   inside the clip).
STEP 6: FK_MODE=BAU /usr/bin/python3 {os.path.realpath(__file__)} finish {row}
   finish checks the 5 takes automatically (exactly 5 products, 4.0 s each, no cut inside a product, no broken/black/frozen
   clip). If it refuses, report the slot it names - do not regenerate without the user's yes.
ENGINE: TrueFan MCP only, folder "Flipkart_Fashion-Rhythm_AI_Profiles" on EVERY call (upload_media too). Rate limit: one timed
   wait (5, then 10, then 15 min) and check once - never loop-poll, never resubmit a queued job.
NO QC STAGES (user 17-Nov): one take per image and per clip, no review sheets. Log every asset id and generation id in
{d}/log.md. Never delete files (move to work/junk). No Drive upload, no sheet edits.
DISK: before starting and before finish run `df -g /System/Volumes/Data`; under 2 GB free -> STOP, log "PAUSED: disk", report.
Final report (short): 480p path, duration, the 5 products in order."""


def check_planned(row, d):
    """21-Nov: automatic, instant checks of a planned reel before assembly (not QC - broken-file checks): exactly 5 products,
    one continuous 4.0 s take each in the planned order, digital zoom 1.0, and no cut / black / frozen frames inside a take."""
    rp = os.path.join(d, "reel_plan.json")
    if not os.path.exists(rp):
        return [f"no reel_plan.json - the row was not planned (run: pipeline.py plan {row})"]
    reel = json.load(open(rp)); plan = json.load(open(os.path.join(d, "plan.json")))
    segs = plan.get("segments", []); bad = []
    slots = [sg.get("slot") for sg in segs]
    if len(segs) != 5 or sorted(x for x in slots if x) != [1, 2, 3, 4, 5]:
        bad.append(f"plan.json must have exactly 5 segments, one per product slot 1-5 (has {len(segs)}, slots {slots})")
    elif slots != reel["order"]:
        bad.append(f"plan.json product order {slots} differs from the planned order {reel['order']}")
    for sg in segs:
        n = sg.get("slot", "?"); a, b = float(sg.get("in", 0)), float(sg.get("out", 0)); src = os.path.join(d, sg["clip"])
        if abs((b - a) - approaches.PER_PRODUCT) > 0.05:
            bad.append(f"slot {n}: the take is {b - a:.2f} s (must be one continuous {approaches.PER_PRODUCT:.1f} s take)")
        if float(sg.get("zoom", 1.0)) != 1.0:
            bad.append(f"slot {n}: digital zoom {sg.get('zoom')} (must be 1.0 - the zoom-in is a camera push-in inside the clip)")
        if not os.path.exists(src):
            bad.append(f"slot {n}: clip missing ({sg['clip']})"); continue
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src],
                           capture_output=True, text=True)
        try:
            D = float(r.stdout.strip())
        except ValueError:
            bad.append(f"slot {n}: the clip cannot be read (broken file)"); continue
        if D < b - 0.05:
            bad.append(f"slot {n}: the clip is {D:.2f} s, shorter than its {b:.2f} s take")
        r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-ss", f"{a:.3f}", "-to", f"{min(b, D):.3f}", "-i", src, "-an",
                            "-vf", "blackdetect=d=0.3:pix_th=0.10,freezedetect=n=0.003:d=2,select='gt(scene,0.15)',showinfo",
                            "-f", "null", "-"], capture_output=True, text=True)
        if r.returncode != 0:
            bad.append(f"slot {n}: the clip cannot be decoded (broken file)")
        if "black_start" in r.stderr:
            bad.append(f"slot {n}: black frames inside the take")
        if "freeze_start" in r.stderr:
            bad.append(f"slot {n}: the picture freezes for 2 s or more")
        cuts = re.findall(r"pts_time:([0-9.]+)", r.stderr)
        if cuts:
            bad.append(f"slot {n}: a cut inside the product's take at {', '.join(cuts[:3])} s")
    if not bad:
        print(f"row {row}: 5 planned takes OK (4.0 s each, planned order, no cut, no black or frozen frames)")
    return bad


def check_sheets(row, d):
    """21-Nov user: every one of the 5 products has its own product sheet (and, outside Makeup, its 6-angle reference sheet)."""
    sp = os.path.join(d, "specs"); bad = []
    miss = [n for n in range(1, 6) if not os.path.exists(os.path.join(sp, f"slot_{n}.txt"))]
    if not is_beauty(row):
        miss += [n for n in range(1, 6) if not os.path.exists(os.path.join(sp, f"slot_{n}", "reference_sheet.png"))]
    for n in range(1, 6):   # 22-Nov: a product that is opened / taken out of its box also needs its open-state sheet
        sf = os.path.join(d, "shots", f"slot_{n}.json")
        if os.path.exists(sf) and json.load(open(sf)).get("open_sheet") and not os.path.exists(os.path.join(sp, f"slot_{n}", "open_sheet.png")):
            bad.append(f"slot {n} is opened / taken out of its box but its open-state sheet is missing (specs/slot_{n}/open_sheet.png)")
    if miss:
        bad.append(f"product sheet missing for slot(s) {sorted(set(miss))} - every product needs its spec sheet"
                         + ("" if is_beauty(row) else " and its reference sheet (STEP 0)") + " before finish")
    return bad


def check_cuts(row, master):
    """21-Nov user: a product's take is never cut or jumped to another scene. Scene cuts may only fall on the product
    boundaries (every 4 s) and at the end slate; any other cut in the assembled master refuses the reel (instant check).
    Threshold 0.15: a real cut scores 0.2-0.9, a continuous take with a push-in stays under 0.05 (measured 21-Nov)."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-v", "info", "-i", master, "-an", "-vf", "select='gt(scene,0.15)',showinfo",
                        "-f", "null", "-"], capture_output=True, text=True)
    per = approaches.PER_PRODUCT
    cuts = [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    bad = [t for t in cuts if t < 5 * per - 0.2 and min(abs(t - k * per) for k in range(6)) > 0.2]
    if bad:
        return [f"a product's take is cut in the middle at {', '.join(f'{t:.2f}' for t in bad)} s (product "
                         f"{', '.join(str(int(t // per) + 1) for t in bad)}) - each product must be ONE continuous take; "
                         f"regenerate that product's clip after the user's yes"]
    print(f"row {row}: no cut inside any product (cuts only at the product boundaries)")
    return []


def _probe_s(f):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return None


def check_text(row, d):
    """23-Nov: the on-screen title is the sheet's film text verbatim, and its price claim matches the 5 products' listing prices.
    Returns (problems, warnings)."""
    bad, warn = [], []
    want = json.load(open(os.path.join(DATA, "film_titles.json"))).get(str(int(row)))
    heads = [s_.get("head") for s_ in json.load(open(os.path.join(d, "plan.json"))).get("supers", [])]
    if not want:
        bad.append("no film title for this row in film_titles.json - load it from the sheet")
    elif heads != [want]:
        bad.append(f"on-screen title {heads} is not the sheet's film text {want!r}")
    if want:
        low = want.lower()
        if re.search(r"(under|from) ₹\s?[\d,]+.*\b(under|from)\b", low):
            warn.append(f"title repeats a price phrase: {want!r} (sheet text - confirm with the sheet owner)")
        if re.search(r"[a-z][A-Z]", want):
            warn.append(f"title may be missing a space: {want!r}")
        prices = []
        for n in range(1, 6):
            try:
                prices.append(float(json.load(open(os.path.join(d, "specs", f"slot_{n}.json"))).get("price")))
            except (OSError, ValueError, TypeError):
                pass
        m = re.search(r"(under|from|starting from|starting at)\s*₹\s?([\d,]+)", low)
        if m and len(prices) == 5:
            x = float(m.group(2).replace(",", ""))
            if m.group(1) == "under" and max(prices) > x:
                bad.append(f"title says under ₹{x:.0f} but a product costs ₹{max(prices):.0f} on its listing")
            if m.group(1) != "under" and min(prices) < x - 0.5:
                warn.append(f"title says from ₹{x:.0f} but the cheapest product is ₹{min(prices):.0f}")
        elif m:
            warn.append(f"price claim not checked: only {len(prices)} of 5 listing prices saved")
    return bad, warn


def finish(row):
    """Assemble the reel, then run every automatic check (23-Nov Garvit: 'block before pay + upload').
    The paid clips are always assembled; a reel that fails a check is written to qc/FAILED.json, is NOT filed in
    01_LATEST_FINAL and can NOT be uploaded. A reel that passes gets qc/pass.json, which upload requires."""
    d = rdir(row); b = json.load(open(os.path.join(d, "brief.json")))
    qd = os.path.join(d, "qc"); os.makedirs(qd, exist_ok=True)
    for f in ("pass.json", "FAILED.json"):
        if os.path.exists(os.path.join(qd, f)):
            os.remove(os.path.join(qd, f))
    bad, warn, card = [], [], []
    master = os.path.join(d, "final", b["out_name"]); p480 = master.replace(".mp4", "_480p.mp4")

    def rec(name, problems=(), warnings=()):
        """23-Nov plan step 6: every check lands in ONE scorecard (qc/scorecard.json) with PASS / WARN / FAIL."""
        problems, warnings = list(problems), list(warnings)
        bad.extend(problems); warn.extend(warnings)
        card.append(dict(check=name, result="FAIL" if problems else "WARN" if warnings else "PASS", detail=problems + warnings))

    def scorecard(final):
        json.dump(dict(row=int(row), result=final, checks=card, at=time.strftime("%Y-%m-%d %H:%M:%S")),
                  open(os.path.join(qd, "scorecard.json"), "w"), indent=1, ensure_ascii=False)
        print(f"\nSCORECARD row {row}: {final}")
        for c in card:
            print(f"  {c['result']:4}  {c['check']}" + (f"  - {'; '.join(c['detail'])[:160]}" if c["detail"] else ""))

    def fail():
        scorecard("FAILED")
        json.dump(dict(row=int(row), master=master, problems=bad, warnings=warn, at=time.strftime("%Y-%m-%d %H:%M:%S")),
                  open(os.path.join(qd, "FAILED.json"), "w"), indent=1, ensure_ascii=False)
        raise SystemExit(f"row {row}: FAILED - not filed, not uploadable (the clips are kept):\n  - "
                         + "\n  - ".join(bad) + f"\nfix the named slot(s), then run: pipeline.py finish {row}")
    try:
        if is_beauty(row):
            finish_beauty(row, d, b)
        else:
            rec("5 product takes (4 s, order, no black / frozen / cut, readable)", check_planned(row, d))
            rec("product sheets and locks", check_sheets(row, d))
            rec("on-screen title = sheet text, price claim vs listings", *check_text(row, d))
            env = dict(os.environ, BBD_OUT=WORK, FK_BATCH=os.path.join(DATA, "batch_100.json"))
            subprocess.run(["nice", "-n", "19", PY, ASM_FK, str(row)], check=True, env=env)
    except (subprocess.CalledProcessError, SystemExit, OSError, ValueError, KeyError) as e:
        rec("assembly", [f"assembly failed: {e}"])
        fail()
    D = _probe_s(master)
    if D is None:
        rec("master readable", ["the assembled master cannot be read"])
    else:
        cap = min(30.0, 5 * approaches.PER_PRODUCT + endslate_s()) + 0.10      # +0.1 s encode rounding; client cap 30 s
        rec(f"length <= {cap - 0.10:.1f} s (is {D:.2f} s)",
            [f"final is {D:.2f} s > {cap - 0.10:.2f} s (5 x {approaches.PER_PRODUCT} s per product + end slate, max 30 s)"] if D > cap else [])
        if not is_beauty(row):
            rec("no cut inside a product", check_cuts(row, master))
    subprocess.run(["nice", "-n", "19", "ffmpeg", "-v", "error", "-y", "-i", master, "-vf", "scale=480:854:flags=lanczos",
                    "-c:v", "libx264", "-crf", "23", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", p480], check=True)
    _rw = []
    for rp_, what in (("limbs_report.json", "extra hand / face"), ("size_report.json", "product changes size")):   # 23-Nov
        try:
            for k_, v_ in json.load(open(os.path.join(d, rp_))).items():
                if v_.get("flagged"):
                    _rw.append(f"slot {k_}: possible {what} in the clip ({len(v_['flagged'])} flag(s), {rp_}) - look before upload")
        except (OSError, ValueError, AttributeError):
            pass
    rec("free clip reports (hand count, size drift)", [], _rw)
    if bad:
        fail()
    # 16-Nov user: local folders like Drive -> BAU finals in 01_LATEST_FINAL/Day N/<Category> (+ Day N/1080p_masters)
    base = os.path.join(LATEST, BAU_DAY.get(BATCH[str(row)]["vertical"], "Day 1")) if BAU else LATEST
    os.makedirs(os.path.join(base, "1080p_masters"), exist_ok=True)
    cdir = os.path.join(base, cat_code(BATCH[str(row)])); os.makedirs(cdir, exist_ok=True)
    shutil.copy(p480, cdir)
    mdst = os.path.join(base, "1080p_masters", os.path.basename(master))
    if os.path.exists(mdst):
        os.remove(mdst)       # 23-Nov: unlink first, so a later re-finish never rewrites the delivered master in place
    if BAU:   # 13-Nov disk: hard link (same file on disk, no second 90 MB copy)
        os.link(master, mdst)
    else:
        shutil.copy(master, mdst)
    for f in os.listdir(os.path.join(d, "work")):          # disk: drop assemble intermediates (seg/body/main), keep clips
        if f.endswith(".mp4"):
            os.remove(os.path.join(d, "work", f))
    filed = os.path.join(cdir, os.path.basename(p480))
    json.dump(dict(row=int(row), file=filed, size=os.path.getsize(filed), duration=D, warnings=warn,
                   at=time.strftime("%Y-%m-%d %H:%M:%S")), open(os.path.join(qd, "pass.json"), "w"), indent=1, ensure_ascii=False)
    scorecard("PASSED" + (" with warnings" if warn else ""))
    print("done:", filed, f"({D:.2f} s, all checks passed)")


# 16-Nov user: ONLY the approved Rhythm BGM (RHY_BGM_*, not approved: 1 2 3 11 13 14 17 19 22) - assets/music/rhythm_bgm_approved
MDIR = os.path.join(PIPE, "assets", "music", "rhythm_bgm_approved")
MUSIC = sorted(f for f in os.listdir(MDIR) if f.endswith(".wav")) if os.path.isdir(MDIR) else []


def musicplan(rows):
    """Rotate the 6 unique tracks over rows in order: never the same track on consecutive rows, counts balanced."""
    plan = json.load(open(os.path.join(DATA, "music_plan.json"))) if os.path.exists(os.path.join(DATA, "music_plan.json")) else {}
    for i, r in enumerate(rows):
        plan[str(r)] = os.path.join(MDIR, MUSIC[i % len(MUSIC)])
    json.dump(plan, open(os.path.join(DATA, "music_plan.json"), "w"), indent=1)
    for r in rows:
        print(r, os.path.basename(plan[str(r)]))


def addrows(path):
    """Add sheet rows (04_DATA/sheet_rows_*.json) to batch_100.json + 04_DATA/rows/row_NNN (brief.json, products/ via products.py)."""
    src = json.load(open(path)); links = src["persona_links"]
    for x in src["rows"]:
        r = int(x["row"]); key = str(r); d = os.path.join(DATA, "rows", f"row_{r:03d}"); os.makedirs(d, exist_ok=True)
        urls = [f"https://www.flipkart.com/product/p/itme?pid={p}" for p in x["pids"]]
        BATCH[key] = dict(BATCH.get(key, {}), name=x["name"], vertical=x["vertical"], folder=FOLDERS[x["vertical"]],
                          home_variant=r % 8, products=urls, music=BATCH.get(key, {}).get("music", os.path.join(MDIR, MUSIC[0])),
                          persona_link=f"https://drive.google.com/file/d/{links[x['name']]}/view")
        bp = os.path.join(d, "brief.json")
        b = json.load(open(bp)) if os.path.exists(bp) else {}
        b.update(row=r, tab=TAB, name=x["name"], music_only=True, vertical=x["vertical"], product_urls=urls,
                 persona={"name": x["name"], "image": os.path.join(OMNI, "personas", f"{x['name'].lower()}.jpg")},
                 out_name=f"{PREFIX}_row{r:03d}_{x['name']}_{re.sub(r'[^A-Za-z]', '', FOLDERS[x['vertical']])}.mp4")
        json.dump(b, open(bp, "w"), indent=1)
        have = os.path.isdir(os.path.join(d, "products")) and len(os.listdir(os.path.join(d, "products"))) >= 5
        old = json.load(open(os.path.join(d, "products.json"))) if os.path.exists(os.path.join(d, "products.json")) else None
        same = bool(old) and all(p in json.dumps(old) for p in x["pids"])
        if not (have and same):
            if os.path.isdir(os.path.join(d, "products")):
                shutil.move(os.path.join(d, "products"), os.path.join(d, "products_old_30oct"))
            subprocess.run(["nice", "-n", "19", PY, os.path.join(OMNI, "scripts/products.py"), str(r)],
                           env=dict(os.environ, BBD_OUT=os.path.join(DATA, "rows")), check=False)
        n = len(os.listdir(os.path.join(d, "products"))) if os.path.isdir(os.path.join(d, "products")) else 0
        print(r, x["name"], x["vertical"], "products:", n, "(kept)" if have and same else "(fetched)")
    json.dump(BATCH, open(os.path.join(DATA, "batch_100.json"), "w"), indent=1)


RCLONE = shutil.which("rclone") or os.path.expanduser("~/bin/rclone"); DRIVE_ROOT = os.environ.get("FK_DRIVE_ROOT", "")


BAU_DAY = {"FashionWearables _Women": "Day 2", "FashionWearables _Men": "Day 2", "women Footwear": "Day 2"}   # every other BAU vertical (ethnic) = Day 1


def upload(rows):
    """Copy each row's final 480p into its Drive category folder (copy, never sync), record file id + link."""
    lp = os.path.join(DATA, "drive_links_final.json"); links = json.load(open(lp)) if os.path.exists(lp) else {}
    for r in rows:
        # 16-Nov user: "drive par bhi folder arrange karna jaise sheet pe hai - Day 1 and Day 2" -> BAU_1500_1/Day N/<category>
        v = BATCH[str(r)]; folder = (f"BAU_1500_1/{BAU_DAY.get(v['vertical'], 'Day 1')}/" if BAU else "") + FOLDERS[v["vertical"]]
        f = [os.path.join(rt, x) for rt, _, fs in os.walk(LATEST) if "1080p_masters" not in rt for x in fs
             if x.startswith(f"{PREFIX}_row{int(r):03d}_") and x.endswith("_480p.mp4") and "_GEST" not in x and "_REF" not in x]
        if not f:
            print(r, "NO FINAL"); continue
        # 23-Nov Garvit: upload only a reel whose finish passed every check, and only that exact file
        pj = os.path.join(rdir(r), "qc", "pass.json")
        if not os.path.exists(pj):
            print(r, "NOT UPLOADED: no passed finish (qc/pass.json) - run finish and fix what it names"); continue
        ok = json.load(open(pj))
        f = [x_ for x_ in f if os.path.abspath(x_) == os.path.abspath(ok["file"])]
        if len(f) != 1 or os.path.getsize(f[0]) != ok["size"]:
            print(r, "NOT UPLOADED: the filed reel is not the one that passed finish - run finish again"); continue
        subprocess.run([RCLONE, "copy", f[0], f"gdrive:{folder}", "--drive-root-folder-id", DRIVE_ROOT, "--tpslimit", "4"], check=True,
                       stderr=subprocess.DEVNULL)
        js = json.loads(subprocess.run([RCLONE, "lsjson", f"gdrive:{folder}", "--drive-root-folder-id", DRIVE_ROOT, "--files-only"],
                                       capture_output=True, text=True).stdout or "[]")
        hit = [x for x in js if x["Name"] == os.path.basename(f[0])]
        if hit:
            links[str(r)] = {"file": f"{folder}/{hit[0]['Name']}", "id": hit[0]["ID"],
                             "link": f"https://drive.google.com/file/d/{hit[0]['ID']}/view?usp=drivesdk"}
            print(r, links[str(r)]["link"])
    json.dump(links, open(lp, "w"), indent=1)


def retitle(rows):
    """Put the sheet's verbatim film text on finished rows: rewrite the super, re-assemble (no new clips), re-copy to LATEST."""
    titles = json.load(open(os.path.join(DATA, "film_titles.json")))
    for r in rows:
        d = rdir(r); pp = os.path.join(d, "plan.json"); plan = json.load(open(pp))
        sup = plan["supers"][0]; sup.update(head=titles[str(int(r))], sub="", y=0.05, max_w=0.66, x=0.42)
        plan["supers"] = [sup]; json.dump(plan, open(pp, "w"), indent=1, ensure_ascii=False)
        finish(r)


def status():
    done = {int(m.group(1)) for root, _, fs in os.walk(LATEST) if "1080p_masters" not in root
            for f in fs for m in [re.match(PREFIX + r"_row(\d+)_.*_480p\.mp4$", f)] if m}
    by = {}
    for r, v in BATCH.items():
        by.setdefault(v["folder"], []).append(int(r))
    for folder, rows in by.items():
        rows.sort(); d = [r for r in rows if r in done]
        print(f"{folder:22s} final {len(d):2d}/{len(rows)}  open: {[r for r in rows if r not in done]}")
    print("also final (not in batch_100):", sorted(done - {int(r) for r in BATCH}))


if __name__ == "__main__":
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "new":
        [new(r) for r in args]
    elif cmd == "prompt":
        print(prompt_beauty(args[0], (args[1:] or [None])[0]) if is_beauty(args[0]) else prompt_bau(args[0], (args[1:] or [None])[0]) if BAU else prompt(args[0]))
    elif cmd == "setapproach":   # setapproach <A-J|HOLD|AUTO> <row> [<row> ... | <from>-<to>]   (AUTO = rotation per vertical)
        rows = [x for r in args[1:] for x in (range(int(r.split("-")[0]), int(r.split("-")[1]) + 1) if "-" in r else [int(r)])]
        approaches.set_rows(DATA, args[0], rows)
    elif cmd == "setslot":   # Makeup: setslot <1-5> <rows...|from-to> = which product slot is the ONE applied product
        import csv
        rows = {x for r in args[1:] for x in (range(int(r.split("-")[0]), int(r.split("-")[1]) + 1) if "-" in r else [int(r)])}
        p = os.path.join(DATA, approaches.SHEET); lines = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
        n = 0
        for r in lines:
            if int(r["row"]) in rows and r["family"] == "makeup":
                r["apply_slot"] = args[0]; n += 1
        w = csv.DictWriter(open(p, "w", newline="", encoding="utf-8"), fieldnames=list(lines[0].keys())); w.writeheader(); w.writerows(lines)
        print(f"{n} makeup rows -> apply slot {args[0]}")
    elif cmd == "approaches":   # per-row selection summary: which rows run with which letter, how many on hold
        import collections
        sh = approaches.load_sheet(DATA); c = collections.defaultdict(collections.Counter)
        for r in sh.values():
            c[r["vertical"]][(r["approach"] or "HOLD").upper()] += 1
        for vert, k in c.items():
            print(f"{vert:26s} " + "  ".join(f"{x}:{k[x]}" for x in "ABCDEFGHIJ" if k.get(x)) + f"  HOLD:{k['HOLD']}")
        if args:   # approaches <letter> -> list the rows set to that letter
            print(" ".join(str(r) for r, x in sorted(sh.items()) if (x["approach"] or "HOLD").upper() == args[0].upper()))
    elif cmd == "plan":     # plan <row> [--confirmed]: OpenAI product plans (dry run without --confirmed) -> reel plan + prompts
        rp = next((a.split("=", 1)[1] for a in args if a.startswith("--replan=")), "")
        plan_row(args[0], "--confirmed" in args, next((a for a in args[1:] if not a.startswith("--")), None),
                 tuple(int(x) for x in rp.split(",") if x.strip()))
    elif cmd == "shots":    # shots <row>: rebuild reel_plan.json + shots/ from the saved plans (no OpenAI call)
        shots_row(args[0], (args[1:] or [None])[0])
    elif cmd == "finish":
        finish(args[0])
    elif cmd == "status":
        status()
    elif cmd == "addrows":
        addrows(args[0])
    elif cmd == "musicplan":
        musicplan(args)
    elif cmd == "retitle":
        retitle(args)
    elif cmd == "upload":
        upload(args)
    else:
        raise SystemExit(__doc__)
