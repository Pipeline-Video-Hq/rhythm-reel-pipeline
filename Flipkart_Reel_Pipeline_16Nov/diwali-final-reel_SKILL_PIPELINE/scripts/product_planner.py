"""PRODUCT PLANNER (user 21-Nov): OpenAI researches each product and plans how it is shown - the real everyday use, the
prerequisites, the life-size, the scene (room, surface, props) and ONE continuous 4 s shot with timed, described movements.

ONLY THE PRODUCT IS SENT to OpenAI: the listing title, brand, specifications, description and listing photos, plus our rule
book and the presentation style (approach letter text). Never the persona, the sheet, the client or the project.

    python3 pipeline.py plan <row>              # dry run: shows exactly what would be sent (nothing is sent, nothing is paid)
    python3 pipeline.py plan <row> --confirmed  # sends ONLY the products that have no valid saved plan, one request each

Rules (user, global): never call OpenAI without the user's explicit approval of that run (--confirmed), never auto-retry a
failed request, never print or share the key. The key is read from OPENAI_API_KEY or the pipeline's .env (not in the zip).

Plans are saved per product + approach in 02_BAU_DATA/product_plans/<PID>_<family>_<variant>_<letter>.json and reused by every
row that has that product. Every plan is checked by validate() before it can be used; a plan with errors blocks the row
(fix the JSON by hand and run `pipeline.py shots <row>`, or delete it and plan again - after the user's yes).
"""
import base64, glob, json, os, re, socket, sys, time, urllib.error, urllib.request
from product_spec import cm_values   # 23-Nov: unit-aware sizes (g / ml are not cm)
import netwait   # 23-Nov: wait out network drops instead of failing the row

PIPE = os.environ.get("FK_PIPE") or os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
PLAN_DIR = os.environ.get("FK_PLAN_DIR") or os.path.join(PIPE, "02_BAU_DATA", "product_plans")
API = "https://api.openai.com/v1/responses"

ROOMS = ["living_room", "bedroom", "bathroom", "kitchen", "dining_area", "entrance_foyer", "balcony", "study",
         "dressing_area", "nursery", "utility_area"]
# framings, from widest to closest; every product shot ends CLOSER than it starts (zoom-in only, never out)
FRAMINGS = {"full_body": 0, "knee_up": 1, "waist_up": 2, "knee_down": 2, "shoulders_up": 3, "feet_close": 3,
            "hands_close": 3, "product_close": 3.5, "macro": 4, "wall_close": 2.5,
            "photo_wide": 0, "photo_mid": 2, "photo_close": 3}   # photo_*: product-photo shots with no person (22-Nov)
SURFACE_KINDS = ["table", "counter", "dresser", "bed", "sofa", "shelf", "stool", "desk", "cabinet_top", "floor", "lap", "none_held", "wall"]
USE_KINDS = ["worn", "applied_to_body", "used_on_object", "handheld_display", "installed", "operated"]
HOME_FAMILIES = {"home_decor", "home_furnishing", "kitchen", "household_utility", "baby_care"}


def listing_size(spec):
    """23-Nov (Serper removed): the size the LISTING itself states (Width / Height / Depth / Length in its specifications), in cm."""
    sp = (spec or {}).get("specifications", {}) or {}
    nums = []
    for k, v in sp.items():
        if re.search(r"pack|box|carton|ship|parcel", str(k), re.I):
            continue                                       # 23-Nov: the box size is not the product size
        if re.search(r"^(width|height|depth|length|diameter)\b", str(k).strip(), re.I):
            m = re.search(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|inch)?", str(v))
            if m:
                x = float(m.group(1)); u = (m.group(2) or "cm").lower()
                nums.append(round(x * (0.1 if u == "mm" else 100 if u == "m" else 2.54 if u == "inch" else 1), 1))
    nums = [x for x in nums if x > 0]
    if len(nums) < 2:
        return None
    nums.sort(reverse=True)
    return dict(max_cm=nums[0], dims=" x ".join(f"{x:g}" for x in nums) + " cm", sources=1, all=1)


def serper_queries(spec):
    """22-Nov (user): Google search through Serper for the TRUE size and use. Only product words are searched (title, brand)."""
    t = re.sub(r"\s+", " ", str(spec.get("title", "")))[:90]
    b = str(spec.get("brand", "")).strip()
    bt = f"{(b + ' ') if b and b.lower() not in t.lower() else ''}{t[:70]}"
    return [f"{t} dimensions size cm", f"{bt} how to use",        # 23-Nov: 4 searches (was 2) so the plan loses nothing without OpenAI's search
            f"{bt} review in hand real size", f"{bt} what is in the box pack contents parts"]


def serper_facts(spec, pid):
    """Google results (answer box, knowledge graph, top results' snippets) for one product - cached per product, so a product
    is searched once. Paid per query: only inside `plan --confirmed` (after the user's yes); a failed query is never retried."""
    cache_dir = os.path.join(PLAN_DIR, "serper"); os.makedirs(cache_dir, exist_ok=True)
    cp = os.path.join(cache_dir, f"{pid}.json")
    res = json.load(open(cp)) if os.path.exists(cp) else {}
    missing = [q for q in serper_queries(spec) if q not in res]
    if missing:                                          # only the searches this product has not had yet
        key = env("SERPER_API_KEY")
        if not key:
            missing = []
        for q in missing:
            req = urllib.request.Request("https://google.serper.dev/search", json.dumps({"q": q, "gl": "in", "num": 10}).encode(),
                                         {"X-API-KEY": key, "Content-Type": "application/json"})
            for _try in range(20):
                try:
                    with urllib.request.urlopen(req, timeout=60) as r:
                        res[q] = json.loads(r.read().decode())
                    break
                except urllib.error.URLError as e:     # 23-Nov: never reached Serper (DNS / refused) -> wait, then send
                    if not netwait.not_sent(e):
                        raise
                    netwait.wait_for_network("https://google.serper.dev")
        json.dump(res, open(cp, "w"), indent=1, ensure_ascii=False)
    out = []
    for q, r in res.items():
        out.append(f"Search: {q}")
        for k in ("answerBox", "knowledgeGraph"):
            if isinstance(r.get(k), dict):
                out.append(f"  {k}: " + "; ".join(f"{a}: {v}" for a, v in r[k].items() if isinstance(v, (str, int, float)))[:400])
        for o in (r.get("organic") or [])[:8]:
            out.append(f"  - {o.get('title', '')} | {o.get('snippet', '')} | {o.get('link', '')}"[:400])
    return "\n".join(out)


_DIM = re.compile(r"((?:\d+(?:\.\d+)?)\s*[a-zA-Z]{0,2}\s*(?:x|×|\*)\s*(?:\d+(?:\.\d+)?)\s*[a-zA-Z]{0,2}(?:\s*(?:x|×|\*)\s*\d+(?:\.\d+)?\s*[a-zA-Z]{0,2})?)"
                  r"\s*(cm|mm|centimet\w*|millimet\w*|inch\w*|in\b|\")", re.I)


def serper_size(pid):
    """23-Nov (user, option 4): the product's real size read IN CODE from the saved Google results - the size most sources agree on.
    Returns dict(max_cm, dims, sources) or None. Free (uses the cached search)."""
    cp = os.path.join(PLAN_DIR, "serper", f"{pid}.json")
    if not pid or not os.path.exists(cp):
        return None
    texts = []
    for r in json.load(open(cp)).values():
        for k in ("answerBox", "knowledgeGraph"):
            if isinstance(r.get(k), dict):
                texts.append(" ".join(str(v) for v in r[k].values() if isinstance(v, (str, int, float))))
        texts += [str(o.get("title", "")) + " " + str(o.get("snippet", "")) for o in (r.get("organic") or [])]
    hits = []
    for t in texts:
        for m in _DIM.finditer(t):
            nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", m.group(1))]
            u = m.group(2).lower()
            f = 0.1 if u.startswith("mm") or u.startswith("milli") else 2.54 if u.startswith(("inch", "in", '"')) else 1.0
            nums = [round(x * f, 1) for x in nums if x > 0]
            ctx = t[max(0, m.start() - 50):m.start()].lower()
            if re.search(r"packag|box|carton|shipping|parcel|courier", ctx):
                continue                                   # the box it ships in, not the product
            sn = sorted(nums, reverse=True)
            if len(sn) == 3 and sn[1] <= 6 and sn[0] >= 8 * sn[1]:
                continue                                   # a rolled tube / long thin pack (a rolled sticker), not the product
            if len(nums) >= 2 and max(nums) < 500:
                hits.append(sn)
    if not hits:
        return None
    best = None
    for h in hits:                                      # the size most sources agree on (longest side within 15 %)
        grp = [g for g in hits if abs(g[0] - h[0]) <= 0.15 * h[0]]
        if best is None or len(grp) > len(best):
            best = grp
    mx = sorted(g[0] for g in best)[len(best) // 2]
    rep = min(best, key=lambda g: abs(g[0] - mx))
    return dict(max_cm=mx, dims=" x ".join(f"{x:g}" for x in rep) + " cm", sources=len(best), all=len(hits))


def env(name, default=""):
    """OPENAI_* from the environment, else from the pipeline's .env (never printed)."""
    if os.environ.get(name):
        return os.environ[name]
    p = os.path.join(PIPE, ".env")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


MODEL = env("OPENAI_MODEL", "gpt-5")
WEB_TOOL = env("OPENAI_WEB_TOOL", "web_search")    # 23-Nov (user): Serper removed - OpenAI's own web search finds sizes, use and parts

SCHEMA = """{
 "product": {
  "type": "exact product type, e.g. 'women's flat slide sandal', 'cartridge razor', '100 ml eau de parfum spray', 'double bedsheet with 2 pillow covers'",
  "category_item": "the one word or two for its category, e.g. 'sandal', 'razor', 'perfume bottle', 'bedsheet', 'rug', 'kurta set'",
  "how_people_use_it": "how a normal person in an Indian home really uses THIS product day to day, step by step",
  "use_kind": "one of: worn | applied_to_body | used_on_object | handheld_display | installed | operated",
  "fastening": "footwear/wearables: none (slip-on) | laces | buckle | velcro | zip | clasp | other; else 'n/a'",
  "parts_visible": ["every visible part WITH ITS COUNT, e.g. '1 silicone teat', '1 steel collar', '2 side straps', '1 wide embroidered strap'"],
  "colours": [{"part": "strap", "name": "lavender", "hex": "#B9A6D8"}],
  "drape": "clothing with a dupatta/pallu: exactly how many, on which shoulder, how it falls; else 'n/a'",
  "life_size": {"dimensions_cm": "the PRODUCT ITSELF, OUT OF ITS BOX - its real size, e.g. 'length 25, width 9, height 2' (never the box or pack size)",
                "package_cm": "the size of the box / pack / carton it is sold in, if a source gives it, e.g. '20 x 13 x 5 (box)' - NOT used for drawing; 'unknown' if not found",
                "size_check": "how you told product size from box size, e.g. 'Amazon lists Item 19.2 x 12.8 x 5.9 cm and Package 20 x 13 x 5 cm'",
                "dimensions_source": "listing | web_search (with the page/site name) | typical (only if nothing found)", "parts_cm": "size of each important part, e.g. 'strap width 2, sole length 25, lid diameter 4'; for an openable product also the OPEN size", "body_relative": "how big it looks on/against the body, e.g. 'as long as her foot', 'about the height of his palm'",
                "held_how": "how it is held or worn, e.g. 'in the right hand, fingers around the bottle, index finger on the nozzle'"}
 },
 "open_state_spec": {"used": false, "how_opened": "if used: the exact hand action that opens the lid/box or takes the product out, with timing", "state": "if used: what the OPEN product/box looks like - inside contents, every part with its count, colours, liner/tissue/insert, dimensions, what sits where", "parts_inside": ["each item visible when open, with count"], "removed_item_goes": "where the lid or taken-out item is held/placed"},
 "part_states": [{"part": "every removable lid, cap, cover, flap or stopper", "start": "closed | open | off", "end": "closed | open | off", "how": "if start != end: the exact hand action, e.g. 'right thumb flips the cap up at 1.0 s, cap stays hinged'; else leave empty"}],
 "parts_role": [{"part": "every separate part of the product, e.g. 'glass dropper with rubber bulb', 'amber bottle', 'cap', 'spare mesh sac', 'box'",
                 "role": "applicator | container | closure | spare | accessory | packaging",
                 "used": "true if THIS part is what does the job in the shot (e.g. the dropper puts the serum on), false if it is not touched",
                 "shown": "true if it is VISIBLE in the shot even though it is not used (e.g. the box standing beside the bottle, the spare sac on the tray), false if it is not in the scene",
                 "first_frame": "where it is in the first frame, e.g. 'in her right hand, tip 3 cm above her left palm' / 'screwed in the bottle' / 'not in the scene'",
                 "how": "if used: exactly how - which hand, which finger, the one movement; if not used: 'not touched'",
                 "never": "what must never happen with it, e.g. 'never used as a spoon', 'never shown as a second dropper'"}],
 "hero": {"main_thing": "the ONE thing a buyer must see - what the product is FOR, e.g. 'fruit inside the silicone mesh sac, ready for the baby to nibble'",
          "ready_state": "how the product looks PREPARED for its real use, already done before the first frame, e.g. 'protective cap already off and resting beside it, the silicone sac filled with small banana pieces visible through the mesh, latch closed'",
          "must_see": "what faces the camera, sharp and large, and where the push-in ends, e.g. 'the fruit-filled silicone sac'",
          "never": "what would show nothing, e.g. 'a plain front view of the empty, capped feeder'"},
 "prerequisites": ["what must ALREADY be true and visible in the first frame for a real use, e.g. 'three-day stubble on the cheeks', 'white shaving foam already on his left cheek', 'cap already off'"],
 "person": {"requirements": ["what the person looks like/wears for this product, e.g. 'bare feet', 'ankle-length trousers so the strap shows', 'hair tied back'"],
            "state_requires": {"short_key": "ONLY lasting states (beard, foam, cream, makeup, wet hair, clothes or footwear worn), e.g. 'beard': 'stubble' - never poses, angles or hand positions"},
            "state_changes": {"short_key": "ONLY lasting changes that stay after the shot, e.g. 'beard': 'one shaved strip' - never poses or angles"}},
 "scene": {"room": "one of: living_room | bedroom | bathroom | kitchen | dining_area | entrance_foyer | balcony | study | dressing_area | nursery | utility_area",
           "acceptable_rooms": ["rooms where this use is still natural, including 'room'"],
           "anchor": "the furniture/surface where the action happens, with its real height, e.g. 'the bathroom sink counter, 85 cm high'",
           "props": [{"item": "a prop the real use needs, e.g. 'shaving foam can'", "size_cm": "e.g. 'height 18, diameter 5'", "placement": "exactly where AND what it rests on, e.g. 'on the sink counter, right of the basin' / 'on the muslin cloth, which lies flat on the changing table' - never 'beside her' or 'in front of her' alone"}],
           "exclude": ["what must NOT be in the scene, e.g. 'any other footwear', 'any other perfume bottle', 'a second rug'"],
           "mount": {"type": "HOME DECOR ONLY (omit otherwise): wall | surface | floor | hanging", "width_cm": 0, "height_cm": 0, "height_from_floor_cm": 0, "gap_to_furniture_cm": 0, "person_distance_cm": 45, "person_side": "which side she/he stands; body turned about 45 degrees toward the item"},
           "surface": {"name": "the ONE surface the product rests on or is set down on, e.g. 'changing table', 'white dresser', 'sofa seat'",
                       "kind": "one of: table | counter | dresser | bed | sofa | shelf | stool | desk | cabinet_top | floor | lap | none_held | wall",
                       "size_cm": "width x depth x height, real size, e.g. '80 x 50 x 90'",
                       "placement": "where it is in the room, e.g. 'against the back wall, centred'",
                       "contents": ["what is already on it from the first frame, e.g. 'the pack stands upright near the front edge'"],
                       "used_when": "e.g. 'the pack stands on it from 0.0 s; both hands work above it'"},
           "why": "one line: why this room and anchor"},
 "shots": [{"framing_start": "full_body | knee_up | waist_up | knee_down | shoulders_up | wall_close (wall items) | feet_close | hands_close | product_close | macro",
          "framing_end": "a CLOSER framing (the push-in end)",
          "close_up_reason": "why the start framing is close (fine hand work: laces, buckle, clasp, razor stroke) or 'none'",
          "action_end_s": 2.5,
          "start_state": "the first frame: pose, where each hand and each foot is, where the product is and its state, what is in frame",
          "end_state": "the last frame: the visible correct result, hand/foot positions, product state, camera closer on the target",
          "push_in_target": "the product detail the camera pushes in on at the end (must be visible in the end pose)",
          "action_summary": "2-3 sentences: the whole action from first to last frame in plain order",
          "movement_type": "one word for the kind of movement: turn | heel_lift | toe_raise | slide | weight_shift | step | tap | lift_and_show | label_turn | spray | apply | smooth | place | pour | open | other",
          "camera_plan": {"start": "camera height in cm, distance to the subject in cm, level or tilt in degrees, phone lens, what fills the frame",
                          "move": "the REAL in-video camera move TOWARD THE PRODUCT, second by second: e.g. '0-4.0 s one smooth continuous dolly-in of 30 cm toward the bottle's label at about 8 cm/s, gentle during the action and a little faster after 2.5 s; no pan, tilt, roll, zoom-lens or shake'",
                          "end": "distance and framing at 4.0 s: about 15-30% closer, the product large and centred, the room still visible around it"},
          "last_frame": {"change": "the ONE change between the first and the last frame, e.g. 'her right index fingertip ends 8 cm to the right of where it started on the same artwork line' - or 'none'",
                         "changed_region": "right hand and forearm only | left hand and forearm only | product only | none",
                         "limbs_end": {"left_hand_arm": "...", "right_hand_arm": "...", "left_leg_foot": "...", "right_leg_foot": "...", "head_gaze": "...", "torso": "...", "arms_in_frame": 2, "hands_in_frame": 2},
                         "identical": "everything that stays pixel-identical to the first frame: the other arm, head, torso, every object and its place, the light",
                         "push_in": {"zoom": 1.25, "target": "what the camera centres on at the end (it is visible in the first frame)"},
                         "edit_prompt": "ONE paragraph for the image-edit model: 'Same picture, camera and framing unchanged. Change ONLY <the change>. Everything else stays identical: <list>.'"},
          "no_person": false,
          "plate_cleanup": "ONLY when no_person is true: what to remove from the original listing photo (stickers, text overlays, watermark, other products) and how to extend its background naturally to a 9:16 portrait frame",
          "ambient": "ONLY when no_person is true: always 'none' - nothing moves on its own, only the camera",
          "counts": "exact counts, e.g. 'one spray', 'one stroke', 'two toe taps'",
          "beats": [
            {"t_start": 0.0, "t_end": 0.4, "moves": "nothing | the body part(s) moving, e.g. 'his right hand'",
             "movement": "WRITE IN FULL, 25+ words: start position, path, direction, distance in cm, speed, how the fingers/palm/wrist/arm move, which finger touches which part, how the product itself moves, and where each moving part ends", "contact": "exactly which finger/palm touches which part of the product or body, with pressure (light/firm)",
             "support": "what holds the product in this beat: e.g. 'her right hand' or 'the changing table top'",
             "everything": {"_note": "ONLY the parts that move or touch something - leave every still part out",
                            "head": "the exact movement (direction, degrees or cm, speed)", "eyes": "...", "mouth": "...", "hair": "...",
                            "shoulders": "...", "torso": "...", "hips": "...", "left_arm": "upper arm, elbow, forearm, wrist", "left_hand_fingers": "palm and each finger",
                            "right_arm": "...", "right_hand_fingers": "...", "left_leg_foot": "knee, ankle, foot, toes", "right_leg_foot": "...",
                            "clothing": "sleeves, hem, dupatta, fabric", "product": "position, angle, which hand or surface holds it", "product_parts": "every lid, cap, strap, part",
                            "props": "every prop in the frame", "surface": "the table / wall / surface", "background": "room, furniture, window, curtains", "light": "...", "camera": "..."},
             "fingers": {"left": "EACH finger of the left hand: thumb, index, middle, ring, little - straight / curled / bent at which joint, what it touches, whether it moves (or 'out of frame')", "right": "the same for the right hand"},
             "limbs": {"left_hand_arm": "what the LEFT hand and arm do in this beat (or 'still at her side' / 'out of frame')", "right_hand_arm": "same for the RIGHT hand and arm", "left_leg_foot": "LEFT leg and foot (or 'out of frame')", "right_leg_foot": "RIGHT leg and foot (or 'out of frame')", "head_gaze": "head angle in degrees and where the eyes look", "torso": "chest/shoulders/hips: still or the exact small movement", "arms_in_frame": 2, "hands_in_frame": 2, "legs_in_frame": 2},
             "still": "what stays still", "product_state": "product state at the end of this beat",
             "camera": "locked (or 'push-in ...' in the last beat)", "gaze": "where the person looks, expression"}
          ]}, "... variant 2 (same shape) ...", "... variant 3 (same shape) ..."],
 "forbidden": ["actions/things that must never happen for THIS product"],
 "approach_note": "how the requested presentation style was adapted to this product (or 'used as given')",
 "schema_version": 8
}"""

RULEBOOK = f"""You plan ONE product shot for a vertical 9:16 Flipkart shopping reel. The images and video are made by AI models
(a still-image model, then a 360p video model that animates between a locked first frame and a locked last frame), so the plan
must be simple, physical and exact. Research the product (use web search if useful) and how real people in Indian homes use
this exact product every day. Reply with ONE JSON object only, exactly this shape (no markdown, no comments):
{SCHEMA}

HARD RULES (each comes from a real defect in delivered reels - follow all of them):
1. ONE CONTINUOUS TAKE of exactly 4.0 s. 0 to action_end_s (2.5, at most 3.0 for a genuinely longer real action such as tying
   laces): the real use or presentation. action_end_s to 4.0: nothing moves except the camera, which pushes in slowly and
   straight to the push_in_target (zoom IN only). No cut, no time skip, no new shot, no zoom out.
2. REAL EVERYDAY USE of THIS product only. Check the listing: laces are tied only on a lace-up; a buckle/velcro/zip/clasp only if
   the listing has one; a slip-on, slide, flip-flop, clog or mule is simply worn. Worn footwear with nothing to fasten is
   shown ONLY with small foot movements (turn the foot, raise the toes with the heel down, lift the heel with the toes down,
   shift the weight); the hands NEVER touch it (no smoothing, rubbing, tapping, pinching, tracing or seating the heel).
   Never invent a feature or a function.
3. PREREQUISITES are visible in the first frame: a razor needs stubble AND shaving foam/gel already on the skin; a trimmer
   needs a beard or stubble; a cream starts as a small amount on the fingertip; a spray starts with the cap already off; a
   lace-up to be tied starts with the laces untied. The product is ALREADY in hand / worn / installed in the first frame:
   never unboxed, taken out of a bag or drawer, put on, taken off or swapped during the shot. Nothing appears or disappears.
4. LIFE-SIZE: give real dimensions (listing first, else typical for this exact product) and how big that looks against the
   body. Every prop has a real size and an exact placement.
5. SCENE BY PRODUCT TYPE: choose the room and the surface where people really use it (razor: bathroom sink; perfume: bedroom
   dresser or by the door; footwear: living room or entrance, by a seat; bedsheet: on the bed; kitchen tool: on the kitchen
   counter). A tidy, lived-in upper-middle-class Indian home, no festive decor. Exclude every other item of the same category
   (no second rug under a rug, no other shoes, no other bottles). NO MIRROR in frame: if the use needs a mirror, the camera
   acts as the mirror (the person looks into the lens).
6. LARGE OR INSTALLED ITEMS (bedsheets, rugs, mats, mattresses, curtains, sofa/table covers, cushions on a sofa) are already in
   place and are NEVER rolled, unrolled, lifted, folded, shaken or taken down; the person smooths one edge with one hand,
   sits on it, or stands on it. Everything rests on a surface or is held in a hand - nothing floats.
7. BODY: one active hand unless the real use needs two (tying laces); say where the other hand rests. A seated person sits on
   the named seat (the anchor) for the whole shot. Head turns at most 30 degrees; a body turn is made with small steps, never
   by pivoting on one foot. Feet stay flat on the floor with weight unless one foot is stepping; a step is at most 30 cm;
   legs never cross. The face is either fully in frame or fully out of frame, never cut through.
8. MOVEMENT DESCRIPTION: beats run without gaps from 0.0 to 4.0 s. Every beat gives the moving body part (the person's OWN
   left/right, e.g. 'his right hand', and the screen side in brackets when it matters), direction, path, distance in cm,
   speed (everyday speed), contact, what stays still, the product state and the camera. At most 3 movement beats before
   action_end_s; each beat at least 0.4 s; exact counts. The last beat (action_end_s to 4.0) is the camera push-in only.
9. CLOSE-UP FOR FINE WORK: if the action is fine hand work (tying laces, a buckle, a watch clasp, a razor stroke), start the
   shot close (feet_close / hands_close / shoulders_up) so the hands and the product are big; the push-in then ends on the
   result (the tied bow, the clean strip).
10. PRODUCT IDENTITY: list every visible part and every colour (name + hex read from the photo). Clothing: exact length,
   pattern and trims; a dupatta/pallu is exactly ONE, on a stated shoulder, a separate fabric layer that stays on that side.
11. VARIANTS: "shots" holds 2 variants (home families: plus the 1 product-in-room variant) with DIFFERENT movement_type values (e.g. worn footwear: heel_lift / toe_raise / weight_shift / slide / step / tap (NEVER turn); a handheld product: lift_and_show / label_turn / the real use). The reel picks one
   variant per product so that no two products share a movement type. Every variant follows all rules; variant 1 is best.
12. STYLE: follow the requested presentation style where it fits the product; where it does not (e.g. 'adjust the strap' on a
   slip-on), use the closest real everyday action and explain it in approach_note.
13. No on-screen text, no claims, no other people, no pets, no speech.
14. SUPPORT (Day 6: packs and bottles hung in the air): in EVERY beat the product is either gripped by a named hand (the
   hand and forearm in frame) or rests on a named surface that is in frame - say which in 'contact'. An action that needs
   both hands (pulling out a wipe, rubbing in lotion, unscrewing a cap) starts with the product already standing on the
   anchor surface. Never held by fingertips alone, never left in the air, never a surface that appears mid-shot.
15. GRIP AND HANDS: hold the product by its body, fingers never covering its cap, nozzle, label or the detail shown. The
   SAME hand holds it from the first frame to the last (never passed to the other hand). To show its side, turn the WRIST
   so hand and product turn together (at most 30 degrees) - the product never turns or slides inside the grip. Exactly
   two hands, both the person's own and both attached to her/his arms.
16. NO OPENING OF PACKAGING: never open, tear, unseal or unbox a sealed pack, carton, box, pouch or wrapper, and nothing is
   taken out of its packaging - packs and boxes stay closed. Parts (caps, lids, hoods, teats, straps, pumps) are not taken
   off or put on unless that is the product's single real-use step; then the part stays in a hand or on the surface and
   both states are written in start_state / end_state.
17. SIZE IN FRAME: a handheld product smaller than 30 cm is never shown in a full_body or knee_up framing - start at waist_up
   or closer so its exact shape stays readable.
18. FORM: use it exactly the way its form works - a roll-on rolls on the skin (never sprays or mists), a spray sprays from
   15-20 cm (never rubbed), a cream or lotion is rubbed in from the fingertips, a stick glides - on the body area where people
   really use it (deodorant/antiperspirant: the underarm, with a sleeveless top).
19. LACES: tying laces starts with the laces untied and the loose ends hanging, and ends with a visible bow.
20. FACE: at least one of the 3 variants starts with a framing that shows the person's whole face (full_body, knee_up,
   waist_up or shoulders_up), so every reel can show the face at least once.
21. FOOTWEAR LEGS (the #1 footwear defect: legs rotating): the legs and feet NEVER rotate, pivot, swivel, twist or turn, and
   nothing is angled outward or inward. The ONLY allowed movements: raise the toes with the heel down (toe_raise), lift
   the heel with the toes down (heel_lift), shift the weight from one foot to the other (weight_shift), slide one foot
   straight forward or back at most 10 cm with the sole flat (slide), ONE straight step forward of at most 25 cm (step),
   one toe tap (tap), or - only for a lace-up - tie the laces while seated (tie_laces). Every foot points exactly the way
   its shin and knee point, in every frame. Both knees stay in frame from the first frame (start at knee_down, knee_up,
   waist_up or full_body; the push-in then goes closer). No turning of the body, no walking turns, no crossing or
   stacking of legs, no sideways slides, no kicking or swinging. movement_type must be one of the words above.
22. SURFACE (a table must never appear out of nowhere): scene.surface names the ONE surface the product rests on or is set
   down on - kind, real size, exact place in the room, what is already on it. It exists in the room from the very first frame
   and is IN the start framing (a surface above the floor needs a start framing of waist_up, knee_up, full_body, hands_close or
   product_close; sofa/bed/stool also allow knee_down). start_state must name it. Every beat that holds the product says in
   'support' the hand or this surface. kind none_held = the product stays in one hand the whole time; floor = shoes on the floor;
   lap = on her lap. Never mention or use any OTHER table, shelf, tray, stool, counter or bench in start_state, end_state or any
   beat - nothing is added, carried in or set up during the shot. Both-hand actions happen with the product standing on this
   surface. Prefer the room's own furniture (sofa, coffee table, side table, bed, counter, dresser, desk) over inventing one.
23. HOLDING HAND ALWAYS VISIBLE: whenever a hand holds, pinches or supports a product, that hand, the wrist and at least the
   forearm are in frame in EVERY frame (never held by a hand outside the frame, behind the product or covered by it). The
   push-in must not crop the holding hand out: a held product never ends at 'macro' (end at product_close or hands_close). No
   arm ever enters from the frame edge without a visible shoulder or body. start_state names the holding hand.
25. LIDS, CAPS, COVERS, LATCHES (user 22-Nov, a cap lifting off inside a clip produced a second cover fading in): NOTHING changes
   state inside the clip. List every removable part in part_states with ONE state (start = end): a part that the shot needs
   open is ALREADY open/off in the first frame (a cap already off stands or lies on the surface, named in start_state and
   scene.props) and stays so; every other part stays closed. No beat opens, closes, lifts, pops, unscrews, snaps, removes or
   replaces anything; part_states never has start different from end; open_state_spec.used is false.
27. ACTION DETAIL: describe every beat like a director directing a hand double. Per beat: the starting position of each moving
   body part, its exact path and direction (towards/away from the camera, left/right of the person), distance in cm, speed
   (slow/medium, cm per second), fingers and grip (which finger, thumb side, palm up or down), wrist and elbow movement,
   how the product moves and which part of it faces the camera, what touches what and how firmly, and the resting position
   at the end of the beat. start_state and end_state list every hand, foot, lid, product part and prop position. No beat
   may be vague ("shows", "uses", "applies"): say what each finger and arm does. Beats still cover 0 to 4 s with no gaps.
30. NOTHING MOVES ON ITS OWN (user 22-Nov): any object that moves - a product, lid, platform, curtain, plant, hair, cloth - moves
   only because a named hand/limb of the person moves it, in that beat's "limbs" text and with contact. Objects at rest stay
   at rest (no swaying, fluttering, rotating, sliding, floating, glowing or self-opening). In the no_person photo variant only the
   camera moves.
31. NOTHING APPEARS (user 22-Nov): every table, shelf, stool, tray, box, prop and product that is in the shot at any time is
   already in the first frame, in its final place, and named in start_state or scene (surface, props, anchor). Nothing is
   added, brought in, fades in or pops up later; the only things that change position are the ones a named limb moves.
32. ONE ACTING LIMB: the video model morphs from the first frame to the last, so extra or doubled limbs appear when many limbs
   change. Use ONE hand for the action whenever the product allows; the other arm hangs relaxed (or is out of frame) in the SAME
   position in the first and the last frame - hanging STRAIGHT DOWN along the body, fingers relaxed, never raised, never on the hip,
   never pointing (a second raised or bent arm is what the image model turns into a third arm); no limb crosses another limb,
   the torso or the face; a hand never passes in front of the face; at most two limbs move in any beat. The person stands in
   profile or three-quarter view toward the product when that hides the far arm.
33. NET CHANGE ZERO (user 22-Nov): the video morphs between its first and last frame, so every difference between them becomes a
   morph, a duplicate or an object that appears. The LAST FRAME IS THE FIRST FRAME, ONLY CLOSER (the code builds it as a crop):
   every object, both arms and the product are in the same place and the same state at 4.0 s as at 0.0 s. Use out-and-back
   actions only (a wrist turn of 30 degrees or less and back, a tilt and back, an index fingertip gliding 10 cm and back, a palm
   presenting and back). Never: set down, put, place, pick up, lift off, remove, take out, hand over, open, close, pour, fill,
   install, peel, flip - nothing is moved from one place to another and nothing changes state. The person's body (shoulders)
   is visible from the first frame: start at full_body, knee_up, waist_up or shoulders_up, never at hands_close or closer.
34. SENSITIVE PRODUCTS (breast pumps, intimate hygiene, sanitary products, lingerie, adult items, medicines, anything used on a
   child's body): shown ONLY as an object held in one hand away from the body, or resting on the surface; never at or against the
   chest, groin or a child; no baby, child, doll, nursing or bare skin; the person is fully clothed; do not demonstrate the use.
   (Gemini refuses such frames - a blocked clip wastes the whole row.) Use the product-photo variant where the family allows it.
35. SHOWABLE AT 360p: the product fills at least a third of the frame width in the last frame; labels face the camera and are not
   covered by fingers; no fine finger work (threading, tying, tiny buttons or clips); no see-through or mirror-like close-ups unless
   the product itself is glass.
37. THE CAMERA MOVES, NOT THE PERSON (row 510, 22-Nov): during the push-in (2.5-4.0 s) the person stays on the same floor spot -
   feet planted, no step, no walk, no lean toward the camera; only the camera comes closer. Outside footwear step shots, no beat
   moves the feet.
40. HERO - SHOW WHAT IT IS FOR (user 22-Nov: "it is a nibbler - what will I do with the front view?"): fill "hero". Every shot shows the
   product's MAIN THING - what it does for the buyer - not just its outside. The product is already in its READY / IN-USE state in the
   first frame (prepared before the shot: a nibbler's sac already filled with fruit and its cap off beside it; a bottle with milk; a
   lotion CLOSED with its label to the camera (open only when the action is the press); a decal installed on the wall) - nothing is filled, opened or prepared inside the
   clip. prerequisites, part_states and start_state describe that ready state; must_see faces the camera and the push-in ends on it.
   A plain front view of an unused product is never the shot.
39. EVERYTHING, EVERY BEAT (user 22-Nov: "every movement, if any, for everything"): in each beat, "everything" lists ONLY the parts
   that MOVE or TOUCH something (from: head, eyes, mouth, hair, shoulders, torso, hips, left_arm, left_hand_fingers, right_arm,
   right_hand_fingers, left_leg_foot, right_leg_foot, clothing, product, product_parts, props, surface, background, light, camera),
   each with the exact movement (what part, direction, cm or degrees, speed, contact, where it ends) - even one finger or a sleeve.
   Every part you leave out is "still" (the code writes that in), so do not write still parts.
38. FINGER AND CAMERA DETAIL (user 22-Nov: "even a finger lifting must be in the plan"): "fingers" describes, finger by finger
   (thumb, index, middle, ring, little), only a hand that holds, touches or moves something (straight, curled or bent at which
   joint, what it touches, whether it moves); a hand left out keeps its fingers still (the code writes that in). Every shot
   fills "camera_plan" (start height and distance, the move in cm, speed and timing, no pan/tilt/roll/zoom-lens/shake, end framing).
42. REAL, NOT A STUDIO (user 23-Nov: "it zooms into a sticker on a white background - no fun"): the push-in ends with the product LARGE
   but the room still around it (wall, furniture, light) - zoom 1.15-1.3, never a macro on a plain background. The no-person
   variant is the product IN THE ROOM (no person), never the white listing photo.
41. ALIVE, NOT STATIONARY (user 23-Nov: "everything feels too still"; "not one person standing still looking dead into the camera"):
   the person is never frozen or posed - she looks mostly at the product and glances at the camera once, shifts her weight, breathes, blinks, her head tilts a little and her smile changes; the action is clearly visible (a 30-degree turn, a 10 cm
   lift toward the camera, a palm or fingertip gliding 10-12 cm over the product); and the camera moves smoothly from the first
   second to the last at ONE even, slow speed (never a jump or cut to a closer shot). Only OBJECTS stay still unless a hand moves them.
43. THE CAMERA MOVE IS PLANNED HERE (user 23-Nov: "no post-production zoom - the only zoom is in the video, planned by OpenAI"): fill
   camera_plan for every shot. The video model films it as a REAL camera dolly-in TOWARD THE PRODUCT for the whole 4 seconds -
   say where it starts (height, distance), how far it moves (cm) at one even speed, what it centres on, and where it ends (about 15-25%
   closer, the product large and centred, the room still visible). There is no other zoom: nothing is cropped or zoomed afterwards.
44. HELD RIGHT, USED RIGHT (user 23-Nov review: products floating, a hairbrush held over the face, a sandal balanced on a palm, a
   dropper cap in mid-air, sandals far too big):
   a) A held product is GRIPPED - fingers around it, thumb on it, touching the palm - between chest and waist height, fully in the
      frame; never above the shoulders, never in front of the face, never balanced on a flat palm, never hanging below a hand.
      Nothing (product, cap, dropper, shoe) floats: a hand around it or a surface under it in every frame.
   b) A tool is shown WHERE it is used, the way it is used: a hairbrush in the hair, bristles in the hair; a comb's teeth in the
      beard or hair; a trimmer's blade on the jawline; a roll-on/deodorant near the underarm; a perfume sprayed at the wrist or neck
      from 15 cm; a serum or oil bottle held upright with its dropper inside. Use = one out-and-back stroke at that place.
   c) The product stays AS SOLD and ONE of each part: cap on, dropper inside the bottle, the pair together; no loose spare part,
      second dropper, extra cap or empty box in the scene unless the props list it.
   d) Size: the product is drawn against her hand and forearm (a sandal is about as long as her forearm; a 30 ml dropper bottle is
      shorter than her fingers); a pair of sandals held up is held by ONE hand around both heel straps, or rests on a surface.
45. CLOSED UNLESS USED (user 23-Nov, every category): a product with a cap, lid, pump, nozzle or dropper is CLOSED and nothing
   from it is on her skin, hair or clothes, unless the shot's action IS that use (a press, a spray, a dab): then it is open from the
   first frame and the action shows the one use, with a hand or surface ready to receive it. No cream, oil, foam or spray appears that
   the action did not put there.
46. PHONE IN A MIRROR SELFIE (user 23-Nov): if a phone is in the shot as a mirror selfie, the camera IS the mirror - the phone's BACK
   (camera lenses) faces the camera and its screen faces her; the screen is never shown to the camera; no mirror frame is drawn.
47. USE THE RIGHT PART (user 23-Nov: "a serum has a dropper - say exactly what to use and what not"): fill "parts_role" with EVERY
   separate part of the product (applicator, container, closure, spare, accessory, packaging). Mark used = true only for the part
   that really does the job in this shot - a serum is applied with its DROPPER (the bottle only holds it), a lotion with the PUMP,
   a perfume with the SPRAY NOZZLE, a nibbler with its SAC, a razor with its BLADE HEAD - and give its exact first-frame position
   and the one movement. Every other part is used = false and is not touched - but it CAN be shown (shown = true, user 23-Nov):
   the bottle standing beside, the box beside the product, the spare sac on the tray all make a fuller, real shot; say where it
   stands in first_frame - ALWAYS on a named surface that is IN THE START FRAMING, in front of or beside her (a counter in front of
   her at waist height, the dresser beside her), never "beside her" in the air; if the shot has no such surface in frame, the part
   is shown = false. A product with loose parts shown is filmed with her standing BEHIND the counter/table they lie on. A part in use is already in its use position in the first frame (the dropper already out of the bottle
   in her hand, the cap already off on the surface); a part not in the listing never appears; a spare or the box is never used
   for the action and never moves.
48. SUPPORT CHAIN (user 23-Nov: a cloth hovered in the air with things on it): every object - product, part, prop, cloth, towel,
   mat, tray, box - rests on something that rests on furniture or the floor; each prop's placement names what it rests on; a cloth
   or mat lies flat ON a table, counter, bed or shelf before anything rests on it. A prop whose placement names no support is
   dropped by the code.
49. STANDS OR LEANS FOR REAL (user 23-Nov: a pair of sandals stood upright on their toes on a table, nothing behind them): an
   object stands upright only if it can really stand on its own base; anything else lies on its natural resting side (shoes and
   sandals always ON THEIR SOLES, side by side). If the shot needs it propped up, PLAN THE PROP for it (user 23-Nov): a display
   stand, easel, riser or the product's own box, in scene.props with its real size and placement on the surface, standing behind
   it and touching it - never leaning against a wall. A hand resting on top is not support unless it grips.
50. HANDLING CONTRACT (Day 6 QC 23-Nov: products floating, caps opening wrongly, wipes hovering, hands swapping): for baby
   care, fragrance, grooming, home decor, kitchen and household items the product is, from the FIRST frame to the last, either
   (a) held in a FULL GRIP - palm against it, all fingers wrapped around it, never balanced on fingertips or pinched - in ONE
   hand that never changes, or (b) resting fully on a surface where it stays. Inside a 4 s take NOTHING is picked up, lifted off
   a surface, put down, placed, handed over, switched between hands, opened, closed, twisted open, unscrewed, popped, pulled
   out (wipe, tissue, item), unwrapped, peeled, poured or squeezed out. Show the product already in its ready state in the first
   frame. Fragrance may be sprayed ONLY with the cap already off in the first frame: the bottle in a full grip, the index finger
   presses the nozzle once. Rules 44-49 above still apply. A plan that breaks this is rejected by the code.
36. LAST FRAME PLAN (user 22-Nov): the last frame is made FROM the first frame by an image edit, then locked to it pixel for pixel
   and cropped to the push-in. Plan it in "last_frame": at most ONE change - one limb ends in a nearby place (at most 10 cm from
   where it started) or the product is turned at most 20 degrees - written in "change" and "edit_prompt"; "changed_region" names
   the only part of the picture that differs; "identical" lists everything else (the other arm, head, torso, every object and its
   place, the light); "limbs_end" says what all six limbs do in the last frame (at most 2 arms, 2 hands); "push_in.zoom" is
   1.15-1.3 (the room stays visible) and its target is visible in the first frame. Out-and-back actions use change "none". NEVER in the last frame: a new
   object, a moved or opened object, a second hand or arm, a different expression, other clothing, other light.
29. LIMBS EVERY SECOND (user 22-Nov, stops extra limbs and physics errors): inside the action (0 to action_end_s) beats are at
   most 1.0 s long, and EVERY beat fills "limbs" for ALL six parts: left hand+arm, right hand+arm, left leg+foot, right
   leg+foot, head/gaze (angle in degrees) and torso - even when still ("right arm hangs relaxed at her side, fingers loose") -
   plus arms_in_frame, hands_in_frame and legs_in_frame (never more than 2 each). Name the support: which hand or surface
   holds each object; a hand that holds something in one beat holds it in the next until it is set down. A limb out of frame
   says "out of frame". Nothing is described with "she shows" or "she uses": every limb is accounted for in every beat.
26. SIZE (every listing photo is a close-up - never judge size from it; user 23-Nov: tell the PRODUCT size from the BOX size): sources
   often give two sizes - the item / product dimensions and the package / box / shipping dimensions. dimensions_cm is ALWAYS the
   product itself out of its box (it is shown out of the box); the box size goes in package_cm and is never used for drawing; write
   in size_check how you told them apart. If only one size is found and it looks like a box (a neat rectangle bigger than the item,
   labelled package / box / shipping), say so and give the item's own size from photos with a hand or from similar products. LOOK UP the real dimensions with the web search tool (the listing's specifications first, then the brand and other retailers) (the listing's specification first, then the brand or other
   retail pages for this exact model) and write them in dimensions_cm (length, width, height/diameter, weight if known), with
   parts_cm for the important parts and dimensions_source naming where they came from. Only if nothing is found write a
   typical size for this exact product type and say "typical". Never guess a size that looks good in frame. The code computes the product's size against the person's height, palm
   and head and puts it into every prompt - never plan a product larger or smaller than real, or held in a way a real hand
   cannot hold it.
28. OPEN BOX / OPENED PRODUCT (user 22-Nov): nothing is opened or taken out of a box inside a clip. A product shown out of its box
   or with its cap off is ALREADY so in the first frame and stays so; open_state_spec.used is false.
24. DISPENSING (pump, squeeze bottle, tube, flip-cap releasing cream, lotion, gel, soap, shampoo or oil): before the press the
   OTHER hand is open, palm up, 5-8 cm directly below the nozzle/spout, in frame. One press releases ONE small dollop (pea or
   coin size) that lands in that palm and stays there; the hand then rubs it in or applies it. The product is never dispensed
   into the air, onto a surface or onto nothing; say 'palm' and 'below' in the beats."""


HOME_DECOR_RULES = """

HOME DECOR RULES (extra for this product; from reels with wrong depth, giant stickers, arms from nowhere and sticker sheets fading in):
D1. The item is ALREADY in its place from the first frame. Nothing is peeled, applied, stuck, hung, unrolled, unpacked, held up as
   a sheet or faded in. A sticker/decal set is shown INSTALLED on the wall in the arrangement of the listing photo; a framed or
   standing item stands on its named surface; a wall hanging hangs on the wall.
D2. scene.mount (schema_version 2): type wall | surface | floor | hanging; the item's real width_cm and height_cm (listing, else
   typical); height_from_floor_cm of its bottom edge; gap_to_furniture_cm (a wall item hangs 20-30 cm above a sofa back or a
   console; a decal starts at least 30 cm above furniture). Items are LIFE-SIZE: compare with the person (a 12 cm butterfly is
   palm-sized; a 60 x 90 cm decal reaches from her shoulder to above her head). A wall or hanging item sets scene.surface.kind
   'wall' (the room's back wall).
D3. DEPTH: person_distance_cm 30-60. The person stands that close to the item, parallel to its wall or surface, body turned
   about 45 degrees toward it, so shoulder, arm and hand form one visible line. She/he never reaches across the room to a far
   wall, never stands in front of the item blocking it, never stands mid-room while touching a wall. The camera is fixed 2-2.5 m
   from the wall, level, so wall, furniture and person share one depth.
D4. LIMBS: the shot starts with the person's upper body in frame (full_body, knee_up or waist_up); at most ONE hand touches or
   points at the item; the other arm hangs at the side or rests on a named piece of furniture; no arm enters from the frame edge.
D5. ONE ITEM, ONE WALL: only this product is on its wall (it is plain in every other shot); same wall, furniture and light all
   reel; no mirror.
D6. Allowed gestures only: fingertips resting on one edge or corner; one fingertip tracing one element; an open palm 20-30 cm
   from the item; straightening a frame by 1 cm; turning a small vase 10 degrees (items under 30 cm); smoothing one decal corner.
   Wall decals, large, heavy or fragile items are never picked up."""
BABY_RULES = """
BABY CARE (user 22-Nov): there is NEVER a baby, child or doll in the picture and nothing is put in or on a child. Show the product as an
object: held in one hand at chest height or resting on the changing table / counter, packs closed. A breast pump or feeding product
is held or placed away from the body and is never shown near the chest. Pacifiers, teats and soothers rest on the surface or are held
by the shield; nothing goes near a mouth. CREAMS AND LOTIONS (user 23-Nov): the bottle/tube is CLOSED (cap shut, pump locked) and
there is NO cream on any hand, unless the shot's action IS the press: then the cap is open from the first frame, her other open palm
is 5-8 cm under the nozzle, ONE press puts ONE pea-size dollop in that palm, and last_frame.change says so. Cream never appears on a
hand that the action did not put there.
"""
HOME_DECOR_RULES += """
WALL DECALS AND STICKERS (user 22-Nov, rows 508-510): a decal is ONLY its printed artwork stuck directly on the wall and following
the wall surface. There is NO white, transparent or paper backing sheet, board, poster rectangle, frame or shadow box around it:
the white background of the listing photo is NOT part of the product. It never stands, leans or floats in front of the person or
furniture and never covers her face or body. Prefer the product-photo variant (rule 'PRODUCT-PHOTO VARIANT') for decals: it needs
no person, so it cannot have a wrong scale or an extra limb.
"""
HOME_DECOR_RULES += """
D7. WALL ITEMS ARE SHOWN BY TOUCH IN A CLOSE-UP (user 22-Nov; overrides D3, D4 and D6 for wall items and wallpapers): the avatar is never in
   front of the item and never points at the wall. framing_start is 'wall_close': the camera is 1.0 m from the wall facing it straight
   on, the item fills the right two-thirds of the frame, she stands at the LEFT edge in profile BESIDE it, only her shoulder, the side
   of her face and her right arm visible (the arm joined to a visible shoulder); her right hand touches the item's surface and
   feels it in ONE way per variant: touch_glide (flat palm glides 10 cm and back), touch_trace (index fingertip traces 8 cm of one line
   and back), touch_smooth (thumb and fingertip smooth 4 cm of one edge and back), touch_brush (backs of the fingers brush 10 cm and
   back), touch_press (fingertips press 1 cm and ease off). Contact stays on the surface all the time; the left arm hangs straight
   down out of frame. A product-photo variant (no person) is still allowed. Use movement_type touch_glide | touch_trace | touch_smooth |
   touch_brush | touch_press | hold.
"""
BABY_RULES += """
SIZES (baby care review, 22-Nov: "diapers too big", "things grew on their own"): baby products are SMALL. Write real sizes from the listing:
a diaper pack is about 30-45 cm tall and is shown CLOSED as the pack; one diaper folded is about 15 x 12 cm (palm-sized), unfolded about
35-45 cm long; a pacifier about 6 cm; a feeding bottle 15-20 cm; a cream tube 10-15 cm; a wipes pack about 20 x 12 cm. Size against her
hand in life_size.body_relative (e.g. 'a folded diaper is as big as her palm'). Nothing gets bigger or smaller during the shot.
"""
FAMILY_RULES = {"home_decor": HOME_DECOR_RULES, "baby_care": BABY_RULES}


DISPLAY_LETTERS = "KLMNOPQRSTUV"   # footwear display approaches (same set as approaches.DISPLAY_LETTERS)
FOOTWEAR_DISPLAY_RULES = """
FOOTWEAR DISPLAY APPROACH (this reel's approach is a DISPLAY one: the shoes are NOT worn - ignore rule 21 and every worn-footwear
rule): the person stands with feet and legs completely still, camera at waist_up or closer (knee_up at most); the shoe is
held in a hand or stands on a table/dresser/turntable. (a) HELD: gripped by the heel counter or toe box (never the laces),
the holding hand, wrist and forearm in frame; the shoe turns ONLY with the wrist, hand and shoe together, at most 30 degrees
to each side; it is never flipped, thrown, spun, dropped or passed between hands (two-shoe approaches use one shoe per hand).
(b) PLATFORM: list the turntable in scene.props (about 30 cm wide, 5 cm high, plain top, placement on the named surface) - it
is in the frame from the first frame; the shoes are fixed on it and turn with it at the same speed; only the platform turns,
at most 30 degrees left then back through the front to 30 degrees right, slowly (about 25 deg per second), and ONLY because
the person's hand (two fingertips on the rim, hand and forearm in frame) pushes it - the platform never turns by itself; table,
room, camera and the rest of the person do not move. Use movement_type hand_turn, platform_turn, lift_and_show,
tilt, present or point. Beats name the exact degrees and the direction (left/right of the camera). The person looks at the
camera with a soft smile, so the face is in frame in the first and last frame. The product is shown as the exact listed pair
(one shoe where the approach says one shoe); laces, buckles and velcro stay as in the listing and are not touched. A PAIR held up is held by ONE hand gripping both heel straps / heel counters together - never hanging under an open
hand, never balanced flat on a palm; otherwise the pair rests ON ITS SOLES on the surface, side by side - never standing upright
on the toes or heels. A sandal is about as long as her forearm - never bigger.
"""


def family_rules(family, letter=None):
    t = FAMILY_RULES.get(family, "") + (PHOTO_RULES if family in PHOTO_FAMILIES else "")
    if family == "footwear" and letter and letter in DISPLAY_LETTERS:
        t += FOOTWEAR_DISPLAY_RULES
    return t


def key(pid, family, variant, letter):
    return f"{pid}_{family}_{variant or 'any'}_{letter}"


def path(k):
    return os.path.join(PLAN_DIR, k + ".json")


def load(k):
    p = path(k)
    if not os.path.exists(p):
        return None
    try:
        return json.load(open(p))
    except ValueError:      # 23-Nov: a half-written file is treated as no plan, never a crash
        return None


def save_plan(k, p):
    """23-Nov: atomic write - another row's process never reads a half-written plan."""
    tmp = path(k) + f".tmp{os.getpid()}"
    json.dump(p, open(tmp, "w"), indent=1, ensure_ascii=False); os.replace(tmp, path(k))


def rejected_count(k):
    rj = os.path.join(PLAN_DIR, "rejected")
    return len(glob.glob(os.path.join(rj, f"{k}.*.json"))) if os.path.isdir(rj) else 0


def listing_fastening(spec):
    """What the LISTING says about fastening (title + Closure/Type fields) - the ground truth for the action check."""
    sp = spec.get("specifications", {})
    keys = [k for k in sp if k.lower() in ("closure", "type", "type for flats", "type for sandals", "type for slippers",
                                           "type for sports shoes", "type for casual shoes", "strap type", "clasp type")]
    txt = " ".join([spec.get("title", "")] + [str(sp[k]) for k in keys]).lower()
    has = lambda *w: any(x in txt for x in w)
    return {"laces": has("lace-up", "lace up", "laces", "lacing"),
            "velcro": has("velcro", "hook and loop", "hook & loop"),
            "buckle": has("buckle", "ankle loop", "ankle strap", "back strap"),
            "zip": has("zip"),
            "slip_on": has("flip flop", "flip-flop", "slipper", "slide", "clog", "slip-on", "slip on", "mule", "thong"),
            "text": txt}


def product_text(spec, family, variant, approach):
    """The ONLY product data that goes to OpenAI: listing title, brand, specs, description + the style requested."""
    sp = spec.get("specifications", {})
    lines = [f"PRODUCT (public Flipkart listing {spec.get('pid', '')})",
             f"Category family: {family.replace('_', ' ')}" + (f" ({variant}'s product)" if variant else ""),
             f"Title: {spec.get('title', '')}", f"Brand: {spec.get('brand', '')}", "Specifications:"]
    lines += [f"  {k}: {v}" for k, v in sp.items() if "address" not in k.lower() and k.lower() not in ("article number", "model id")]
    if spec.get("description"):
        lines.append(f"Description: {spec['description']}")
    lines.append("Listing photos: attached (Image 1 is the main photo).")
    lines.append("IMPORTANT (user 22-Nov): EVERY listing photo is a studio CLOSE-UP - its scale says nothing about the real size. Use the web "
                 "search tool to find this exact product's real dimensions and weight, pack contents and part counts, how people really hold "
                 "and use it, and real-life photos of it in a hand or a room (the listing, the brand's site, other retailers, reviews). Base "
                 "life_size, parts_visible, held_how and the scene on what you found, and name the sources in life_size.dimensions_source.")
    lines.append(f"PRESENTATION STYLE requested for this reel: approach {approach['letter']} '{approach['name']}' - "
                 f"use: {approach['main']} | push-in ends on: {approach['detail']}")
    return "\n".join(lines)


def photos(row_dir, slot, n=3):
    return sorted(glob.glob(os.path.join(row_dir, "products", f"p{slot}_*.jpg")))[:n]


def payload(text, photo_paths, family=None, letter=None):
    content = [{"type": "input_text", "text": text}]
    for p in photo_paths:
        b64 = base64.b64encode(open(p, "rb").read()).decode()
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"})
    body = {"model": MODEL, "instructions": RULEBOOK + family_rules(family, letter), "input": [{"role": "user", "content": content}],
            "reasoning": {"effort": env("OPENAI_REASONING", "low")},
            "max_output_tokens": int(env("OPENAI_MAX_OUTPUT", "18000"))}     # 23-Nov (user): 18k cap (thinking + answer); saved plans used 5.8k-15k     # 23-Nov (user: faster) - OPENAI_REASONING=medium/high for more care
    if WEB_TOOL:
        body["tools"] = [{"type": WEB_TOOL}]
    return body


def call(body):
    k = env("OPENAI_API_KEY")
    if not k:
        raise RuntimeError("no OPENAI_API_KEY (environment or pipeline .env)")
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"})
    for _try in range(20):
        try:
            with urllib.request.urlopen(req, timeout=1500) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code >= 500 and _try < 3:   # 23-Nov: a 5xx is a server failure (not a billed reply) - wait a minute, send again
                time.sleep(60); continue
            raise RuntimeError(f"OpenAI HTTP {e.code}: {e.read().decode(errors='ignore')[:600]}")
        except (socket.timeout, TimeoutError) as e:
            raise SentTimeout(f"OpenAI did not answer in 25 min ({e}) - it may have been accepted")
        except urllib.error.URLError as e:
            if not netwait.not_sent(e):
                if isinstance(getattr(e, "reason", None), (socket.timeout, TimeoutError)):
                    raise SentTimeout(f"OpenAI did not answer ({e}) - it may have been accepted")
                raise
            netwait.wait_for_network(API)    # DNS / refused / TLS: never reached OpenAI, not billed - wait, then send
    raise RuntimeError("OpenAI: network kept failing")


class SentTimeout(Exception):
    """The request was sent but no answer came: it may have been billed, so it is never re-sent automatically."""


def response_text(resp):
    st = resp.get("status")
    if st and st != "completed":   # 23-Nov: an incomplete / refused reply is a failure, never half a plan
        raise ValueError(f"OpenAI reply status '{st}' ({json.dumps(resp.get('incomplete_details') or resp.get('error'))[:200]})")
    if isinstance(resp.get("output_text"), str):
        return resp["output_text"]
    out = []
    for item in resp.get("output", []):
        for c in item.get("content", []) or []:
            if c.get("type") in ("output_text", "text") and c.get("text"):
                out.append(c["text"])
    return "\n".join(out)


def parse(text):
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("no JSON object in the reply")
    p = json.loads(text[a:b + 1])
    # 23-Nov: shape check before validate() (a string where an object is expected crashed the whole row's planning)
    if not isinstance(p, dict):
        raise ValueError("the reply is not a JSON object")
    for k_, t_ in (("product", dict), ("scene", dict)):
        if not isinstance(p.get(k_), t_):
            raise ValueError(f"'{k_}' is missing or not an object")
    sc = p["scene"]
    if not isinstance(sc.get("acceptable_rooms", []), list):
        raise ValueError("scene.acceptable_rooms is not a list")
    if not isinstance(p["product"].get("life_size", {}), dict):
        raise ValueError("product.life_size is not an object")
    return p


# ---------------------------------------------------------------------------------------------------------------- checks
SIDE_OK = re.compile(r"(her|his|their|person's|the person's|screen|viewer's|own)\s+(\w+\s+)?$", re.I)


def shots_of(plan):
    """The shot variants of a plan (older single 'shot' plans are read as one variant)."""
    v = plan.get("shots") if isinstance(plan.get("shots"), list) else [plan["shot"]] if isinstance(plan.get("shot"), dict) else []
    return [x for x in v if isinstance(x, dict)]


def _texts(s):
    t = [s.get("start_state", ""), s.get("end_state", ""), s.get("action_summary", ""), s.get("push_in_target", "")]
    for b in s.get("beats", []) or []:
        t += [str(b.get(x, "")) for x in ("moves", "movement", "contact", "still", "product_state", "camera", "gaze")]
    return " | ".join(t)



PHOTO_FAMILIES = {"home_decor", "home_furnishing", "kitchen", "household_utility"}   # 23-Nov (user): the no-person room shot is for HOME only
PHOTO_RULES = """
PRODUCT-PHOTO VARIANT (this family only, user 22-Nov): besides the 2 person variants, add EXACTLY ONE product-photo variant with
"no_person": true. Its first frame is the ORIGINAL LISTING PHOTO of the product (cleaned: plate_cleanup says what to remove -
stickers, text overlays, watermarks, other products - and how to extend its background to 9:16), with NO person, no hand and no
arm anywhere. ONLY the camera moves (a slow push-in from photo_wide or photo_mid to photo_mid or photo_close, 0 to 4 s):
nothing in the picture moves on its own - no swaying, fluttering, light shift, rotation or sliding ("ambient" is always "none"). The product, its colours, size against
its surroundings and every part stay exactly as in the photo; nothing appears, moves into place, peels, opens or changes.
Framings for it are photo_wide, photo_mid, photo_close only. movement_type "camera". Write its beats (moves = camera) in the
same detail. The other 2 variants keep the person. The reel always keeps at least one avatar shot.
"""

SELF_MOVE = re.compile(r"\b(sways?|swaying|flutter\w*|swings?|swinging|rotat\w*|spins?|spinning|turns? (on|by) (its|itself)|slides?|sliding|rolls?|rolling|drifts?|floats?|waves?|ripples?|shimmers?|sparkles?|twinkles?|glows?|flicker\w*|breathes?|moves? (by itself|on its own))\b")
PERSON_WORDS = re.compile(r"\b(person|someone|hands?|fingers?|arms?|palm|thumb)\b")   # artwork words (girl, boy, face ...) describe the product, not a person


def validate_photo_shot(sh, plan, family):
    """22-Nov: a product-photo shot (no person): the listing photo as the first frame, camera-only motion."""
    E, W = [], []
    if family not in PHOTO_FAMILIES:
        E.append(f"no_person (product-photo) shots are only for {sorted(PHOTO_FAMILIES)}")
    fs, fe = sh.get("framing_start"), sh.get("framing_end")
    if fs not in ("photo_wide", "photo_mid", "photo_close") or fe not in ("photo_wide", "photo_mid", "photo_close"):
        E.append(f"a product-photo shot uses only photo_wide / photo_mid / photo_close (got {fs} -> {fe})")
    elif FRAMINGS[fe] <= FRAMINGS[fs]:
        E.append("the product-photo shot must end closer than it starts (push-in)")
    if len(str(sh.get("plate_cleanup", ""))) < 15:
        E.append("plate_cleanup is missing (what to remove from the listing photo and how to extend it to 9:16)")
    beats = sorted(sh.get("beats", []), key=lambda b: float(b.get("t_start", 0)))
    try:
        t = 0.0
        for b in beats:
            if abs(float(b["t_start"]) - t) > 0.06:
                E.append(f"beats have a gap or overlap at {t:.1f} s"); break
            t = float(b["t_end"])
        if abs(t - 4.0) > 0.06:
            E.append(f"beats end at {t:.1f} s, not 4.0 s")
    except (KeyError, TypeError, ValueError):
        E.append("beats need numeric t_start and t_end")
    if str(sh.get("ambient", "none")).strip().lower() not in ("none", "", "nothing", "n/a"):
        E.append("ambient must be 'none': nothing moves on its own in a product-photo shot, only the camera")
    for b in beats:
        if str(b.get("moves", "")).strip().lower() not in ("camera", "nothing", "none"):
            E.append(f"beat {b.get('t_start')}-{b.get('t_end')}: only the camera may move, got '{b.get('moves')}'")
        if SELF_MOVE.search(re.sub(r"\bcamera\s+(?:\w+\s+){0,2}(rolls?|slides?|glides?|drifts?|waves?)\b", "", re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", str(b.get("movement", "")).lower()))):
            E.append(f"beat {b.get('t_start')}-{b.get('t_end')}: something in the picture moves on its own ({SELF_MOVE.search(str(b.get('movement', '')).lower()).group(0)}) - only the camera moves")
    txt = " ".join([str(sh.get(k, "")) for k in ("start_state", "end_state", "action_summary", "ambient")] +
                   [" ".join(str(b.get(x, "")) for x in ("movement", "contact")) for b in beats]).lower()
    txt = re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", txt)
    if PERSON_WORDS.search(txt):
        E.append("a product-photo shot has no person, hand or arm - remove: " + PERSON_WORDS.search(txt).group(0))
    mv_ = re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", " ".join([str(sh.get("action_summary", ""))] + [str(b.get("movement", "")) for b in beats]).lower())
    if re.search(r"\b(peels?|peeling|opens?|opening|appears?|slides? in|moves? into place|assembles?|unfolds?|fades? in)\b", mv_):
        E.append("the product must not change, open, peel or appear in a product-photo shot")
    return E, W



LOCK_FAMILIES = {"home_decor", "home_furnishing", "kitchen", "household_utility", "baby_care", "grooming", "fragrance", "fashion_wearables",
                 "footwear", "ethnic", "everyday_clothing"}   # 23-Nov (user): every rule covers EVERY category
_STATE_VERBS = (r"(sets?|puts?|places?|lays?|drops?|picks?|removes?|takes?|pulls?|hands?|passes?|opens?|closes?|unscrews?|screws?|pops?|"
                r"unwraps?|peels?|pours?|fills?|empties|installs?|attaches?|detaches?|snaps?|flips?|lifts?|raises?|lowers?)")
_STATE_OBJ = (r"(product|pack|packet|bottle|jar|tube|cover|cap|lid|cloth|towel|tray|box|toy|pacifier|soother|nibbler|feeder|sac|latch|"
              r"ring|handle|decal|sticker|item|pump|teat|nipple|cup|bowl|spoon|brush|comb|razor)")
STATE_CHANGE = re.compile(r"\b" + _STATE_VERBS + r"\b(?:\s+(?:up|down|off|out|away|aside|back|over))?\s+(?:(?:the|her|his|a|an|one|that|this)\s+)?(?:[\w\-]+\s+){0,2}" + _STATE_OBJ + r"\b")


def _limbs(left, right, head, torso):
    return dict(left_hand_arm=left, right_hand_arm=right, left_leg_foot="out of frame", right_leg_foot="out of frame",
                head_gaze=head, torso=torso, arms_in_frame=2, hands_in_frame=2, legs_in_frame=0)


def safe_shot(plan, idx=0):
    """A shot that cannot break the first-frame = last-frame rule: ONE out-and-back movement of ONE limb, everything else still.
    Used when no variant of the OpenAI plan is safe (home families only). Written in code, so it is always valid."""
    pr = plan.get("product", {}); sc = plan.get("scene", {}) if isinstance(plan.get("scene"), dict) else {}
    mount = sc.get("mount") if isinstance(sc.get("mount"), dict) else None
    sf = sc.get("surface") if isinstance(sc.get("surface"), dict) else {}
    surf = str(sf.get("name") or "the surface")
    item = str(pr.get("category_item") or "product")[:40]
    dims = cm_values(str(pr.get("life_size", {}).get("dimensions_cm", "")))
    big = max(dims) if dims else 20.0
    wall = bool(mount) and mount.get("type") in ("wall", "hanging")
    fam_ = str((plan.get("_meta") or {}).get("family", ""))
    feet = fam_ == "footwear" or bool(re.search(r"\b(shoe|sandal|slipper|sneaker|heel|boot|loafer|mule|clog|chappal|flip.?flop|slide|footwear)s?\b", str(pr.get("type", "")).lower()))
    kind = "decal" if wall else ("worn_feet" if pr.get("use_kind") == "worn" and feet else "worn_body" if pr.get("use_kind") == "worn"
                                 else ("held" if big <= 45 else "surface"))
    v = idx % 3
    still = "every object stays perfectly still while she moves naturally"
    hero = plan.get("hero") if isinstance(plan.get("hero"), dict) else {}
    ready = (f" The {item} is already READY FOR USE in this first frame: {hero.get('ready_state')}; its main thing - {hero.get('main_thing')} - "
             f"faces the camera, large and sharp.") if hero.get("ready_state") else ""
    ff = "wall_close" if kind == "decal" else "knee_down" if kind == "worn_feet" else "waist_up"
    if kind == "worn_feet":   # 23-Nov: footwear worn - only toes up, heel up or a weight shift (legs never rotate)
        floor = surf if surf != "the surface" else "the floor"
        start = (f"Knee-down. She stands on {floor} wearing the {item}, feet parallel and pointing at the camera, both knees in frame, "
                 f"both soles flat with weight; her hands rest at her sides out of frame.")
        out_txt, back_txt, mtype = [("the toes of her right foot lift 4 cm with the heel staying down", "the toes lower back flat", "toe_raise"),
                                    ("the heel of her right foot lifts 4 cm with the toes staying down", "the heel lowers back flat", "heel_lift"),
                                    ("her weight shifts slowly onto her right foot, the left heel lifting 2 cm", "her weight shifts back to both feet, both soles flat", "weight_shift")][idx % 3]
        who, summary = "her right foot", f"She shows the {item} with one small foot movement and back."
        right0 = "out of frame"; sup = f"{floor} (the shoes are worn)"; head = "out of frame"; torso = "out of frame"; pushin = f"the {item} on her right foot"
    elif kind == "worn_body":   # 23-Nov: clothing / wearables worn - she feels it, never takes it off or puts it on
        start = (f"Waist-up. She wears the {item} exactly as listed, standing relaxed in {surf if surf != 'the surface' else 'the room'}; her right "
                 f"hand rests on the {item} where it is worn; her left arm hangs straight down; a warm natural smile, eyes on the {item}.")
        out_txt, back_txt, mtype = [("her right palm smooths slowly 10 cm along the fabric/surface of the item where it is worn", "the palm glides back to where it started", "touch_glide"),
                                    ("her right fingertips feel the item's edge or texture, gliding 6 cm along it", "the fingertips glide back to where they started", "touch_trace"),
                                    ("she turns her shoulders 15 degrees to her left to show the side of the item, feet planted", "she turns back to the front", "present")][idx % 3]
        who, summary = "her right hand", f"She feels the {item} she is wearing and returns to the start."
        right0 = "rests on the worn item"; sup = "she wears it"; head = "turned a little toward the item, eyes on it"; torso = "relaxed, a small natural weight shift"
        pushin = f"the {item} where her hand is"
    elif kind == "decal":       # user 22-Nov: a close-up BESIDE the wall item, touching it - never in front of it, never pointing
        v = idx % 5
        start = (f"Close-up beside the wall. The camera is 1.0 m from {surf}, facing it straight on; the {item} is already on the wall in "
                 f"its final place and fills the right two-thirds of the frame; she stands at the LEFT edge of the frame in profile, close to "
                 f"the wall and BESIDE the {item} (never in front of it); only her shoulder, the side of her face and her right arm are "
                 f"visible; her right hand rests on the {item}'s surface; her left arm hangs straight down out of frame; soft closed smile, "
                 f"eyes on the {item}.")
        touch = [("touch_glide", "her flat right palm", "glides slowly 10 cm to her right across the surface, staying in contact, feeling the smooth finish", "glides back the same 10 cm to exactly where it started"),
                 ("touch_trace", "her right index fingertip", "traces slowly 8 cm along one line of the artwork, in contact with it", "traces back the same 8 cm to exactly where it started"),
                 ("touch_smooth", "her right thumb and index fingertip", "smooth slowly 4 cm along the item's lower edge, in contact with it", "smooth back the same 4 cm to exactly where they started"),
                 ("touch_brush", "the backs of her right fingers", "brush lightly 10 cm across the surface, feeling its texture", "brush back the same 10 cm to exactly where they started"),
                 ("touch_press", "her right fingertips", "press lightly 1 cm into the surface in the same spot", "ease off to the light touch they started with")][v]
        mtype, who, o_, b_ = touch
        out_txt, back_txt = f"{who} {o_}", f"{who} {b_}"
        summary = f"She feels the {item} by touch ({mtype.replace('touch_', '')}) and returns to the start."
        right0 = "rests on the item's surface, still"; sup = f"{surf} (the {item} is stuck on it)"
        head = "in profile, turned toward the item, eyes on it"; torso = "still, in profile beside the wall"
        pushin = f"the {item} under her hand"
    elif kind == "held":
        start = (f"Waist-up. She faces the camera and holds the {item} in her right hand at chest height by its sturdiest part, its front label to "
                 f"the camera - hand, wrist and forearm fully in frame; {surf} is behind her; her left arm hangs straight down along her body, "
                 f"fingers relaxed; a warm natural smile, eyes on the product (she glances at the camera only once).")
        if v == 0:
            out_txt = "her right wrist turns the hand and the product together 30 degrees to her left, then 30 degrees to her right"
            back_txt = "the wrist turns back to the front"
            mtype, who, summary = "hand_turn", "her right wrist", f"She turns the {item} 30 degrees each way and back to the front."
        elif v == 2:
            out_txt = "her right hand brings the product 10 cm toward the camera and 5 cm up, showing it proudly, while she looks from it to the lens"
            back_txt = "the hand carries it back the same way to exactly where it started"
            mtype, who, summary = "lift_and_show", "her right hand and forearm", f"She brings the {item} toward the camera and back."
        else:
            out_txt = "her right wrist tilts the top of the product 25 degrees toward the camera while she glances down at it"
            back_txt = "the wrist tilts back to level and she looks back at the lens"
            mtype, who, summary = "tilt", "her right wrist", f"She tilts the {item} 25 degrees toward the camera and back."
        right0 = "holds the product at chest height, label to camera, still"; sup = "her right hand"
        head = "turned a little toward the product, eyes on it"; torso = "relaxed, a small natural weight shift"
        pushin = hero.get("must_see") or f"the {item} label"
    else:
        start = (f"Waist-up. She stands facing the camera behind {surf}; the {item} rests on it in front of her in its final place; her right hand "
                 f"rests flat on {surf} 20 cm to the right of the {item}, not touching it; her left arm hangs straight down along her body; "
                 f"a warm natural smile, eyes on the product (she glances at the camera only once).")
        if v == 2:
            out_txt = f"her right fingertips glide 10 cm along the top edge of the {item}, feeling it, while she looks at it"
            back_txt = "the fingertips glide back to exactly where they started and she looks back at the lens"
            mtype, who, summary = "touch_trace", "her right fingertips", f"She runs her fingertips along the {item} and back."
        elif v == 1:
            out_txt = f"her open right palm glides 12 cm over the {item}'s surface, feeling it, while she looks down at it"
            back_txt = "the palm glides back to exactly where it started and she looks back at the lens, smiling"
            mtype, who, summary = "touch_glide", "her right palm", f"She feels the {item} with her palm and back."
        else:
            out_txt = f"her right hand slides 12 cm toward the {item} along {surf} and her fingertips rest on its nearest edge, while she looks at it"
            back_txt = "the hand slides back to exactly where it started and she looks back at the lens, smiling"
            mtype, who, summary = "present", "her right hand", f"She reaches to the {item}, touches it and back."
        right0 = f"rests flat on {surf} 20 cm to the right of the product, still"; sup = f"{surf}"
        head = "turned a little toward the product, eyes on it"; torso = "relaxed, a small natural weight shift"
        pushin = f"the {item}"
    fing = {"worn_feet": "out of frame", "worn_body": "palm flat on the item, fingers together; they move only as the movement says, no finger lifts or spreads", "decal": "thumb relaxed beside the index finger, not touching; the fingers named in the movement keep the same shape all the way (no finger lifts, spreads or curls); the others stay still, gently curved",
            "held": "thumb on the front of the product, index, middle and ring fingers wrapped round the back, little finger under it - the grip never changes, no finger lifts or slides",
            "surface": "palm flat, all five fingers straight and together, resting on the surface; no finger lifts, spreads or taps"}[kind]
    lt = "hangs straight down along her body, out of frame" if kind == "decal" else "hangs straight down along her body, fingers relaxed, still"
    na = 1 if kind == "decal" else 2
    mk = lambda t0, t1, moves, mv, rh, prod: dict(
        t_start=t0, t_end=t1, moves=moves, movement=mv, contact="none beyond what the first frame already shows", support=sup,
        still=still, product_state=prod, camera="one smooth continuous dolly-in from 0.0 s, a little faster after 2.5 s, no shake",
        gaze=head, limbs=dict(_limbs(lt, rh, head, torso), arms_in_frame=na, hands_in_frame=na),
        everything=dict(
            head=("natural small movement: tilts about 8 degrees toward the product while she looks at it, then back toward the camera"
                  if moves not in ("nothing", "camera") else "natural small movement, facing as in the first frame"),
            eyes="alive: on the product most of the time, ONE natural glance to the camera near the end, natural blinks - never a fixed stare",
            mouth="a soft smile that widens a little - no talking", hair="moves only with her head, every strand attached",
            shoulders="natural breathing, relaxed, moving slightly with the action", torso="natural breathing and a small weight shift - " + torso, hips="still" if kind != "decal" else "out of frame",
            left_arm=("out of frame" if kind == "decal" else "still - " + lt), left_hand_fingers=("out of frame" if kind == "decal" else "still, relaxed and slightly curled"),
            right_arm=("the forearm and wrist carry the hand exactly as described in the movement, the upper arm and shoulder do not move"
                       if moves not in ("nothing", "camera", "her eyelids") else "still, " + rh),
            right_hand_fingers=(("move with the hand as described, keeping their shape - " + fing) if (kind in ("decal", "surface", "worn_body") and moves not in ("nothing", "camera", "her eyelids")) else ("out of frame" if kind == "worn_feet" else "still - " + fing)),
            left_leg_foot=("still, sole flat with weight, pointing at the camera" if kind == "worn_feet" else "out of frame"),
            right_leg_foot=(("moves only as described - " + out_txt) if (kind == "worn_feet" and moves not in ("nothing", "camera")) else ("still, sole flat with weight" if kind == "worn_feet" else "out of frame")),
            clothing="still, sleeves and hem keep every fold; nothing sways",
            product=("moves only together with her hand and wrist exactly as described, the grip never changes" if (kind == "held" and moves not in ("nothing", "camera", "her eyelids")) else "still - " + prod + (", held by her right hand" if kind == "held" else "")),
            product_parts="still - every cap, lid, part and label exactly as in the first frame - nothing opens, moves or changes",
            props="still, every prop exactly in its place", surface="still - " + sup, background="still - the room, furniture and wall unchanged",
            light="constant - no flicker or change", camera="moving: one smooth continuous dolly-in toward the push-in target from 0.0 s, no shake"),
        fingers=dict(left=("out of frame" if kind == "decal" else "all five fingers relaxed and slightly curled, thumb resting against the index finger, none moves"),
                     right=fing))
    beats = [
        mk(0.0, 0.8, "nothing", f"Everything holds still for a moment exactly as in the first frame: her right arm stays where it is, her left arm hangs straight down, her head and torso do not move and the {item} stays exactly where it is.", right0, f"the {item} in its place, unchanged"),
        mk(0.8, 1.6, who, f"Slowly, over 0.8 s, {out_txt}; {still}.", "moving as described", f"the {item} unchanged"),
        mk(1.6, 2.5, who, f"Slowly, over 0.9 s, {back_txt}; it ends in exactly the same place and pose as at 0.0 s; {still}.", right0, f"the {item} unchanged"),
        mk(2.5, 4.0, "camera", "The camera pushes slowly and steadily straight in on the product; every object, both arms and the product stay exactly where they were at 0.0 s, nothing moves, nothing appears.", right0, f"the {item} unchanged"),
    ]
    return dict(framing_start=ff, framing_end="product_close", start_state=start + ready,
                last_frame=dict(change="none", changed_region="none", identical="everything", push_in=dict(zoom=1.25, target=pushin)),
                end_state="Identical to the first frame - the same objects, the same pose of both arms and of the product - only the camera is closer.",
                push_in_target=pushin, action_summary=summary + " One clear out-and-back movement; she stays natural and alive, the camera glides in throughout.", action_end_s=2.5,
                movement_type=mtype, counts="one out-and-back movement", beats=beats, no_person=False, safe=True,
                camera_plan=dict(start="the start framing position, level, phone main lens, everything sharp",
                                 move="one smooth continuous dolly-in for the whole 4 s, gentle during the action and a little faster after 2.5 s; no pan, tilt, roll, zoom-lens or shake",
                                 end="about 1.25x closer, the product large and the room around it still visible"))


_EK = ("head", "eyes", "mouth", "hair", "shoulders", "torso", "hips", "left_arm", "left_hand_fingers", "right_arm", "right_hand_fingers",
       "left_leg_foot", "right_leg_foot", "clothing", "product", "product_parts", "props", "surface", "background", "light", "camera")


def fill_routine(sh):
    """23-Nov (user: faster): OpenAI writes only what moves; the code fills every part it left out as still, so every prompt still
    carries the full 21-part checklist, both hands' fingers and all six limbs."""
    for b in sh.get("beats", []) or []:
        ev = b.get("everything") if isinstance(b.get("everything"), dict) else {}
        ev.pop("_note", None)
        for k in _EK:
            if not str(ev.get(k, "")).strip():
                ev[k] = "locked" if k == "camera" and float(b.get("t_end", 0) or 0) <= 0 else ("still" if k != "camera" else (b.get("camera") or "moving as the camera plan says"))
        b["everything"] = ev
        fg = b.get("fingers") if isinstance(b.get("fingers"), dict) else {}
        for k in ("left", "right"):
            if not str(fg.get(k, "")).strip():
                fg[k] = "still - all five fingers keep their shape, none lifts, spreads or curls"
        b["fingers"] = fg
        lb = b.get("limbs") if isinstance(b.get("limbs"), dict) else {}
        for k in ("left_hand_arm", "right_hand_arm", "left_leg_foot", "right_leg_foot", "head_gaze", "torso"):
            if not str(lb.get(k, "")).strip():
                lb[k] = ev.get({"left_hand_arm": "left_arm", "right_hand_arm": "right_arm", "head_gaze": "head"}.get(k, k), "still")
        lb.setdefault("arms_in_frame", 2); lb.setdefault("hands_in_frame", 2); lb.setdefault("legs_in_frame", 0)
        b["limbs"] = lb


HANDLING_FAMILIES = {"baby_care", "fragrance", "grooming", "home_decor", "kitchen", "household_utility"}
_PART = r"(cap|lid|pump|top|nozzle|flap|seal|zip|zipper|cover|stopper|pack|packet|pouch|box|bottle|jar|tube|tub|wipe|wipes|tissue|sachet|carton|case)"
_DET = r"(?:(?:the|its|her|his|a|an|one|that|this)\s+)?(?:[\w-]+\s+){0,2}"
HANDLING_BAD = re.compile(
    r"\b(pick(s|ed|ing)? (it |them |" + _DET + r"[\w-]+ )?up|lift(s|ed|ing)? (?!(?:her |his |the |its |one |an? )?(?:index |middle )?(?:finger|fingertip|fingers|fingertips|hand|palm|thumb)\b)(it |" + _DET + r"[\w-]+ )?(up )?(off|from|out of)|"
    r"(put|set)(s|ting)? (it |them |" + _DET + r"[\w-]+ )?(down|back)|plac(es|ed|ing) (it|them|the|her|his)\b|"
    r"(hands|handed|handing|passes|passed|passing) (it|them|the [\w-]+) (to|over|into)|switch(es|ed|ing)? hands|(other|second) hand takes|"
    r"(opens|opened|opening|open (?=it|the|its|her|his)|closes|closing|close (?=it|the|its)|unscrew\w*|screw\w* (?=on|off|the)|twist\w*|"
    r"pops?|popping|flips?|flipping|remov\w*|unzip\w*|unseal\w*|tears?|tearing|unwrap\w*|peel\w*) (it |them )?(open |off |up )?" + _DET + _PART + r"|"
    r"" + _PART + r" (opens|is opened|comes off|is removed|pops)|"
    r"(pull|draw|take|tak)\w* (out|up)? ?" + _DET + r"(wipe|wipes|tissue|sheet|item|one)|(pull|draw|take)s? (it |them )?out|"
    r"pour\w*|squeez\w* out)\b")
_NEG = re.compile(r"\b(no|zero|without|never|not|nothing|nobody|avoid\w*|instead of|rather than)\b[^.;|]*")


def handling_errors(sh, family):
    """Rule 50 (23-Nov, Day 6 QC): one structured handling contract, checked in code on EVERY beat, not only the last frame."""
    if family not in HANDLING_FAMILIES or sh.get("safe") or sh.get("no_person"):
        return []
    txt = " | ".join([str(sh.get("action_summary", ""))] + [" ".join(str(b_.get(k_, "")) for k_ in ("movement", "moves", "product_state"))
                                                             for b_ in sh.get("beats", []) if isinstance(b_, dict)]).lower()
    txt = _NEG.sub("", txt)
    hits = sorted({m.group(0) for m in HANDLING_BAD.finditer(txt)})
    return [f"rule 50 handling contract: '{', '.join(hits[:4])}' inside the 4 s take - start with the product already held in a full "
            f"grip (or resting on the surface) in its ready state; nothing is picked up, put down, opened or pulled out"] if hits else []


def validate_shot(sh, plan, spec, family):
    """Errors/warnings of ONE shot variant."""
    E, W = [], []
    fill_routine(sh)
    for k in ("framing_start", "framing_end", "start_state", "end_state", "push_in_target", "action_summary", "beats"):
        if not sh.get(k):
            E.append(f"shot.{k} missing")
    if E:
        return E, W
    if sh.get("safe"):          # built in code: one out-and-back movement of one limb - always valid
        return E, W
    if sh.get("no_person"):
        return validate_photo_shot(sh, plan, family)
    E += handling_errors(sh, family)
    for b_ in sh["beats"]:
        if str(b_.get("moves", "")).strip().lower() not in ("nothing", "none", "") and len(str(b_.get("movement", "")).split()) < 20:
            W.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: movement is under 20 words - describe hand, fingers, path, cm and speed in more detail")
    _mt = ((plan.get("scene") or {}).get("mount") or {}) if isinstance((plan.get("scene") or {}).get("mount"), dict) else {}
    if family == "home_decor" and _mt.get("type") in ("wall", "hanging") and not sh.get("safe"):      # 22-Nov: wall decor = touch close-up
        if sh.get("framing_start") != "wall_close" or not str(sh.get("movement_type", "")).lower().startswith(("touch", "hold")):
            E.append("wall decor is shown ONLY as a touch close-up (framing wall_close, movement_type touch_* , the avatar beside the wall, never in front of it) or as a product-photo shot")
        if re.search(r"\b(points?|pointing|presents?|presenting|gestures?|open palm)\b", " ".join([str(sh.get("action_summary", ""))] + [str(b_.get("movement", "")) for b_ in sh["beats"]]).lower()):
            E.append("the avatar never points at or presents the wall - she touches it")
    lf_ = sh.get("last_frame")
    if family in LOCK_FAMILIES and not sh.get("safe"):
        if not isinstance(lf_, dict):
            (E if plan.get("schema_version", 1) >= 4 else W).append("last_frame plan missing (rule 36)")
        else:
            _chg = str(lf_.get("change", "")).strip().lower()
            if _chg not in ("none", "") and (STATE_CHANGE.search(_chg) or len({m_ for m_ in re.findall(r"\b(left|right)\b", _chg)}) > 1):
                E.append("last_frame.change moves or changes an object, or changes both sides - one limb or the product only")
            try:
                _z = float((lf_.get("push_in") or {}).get("zoom", 1.4))
                if not 1.15 <= _z <= 1.3:
                    W.append(f"last_frame.push_in.zoom {_z} is outside 1.15-1.3 - it is clamped (the room stays visible)")
            except (TypeError, ValueError):
                E.append("last_frame.push_in.zoom must be a number")
            _le = lf_.get("limbs_end") if isinstance(lf_.get("limbs_end"), dict) else {}
            for _k in ("arms_in_frame", "hands_in_frame"):
                try:
                    if int(_le.get(_k, 0)) > 2:
                        E.append(f"last_frame.limbs_end.{_k} is more than 2")
                except (TypeError, ValueError):
                    pass
            if _chg not in ("none", "") and (len(str(lf_.get("identical", ""))) < 20 or len(str(lf_.get("edit_prompt", ""))) < 40):
                E.append("last_frame needs 'identical' and 'edit_prompt' when something changes")
    if family in LOCK_FAMILIES and family != "footwear" and not sh.get("safe") and not sh.get("no_person"):   # user 23-Nov: "everything feels too still"
        _act = " ".join([str(sh.get("action_summary", ""))] + [str(b_.get("movement", "")) for b_ in sh["beats"]]).lower()
        _cm = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:-|–)?\s*(?:\d+(?:\.\d+)?)?\s*cm\b", _act)]
        _dg = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*(?:deg|degrees|°)", _act)]
        if re.search(r"\b(tiny|slight(ly)?|subtle|minimal|barely|micro|imperceptible|holds? (it )?still|blinks? once)\b", str(sh.get("action_summary", "")).lower()) \
                or ((_cm or _dg) and max(_cm or [0]) < 5 and max(_dg or [0]) < 15):
            E.append("the action is too small - the video looks stationary (rule 41): use a clearly visible out-and-back movement (30-degree turn, 10 cm lift, 10-12 cm glide)")
    if family in LOCK_FAMILIES and not sh.get("safe"):     # 22-Nov: first frame = last frame, only closer
        if sh.get("framing_start") not in ("full_body", "knee_up", "waist_up", "shoulders_up", "wall_close") + (("knee_down",) if family == "footwear" else ()):
            E.append(f"start framing '{sh.get('framing_start')}' hides the person's body - start at full_body, knee_up, waist_up or shoulders_up so no arm comes from nowhere")
        _lt = re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", " ".join(
            [str(sh.get("action_summary", ""))] + [" ".join(str(b_.get(x, "")) for x in ("movement", "contact", "product_state")) for b_ in sh["beats"]]).lower())
        _m = STATE_CHANGE.search(_lt)
        if _m:
            E.append(f"the action moves or changes something ('{_m.group(0)[:50]}') - first frame = last frame: out-and-back movements only, nothing set down, lifted, opened or moved")
    # 22-Nov: every beat states what EVERY limb does (schema_version 3 = error, older plans = warning)
    _sv3 = plan.get("schema_version", 1) >= 3
    _bad = []
    try:
        _ae = float(sh.get("action_end_s", 2.5))
    except (TypeError, ValueError):
        _ae = 2.5
    for b_ in sh["beats"]:
        try:
            if float(b_.get("t_start", 0)) >= _ae - 0.05:
                continue
            if float(b_.get("t_end", 0)) - float(b_.get("t_start", 0)) > 1.0 + 1e-6:
                _long = float(b_.get("t_end", 0)) - float(b_.get("t_start", 0)) > 1.6 + 1e-6
                _msg = f"beat {b_.get('t_start')}-{b_.get('t_end')} is longer than 1.0 s inside the action (split it so every second says what each limb does)"
                (_bad if _long else W).append(_msg)   # 1.0-1.6 s with all limbs filled is a warning, over 1.6 s an error
        except (TypeError, ValueError):
            pass
        lb = b_.get("limbs") if isinstance(b_.get("limbs"), dict) else {}
        miss = [k for k in ("left_hand_arm", "right_hand_arm", "left_leg_foot", "right_leg_foot", "head_gaze", "torso") if not str(lb.get(k, "")).strip()]
        if miss:
            _bad.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: limbs missing {miss}")
        for ck, mx in (("arms_in_frame", 2), ("hands_in_frame", 2), ("legs_in_frame", 2)):
            try:
                if lb and int(lb.get(ck, 0)) > mx:
                    E.append(f"beat {b_.get('t_start')}: {ck} = {lb.get(ck)} (a person has at most {mx})")
            except (TypeError, ValueError):
                _bad.append(f"beat {b_.get('t_start')}: {ck} must be a number")
    (E if _sv3 else W).extend(_bad[:6])
    _ek = ("head", "eyes", "mouth", "hair", "shoulders", "torso", "hips", "left_arm", "left_hand_fingers", "right_arm", "right_hand_fingers",
           "left_leg_foot", "right_leg_foot", "clothing", "product", "product_parts", "props", "surface", "background", "light", "camera")
    _eb = []
    for b_ in sh["beats"]:
        ev_ = b_.get("everything") if isinstance(b_.get("everything"), dict) else {}
        miss_ = [k_ for k_ in _ek if not str(ev_.get(k_, "")).strip()]
        if miss_:
            _eb.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: 'everything' misses {miss_[:6]}{'...' if len(miss_) > 6 else ''} (rule 39)")
    (E if plan.get("schema_version", 1) >= 6 else W).extend(_eb[:3])
    _sv5 = plan.get("schema_version", 1) >= 5
    _fb = [f"beat {b_.get('t_start')}-{b_.get('t_end')}: 'fingers' missing for a hand (finger-by-finger detail, rule 38)" for b_ in sh["beats"]
           if not (isinstance(b_.get("fingers"), dict) and str(b_["fingers"].get("left", "")).strip() and str(b_["fingers"].get("right", "")).strip())]
    if not (isinstance(sh.get("camera_plan"), dict) and all(str(sh["camera_plan"].get(k_, "")).strip() for k_ in ("start", "move", "end"))):
        _fb.append("camera_plan (start / move / end) missing (rule 38)")
    (E if _sv5 else W).extend(_fb[:4])
    # 22-Nov: a lid/cap/cover changes state ONLY through a declared part_states change done by a named hand
    _ps = plan.get("part_states") if isinstance(plan.get("part_states"), list) else []
    _changing = [str(x.get("part", "")).lower() for x in _ps if isinstance(x, dict) and str(x.get("start", "")).strip().lower() != str(x.get("end", "")).strip().lower()]
    _lid = re.compile(r"\b(lid|cap|cover|flap|stopper|cork|hood|teat cap|top)\b[^.;|]{0,25}\b(open\w*|clos\w*|pops?|popp\w*|flips?|flip\w*|unscrew\w*|screw\w*|twist\w*|snaps?|slides? (off|open|shut)|comes? off|falls?|lifts?|lift\w*|removed?|put (back )?on)\b"
                      r"|\b(open\w*|clos\w*|uncap\w*|unscrew\w*|snaps?|pops?|flips?)\b[^.;|]{0,25}\b(lid|cap|cover|flap|stopper|cork|hood)\b")
    for b_ in sh["beats"]:
        _t = re.sub(r"\b(no|without|never|not|nothing|stays?|remains?|keeps?)\b[^.;|,]*", "", " ".join(str(b_.get(x, "")) for x in ("movement", "contact", "product_state")).lower())
        _m = _lid.search(_t)
        if _m:
            _hand = re.search(r"\b(hand|thumb|finger|fingers|fingertip|palm)\b", str(b_.get("moves", "")).lower() + " " + _t)
            if not _changing or family in LOCK_FAMILIES:
                E.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: a lid/cap changes state ('{_m.group(0)}') but part_states does not declare it - a lid never opens or closes on its own; declare it with the hand action or remove it")
            elif not _hand:
                E.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: a lid/cap changes state ('{_m.group(0)}') with no hand doing it")
    # 22-Nov: nothing appears out of nowhere - every table/shelf/prop named later was already in the first frame
    _NOUN = r"(table|shelf|stool|tray|bench|counter|chair|sofa|bed|cabinet|rack|stand|box|basket|bag|plant|vase|mat|rug|cushion|pillow|towel|bottle|jar|cup|bowl|mirror|frame|lamp|drawer|trolley|cart|crate)"
    _sc = plan.get("scene") if isinstance(plan.get("scene"), dict) else {}
    _first = " ".join([str(sh.get("start_state", "")), json.dumps(_sc, ensure_ascii=False), json.dumps(plan.get("prerequisites", ""), ensure_ascii=False),
                       str(plan.get("product", {}).get("type", "")), str(plan.get("product", {}).get("held_how", ""))]).lower()
    _later = " ".join([str(sh.get("end_state", ""))] + [" ".join(str(b_.get(x, "")) for x in ("contact", "support", "product_state")) for b_ in sh["beats"]]).lower()
    _later = re.sub(r"\b(no|without|never|not|nothing|any other)\b[^.;|,]*", "", _later)
    _new = sorted({m.group(1) for m in re.finditer(r"\b" + _NOUN + r"s?\b", _later)
                   if not re.search(r"\b" + m.group(1) + r"s?\b", _first)})
    if _new:
        E.append("appears out of nowhere: " + ", ".join(_new) + " is used later in the shot but is not in the first frame (start_state / scene) - put it in the first frame or remove it")
    if family != "footwear":     # 22-Nov row 510: the person walked toward the camera during the push-in
        for b_ in sh["beats"]:
            _w = re.sub(r"\b(no|zero|without|never|not|nothing|avoid\w*)\b[^.;|]*", "", " ".join(str(b_.get(x, "")) for x in ("moves", "movement")).lower())
            if re.search(r"\b(steps?|stepping|walks?|walking|strides?|approach(es|ing)?|comes? closer|moves? closer|leans? (in|forward|toward))\b", _w):
                E.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: the person steps, walks or comes closer - she stays on her spot, only the camera moves")
                break
    # 22-Nov (user): no table / sliding table / object enters the frame, nothing floats in the air
    _alltxt = re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", " ".join([str(sh.get(k, "")) for k in ("start_state", "end_state", "action_summary")] +
                     [" ".join(str(b_.get(x, "")) for x in ("movement", "contact", "support", "product_state")) for b_ in sh["beats"]]).lower())
    _enter = re.search(r"\b(slides?|sliding|rolls?|rolling|glides?|wheels?|pushed|pulled|carried|brought|lowered|enters?|walks? in|appears?|fades? in|pops? up|drops? in)\b[^.;|]{0,30}\b(table|shelf|stool|tray|trolley|cart|bench|stand|box|basket|bag|chair|platform|board|sheet|frame|drawer)\b", _alltxt)
    if _enter:
        E.append(f"an object or piece of furniture enters the frame ('{_enter.group(0)[:60]}') - everything is already there in the first frame")
    _air = re.search(r"\b(floats?|floating|hovers?|hovering|hangs? in (the )?air|suspended|levitat\w*|in mid-?air|midair|held by nothing|unsupported)\b", _alltxt)
    if _air:
        E.append(f"something floats in the air ('{_air.group(0)}') - every object rests on a visible surface or is held by a visible hand")
    for b_ in sh["beats"]:   # 22-Nov: nothing moves on its own - a moving object needs a moving limb that moves it
        _mv = re.sub(r"\b(no|zero|without|never|not|nobody|nothing|avoid\w*|prevent\w*|free of)\b[^.;|]*", "", " ".join(str(b_.get(x, "")) for x in ("movement", "product_state")).lower())
        if str(b_.get("moves", "")).strip().lower() in ("nothing", "none", "camera", "") and SELF_MOVE.search(_mv):
            E.append(f"beat {b_.get('t_start')}-{b_.get('t_end')}: '{SELF_MOVE.search(_mv).group(0)}' happens while no limb moves - nothing moves on its own, the avatar must do it")
    fs, fe = sh["framing_start"], sh["framing_end"]
    if fs not in FRAMINGS or fe not in FRAMINGS:
        E.append(f"framing must be one of {list(FRAMINGS)} (got {fs} -> {fe})")
    elif FRAMINGS[fe] <= FRAMINGS[fs]:
        E.append(f"framing_end '{fe}' is not closer than framing_start '{fs}' (the shot must end with a zoom-in)")
    try:
        ae = float(sh.get("action_end_s", 2.5))
    except (TypeError, ValueError):
        ae = -1
    if not 2.5 - 1e-6 <= ae <= 3.0 + 1e-6:
        E.append(f"action_end_s {sh.get('action_end_s')} must be 2.5 (at most 3.0 for a longer real action)")
        ae = 2.5
    try:
        beats = sorted(sh["beats"], key=lambda b: float(b["t_start"]))
        ts = [(float(b["t_start"]), float(b["t_end"])) for b in beats]
    except (KeyError, TypeError, ValueError):
        return E + ["every beat needs numeric t_start and t_end"], W
    if abs(ts[0][0]) > 0.05:
        E.append("the first beat must start at 0.0 s")
    if abs(ts[-1][1] - 4.0) > 0.05:
        E.append(f"the last beat must end at 4.0 s (ends at {ts[-1][1]})")
    for (a0, a1), (b0, b1) in zip(ts, ts[1:]):
        if abs(a1 - b0) > 0.05:
            E.append(f"gap or overlap between beats at {a1}-{b0} s (beats must run without gaps)")
    moving = 0
    for b, (t0, t1) in zip(beats, ts):
        for f in ("moves", "movement", "contact", "still", "product_state", "camera", "gaze"):
            if not str(b.get(f, "")).strip():
                E.append(f"beat {t0}-{t1} s: '{f}' missing (every movement must be fully described)")
        if t1 - t0 < 0.3 - 1e-6:
            E.append(f"beat {t0}-{t1} s is shorter than 0.3 s")
        mv = str(b.get("moves", "")).lower().strip()
        if t0 >= ae - 0.05:   # the push-in part: camera only
            if not (mv.startswith("camera") or mv in ("nothing", "none")):
                E.append(f"beat {t0}-{t1} s is in the push-in part but moves '{b.get('moves')}' (only the camera may move)")
            if "push" not in (str(b.get("camera", "")) + " " + str(b.get("movement", ""))).lower():
                E.append(f"beat {t0}-{t1} s: the end of the shot must be a camera push-in")
        else:
            if mv not in ("nothing", "none", ""):
                moving += 1
            if t1 > ae + 0.05:
                E.append(f"beat {t0}-{t1} s runs past action_end_s {ae} (the action ends before the push-in)")
        txt = (str(b.get("movement", "")) + " " + str(b.get("moves", ""))).lower()
        if "head" in mv:
            for d in re.findall(r"(\d+(?:\.\d+)?)\s*(?:°|deg|degree)", txt):
                if float(d) > 30:
                    E.append(f"beat {t0}-{t1} s: head turn {d} degrees (max 30)")
        if any(w in mv for w in ("foot", "feet", "leg")):
            for d in re.findall(r"(\d+(?:\.\d+)?)\s*cm", txt):
                if float(d) > 30:
                    E.append(f"beat {t0}-{t1} s: foot/leg moves {d} cm (a step is at most 30 cm)")
    if moving > 3:
        E.append(f"{moving} movement beats before the push-in (at most 3)")
    if not any(t0 >= ae - 0.05 for t0, _ in ts):
        E.append("no push-in beat after action_end_s")
    # forbidden patterns (each one a delivered defect)
    T = _texts(sh).lower()
    pats = [(r"\bcuts? (to|away)\b|\bjump[- ]cut\b|\bnew shot\b|\bscene change\b|\bzoom(s|ing)? out\b",
             "a cut / scene change / zoom-out inside the product shot"),
            (r"\bflip(s|ped|ping)?\b|upside[- ]down|\bturns? (it|them|the \w+) over\b", "the product is flipped / turned over"),
            (r"\bunbox|\bout of (the|a|its) (box|bag|pouch|drawer|cupboard)|\b(from|out of) nowhere\b",
             "the product is taken out / appears (it must already be in hand, worn or installed)")]
    if family in HOME_FAMILIES:
        pats += [(r"\b(un)?roll(s|ed|ing)?\b", "a large textile is rolled or unrolled"),
                 (r"\blift(s|ed|ing)? (up )?(the |a )?(mattress|rug|mat|carpet|bedsheet|sheet|curtain|blanket|quilt|comforter|dohar)",
                  "a large textile is lifted"),
                 (r"\btakes? (it |them |the \w+ )?down\b|\bshak(e|es|ing)\b", "an installed item is taken down or shaken")]
    if family == "footwear":
        fw = r"(shoes?|sandals?|slippers?|pair|flip[- ]?flops?|sneakers?|heels|boots?|loafers?|mules?|clogs?|slides|chappals?|footwear|them|it)"
        pats += [(rf"\b(takes?|taking|took|slips?|slipping|kicks?|pulls?|pulling) (off (the |her |his )?{fw}|(the |her |his )?{fw} off)\b"
                  rf"|\bremov(e|es|ing) (the |her |his )?{fw}", "footwear is taken off (the pair stays on both feet)"),
                 (rf"\b(puts?|putting|slips?|slipping|pulls?|pulling) (on (the |her |his )?{fw}|(the |her |his )?{fw} on)\b"
                  r"|\bslid(e|es|ing) (her |his )?(right |left )?(foot|feet|toes) (in|into)\b"
                  rf"|\bsteps? (in|into) (the |her |his )?{fw}",
                  "footwear is put on during the shot (the pair is already worn in the first frame)")]
    for rx, why in pats:
        if re.search(rx, T):
            E.append(f"forbidden: {why}")
    if re.search(r"\bmirror\b", T) and not re.search(r"camera (acts as|is|as) (the|a) mirror", T):
        E.append("a mirror appears in the shot (no mirror in frame; the camera acts as the mirror)")
    if family in ("footwear", "footwear_display", "fashion_wearables"):   # actions must match the LISTING (laces on sandals ...)
        lf = listing_fastening(spec)
        if re.search(r"\b(tie|ties|tied|tying|untied|retie) (the |her |his )?(shoe)?laces\b|\bshoelaces?\b|\blaces\b|\bknot\b", T) \
                and not lf["laces"]:
            E.append("the shot ties/handles laces but the listing is not a lace-up")
        if re.search(r"\bbuckle", T) and not lf["buckle"]:
            E.append("the shot uses a buckle but the listing has none")
        if re.search(r"velcro|hook[- ]and[- ]loop", T) and not lf["velcro"]:
            E.append("the shot uses velcro but the listing has none")
        if lf["slip_on"] and re.search(r"\b(adjust|fasten|tighten)", T):
            E.append("the shot adjusts/fastens a slip-on (it has nothing to adjust)")
        if family == "footwear" and not (lf["laces"] or lf["buckle"] or lf["velcro"] or lf["zip"]):
            try:
                ae2 = float(sh.get("action_end_s", 2.5))
            except (TypeError, ValueError):
                ae2 = 2.5
            for b in sh.get("beats", []):
                try:
                    early = float(b.get("t_start", 0)) < ae2 - 0.05
                except (TypeError, ValueError):
                    early = True
                if early and re.search(r"\b(hand|hands|finger|fingers|fingertip|fingertips|thumb|palm)\b", str(b.get("moves", "")).lower()):
                    E.append("a hand touches the worn footwear (nothing to fasten - show it with foot movements only)")
                    break
    # Day 6 checks (21-Nov): support, two hands in the air, packaging, turning inside the grip, size in frame, form, laces, hand swap
    sup = re.compile(r"\b(hand|hands|holds?|holding|held|grips?|gripped|gripping|palm|fingers|in (her|his)|rests?|resting|on the|on a|"
                     r"on (her|his)|placed|sits? on|stands? on|standing on|worn|wears?|wearing|lies? on|lying on|hung|hanging from|"
                     r"installed|spread on|fitted on)\b")
    base = re.compile(r"\b(on the|on a|rests?|resting|placed|stands? on|standing on|lies? on|lying on|worn|installed|spread on|fitted on)\b")
    held = set()
    needs_support = plan.get("product", {}).get("use_kind") in ("handheld_display", "applied_to_body", "operated", "used_on_object")
    supported = False
    for b, (t0, t1) in zip(beats, ts):
        if t0 >= ae - 0.05:
            continue
        cp = (str(b.get("contact", "")) + " " + str(b.get("product_state", ""))).lower()
        here = bool(str(b.get("support", "")).strip() or sup.search(cp)
                    or re.search(r"contact with|against (the|her|his)|on (the|a|her|his) \w+|\bon \w+|\bin \w+ (hand|fingers|palm)", cp))
        carried = supported and re.search(r"unchanged|same|still|as before|continues", cp)
        if needs_support and not (here or carried):
            E.append(f"beat {t0}-{t1} s: does not say what holds or supports the product (a named hand or a named surface)")
        supported = here or bool(carried)
        mvb = str(b.get("moves", "")).lower()
        ps = str(b.get("product_state", "")).lower()
        on_surface = re.search(r"\b(rests?|resting|placed|stands?|standing|lies?|lying|sits?|sitting|set down|put down)\b[^.|;]{0,30}\b(on|in)\b"
                               r"|\bon (the|a|her|his) (\w+ )?(table|counter|bed|shelf|dresser|vanity|floor|sofa|chair|stool|desk|tray|"
                               r"cabinet|sink|surface|mat|bench|cot|crib|lap|top)\b", ps)
        if needs_support and ("both hands" in mvb or ("left hand" in mvb and "right hand" in mvb)) and not on_surface:
            E.append(f"beat {t0}-{t1} s: both hands are busy while the product is in the air - set it down on the surface first")
        for hnd in re.findall(r"\b(left|right) hand", str(b.get("product_state", "")).lower()):
            held.add(hnd)
        mvt = str(b.get("movement", "")).lower()
        if family not in ("footwear",) and "platform" not in mvt and "turntable" not in mvt and re.search(r"\b(turn|turns|turning|rotat\w*|spin\w*|swivel\w*)\b[^.|;]{0,30}\b(bottle|tube|jar|pack|can|box|product|it|bib|carton)\b", mvt) \
                and "wrist" not in mvt:
            E.append(f"beat {t0}-{t1} s: the product turns without the wrist - turn the wrist so hand and product turn together")
    if len(held) > 1 and plan.get("product", {}).get("use_kind") != "worn" and family != "footwear_display":
        E.append("the product moves between the left and the right hand (one hand holds it the whole time)")
    osp = plan.get("open_state_spec") if isinstance(plan.get("open_state_spec"), dict) else {}
    opens = re.search(r"\b(open(s|ed|ing)?|lifts? (off |up )?the lid|takes? (it |them |the \w+ )?out of|removes? (it |them |the \w+ )?from (the )?(box|case|pouch)|unbox\w*)\b[^.|;]{0,40}\b(box|case|lid|carton|pack|packet|pouch|packaging)\b", T)
    if opens and not osp.get("used"):
        E.append("the shot opens a box/lid or takes the product out, but open_state_spec.used is not true - describe the open state (rule 28)")
    if osp.get("used") and (len(str(osp.get("state", ""))) < 40 or len(str(osp.get("how_opened", ""))) < 15 or not osp.get("parts_inside")):
        E.append("open_state_spec.used is true but state / how_opened / parts_inside are missing or too short")
    tear = r"\b(tear(s|ing)?|rip(s|ping)?|unseal\w*|peel(s|ing)? open|cuts? open)\b[^.|;]{0,40}\b(box|carton|pack|packet|pouch|wrapper|seal|flap|packaging|film|wrap)\b"
    if re.search(tear if osp.get("used") else r"\b(open(s|ed|ing)?|tear(s|ing)?|rip(s|ping)?|unseal\w*|peel(s|ing)? open)\b[^.|;]{0,40}\b(box|carton|pack|packet|pouch|wrapper|seal|flap|packaging)\b", T):
        E.append("forbidden: sealed packaging is opened/torn (packs and boxes stay closed)")
    try:
        dims = cm_values(str(plan.get("product", {}).get("life_size", {}).get("dimensions_cm", "")))
    except ValueError:
        dims = []
    if dims and max(dims) < 30 and plan.get("product", {}).get("use_kind") in ("handheld_display", "applied_to_body", "operated", "used_on_object") \
            and sh.get("framing_start") in ("full_body", "knee_up"):
        E.append(f"a {max(dims):.0f} cm handheld product starts in a {sh.get('framing_start')} framing (too small - start at waist_up or closer)")
    ty0 = (plan.get("product", {}).get("type", "") + " " + spec.get("title", "")).lower()
    if re.search(r"roll[- ]?on|roller ball", ty0) and re.search(r"\b(spray|sprays|spraying|mist|nozzle|spritz)\b", T):
        E.append("a roll-on is sprayed (a roll-on rolls on the skin)")
    if re.search(r"\bspray\b|aerosol|body mist", ty0) and not re.search(r"roll[- ]?on", ty0) and re.search(r"\broll(s|ing)? (it |the \w+ )?(on|over|along)\b", T):
        E.append("a spray is rolled on (a spray sprays from 15-20 cm)")
    if family in ("footwear", "fashion_wearables") and listing_fastening(spec)["laces"] and \
            re.search(r"\b(tie|ties|tied|tying) (the |her |his )?(shoe)?laces\b|\bbow\b", T):
        if not re.search(r"untied|loose", str(sh.get("start_state", "")).lower()) or not re.search(r"\bbow\b|\btied\b|knot", str(sh.get("end_state", "")).lower()):
            E.append("tying laces must start untied (loose ends hanging) and end with a visible bow")
    hand_held = any(re.search(r"\b(hand|fingers?|palm)\b", str(b.get("support", "")).lower()) for b in beats)
    if hand_held:   # user 22-Nov: the holding hand is always visible
        if "macro" in (sh.get("framing_start"), sh.get("framing_end")):
            E.append("a 'macro' framing would crop out the holding hand - end at product_close or hands_close (the hand stays in frame)")
        if not re.search(r"hand|fingers|palm", str(sh.get("start_state", "")).lower()):
            E.append("start_state must show and name the holding hand (wrist and forearm in frame)")
    ty1 = (str(plan.get("product", {}).get("type", "")) + " " + str(spec.get("title", "")) + " " + str(plan.get("product", {}).get("how_people_use_it", ""))).lower()
    full1 = _texts(sh).lower()
    if re.search(r"\b(pump|pumps|pumped|dispens\w*|squeez\w*|flip[- ]?cap)\b", full1) and \
            re.search(r"cream|lotion|moistur\w*|gel\b|serum|sunscreen|\boil\b|soap|shampoo|wash\b|sanitizer|paste", ty1):
        if not (re.search(r"\b(palm|cupped hand|open hand)\b", full1) and re.search(r"\b(below|under|beneath)\b", full1)):
            E.append("a pump/squeeze dispenser needs the other hand's open palm directly below the nozzle to catch the dollop (palm in frame)")
    if family == "home_decor" and sh.get("framing_start") not in ("full_body", "knee_up", "waist_up", "shoulders_up", "wall_close"):
        E.append("home decor starts with the person's upper body in frame (full_body, knee_up, waist_up or wall_close) so every arm is joined to a "
                 "visible body; the push-in then goes closer")
    sf = (plan.get("scene") or {}).get("surface")
    if isinstance(sf, dict) and sf.get("kind"):   # user 21-Nov: the surface exists from the first frame - no table appears from nowhere
        kind = sf["kind"]; first = str(sh.get("start_state", "")).lower()
        sw = {w for w in re.findall(r"[a-z]{4,}", (str(sf.get("name", "")) + " " + kind).lower()) if w not in ("none", "held", "with", "from")}
        if kind not in ("none_held", "lap", "floor"):
            if sw and not any(w in first for w in sw):
                E.append(f"start_state does not show the surface '{sf.get('name')}' (it must be in the first frame)")
            okf = {"full_body", "knee_up", "waist_up", "hands_close", "product_close"} | ({"knee_down"} if kind in ("sofa", "bed", "stool") else set()) | ({"shoulders_up", "wall_close"} if kind == "wall" else set())
            if sh.get("framing_start") not in okf:
                E.append(f"the surface '{sf.get('name')}' is not in the start framing '{sh.get('framing_start')}' - start at {sorted(okf)}")
        allowed = sw | set(re.findall(r"[a-z]{4,}", str((plan.get("scene") or {}).get("anchor", "")).lower())) | set(re.findall(r"[a-z]{4,}", first))
        later = " ".join([str(sh.get("end_state", ""))] + [" ".join(str(b.get(x, "")) for x in ("moves", "movement", "contact", "support", "product_state")) for b in sh.get("beats", [])]).lower()
        for fw in re.findall(r"\b(table|counter|shelf|stool|tray|bench|desk|dresser|cabinet|trolley)\b", later):
            if fw not in allowed:
                E.append(f"a '{fw}' appears in the shot but is not the planned surface or in the first frame (nothing is added mid-shot)")
                break
    if family == "footwear_display":   # 22-Nov: shoes held or on a platform
        if sh.get("framing_start") not in ("waist_up", "knee_up", "shoulders_up", "hands_close", "product_close"):
            E.append(f"display shot starts in '{sh.get('framing_start')}' - start at waist_up (or knee_up, shoulders_up, hands_close) so the person and the shoe are both in frame")
        dtxt = " ".join(str(sh.get(k, "")) for k in ("start_state", "end_state", "action_summary")) + " " + \
               " ".join(" ".join(str(b.get(x, "")) for x in ("moves", "movement", "contact", "product_state")) for b in sh.get("beats", []))
        dtxt = dtxt.lower()
        for rx, why in [(r"\b(wears?|wearing|worn|puts? on|putting on|slips? (it |them )?on|steps? (in|into)|takes? off|slips? off)\b(?![^.;|]{0,12}\b(not|never)\b)", "the shoes are worn / put on / taken off (display approaches never wear them)"),
                        (r"\b(flips?|flipping|spins?|spinning|throws?|tosses?|drops?|swaps? hands|passes? (it|the shoe) to)\b", "the shoe is flipped / spun / thrown / passed between hands"),
                        (r"\b(legs?|feet|foot|knees?|ankles?)\b[^.;|]{0,20}\b(turn|rotat|pivot|move|step|lift|tap|shift)", "the person's legs or feet move (they stay completely still in display approaches)")]:
            if re.search(rx, dtxt):
                E.append("display shot: " + why)
        for d in re.findall(r"(\d+(?:\.\d+)?)\s*(?:degrees|degree|deg|°)", dtxt):
            if float(d) > 30:
                E.append(f"display shot: a turn of {d} degrees (max 30 for a shoe or platform)")
        mt_ = str(sh.get("movement_type", "")).strip().lower()
        if mt_ not in ("hand_turn", "platform_turn", "lift_and_show", "tilt", "present", "point", "label_turn", "place", "other"):
            E.append(f"display movement_type '{sh.get('movement_type')}' must be one of hand_turn, platform_turn, lift_and_show, tilt, present, point")
    if family == "footwear":   # user 21-Nov: legs must never rotate; knees always in frame; tiny, straight movements only
        if sh.get("framing_start") not in ("knee_down", "knee_up", "waist_up", "full_body"):
            E.append(f"footwear shot starts in '{sh.get('framing_start')}' - it must start with the knees in frame (knee_down, "
                     "knee_up, waist_up or full_body) so the legs are visibly attached; the push-in then goes closer")
        if str(sh.get("movement_type", "")).strip().lower() not in ("heel_lift", "toe_raise", "weight_shift", "slide", "step", "tap",
                                                                      "tie_laces"):
            E.append(f"footwear movement_type '{sh.get('movement_type')}' is not one of heel_lift, toe_raise, weight_shift, slide, "
                     "step, tap, tie_laces (no turning or rotating, ever)")
        rot = re.compile(r"\b(turn|turns|turning|turned|rotat\w*|pivot\w*|swivel\w*|twist\w*|spin\w*|angl\w*|outward|inward|"
                         r"sideways|cross\w*|swing\w*|kick\w*|flick\w*|sweep\w*|arc|arcs|yaw)\b")
        try:
            ae3 = float(sh.get("action_end_s", 2.5))
        except (TypeError, ValueError):
            ae3 = 2.5
        for b in sh.get("beats", []):
            try:
                if float(b.get("t_start", 0)) >= ae3 - 0.05:
                    continue
            except (TypeError, ValueError):
                pass
            mvb2 = str(b.get("moves", "")).lower()
            if not re.search(r"foot|feet|leg|knee|toe|heel|shoe|sandal|ankle", mvb2):
                continue
            txt2 = mvb2 + " " + str(b.get("movement", "")).lower()
            if rot.search(txt2):
                E.append(f"beat {b.get('t_start')}-{b.get('t_end')} s: legs/feet must not rotate, turn, angle, cross or swing "
                         f"('{rot.search(txt2).group(0)}') - only toe raise, heel lift, weight shift, straight slide (max 10 cm), "
                         "one straight step (max 25 cm) or a tap")
            if re.search(r"\d+(?:\.\d+)?\s*(?:°|deg)", txt2):
                E.append(f"beat {b.get('t_start')}-{b.get('t_end')} s: no angle changes of legs or feet (found degrees)")
            lim = 25 if re.search(r"\bstep", txt2) else 10
            if any(float(x) > lim for x in re.findall(r"(\d+(?:\.\d+)?)\s*cm", txt2)):
                E.append(f"beat {b.get('t_start')}-{b.get('t_end')} s: a foot moves more than {lim} cm")
    pq = (" ".join(map(str, plan.get("prerequisites", []))) + " " + sh.get("start_state", "")).lower()
    ty = (plan.get("product", {}).get("type", "") + " " + spec.get("title", "")).lower()
    if "razor" in ty and "electric" not in ty:
        if not re.search(r"foam|gel|cream|lather|soap", pq):
            E.append("a razor shot needs shaving foam/gel already on the skin in the first frame")
        if not re.search(r"stubble|beard|hair", pq):
            E.append("a razor shot needs visible stubble/beard in the first frame")
    if re.search(r"trimmer|shaver", ty) and not re.search(r"stubble|beard|hair", pq):
        E.append("a trimmer/shaver shot needs visible stubble/beard/hair in the first frame")
    full = _texts(sh)
    for m in re.finditer(r"\b(left|right)\b", full, re.I):
        if not SIDE_OK.search(full[max(0, m.start() - 25):m.start()]):
            W.append(f"'{full[max(0, m.start() - 25):m.end()]}': say whose left/right (her/his/screen)")
            break
    return E, W


_SIZE_KEYS = re.compile(r"^(product )?(dimensions?|width|height|depth|length|diameter)( \(.*\))?$", re.I)


def listing_cm(spec):
    """23-Nov: lengths (cm) the Flipkart listing itself states, only from size fields and only with an explicit unit
    (a bare 'Size 7' or 'Knee Length' is not a length)."""
    out = []
    for k, v in ((spec or {}).get("specifications") or {}).items():
        if _SIZE_KEYS.match(str(k).strip()) and re.search(r"\d\s*(mm|cm|m|inch|inches|in|ft)\b", str(v), re.I):
            out += cm_values(v)
    return out


def validate(plan, spec, family):
    """Returns (errors, warnings). Errors block the row: they are the QC defects of Day 1-5, caught BEFORE any generation.
    A plan is usable when the product/scene parts are clean and at least one shot variant is clean; _meta.valid_variants
    lists the clean variants (indexes)."""
    E, W = [], []
    if not isinstance(plan, dict):
        return ["the plan is not a JSON object"], []
    if isinstance(plan.get("shots"), list):       # built-in safe shots are rebuilt from the current code every time
        plan["shots"] = [x for x in plan["shots"] if not (isinstance(x, dict) and x.get("safe"))]
    if family == "footwear" and plan.get("_meta", {}).get("letter") in DISPLAY_LETTERS:
        family = "footwear_display"      # 22-Nov: shoes held / on a platform, not worn - the worn-footwear checks do not apply
    for top in ("product", "prerequisites", "person", "scene", "forbidden"):
        if top not in plan:
            E.append(f"missing '{top}'")
    if not shots_of(plan):
        E.append("missing 'shots' (3 shot variants)")
    if E:
        return E, W
    pr, sc = plan["product"], plan["scene"]
    for k in ("type", "category_item", "how_people_use_it", "use_kind", "parts_visible", "colours", "life_size"):
        if not pr.get(k):
            E.append(f"product.{k} missing")
    for k in ("room", "acceptable_rooms", "anchor", "exclude"):
        if not sc.get(k):
            E.append(f"scene.{k} missing")
    if E:
        return E, W
    if pr["use_kind"] not in USE_KINDS:
        E.append(f"product.use_kind '{pr['use_kind']}' is not one of {USE_KINDS}")
    for c in pr.get("colours", []):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(c.get("hex", "")) if isinstance(c, dict) else ""):
            W.append(f"colour {c} has no #RRGGBB hex")
    ls = pr.get("life_size", {}) if isinstance(pr.get("life_size"), dict) else {}
    try:      # 23-Nov (option 4): OpenAI's size is checked against what the Google results agree on; a clear mismatch uses Google's
        _ss = listing_size(spec)
        _ob = max(cm_values(str(ls.get("dimensions_cm", ""))) or [0])   # 23-Nov: unit-aware (g / ml are not cm)
        if _ss and _ss["sources"] >= 2 and _ob and abs(_ob / _ss["max_cm"] - 1) > 0.3:
            W.append(f"size: OpenAI said {ls.get('dimensions_cm')} but {_ss['sources']} Google results agree on {_ss['dims']} - Google's size is used")
            ls["dimensions_cm"] = f"{_ss['dims']} (longest side {_ss['max_cm']:g} cm, {_ss['sources']} Google results agree)"
            ls["dimensions_source"] = str(ls.get("dimensions_source", "")) + "; corrected to the Google consensus"
        elif _ss and _ss["sources"] >= 2:
            ls["dimensions_source"] = str(ls.get("dimensions_source", "")) + f"; matches {_ss['sources']} Google results ({_ss['dims']})"
    except Exception:
        pass
    if re.search(r"\b(box|package|packaging|carton|shipping)\b", str(ls.get("dimensions_cm", "")), re.I):
        W.append("dimensions_cm mentions the box/package - the product's own out-of-box size must be used (rule 26)")
    if not re.search(r"\d", str(ls.get("dimensions_cm", ""))):
        E.append("product.life_size.dimensions_cm has no numbers (life-size is required)")
    if family in LOCK_FAMILIES:        # 22-Nov: no state change inside a clip - a part keeps its START state
        for x_ in (plan.get("part_states") or []):
            if isinstance(x_, dict) and str(x_.get("end", "")).strip().lower() != str(x_.get("start", "")).strip().lower():
                W.append(f"part_states: '{x_.get('part')}' {x_.get('start')} -> {x_.get('end')} is ignored - it stays {x_.get('start')} in every frame")
                x_["end"] = x_.get("start")
        if isinstance(plan.get("open_state_spec"), dict) and plan["open_state_spec"].get("used"):
            W.append("open_state_spec ignored: nothing is opened or taken out inside a clip"); plan["open_state_spec"]["used"] = False
    _pr = plan.get("parts_role")
    if not (isinstance(_pr, list) and _pr and all(isinstance(x, dict) and x.get("part") for x in _pr)):
        (E if plan.get("schema_version", 1) >= 8 else W).append("parts_role missing - which part is used and which is not (rule 47)")
    _h = plan.get("hero") if isinstance(plan.get("hero"), dict) else {}
    if not (_h.get("main_thing") and _h.get("ready_state") and _h.get("must_see")):
        (E if plan.get("schema_version", 1) >= 7 else W).append("hero (main thing / ready_state / must_see) missing - rule 40: show what the product is FOR")
    ps_ = plan.get("part_states")
    if ps_ is None:
        W.append("product.part_states missing (lid/cap state) - re-plan to add it")
    elif isinstance(ps_, list):
        for x in ps_:
            if isinstance(x, dict) and str(x.get("start", "")).strip().lower() != str(x.get("end", "")).strip().lower() \
                    and len(str(x.get("how", ""))) < 15:
                E.append(f"part_states: '{x.get('part')}' changes {x.get('start')} -> {x.get('end')} without a 'how' (hand action)")
    try:   # 22-Nov: real-life size sanity - a hand-held product must fit one real hand
        big_ = max(cm_values(str(ls.get("dimensions_cm", ""))) or [0])
        if pr.get("use_kind") in ("handheld_display", "applied_to_body", "operated") and big_ > 45:
            E.append(f"life_size {big_:g} cm is too large to be hand-held with one real hand (check the dimensions or the use_kind)")
        if 0 < big_ < 0.5:
            E.append(f"life_size {big_:g} cm - dimensions look like metres or a wrong unit (use cm)")
    except ValueError:
        pass
    _ty = (str(pr.get("type", "")) + " " + str(pr.get("category_item", ""))).lower()
    try:   # 22-Nov baby care review: diapers drawn far too big
        _bg = max(cm_values(str(ls.get("dimensions_cm", ""))) or [0])
        if "diaper" in _ty and _bg > 60:
            E.append(f"a diaper product of {_bg:g} cm - a diaper pack is about 30-45 cm, one diaper about 35-45 cm unfolded (check the size)")
        if family == "baby_care" and _bg > 70 and not re.search(r"\b(stroller|pram|cot|crib|bed|mattress|playpen|walker|bath ?tub|car seat|high chair|carrier)\b", _ty):
            E.append(f"a baby-care product of {_bg:g} cm - baby products are small; check the dimensions")
    except ValueError:
        pass
    # 23-Nov: REAL SIZE is grounded in the listing - when the listing states a size with a unit, the plan must agree (25 %)
    lst = listing_cm(spec)
    mine = cm_values(str(ls.get("dimensions_cm", "")))
    if lst and mine and abs(max(mine) - max(lst)) > 0.25 * max(lst):
        E.append(f"life_size longest side {max(mine):g} cm disagrees with the listing ({max(lst):g} cm) - use the listing's size")
    if lst and "typical" in str(ls.get("dimensions_source", "")).lower():
        E.append(f"dimensions marked 'typical' although the listing gives a size ({max(lst):g} cm) - use the listing's size")
    if not ls.get("dimensions_source"):
        W.append("product.life_size.dimensions_source missing (where the dimensions came from)")
    elif "typical" in str(ls.get("dimensions_source")).lower():
        W.append("dimensions are only typical for the product type (no listing or web source found)")
    if not ls.get("body_relative"):
        E.append("product.life_size.body_relative missing")
    if sc["room"] not in ROOMS:
        E.append(f"scene.room '{sc['room']}' is not one of {ROOMS}")
    bad_rooms = [r for r in sc["acceptable_rooms"] if r not in ROOMS]
    if bad_rooms and any(r in ROOMS for r in sc["acceptable_rooms"]):
        W.append(f"scene.acceptable_rooms has unknown rooms {bad_rooms} (ignored - a valid room remains)")
        sc["acceptable_rooms"] = [r for r in sc["acceptable_rooms"] if r in ROOMS]
        bad_rooms = []
    if bad_rooms:
        E.append(f"scene.acceptable_rooms has unknown rooms {bad_rooms}")
    if sc["room"] in ROOMS and sc["room"] not in sc["acceptable_rooms"]:
        sc["acceptable_rooms"].insert(0, sc["room"])
    for p in sc.get("props", []) or []:
        if not (isinstance(p, dict) and p.get("item") and re.search(r"\d", str(p.get("size_cm", ""))) and p.get("placement")):
            E.append(f"prop {p} needs item, size_cm (numbers) and placement")
        elif "mirror" in str(p.get("item", "")).lower():
            E.append("a mirror is listed as a prop - no mirror in frame (the camera acts as the mirror)")
    sf = sc.get("surface")
    if plan.get("schema_version", 1) >= 2 or sf:
        if not isinstance(sf, dict):
            E.append("scene.surface missing (the surface the product rests on must be planned)")
        else:
            if sf.get("kind") not in SURFACE_KINDS:
                E.append(f"scene.surface.kind '{sf.get('kind')}' is not one of {SURFACE_KINDS}")
            elif sf["kind"] not in ("floor", "lap", "none_held"):
                if not re.search(r"\d", str(sf.get("size_cm", ""))):
                    E.append("scene.surface.size_cm needs real numbers")
                if not sf.get("placement"):
                    E.append("scene.surface.placement missing (where it is in the room)")
    else:
        W.append("old plan without scene.surface - the reel planner derives the surface from the anchor")
    if family == "home_decor" and plan.get("schema_version", 1) >= 2:   # user 22-Nov: decor depth and scale
        mt = sc.get("mount") if isinstance(sc.get("mount"), dict) else None
        num = lambda x: re.search(r"\d+(?:\.\d+)?", str(x))
        if not mt:
            E.append("scene.mount missing (home decor needs type, size, height, gap and person distance)")
        else:
            if mt.get("type") not in ("wall", "surface", "floor", "hanging"):
                E.append(f"scene.mount.type '{mt.get('type')}' is not wall | surface | floor | hanging")
            for k_ in ("width_cm", "height_cm", "person_distance_cm"):
                if not num(mt.get(k_)):
                    E.append(f"scene.mount.{k_} needs a number")
            if mt.get("type") in ("wall", "hanging"):
                if not num(mt.get("height_from_floor_cm")):
                    E.append("scene.mount.height_from_floor_cm needs a number for a wall/hanging item")
                if (sc.get("surface") or {}).get("kind") != "wall":
                    E.append("a wall/hanging item needs scene.surface.kind 'wall' (the room's back wall)")
            pd = num(mt.get("person_distance_cm"))
            if pd and not 20 <= float(pd.group(0)) <= 70:
                E.append(f"person_distance_cm {pd.group(0)} is outside 20-70 (stand close to the item, never reach across the room)")
    if pr.get("use_kind") in ("applied_to_body", "used_on_object", "operated") and not plan.get("prerequisites"):
        E.append("no prerequisites for a product that is used/applied (what must already be true in the first frame?)")
    if not plan.get("forbidden"):
        W.append("forbidden list is empty")
    good = []
    for i, sh in enumerate(shots_of(plan)):
        e, w = validate_shot(sh, plan, spec, family)
        if e:
            W.append(f"shot variant {i + 1} not usable: " + "; ".join(e))
        else:
            good.append(i)
        W += [f"shot variant {i + 1}: {x}" for x in w]
    _sv = shots_of(plan)
    if family in LOCK_FAMILIES and isinstance(plan.get("shots"), list) and not any(not _sv[i_].get("no_person") for i_ in good):
        # 22-Nov: no safe avatar variant -> built-in shots that cannot break the lock rule (decor: 5 touch close-ups)
        _mt2 = (plan.get("scene") or {}).get("mount") if isinstance((plan.get("scene") or {}).get("mount"), dict) else {}
        k_ = 5 if (_mt2 or {}).get("type") in ("wall", "hanging") else 3
        n0 = len(plan["shots"])
        plan["shots"] += [safe_shot(plan, k) for k in range(k_)]; good = good + list(range(n0, n0 + k_))
        W.append("no OpenAI variant is safe - the built-in safe shot (one out-and-back movement) is used")
    # 23-Nov Garvit ('block before pay'): the 22-Nov FK_LAX 'fewest findings' fallback is removed - a plan with no clean
    # variant is never paid for
    if not good:
        E.append("no shot variant passes the checks (see warnings for each variant)")
    plan.setdefault("_meta", {})["valid_variants"] = good
    return E, W


# ------------------------------------------------------------------------------------------------------------------- run
def plan_products(row_dir, items, family, variant, approach, confirmed=False, replan=()):
    """items: [(slot, pid, spec_dict)]. Returns ({slot: plan}, problems). Dry run (confirmed=False) only shows what would be
    sent. Never re-sends a failed request (user rule): a failed product is reported and left for the user to decide."""
    os.makedirs(PLAN_DIR, exist_ok=True)
    reqdir = os.path.join(row_dir, "planner_requests"); os.makedirs(reqdir, exist_ok=True)
    plans, problems, todo = {}, [], []
    for slot, pid, spec in items:
        k = key(pid, family, variant, approach["letter"])
        p = load(k)
        tm = path(k) + ".timeout.json"
        if p is None and os.path.exists(tm) and slot not in replan:   # 23-Nov: a timed-out request is never re-sent automatically
            problems.append(f"slot {slot} {pid}: the OpenAI request timed out after sending ({json.load(open(tm)).get('at')}) - "
                            f"NOT re-sent; re-plan only after the user's yes (--replan={slot})")
            continue
        if p is not None and slot in replan:
            problems.append(f"slot {slot} {pid}: re-plan requested - it will be re-requested (old plan kept in {PLAN_DIR}/rejected/)")
            p = None
        if p is not None:
            e, w = validate(p, spec, family)
            p.setdefault("_meta", {}).update(errors=e, warnings=w, valid=not e)
            if confirmed:          # 23-Nov: a dry run never changes the shared plan files
                save_plan(k, p)
            if not e:
                plans[slot] = p
                continue
            if rejected_count(k) >= 2 and slot not in replan:   # 23-Nov: never pay again and again for the same failing product
                problems.append(f"slot {slot} {pid}: planned {rejected_count(k) + 1} times and still fails the checks - NOT re-requested; "
                                f"look at the errors, then re-plan only after the user's yes (--replan={slot}):\n    - " + "\n    - ".join(e))
                continue
            problems.append(f"slot {slot} {pid}: saved plan fails the checks - it will be re-requested (the old one is kept in "
                            f"{PLAN_DIR}/rejected/):\n    - " + "\n    - ".join(e))
        text = product_text(spec, family, variant, approach)
        ph = photos(row_dir, slot)
        json.dump(dict(model=MODEL, web_tool=WEB_TOOL or None, instructions=RULEBOOK + family_rules(family, approach["letter"]), product_text=text,
                       photos=[os.path.basename(x) for x in ph]),
                  open(os.path.join(reqdir, f"slot_{slot}_{pid}.json"), "w"), indent=1, ensure_ascii=False)
        todo.append((slot, pid, spec, k, text, ph))
    if not todo:
        return plans, problems
    print(f"OpenAI requests needed: {len(todo)} (model {MODEL}, web research {'on' if WEB_TOOL else 'off'}). ONLY product data is sent:")
    for slot, pid, spec, k, text, ph in todo:
        print(f"  slot {slot} {pid}: '{spec.get('title', '')[:70]}' + {len(spec.get('specifications', {}))} specs"
              f"{' + description' if spec.get('description') else ''} + {len(ph)} listing photos ({', '.join(os.path.basename(x) for x in ph)})")
    print(f"  exact request texts: {reqdir}/slot_*.json (+ the rule book, the same for every product)")
    if False:      # 23-Nov: Serper removed
        def _miss(pid, spec):
            cp_ = os.path.join(PLAN_DIR, "serper", f"{pid}.json"); have = json.load(open(cp_)) if os.path.exists(cp_) else {}
            return sum(1 for q in serper_queries(spec) if q not in have)
        nq = sum(_miss(pid, spec) for _, pid, spec, *_ in todo)
        print(f"  + Google searches via Serper: {nq} (up to 4 per product, only those not searched before; only the product title/brand is searched), "
              f"their results are added to that product's OpenAI request")
    if not confirmed:
        print("DRY RUN - nothing was sent. After the user approves, run again with --confirmed.")
        problems.append(f"{len(todo)} product(s) not planned yet (dry run)")
        return plans, problems
    import concurrent.futures, threading
    lock = threading.Lock()

    def one(item):    # user 22-Nov: every product's request is sent AT THE SAME TIME (one thread each)
        slot, pid, spec, k, text, ph = item
        probs = []
        import fcntl   # 23-Nov: one request per product across ALL rows' processes (rows sharing a PID wait, then reuse it)
        lf = open(path(k) + ".lock", "w"); fcntl.flock(lf, fcntl.LOCK_EX)
        try:
            again = load(k)
            if again is not None and slot not in replan:
                e_, w_ = validate(again, spec, family)
                if not e_:
                    return slot, again, probs
            return _one_locked(slot, pid, spec, k, text, ph, probs)
        finally:
            fcntl.flock(lf, fcntl.LOCK_UN); lf.close()

    def _one_locked(slot, pid, spec, k, text, ph, probs):
        with lock:
            if os.path.exists(path(k)):   # a rejected saved plan: keep it, never delete (user rule)
                rj = os.path.join(PLAN_DIR, "rejected"); os.makedirs(rj, exist_ok=True)
                os.replace(path(k), os.path.join(rj, f"{k}.{time.strftime('%Y%m%d-%H%M%S')}.json"))
        t0 = time.time()
        facts = ""        # 23-Nov (user): Serper removed completely - OpenAI's web search does the research
        if facts:
            text = (text + "\n\nGOOGLE SEARCH RESULTS for this exact product (via Serper) - use them for the real size, parts, pack contents "
                    "and how it is used; trust numbers that agree across sources and name them in life_size.dimensions_source:\n" + facts)
        try:
            resp = call(payload(text, ph, family, approach["letter"]))
        except SentTimeout as ex:
            json.dump(dict(at=time.strftime("%Y-%m-%d %H:%M:%S"), error=str(ex)), open(path(k) + ".timeout.json", "w"))
            return slot, None, probs + [f"slot {slot} {pid}: {ex} - NOT re-sent; ask the user before sending again"]
        except Exception as ex:   # never retried automatically
            return slot, None, probs + [f"slot {slot} {pid}: OpenAI request failed ({ex}) - NOT retried; ask the user before sending again"]
        json.dump(resp, open(os.path.join(PLAN_DIR, k + ".raw.json"), "w"), indent=1, ensure_ascii=False)
        try:
            p = parse(response_text(resp))
        except Exception as ex:
            return slot, None, probs + [f"slot {slot} {pid}: reply was not valid JSON ({ex}); raw reply in {k}.raw.json"]
        p["_meta"] = dict(letter=approach["letter"])
        e, w = validate(p, spec, family)
        p["_meta"] = dict(pid=pid, key=k, family=family, variant=variant, letter=approach["letter"], model=MODEL,
                          created=time.strftime("%Y-%m-%d %H:%M"), seconds=round(time.time() - t0, 1),
                          usage=resp.get("usage"), errors=e, warnings=w, valid=not e,
                          valid_variants=p.get("_meta", {}).get("valid_variants", []))
        save_plan(k, p)
        if os.path.exists(path(k) + ".timeout.json"):
            os.remove(path(k) + ".timeout.json")     # answered now - the earlier timeout no longer applies
        print(f"  slot {slot} {pid}: planned ({'OK' if not e else str(len(e)) + ' errors'}) -> {path(k)}", flush=True)
        if e:
            probs.append(f"slot {slot} {pid}: plan has errors (not used):\n    - " + "\n    - ".join(e))
        return slot, p, probs

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(todo))) as ex_:
        for slot, p, probs in ex_.map(one, todo):
            problems += probs
            if p is not None:
                plans[slot] = p
    return plans, problems


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[1] == "serper-test":    # one paid query - only after the user's yes
    _k = env("SERPER_API_KEY")
    _r = json.loads(urllib.request.urlopen(urllib.request.Request("https://google.serper.dev/search", json.dumps({"q": sys.argv[2], "gl": "in", "num": 5}).encode(),
                                                                {"X-API-KEY": _k, "Content-Type": "application/json"}), timeout=60).read().decode())
    for _o in (_r.get("organic") or [])[:5]:
        print("-", _o.get("title"), "|", _o.get("snippet"))
    sys.exit(0)
if __name__ == "__main__":   # re-check a hand-edited plan: product_planner.py --check <plan.json> <slot_N.json spec> <family>
    if sys.argv[1:2] == ["--check"]:
        e, w = validate(json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), sys.argv[4])
        print("\n".join(["ERRORS:"] + e if e else ["OK"]) + ("\nwarnings:\n" + "\n".join(w) if w else ""))
        sys.exit(1 if e else 0)
    print(__doc__)
