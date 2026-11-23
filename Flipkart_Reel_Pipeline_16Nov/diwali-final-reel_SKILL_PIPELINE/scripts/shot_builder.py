"""SHOT BUILDER (user 21-Nov): writes every image and clip prompt of a planned row from the plans + locks, so the worker only
pastes them. Nothing here calls a model.

Per product = ONE continuous 4 s take at 360p (no cut inside a product, zoom-in only):
  start still  = an EDIT of the room master (same room, props, light, person size) with the product in its first state
  end still    = an EDIT of the start still: the correct result, camera pushed straight in on the detail
  clip         = Omni 1.2 first/last-frame interpolation between the two stills, 4 s, 360p, 9:16, with the timed beats
Files: <row>/shots/room_<room>.json, slot_<N>.json, plan_skeleton.json, ORDER.md
"""
import re, json, os
from product_spec import cm_values   # 23-Nov: unit-aware sizes (g / ml are not cm)
import reel_planner as RP
from product_planner import shots_of, FRAMINGS, LOCK_FAMILIES, HANDLING_FAMILIES

NEGATIVE = ("STYLE: a warm, lived-in, everyday Indian home in soft natural daylight from the window - cosy and real, not a showroom; only "
            "the objects named in the room list and in this prompt are present.")   # 22-Nov: stated positively - a list of banned things primes the model to draw them
PHOTO = ("Photoreal phone photo, portrait 9:16, natural light, real skin texture with pores, real fabric with small natural "
         "creases, no beauty filter, no smoothing, no lightening, no on-screen text.")
PHYSICS = ("PHYSICS (every rule the user set, 21-23 Nov). BODY: exactly two arms, two hands with five fingers and two legs, all joined to her body; "
           "every hand belongs to HER arm and shoulder; no arm enters from the frame edge without her shoulder; left/right = her OWN left/right; "
           "the arm that is not acting hangs straight down, relaxed, the same in every frame; no limb crosses another or the face; head turns "
           "at most 30 degrees; feet flat with weight unless stepping; seated = fully on a visible seat; she is ALIVE (breathing, blinks, small "
           "head and eye movement, soft closed-mouth smile, no talking), looks mostly at the product, only glances at the camera. "
           "HOLDING: a held product is GRIPPED (fingers round it, thumb on it, touching the palm), between chest and waist height, fully in "
           "frame, the holding hand, wrist and forearm always visible; never above the shoulders, over the face, balanced on a flat palm or "
           "hanging under a hand; the same hand holds it throughout; it turns only with the wrist. A tool is used where it is used (brush in "
           "the hair, comb in the beard). Mirror-selfie: the camera is the mirror - the phone's back faces the camera, its screen faces her. "
           "SUPPORT - NOTHING FLOATS OR STANDS ON NOTHING: every object (product, cap, dropper, part, prop, cloth, mat, tray, box, shoe) is "
           "either gripped by a hand or rests on something that rests on furniture or the floor, touching it with a contact shadow; a cloth "
           "or mat lies flat on a table/counter/bed before anything rests on it; a loose part with no surface in the frame is not in the "
           "picture; an object stands upright only if it can stand on its own base - otherwise it lies on its natural side (shoes ON THEIR "
           "SOLES) or leans on the stand, riser or box the plan placed for it (never against a wall), touching it; a hand resting on top "
           "is not support. "
           "NOTHING MOVES ON ITS OWN: an object moves only when a named hand moves it. CAMERA: steady, no shake, tilt, roll, focus or "
           "exposure change; one smooth push-in toward the product. PACE: slow, even, everyday speed, no snapping.")
CONTINUITY = ("NOTHING APPEARS: every table, shelf, stool, tray, box, prop and product visible at any moment is already in the first frame in its final place; nothing is added, brought in, faded in, popped up or replaced during the clip. "
              "CONTINUITY: the room, walls, floor, every background prop in the bible, the light and its direction, the person's "
              "face, hair, body size, outfit and accessories stay exactly as in the first frame for the whole clip; nothing appears, "
              "disappears, moves or changes except what the timeline describes.")
FAMILY_PHYSICS = {
 "_decal_note": "",
 "footwear_display": "DISPLAY SHOT (footwear NOT worn): the person's legs and feet stay completely still and mostly out of frame; the shoe is held by the heel counter or toe box in the holding hand (hand, wrist and forearm always in frame) or stands fixed on a table or turntable. The shoe turns ONLY with the wrist (hand and shoe together, at most 30 degrees each way) - it never flips, spins, slips, floats or changes size, and exactly the listed shoe(s) appear, with every part, colour and lace/buckle as in the sheet. A turntable (30 cm wide, 5 cm high) is in the frame from the first frame; it turns ONLY while her hand (two fingertips on the rim, hand and forearm in frame) pushes it, the shoes fixed to it turn at the same speed, and the table, room, camera and the rest of her do not move. NOTHING in the picture moves on its own.",
 "home_decor": "DECOR: the item is already installed/placed and life-size (wall decals are never peeled, applied or faded in; no sticker "
               "sheet); the person stands 30-60 cm from it, parallel to its wall or surface, body turned about 45 degrees toward it, shoulder, "
               "arm and hand in one visible line; at most one hand touches or points at it, the other arm hangs at the side; no arm comes from "
               "the frame edge; only this product is on its wall; the wall, furniture and depth never change.",
 "footwear": "FEET AND LEGS: one shoe on each foot, the left and right shoes a mirrored pair; both big toes on the inner sides; the pair stays on both feet the whole time (never taken off, put on or swapped). LEGS NEVER ROTATE: every foot points exactly the way its shin and knee point in every frame, as in the first frame; no leg, knee, ankle or foot turns, pivots, twists, swings or angles; both knees stay in frame; the legs keep their length and thickness; no leg crosses or bends sideways or backwards; feet move only up and down (toes or heel) or straight along the floor by a few cm; the body does not turn.",
 "ethnic": "GARMENT: the exact length, pattern, colours and trims of the listing; a dupatta/pallu is exactly ONE, on the stated "
           "shoulder, a separate fabric layer that stays on that side and never merges with the kurta.",
 "everyday_clothing": "GARMENT: the exact length, pattern, colours and trims of the listing; it never changes between frames.",
 "home_furnishing": "TEXTILES: already in place; never rolled, unrolled, lifted, folded, shaken or taken down; one hand at most "
                    "smooths one edge.",
}


def _l(x):
    return "; ".join(map(str, x)) if isinstance(x, list) else str(x or "")


def scale_text(plan, height):
    """Product size against the person, computed in code (user 22-Nov): real longest side as % of height, palm and head."""
    ls = plan["product"].get("life_size", {})
    nums = cm_values(str(ls.get("dimensions_cm", "")))
    if not nums:
        return ""
    h = float(height or 160); man = h > 168
    palm, head, foot = (19 if man else 17), (23 if man else 21), (27 if man else 23)
    big = max(nums)
    return (f"SCALE LOCK: the product's longest side is {big:g} cm = {100 * big / h:.0f}% of the person's {h:g} cm height = "
            f"{big / palm:.1f}x the length of the person's hand ({palm} cm), {big / head:.1f}x the head height ({head} cm), "
            f"{big / foot:.1f}x the foot length ({foot} cm). Draw it at exactly this size against the body and the room - never "
            f"enlarged or shrunk to look better in frame; the hand wraps around it only as far as a real hand would.")


def lid_text(plan, locked=False):
    ps = plan.get("part_states") or []
    if locked:     # 22-Nov: nothing opens, closes or lifts inside a clip - every part keeps the state it has in the FIRST frame
        rows = "; ".join(f"{p.get('part')}: {p.get('start')}" for p in ps if isinstance(p, dict))
        return ("LID/CAP LOCK: every lid, cap, cover, latch, flap and stopper stays EXACTLY as the first frame shows it in every frame to the "
                "last (" + (rows + "; " if rows else "") + "a closed part stays closed, an open or removed part stays open or removed where it is). "
                "NOTHING is opened, closed, lifted, popped, unscrewed, snapped or replaced and no cover, cap or piece appears or disappears.")
    if not ps:
        return ("LID/CAP LOCK: every lid, cap, cover, flap and stopper is in EXACTLY the state the start still shows, in every single frame "
                "of the clip, to the last frame. It NEVER opens, closes, pops, flips, lifts, slides, unscrews or turns - not by itself and "
                "not by a hand, because no hand action on it is planned. A closed lid stays closed, an open one stays open.")
    rows = "; ".join(f"{p.get('part')}: {p.get('start')} at the start -> {p.get('end')} at the end"
                     + (f" ({p.get('how')})" if p.get('how') else "") for p in ps if isinstance(p, dict))
    return (f"LID/CAP STATE: {rows}. A part changes state ONLY through the hand action named in the beats (hand on the part, "
            f"a visible turn or lift, the removed part held in the hand or set on the surface); otherwise it keeps its state "
            f"in every frame and never opens, closes, pops or slides by itself.")


def open_text(plan, locked=False):
    if locked:
        return ""
    o = plan.get("open_state_spec") if isinstance(plan.get("open_state_spec"), dict) else {}
    if not o.get("used"):
        return ""
    return (f"OPEN-STATE SPEC: when opened / taken out the product looks exactly like this (see the open-state reference sheet): "
            f"{o.get('state')}. Inside: {_l(o.get('parts_inside'))}. Opened by: {o.get('how_opened')}. The lid or taken-out item "
            f"goes {o.get('removed_item_goes') or 'in the other hand'} and stays there. Nothing inside changes, multiplies or appears.")


def open_sheet_prompt(plan):
    o = plan.get("open_state_spec") if isinstance(plan.get("open_state_spec"), dict) else {}
    return (f"Reference sheet of the OPENED state of the product in Image 1 ({plan['product']['type']}): one 3:2 image on seamless pure "
            f"white, a 3 x 2 grid of six equal panels, no lines or text: 1 closed (front), 2 opening, 3 fully open from the front, 4 fully "
            f"open from above, 5 the taken-out item or the lid on its own, 6 a close-up of the contents. The open state is: "
            f"{o.get('state')}. Inside: {_l(o.get('parts_inside'))}. Every colour, part and count exactly as in Image 1, nothing invented, "
            f"no stickers, labels not printed on the product, prices, hands or models. Photoreal, sharp.")


_JUNK = re.compile(r"^\s*(Name and address|Importer|Packer|Manufacturer|Country of Origin|Customer Care|Generic Name|Common or Generic|"
                   r"Model Number|Model ID|HSN|Seller|Warranty|Care Instruction|Return Policy|Net Quantity.*Marketed)", re.I)


def clean_spec(txt, cap=2200):
    """22-Nov: listing legal text (importer/packer addresses, model numbers ...) is noise that the image model can print as text
    and that pushes the prompt toward its size limit - drop it, shorten marketing lines, cap the block."""
    out = []
    for ln in (txt or "").split("\n"):
        if _JUNK.match(ln):
            continue
        out.append(ln if len(ln) <= 260 else ln[:257] + "...")
    return "\n".join(out)[:cap]


CAM_DIST = {"wall_close": 0.6, "full_body": 2.6, "knee_up": 1.8, "waist_up": 1.2, "knee_down": 1.0, "shoulders_up": 0.8, "feet_close": 0.6,
            "hands_close": 0.5, "product_close": 0.5, "macro": 0.3}


def onscreen_text(plan, shot):
    """22-Nov: the product's size as a share of the PICTURE (the image model follows 'x% of the picture width' far better than cm)."""
    if not shot:
        return ""
    ls = plan["product"].get("life_size", {})
    nums = cm_values(str(ls.get("dimensions_cm", "")))
    if not nums:
        return ""
    mount = (plan.get("scene", {}).get("mount") or {}).get("type") if isinstance(plan.get("scene", {}).get("mount"), dict) else None
    dist = CAM_DIST.get(shot.get("framing_start"), 1.2) + (0.45 if mount in ("wall", "hanging") else 0.0)
    width_cm = 0.933 * dist * 100           # picture width at that distance (phone camera, about 50 degrees across a 9:16 frame)
    big = max(nums)
    return (f" ON SCREEN in the first frame: its longest side is about {100 * big / width_cm:.0f}% of the PICTURE WIDTH and about "
            f"{100 * big / (width_cm * 16 / 9):.0f}% of the PICTURE HEIGHT "
            f"(the person's shoulders are about {100 * 40 / (0.933 * CAM_DIST.get(shot.get('framing_start'), 1.2) * 100):.0f}% of the picture width) - "
            f"draw it that small or that large, never bigger.")


_SURF = re.compile(r"\b(counter|table|tray|shelf|dresser|desk|stool|mat|bed|sofa|floor|cabinet|top|surface|box|in her (left |right )?hand)\b", re.I)


def product_lock(slot, plan, spec_txt, ident, height=None, shot=None, locked=False):
    spec_txt = clean_spec(spec_txt)
    pr = plan["product"]; ls = pr.get("life_size", {})
    cols = "; ".join(f"{c.get('part', '')}: {c.get('name', '')} {c.get('hex', '')}".strip() for c in pr.get("colours", []) if isinstance(c, dict))
    t = (f"PRODUCT LOCK (slot {slot}): {pr['type']}. Visible parts: {_l(pr.get('parts_visible'))}. Colours: {cols}. "
         f"Real size: {ls.get('dimensions_cm', '')}" + (f" (parts: {ls['parts_cm']})" if ls.get('parts_cm') else "")
         + f" - {ls.get('body_relative', '')}. Held/worn: {ls.get('held_how', '')}.")
    _parts = [x for x in (plan.get("parts_role") or []) if isinstance(x, dict) and x.get("part")]
    if _parts:   # 23-Nov (user): exactly which part is used and which is not
        _used = [x for x in _parts if str(x.get("used", "")).strip().lower() in ("true", "yes", "1")]
        _not = [x for x in _parts if x not in _used]
        t += (" PARTS - USE / DO NOT USE: "
              + "; ".join(f"USE the {x['part']} ({x.get('role', '')}) - first frame: {x.get('first_frame', '')}; how: {x.get('how', '')}" for x in _used)
              + ("; " if _used and _not else "")
              + "; ".join((f"SHOW but do NOT use the {x['part']} ({x.get('role', '')}) - lying ON {x.get('first_frame')}, on that surface with a "
                            f"contact shadow (the surface is in the frame, in front of or beside her), never in the air, never touched or moved"
                           if str(x.get("shown", "")).strip().lower() in ("true", "yes", "1") and _SURF.search(str(x.get("first_frame", ""))) else
                           f"the {x['part']} ({x.get('role', '')}) is not in this shot") for x in _not)
              + ". " + " ".join(f"Never: {x['never']}." for x in _parts if x.get("never")))
    _hero = plan.get("hero") if isinstance(plan.get("hero"), dict) else {}
    if _hero.get("main_thing"):
        t += (f" MAIN THING TO SHOW (what the product is FOR): {_hero['main_thing']}. It is READY FOR USE from the first frame: "
              f"{_hero.get('ready_state', '')}. {_hero.get('must_see', '')} faces the camera, large and sharp, and the push-in ends on it. "
              f"Never just {_hero.get('never') or 'a plain front view of the unused product'}.")
    t += (" The ruler in the reference sheet's last panel is ONLY a size guide - it never appears in the scene or the video.")
    t += (" AS SOLD, ONE OF EACH: the product is assembled exactly as sold (cap on, dropper inside the bottle, a pair together - except a part that PARTS says is in use, which is where PARTS puts it); no "
          "SECOND copy of anything; the box, the spare and the other parts appear only where PARTS puts them (shown, untouched); its "
          "shape and label never change.")
    t += (" SIZE LOCK ACROSS THE CLIP: the product has exactly the same size relative to her hand, her body and the room in EVERY frame "
          "from the first to the last; only the camera's push-in makes everything look bigger together - the product never grows, "
          "swells, stretches or shrinks by itself.")
    t += (" SIZE SOURCE: the listing photo and the reference sheet are close-ups - NEVER copy their size; the size comes ONLY from the "
          "numbers below, against her hand.")
    t += " " + scale_text(plan, height) + onscreen_text(plan, shot) + " " + lid_text(plan, locked)
    if open_text(plan, locked):
        t += " " + open_text(plan, locked)
    if pr.get("drape") and str(pr["drape"]).lower() not in ("n/a", "na", "none", ""):
        t += f" Drape: {pr['drape']}."
    t += (" Exactly ONE of this product anywhere in the frame (no second or spare copy on the table, shelf or floor). Every part "
          "keeps its count (no extra or missing cap, lid, teat or strap). It keeps this exact size, shape, colours and every part from the first "
          "frame to the last; it never changes, morphs, swaps, flips, appears or disappears.")
    if ident:
        t += "\n" + ident.strip()
    if spec_txt:
        t += "\n" + spec_txt.strip()
    t += "\nNEVER for this product: " + _l(plan.get("forbidden"))
    return t


CONTINUITY += (" THE CAMERA MOVES, NOT THE PERSON (row 510, 22-Nov: she walked toward the camera instead of a push-in): the person stays on "
               "the SAME spot of the floor for the whole clip - feet planted, no step, no walk, no lean toward the camera; her size in the "
               "frame grows ONLY because the camera dollies closer, and her distance to the wall and the furniture never changes.")
CONTINUITY += (" NOTHING GROWS OR SHRINKS (baby care review, 22-Nov): during the push-in EVERYTHING in the picture grows by exactly the same "
               "amount, together - the product, the hand, the person, the furniture and the wall; no object ever changes size relative to the "
               "hand or to anything else, and the product keeps the exact size it has in the first frame.")
CONTINUITY += (" NO ENTRIES, NO AIR: no table, sliding table, shelf, stool, tray, trolley, board or any furniture or object slides, rolls, "
               "glides, is pushed, carried, lowered or fades into the frame; nothing floats, hovers or hangs in the air - in every frame every "
               "object rests on a visible surface or is held by a visible hand.")
CONTINUITY += (" LIGHT: the light, exposure, white balance and colour stay constant from the first frame to the last; the picture "
               "never flickers, pulses or changes brightness.")


def zoom_factor(fs, fe):
    """Zoom of the end frame for a push-in from framing fs to fe (the end frame is a crop of the action-end picture)."""
    d = FRAMINGS.get(fe, 3) - FRAMINGS.get(fs, 2)
    return round(min(1.3, max(1.15, 1 + 0.1 * d)), 2)      # 23-Nov: the room stays visible at the end (was up to 2.0)


CAM_BEAT = "continuing the same slow, even dolly-in (no stop, no jump, no cut)"


def beats_text(shot):
    """23-Nov (Day 6 QC 'transition jerk', 30 of 39 flagged reels): the beats said 'camera: locked' during the action and a
    separate push-in in the last 1.5 s; Omni rendered that as a HARD CUT to a close-up about 2 s into the take. Every beat
    now carries the SAME continuous camera move (the CAMERA line describes it once)."""
    out = []
    prev_ev = {}
    for b in sorted(shot["beats"], key=lambda b: float(b["t_start"])):
        lb = b.get("limbs") if isinstance(b.get("limbs"), dict) else {}
        ev = b.get("everything") if isinstance(b.get("everything"), dict) else {}
        if ev:   # 22-Nov: every part, every beat - moving parts in full, still parts named (keeps the prompt under Omni's limit)
            ev = {k: (CAM_BEAT if "camera" in k.lower() else v) for k, v in ev.items()}   # 23-Nov: one continuous camera move
            same = [k.replace("_", " ") for k, v in ev.items() if prev_ev.get(k) == v and not str(v).strip().lower().startswith(("still", "out of frame", "constant", "locked"))]
            mv = [f"{k.replace('_', ' ')}: {v}" for k, v in ev.items() if not str(v).strip().lower().startswith(("still", "out of frame", "constant", "locked"))
                  and prev_ev.get(k) != v]
            prev_ev = dict(ev)
            st = [k.replace("_", " ") for k, v in ev.items() if str(v).strip().lower().startswith(("still", "constant", "locked"))]
            of = [k.replace("_", " ") for k, v in ev.items() if str(v).strip().lower().startswith("out of frame")]
            out.append(f"- {float(b['t_start']):.1f}-{float(b['t_end']):.1f} s | MOVES: {'; '.join(mv) if mv else 'nothing'} | " +
                       (f"SAME AS THE BEAT BEFORE: {', '.join(same)} | " if same else "") +
                       f"COMPLETELY STILL: {', '.join(st) or '-'}" + (f" | OUT OF FRAME: {', '.join(of)}" if of else "") +
                       f" | action: {b.get('movement')} | held/supported by: {b.get('support')}"
                       + (f" | contact: {b.get('contact')}" if b.get('contact') and not str(b.get('contact')).lower().startswith('none') else ""))
            continue
        fg = b.get("fingers") if isinstance(b.get("fingers"), dict) else {}
        fingers = (f" | FINGERS: left hand: {fg.get('left')}; right hand: {fg.get('right')}" if fg else "")
        limbs = (f" | LIMBS: left hand/arm: {lb.get('left_hand_arm')}; right hand/arm: {lb.get('right_hand_arm')}; left leg/foot: "
                 f"{lb.get('left_leg_foot')}; right leg/foot: {lb.get('right_leg_foot')}; head: {lb.get('head_gaze')}; torso: "
                 f"{lb.get('torso')}; in frame: {lb.get('arms_in_frame')} arms, {lb.get('hands_in_frame')} hands, {lb.get('legs_in_frame')} legs") if lb else ""
        out.append(f"- {float(b['t_start']):.1f}-{float(b['t_end']):.1f} s | moves: {b.get('moves')} | movement: {b.get('movement')} | "
                   f"contact: {b.get('contact')} | stays still: {b.get('still')} | product: {b.get('product_state')} | "
                   f"camera: {CAM_BEAT} | gaze: {b.get('gaze')}{limbs}{fingers}")
    return "\n".join(out)


def room_master(reel, room, first_room):
    b = reel["bibles"][room]
    man = reel["persona"]["gender"] == "men"
    if room == first_room:
        refs = [("persona_sheet", "the person (face, hair, build)")]
        head = "Create the ROOM MASTER image of this reel: IMAGE_REF_0 is the persona sheet (the person)."
    else:
        refs = [(f"room_master:{first_room}", "the same person, outfit, light and home style"), ("persona_sheet", "the person")]
        head = (f"Create the ROOM MASTER image for the {room.replace('_', ' ')}: the same person, outfit and home style as IMAGE_REF_0, "
                f"now in this room; IMAGE_REF_1 is the persona sheet.")
    outfit = reel["outfit"] if reel["family"] not in RP.CLOTHING_FAMILIES else (
        "plain neutral home clothes (a plain beige T-shirt and off-white trousers)" if man else
        "plain neutral home clothes (a plain beige cotton kurta and off-white trousers)")
    prompt = (f"{head} {'He' if man else 'She'} stands on the spot about 1 m in front of {b['back']}, relaxed, arms at the sides, "
              f"looking at the camera with a soft smile. Camera: {RP.CAMERA['full_body']}, facing {b['back']}.\n"
              f"{reel['person_lock'].replace(reel['outfit'], outfit)}\n{RP.background_text(b)}\n{PHYSICS}\n{PHOTO}\n{NEGATIVE}")
    return dict(name=f"room_master:{room}", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
                refs=[r for r, _ in refs], ref_roles=dict(refs), prompt=prompt,
                note="Every other image of this room is an edit of this one - it fixes the room, the props, the light and the person's size.")


def first_only(f, s):
    """23-Nov (user: "the zoom should be in the video, not post-production"): the clip gets ONLY the first picture; the video model makes
    the camera move itself - a real dolly-in toward the product with natural depth. No end picture is made or cropped."""
    if os.environ.get("FK_END_MODE", "first") != "first":
        return f
    f["end_still"] = dict(name=f"slot_{s}_end", tool="none", first_only=True, prompt="(no end picture: the video model moves the camera itself)")
    f["end_action"] = None
    c = f["clip"]
    photo = bool(f.get("photo_shot"))
    # 23-Nov (user: "product changing in the next frame is a major problem", "always send the avatar as reference"):
    # the video model gets the first frame AND the product's references and the persona, with their roles declared first.
    refs = [f"slot_{s}_start"] + ([] if photo else [f"slot_{s}_reference_sheet"]) + [f"slot_{s}_listing_photo"] + ([] if photo else ["persona_sheet"])
    c["image_asset_ids"] = refs
    roles = ["the first image is the STARTING FRAME <FIRST_FRAME> - the video starts exactly on it"]
    k = 1
    if not photo:
        roles.append(f"<IMAGE_REF_{k}> is the product's 6-view reference sheet - its exact shape, every part and its label"); k += 1
    roles.append(f"<IMAGE_REF_{k}> is the product's listing photo - its true colours and printed text (its white background is not part of the scene)"); k += 1
    if not photo:
        roles.append(f"<IMAGE_REF_{k}> is the persona sheet - the person's identity: the same face, skin tone, hair and build in every frame")
    head = ("IMAGE ROLES: " + "; ".join(roles) + ". PRODUCT IDENTITY IN EVERY FRAME: frame after frame the product keeps EXACTLY the same "
            "shape, size, colours, cap, parts and label as in <FIRST_FRAME> and the reference images - it never changes, morphs, melts, "
            "swaps, flips or becomes a different product, not even for one frame; the person never changes either.\n")
    p = c["prompt"]
    p = p.replace("<FIRST_FRAME> is the first frame and <LAST_FRAME> is the last frame of ONE continuous", "<FIRST_FRAME> is the first frame of ONE continuous")
    p = p.replace("Animate between them following the timeline exactly.", "Animate from it following the timeline exactly.")
    p = re.sub(r"THE LAST FRAME IS THE FIRST FRAME[^\n]*\n", "AT 4.0 s every object, both arms and the product are in the same place and the same state as in <FIRST_FRAME>; "
               "only the camera has come closer - a REAL camera dolly-in filmed in this video (never a digital zoom or crop), with natural "
               "depth: the product and the person grow a little faster than the wall behind them.\n", p)
    p = p.replace("until it matches <LAST_FRAME> exactly at 4.0 s", "until 4.0 s, ending about 25% closer on the product")
    p = p.replace("exactly on <LAST_FRAME>", "at 4.0 s").replace("<LAST_FRAME>", "the end of the clip")
    # the product's look now travels as reference images - its long listing spec text is not needed in the clip prompt
    p = re.sub(r"PRODUCT SPEC \(slot[^\n]*\n(?:  [^\n]*\n)*", "PRODUCT SPEC: exactly as in the reference images above.\n", p)
    c["prompt"] = head + p
    return f


def photo_slot_files(reel, s, plan, shot, room):
    """22-Nov: product-photo shot, no person: the cleaned LISTING PHOTO is the first frame; only the camera moves."""
    pr = plan["product"]; ls = pr.get("life_size", {})
    lock = (f"PRODUCT: {pr['type']}, real size {ls.get('dimensions_cm', '')}. Exactly as in the photo: same design, colours, parts and "
            f"size against its surroundings; nothing is added, removed, moved or changed except what the cleanup says.")
    # 23-Nov (user): never the white studio listing photo - the product IN THE ROOM, no person, with the room visible around it
    b = reel["bibles"][room]
    place = b.get("surfaces", {}).get(s) or b.get("anchors", {}).get(s) or "its real place in this room"
    mt = (plan.get("scene") or {}).get("mount") if isinstance((plan.get("scene") or {}).get("mount"), dict) else {}
    wall = (mt or {}).get("type") in ("wall", "hanging")
    start = dict(name=f"slot_{s}_start", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
                 refs=[f"room_master:{room}", f"slot_{s}_listing_photo"],
                 ref_roles={f"room_master:{room}": "the room, its furniture, props and light (the person is removed)",
                            f"slot_{s}_listing_photo": "the product's exact design and colours (its white photo background is NOT part of it)"},
                 prompt=(f"Edit IMAGE_REF_0 (the room master): the SAME room, light and every background prop, but WITHOUT the person - nobody "
                         f"and no hand or arm in the picture. Place the {pr['type']} exactly as in IMAGE_REF_1 (design, colours, parts - the white "
                         f"background of that photo is NOT part of the product) in its real place: {place}"
                         f"{', stuck flat on the wall as printed artwork only, no white sheet or board around it' if wall else ''}, at its real "
                         f"life size {ls.get('dimensions_cm', '')}. COMPOSITION: the product's centre is at the centre of the frame (half-way across, 55% "
                         f"down). CAMERA: a real room view facing {b['back']}, the product about a third of the "
                         f"frame and clearly the subject, the room around it (wall, furniture, plant, lamp, light) clearly visible so it feels "
                         f"like a real home - never a plain or white background. {lock}\n{RP.background_text(b)}\n{PHOTO}\n{NEGATIVE}"))
    if os.environ.get("FK_END_MODE", "locked") != "push":   # 22-Nov: the last frame is the first frame, closer (local crop) - nothing can change
        end = dict(name=f"slot_{s}_end", tool="local-crop", aspect_ratio="9:16", refs=[], prompt="(built locally: the first frame, closer)",
                   locked=dict(base=f"slot_{s}_start", zoom=1.25, aim=[0.5, 0.55]))
    else:
      end = dict(name=f"slot_{s}_end", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
               refs=[f"slot_{s}_start"], ref_roles={f"slot_{s}_start": "this product's first frame - everything stays identical"},
               prompt=(f"Edit IMAGE_REF_0: the same picture with ONLY the camera pushed straight in ({shot['framing_end']}), centred on "
                       f"{shot['push_in_target']}. Nothing else changes: {shot['end_state']}. No person, hand or arm. {lock}\n{PHOTO}\n{NEGATIVE}"))
    clip = dict(name=f"slot_{s}_clip", tool="generate_video", model="gemini-omni-1.2-flash", resolution="360p", aspect_ratio="9:16",
                duration_seconds=4, image_asset_ids=[f"slot_{s}_start", f"slot_{s}_end"], out=f"clips/slot_{s}.mp4",
                prompt=(f"<FIRST_FRAME> is the first frame and <LAST_FRAME> is the last frame of ONE continuous take of exactly 4.0 "
                        f"seconds, portrait 9:16: a real room with the product and no person, where ONLY the camera glides in slowly and smoothly, ending with the product large and the room still visible around it. "
                        f"NOTHING IN THE PICTURE MOVES ON ITS OWN: no swaying, fluttering, light change, rotation, sliding or morphing; "
                        f"no person, hand or arm appears. No cut, no zoom-out.\nTIMELINE:\n{beats_text(shot)}\n{lock}\n{CONTINUITY}\n{NEGATIVE}"))
    return first_only(dict(slot=s, room=room, photo_shot=True, variant=reel["variant_of"][str(s)] + 1, product=pr["type"],
                action=shot["action_summary"], framing=f"{shot['framing_start']} -> {shot['framing_end']}",
                push_in=shot["push_in_target"], start_still=start, end_still=end, clip=clip), s)


def _pron(o, man):
    """The plan text may use the wrong pronoun for this persona (plans are shared across personas): rewrite he/his/him <-> she/her."""
    import re as _re
    if isinstance(o, str):
        if man:
            m = {"she": "he", "her": "his", "hers": "his", "herself": "himself"}
        else:
            m = {"he": "she", "his": "her", "him": "her", "himself": "herself"}
        def f(x):
            w = x.group(0); r = m[w.lower()]
            return r.capitalize() if w[0].isupper() else r
        return _re.sub(r"\b(" + "|".join(m) + r")\b", f, o, flags=_re.I)
    if isinstance(o, list):
        return [_pron(x, man) for x in o]
    if isinstance(o, dict):
        return {k: _pron(v, man) for k, v in o.items()}
    return o


DISPENSE_TXT = ("DISPENSING: the other hand is open, palm up, 5-8 cm directly below the nozzle in frame; ONE press puts one pea-size dollop "
               "in that palm and it stays there; it is never dispensed into the air or onto a surface.")
_IN_USE = re.compile(r"dollop|cream (is |already )?on|lotion (is |already )?on|on the back of her|in her (left |right )?palm|cap (is |hinged )?(fully )?open|"
                     r"cap (is )?off|cap already off|flip.?cap open|pump (is |already )?unlocked|unlocked|nozzle (is )?open|already open|palm (already )?open below", re.I)


def _closed(text):
    """Drop every 'in use' clause (dollop on a hand, cap open, pump unlocked) from a text - user 23-Nov."""
    if not isinstance(text, str):
        return text
    parts = re.split(r"(?<=[;.])\s+|;\s*", text)
    return " ".join(x for x in parts if x and not _IN_USE.search(x)).strip()


def closed_unless_used(plan, shot):
    """User 23-Nov: a cream/lotion/pump product is CLOSED and nothing is on her hands unless the shot's action IS the press."""
    import copy
    act = " ".join([str(shot.get("action_summary", ""))] + [str(b.get("movement", "")) for b in shot.get("beats", [])]).lower()
    if re.search(r"\b(press|presses|pressing|pump|pumps|pumping|dispens\w*|squeez\w*)\b", act) or any(
            isinstance(x, dict) and str(x.get("used", "")).strip().lower() in ("true", "yes", "1") and str(x.get("role", "")).lower() == "applicator"
            and re.search(r"\b(drop|dropper|apply|applies|dab|spray|sprays|pump|squeeze|stroke|glide)\w*", act) for x in (plan.get("parts_role") or [])):
        return plan, shot
    plan, shot = copy.deepcopy(plan), copy.deepcopy(shot)
    h = plan.get("hero") if isinstance(plan.get("hero"), dict) else None
    if h:
        h["ready_state"] = (_closed(h.get("ready_state", "")) + " The product is CLOSED (cap shut, pump locked) and nothing is on her hands.").strip()
        for k in ("main_thing", "must_see"):
            if _IN_USE.search(str(h.get(k, ""))):
                h[k] = f"the {plan['product'].get('category_item') or 'product'} itself, closed, its label and design facing the camera"
    plan["prerequisites"] = [x for x in (plan.get("prerequisites") or []) if not _IN_USE.search(str(x))]
    for x in (plan.get("part_states") or []):
        if isinstance(x, dict) and re.search(r"cap|lid|pump|nozzle|latch|flip", str(x.get("part", "")), re.I):
            x["start"] = x["end"] = "closed"
    shot["start_state"] = _closed(shot.get("start_state", "")) + " The product is CLOSED and there is no cream on any hand."
    if _IN_USE.search(str(shot.get("push_in_target", ""))):
        shot["push_in_target"] = "the product's label and design"
    shot["end_state"] = _closed(shot.get("end_state", ""))
    for b in shot.get("beats", []):
        for k in ("movement", "contact", "product_state", "support"):
            if isinstance(b.get(k), str) and _IN_USE.search(b[k]):
                b[k] = _closed(b[k]) or "unchanged"
        ev = b.get("everything") if isinstance(b.get("everything"), dict) else {}
        for k, v in list(ev.items()):
            if isinstance(v, str) and _IN_USE.search(v):
                ev[k] = _closed(v) or "still"
    return plan, shot


def slot_files(reel, s, plan, spec_txt, ident, family):
    room = reel["room_of"][str(s)]; b = reel["bibles"][room]
    shot = shots_of(plan)[reel["variant_of"][str(s)]]
    plan = _pron(plan, reel["persona"].get("gender") == "men")
    shot = shots_of(plan)[reel["variant_of"][str(s)]]
    plan, shot = closed_unless_used(plan, shot)
    _disp = bool(re.search(r"\b(press|presses|pressing|pump|pumps|pumping|dispens\w*|squeez\w*)\b", " ".join(
        [str(shot.get("action_summary", ""))] + [str(b.get("movement", "")) for b in shot.get("beats", [])]).lower()))
    PHY = PHYSICS + (" " + DISPENSE_TXT if _disp else "")
    if family in HANDLING_FAMILIES:   # 23-Nov rule 50 (Day 6 QC: floating products, wrong opening): one grip, held the whole take
        PHY += (" GRIP LOCK: from the first frame to the last the product is either held in ONE hand in a FULL GRIP - palm against it, "
                "all fingers wrapped around it, never balanced on fingertips, pinched or floating near the fingers - or it rests fully on "
                "the surface where it stays. It never leaves the hand, never changes hands, never rises without the hand, and no cap, "
                "lid, pump, wipe or part opens, comes off or comes out.")
    if shot.get("no_person"):
        return photo_slot_files(reel, s, plan, shot, room)
    # 22-Nov: locked last frame for every family; only a shot whose action really travels (a step, a slide, a walk) keeps the edited end frame
    locked = os.environ.get("FK_END_MODE", "locked") == "locked" and (family in LOCK_FAMILIES or str(shot.get("movement_type", "")).lower() not in ("step", "slide", "walk", "weight_shift"))
    pl = product_lock(s, plan, spec_txt, ident, reel["persona"].get("height_cm"), shot, locked)
    bg = RP.background_text(b)
    fam = FAMILY_PHYSICS.get("footwear_display" if reel.get("display") else family, "")
    swap = [k for k, owners in b["swap"].items() if s in owners]
    swap_txt = (f" In this shot the room's plain {', '.join(swap)} is REPLACED by this product (only one at a time)." if swap else "")
    ae = float(shot.get("action_end_s", 2.5))
    surf = b.get("surfaces", {}).get(s)
    sf_start = (f"   SURFACE: {surf} - it is part of the room master and visible in this frame; the product rests on it or is set "
                f"down on it; no table, shelf, tray or other surface is added.\n") if surf else ""
    sf_clip = (f"SURFACE: {surf} is in the frame from the first frame to the last; no table, shelf, stool or other surface appears, "
               f"moves or changes.\n") if surf else ""
    # user 22-Nov: every table, chair, stand or support the shot uses is IN THE FIRST PICTURE - never added in the middle
    _sc = plan.get("scene") or {}
    _sup = []
    if isinstance(_sc.get("surface"), dict) and _sc["surface"].get("name"):
        _sup.append(str(_sc["surface"]["name"]))
    if _sc.get("anchor"):
        _sup.append(str(b["anchors"].get(s, _sc["anchor"])))
    _sup += [str(p_.get("item")) for p_ in (_sc.get("props") or []) if isinstance(p_, dict) and p_.get("item")]
    _bt = " ".join(str(x_.get(k_, "")) for x_ in shot.get("beats", []) for k_ in ("movement", "contact", "support")).lower()
    _sup += [w_ for w_ in ("table", "chair", "stool", "sofa", "bed", "shelf", "counter", "cabinet", "dresser", "tray", "stand", "rack")
             if re.search(r"\b" + w_ + r"\b", _bt) and not any(w_ in x_.lower() for x_ in _sup)]
    sup_txt = ("SUPPORTS ALREADY IN THIS FIRST PICTURE (every one visible, in its final place, from the first frame): " + "; ".join(dict.fromkeys(_sup)) +
               ". No table, chair, stool, stand, shelf, tray or prop is added later; nothing rests on or stands against anything not in this list.\n") if _sup else ""
    ls = plan["product"].get("life_size", {})
    opened = bool((plan.get("open_state_spec") or {}).get("used")) and not locked
    start = dict(
        name=f"slot_{s}_start", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
        refs=[f"room_master:{room}", f"slot_{s}_reference_sheet", f"slot_{s}_listing_photo"] + ([f"slot_{s}_open_sheet"] if opened else []) + ["persona_sheet"],
        ref_roles={f"room_master:{room}": "fixes the room, every background prop, the light, the camera direction and the person's real size",
                   f"slot_{s}_reference_sheet": "the product's exact shape and every part",
                   f"slot_{s}_listing_photo": "the product's true colours",
                   "persona_sheet": "the person's face, skin tone and hair - they must match exactly",
                   **({f"slot_{s}_open_sheet": "the OPEN state: contents, parts and counts when opened or taken out"} if opened else {})},
        prompt=(f"Edit IMAGE_REF_0 (the room master). Keep EXACTLY: the same room and every background prop (bible below), the same "
                f"light, the same person (face, hair, body size against the room; IMAGE_REF_{3 + (1 if opened else 0)} is her persona sheet - "
                f"SAME PERSON IN EVERY PRODUCT (row 1183, 23-Nov: the avatar changed between products): the same face, the same skin tone "
                f"on the face, arms and hands, the same body build and height, the same hair and the same jewellery as the persona sheet "
                f"and the room master; never a different woman). "
                f"{'HER WHOLE HEAD AND FACE ARE INSIDE THE FRAME (the top of her head below the top edge) so she is recognisable. ' if shot['framing_start'] in ('waist_up', 'knee_up', 'full_body', 'shoulders_up') else ''}"
                f"Change only:\n"
                f"1. CAMERA: move to the {shot['framing_start']} position - {RP.CAMERA[shot['framing_start']]}; still facing {b['back']}.\n"
                f"2. PRODUCT: the {plan['product']['type']} exactly as in IMAGE_REF_1 (shape, every part) and IMAGE_REF_2 (true colours), "
                f"life-size {ls.get('dimensions_cm', '')} ({ls.get('body_relative', '')}); {ls.get('held_how', '')}.{swap_txt}"
                f"{' IMAGE_REF_3 shows the product OPENED (contents, parts and counts when opened or taken out) - use it whenever the product is shown open.' if opened else ''}\n"
                f"3. THE MOMENT (first frame): {shot['start_state']}\n"
                f"   COMPOSITION (the camera will zoom in toward the product, so it must sit here): "
                f"{'the product fills the right two-thirds of the frame, its centre about 60% from the left edge and 45% from the top; she is at the left edge' if shot['framing_start'] == 'wall_close' else 'the product is at the CENTRE of the frame - its centre about half-way across and 55% down from the top - large, sharp and unblocked'}.\n"
                f"   Already true and visible: {_l(plan.get('prerequisites'))}.\n"
                f"{sf_start}   {sup_txt}"
                f"   Anchor (the room's own furniture - wherever the text names a seat or surface it means this; no other "
                f"furniture is added; it is visible in this frame): {b['anchors'].get(s, plan['scene']['anchor'])}.\n"
                f"{pl}\n{reel['person_lock']}\n{bg}\n{PHY}\n{fam}\n{PHOTO}\n{NEGATIVE}"))
    end = dict(
        name=f"slot_{s}_end", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
        refs=[f"slot_{s}_start"] + ([f"slot_{s}_open_sheet"] if opened else []),
        ref_roles={f"slot_{s}_start": "this product's first frame - everything stays identical",
                   **({f"slot_{s}_open_sheet": "the OPEN state of the product (contents, parts, counts)"} if opened else {})},
        prompt=(f"Edit IMAGE_REF_0 (this product's first frame): the same continuous moment {4.0:.1f} s later, the camera moved straight "
                f"forward. Keep EXACTLY: the person, outfit, room, every background prop, the light and the product (same size, shape, "
                f"colours, every part). Change only:\n"
                f"{'IMAGE_REF_1 shows the product OPENED - when the result shows it open, it looks exactly like that.' + chr(10) if opened else ''}"
                f"1. THE RESULT (last frame): {shot['end_state']}\n"
                f"2. CAMERA: pushed straight in to the {shot['framing_end']} position - {RP.CAMERA[shot['framing_end']]} - centred on "
                f"{shot['push_in_target']}.\n{pl}\n{bg}\n{PHY}\n{fam}\n{PHOTO}\n{NEGATIVE}"))
    end_action = None
    lf = shot.get("last_frame") if isinstance(shot.get("last_frame"), dict) else {}
    zf = zoom_factor(shot["framing_start"], shot["framing_end"])
    try:
        zf = min(1.3, max(1.15, float((lf.get("push_in") or {}).get("zoom", zf))))
    except (TypeError, ValueError):
        pass
    changed = (str(lf.get("change", "none")).strip().lower() not in ("", "none", "n/a", "no change")
               and str(lf.get("changed_region", "none")).strip().lower() not in ("", "none") and len(str(lf.get("edit_prompt", ""))) >= 40)
    last_txt = ""
    if locked and changed:   # PLANNED LAST FRAME (OpenAI): an edit of the first frame with ONE change, pasted onto the first frame, cropped
        end_action = dict(
            name=f"slot_{s}_end_action", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
            refs=[f"slot_{s}_start"], ref_roles={f"slot_{s}_start": "this product's first frame - everything stays identical"},
            prompt=(f"Edit IMAGE_REF_0 (this product's first frame): the same picture. Camera, framing, lens, light and every object stay "
                    f"EXACTLY as in IMAGE_REF_0 - NO zoom, NO camera move. {lf['edit_prompt']} Identical to IMAGE_REF_0: "
                    f"{lf.get('identical', 'everything else')}. The person keeps exactly the same arms and hands as in IMAGE_REF_0 - no "
                    f"extra arm, hand or finger; the same face, expression, clothes and hair.\n{pl}\n{PHY}\n{fam}\n{PHOTO}\n{NEGATIVE}"))
        end = dict(name=f"slot_{s}_end", tool="local-composite", aspect_ratio="9:16", refs=[], prompt="(built locally: the planned change pasted on the first frame, closer)",
                   composite=dict(base=f"slot_{s}_start", edit=f"slot_{s}_end_action", zoom=zf))
        last_txt = (f"THE LAST FRAME IS THE FIRST FRAME, CLOSER, WITH ONE CHANGE ONLY: {lf['change']}. Everything else - every object, "
                    f"the other arm, head, torso, the light - is identical in both frames; nothing is added, removed, opened or moved.\n")
    elif locked:          # LOCKED END FRAME: the last frame is the first frame, only closer - a crop made locally (free), never generated
        end = dict(name=f"slot_{s}_end", tool="local-crop", aspect_ratio="9:16", refs=[], prompt="(built locally: the first frame, closer)",
                   locked=dict(base=f"slot_{s}_start", zoom=zf, aim=([0.6, 0.45] if shot["framing_start"] == "wall_close" else [0.5, 0.55])))
        last_txt = ("THE LAST FRAME IS THE FIRST FRAME, ONLY CLOSER: every object, both arms and the product are in the same place and the "
                    "same state in both frames; whatever moves in between goes out and comes back exactly. Nothing is added, removed, opened or moved.\n")
    elif os.environ.get("FK_END_MODE") == "composite":   # 22-Nov experiment: pixel-locked end frame (see continuity.py)
        zf = zoom_factor(shot["framing_start"], shot["framing_end"])
        end_action = dict(
            name=f"slot_{s}_end_action", tool="generate_nano_banana_image", aspect_ratio="9:16", image_size="1K",
            refs=[f"slot_{s}_start"] + ([f"slot_{s}_open_sheet"] if opened else []),
            ref_roles={f"slot_{s}_start": "this product's first frame - everything stays identical",
                       **({f"slot_{s}_open_sheet": "the OPEN state of the product"} if opened else {})},
            prompt=(f"Edit IMAGE_REF_0 (this product's first frame): the same continuous moment {ae:.1f} s later with the camera EXACTLY "
                    f"where it was - same position, same framing, same lens, NO zoom, NO push-in. Keep every pixel of the room, every "
                    f"background prop, the light, the person's face, hair, outfit and body, and every limb that is not part of the "
                    f"action IDENTICAL to IMAGE_REF_0. Change ONLY the acting hand/limb and the product to this result: "
                    f"{shot['end_state']} (ignore any camera movement in that text - the camera does not move).\n"
                    f"{pl}\n{PHY}\n{fam}\n{PHOTO}\n{NEGATIVE}"))
        end["composite"] = dict(base=f"slot_{s}_start", edit=f"slot_{s}_end_action", zoom=zf)
    # 22-Nov: the room list and person description are already IN both frames - the clip prompt only names them (keeps it far under 20k)
    clip_ctx = (f"PERSON AND ROOM: exactly as in <FIRST_FRAME> - the same woman (face, hair, height {reel['persona'].get('height_cm', 160)} cm, "
                f"outfit: {reel['outfit']}), the same {room.replace('_', ' ')}, every background prop in its place, the same light; "
                f"nothing in the room changes, moves, appears or disappears.")
    if reel["persona"].get("gender") == "men":
        clip_ctx = clip_ctx.replace("woman", "man")
    _cp = shot.get("camera_plan") if isinstance(shot.get("camera_plan"), dict) else {}
    _guard = (f"It is a REAL camera move filmed in this video (never a digital zoom or crop): it always moves TOWARD THE PRODUCT "
              f"({plan['product'].get('category_item') or plan['product']['type']} - {shot['push_in_target']}), never toward her face or hands, "
              f"smooth and continuous at one even speed for the whole 4 seconds, ending only about 15-25% closer with the product large AND "
              f"the room still visible - it never jumps or cuts to a closer shot; "
              f"no pan, tilt, roll, zoom-lens, focus pull or shake; it never stops, goes back or turns. No object moves unless the timeline says so.")
    if _cp and all(str(_cp.get(k_, "")).strip() for k_ in ("start", "move", "end")):     # 23-Nov: the camera move is PLANNED BY OPENAI
        cam_txt = (f"CAMERA (planned): start - {_cp['start']}; move - {_cp['move']}; end - {_cp['end']}. {_guard}\n")
    else:
        cam_txt = (f"CAMERA: from 0.0 s the camera starts at the start position ({RP.CAMERA.get(shot['framing_start'], shot['framing_start'])}) and "
                   f"glides in at ONE even, slow speed from 0.0 s to 4.0 s (the same speed during and after the action). {_guard}\n")
    clip = dict(
        name=f"slot_{s}_clip", tool="generate_video", model="gemini-omni-1.2-flash", resolution="360p", aspect_ratio="9:16",
        duration_seconds=4, image_asset_ids=[f"slot_{s}_start", f"slot_{s}_end"], out=f"clips/slot_{s}.mp4",
        prompt=(f"<FIRST_FRAME> is the first frame and <LAST_FRAME> is the last frame of ONE continuous real phone take of exactly "
                f"4.0 seconds, portrait 9:16. Animate between them following the timeline exactly.\n"
                f"{last_txt}{sup_txt}{cam_txt}"
                f"FORMAT: one continuous take - no cut, no jump, no time skip, no zoom out, nothing new enters the frame. The camera "
                f"moves in slowly and smoothly from the first second to the last, until it matches <LAST_FRAME> exactly at 4.0 s. "
                f"The person is ALIVE and ENGAGED, never a stiff pose staring into the lens (user 23-Nov): she mostly looks at the product and "
                f"enjoys it, glances at the camera once with a natural smile, shifts her weight a little, her shoulders and head move "
                f"naturally, she breathes and blinks. The ROOM feels alive too: warm daylight, a real lived-in home, and the camera move gives "
                f"natural depth - the background shifts slightly behind her as the camera comes in. Only the OBJECTS stay perfectly still. "
                f"Silent, no speech, no on-screen text.\n"
                f"ACTION: {shot['action_summary']} ({shot.get('counts', '')}).\nTIMELINE:\n{beats_text(shot)}\n"
                f"{sf_clip}{pl}\n{clip_ctx}\n{PHY}\n{fam}\n{CONTINUITY}\n{NEGATIVE}"))
    return first_only(dict(slot=s, room=room, variant=reel["variant_of"][str(s)] + 1, product=plan["product"]["type"],
                action=shot["action_summary"], framing=f"{shot['framing_start']} -> {shot['framing_end']}",
                push_in=shot["push_in_target"], start_still=start, end_still=end, clip=clip, end_action=end_action,
                sheet_scale=str(plan["product"].get("life_size", {}).get("dimensions_cm", "")),
                **({"open_sheet": dict(name=f"slot_{s}_open_sheet", prompt=open_sheet_prompt(plan), refs=[f"slot_{s}_listing_photo"], aspect_ratio="3:2")} if opened else {})), s)


def write(row_dir, reel, plans, specs_txt, idents, family):
    sd = os.path.join(row_dir, "shots"); os.makedirs(sd, exist_ok=True)
    first = reel["rooms"][0]
    for r in reel["rooms"]:
        json.dump(room_master(reel, r, first), open(os.path.join(sd, f"room_{r}.json"), "w"), indent=1, ensure_ascii=False)
    md = [f"# Row {reel['row']} - planned shots ({family}, persona {reel['persona']['name']})",
          f"Rooms: {', '.join(reel['rooms'])} | product order: {reel['order']}", ""]
    for s in reel["order"]:
        f = slot_files(reel, s, plans[s], specs_txt.get(s, ""), idents.get(s, ""), family)
        if reel["persona"].get("gender") != "men":
            f = _pron(f, False)
        json.dump(f, open(os.path.join(sd, f"slot_{s}.json"), "w"), indent=1, ensure_ascii=False)
        md.append(f"- slot {s} ({f['room']}): {f['product']} | variant {f['variant']} | {f['framing']} | {f['action']} | push-in: {f['push_in']}")
    json.dump(dict(segments=[dict(clip=f"clips/slot_{s}.mp4", slot=s, **{"in": 0.0, "out": 4.0}, zoom=1.0) for s in reel["order"]]),
              open(os.path.join(sd, "plan_skeleton.json"), "w"), indent=1)
    open(os.path.join(sd, "ORDER.md"), "w").write("\n".join(md) + "\n")
    return sd
