"""Presentation APPROACHES A-E per vertical family (REEL_PRESENTATION_IMPLEMENTATION_SPEC.md, user 16-Nov).

One approach per REEL, applied to ALL five product slots (never one approach per product). Each family has exactly five
alternatives, lettered A-E in the spec's order. Men's and women's verticals share the letters/IDs but get their own actions.
Makeup is NOT here yet (user 16-Nov: "don't add approaches for beauty now") - Makeup rows keep the Beauty pipeline route.

PER ROW (user 16-Nov): 02_BAU_DATA/row_approaches.csv has one line per sheet row; its "approach" column is the letter that row
uses (A-E). Empty or HOLD = the row is on hold and will not run. Edit the CSV directly or use
`pipeline.py setapproach <A-E|HOLD> <rows...>`. FK_APPROACH=<letter> / `prompt <row> <letter>` override one run.
"""
import json, os

# exact CSV label -> (family, variant). Aliases = older normalised names already used in this pipeline.
VERTICALS = {
    "Women's Ethnic Wear": ("ethnic", "women"),
    "Men Ethnic": ("ethnic", "men"), "Men's Ethnic Wear": ("ethnic", "men"),
    "women Footwear": ("footwear", "women"), "WomenFW": ("footwear", "women"), "Women's Footwear": ("footwear", "women"),
    "Men Footwear": ("footwear", "men"), "Men's Footwear": ("footwear", "men"),
    "Women western": ("everyday_clothing", "women"), "WomenWesternCore": ("everyday_clothing", "women"),
    "Men casual": ("everyday_clothing", "men"),
    "FashionWearables _Women": ("fashion_wearables", "women"), "FashionWearables _Men": ("fashion_wearables", "men"),
    "Home Decore": ("home_decor", None), "Home Decor": ("home_decor", None),
    "HomeFurnishing": ("home_furnishing", None),
    "household kitchen": ("kitchen", None), "House Hold Kitchen": ("kitchen", None),
    "Household suppliers": ("household_utility", None),
    "baby care": ("baby_care", None), "BabyCare": ("baby_care", None),
    "women fragrance": ("fragrance", "women"), "Men fragrance": ("fragrance", "men"),
    "Grooming Men": ("grooming", "men"),
}


def F(letter, fid, name, main, detail, display=False):
    """main / detail: a string (same for everyone) or {"women": ..., "men": ...}. display=True: footwear NOT worn (held / on a platform)."""
    return dict(letter=letter, id=fid, name=name, main=main, detail=detail, display=display)


# 17-Nov user: hanger shots came out physically wrong (top hanging sideways with the collar off the hook, trousers not
# held by the hanger, hooks hanging from nothing). Pasted VERBATIM into every plate and clip prompt that shows a hanger.
HANGER_PHYSICS = (
    "HANGER PHYSICS (any shot with a garment on a hanger): the hanger is HELD by the person's hand by its hook at chest height, "
    "or its hook sits over a real visible rail, wardrobe rod or door hook - never a hook hanging from nothing. "
    "TOPS / KURTAS / SHIRTS / JACKETS / DRESSES: ONE garment per hanger, hung UPRIGHT and SYMMETRIC - the hanger's two arms sit "
    "inside the garment's two shoulders, the collar or neckline is centred on the hanger neck right under the hook, both shoulder "
    "seams rest on the hanger ends, the front faces the camera, and the body and both sleeves fall straight down under gravity "
    "(no twist, no tilt, no garment hanging off one shoulder or sideways, no sleeve lifted or folded across). Buttons, plackets "
    "and hems hang in their natural vertical position. "
    "TROUSERS / PYJAMAS / SKIRTS / BOTTOMS: on their OWN hanger, either clipped by the waistband to a clip hanger (waistband "
    "horizontal and level, legs hanging straight down side by side) or folded once over the hanger's bar (legs folded "
    "evenly, hanging straight) - the hanger visibly carries the garment; never a hanger floating behind or above it. "
    "A SET (top + bottom): ONE hanger carries the whole set - the top hung on it as above, and the bottom folded once over the "
    "same hanger's bar UNDER the top, its folded legs hanging straight down below the top's hem (never a second hanger "
    "floating beside it). A SAREE: folded neatly over the hanger bar with the pallu and border falling straight. "
    "HANDS: exactly two, each traced along its own forearm to its own shoulder - ONE hand holds the hook at chest height, the "
    "other hand either hangs relaxed at his/her side or holds the hem edge on ITS OWN side of the body; never two hands from "
    "one arm. "
    "Plain everyday plastic or wooden hanger. The garment shape stays exactly the listing's - the hanger does not change its "
    "cut, length or drape. AVOID: garment hanging sideways, collar off the hook, hook attached to nothing, hanger behind "
    "the garment not touching it, garment floating against a wall, twisted or bunched fabric.")

FAMILIES = {
 "ethnic": dict(framing="full outfit, shoulder-to-feet for the main view", formats=[
  F("A", "mirror_try_on", "Mirror-selfie try-on",
    {"women": "Face a full-length mirror, phone in one hand, one foot slightly ahead. Free hand smooths the kurta front or lightly lifts the pallu/dupatta edge. Gentle quarter-turn (two small steps, no pivot on one foot) shows the side drape; return to a relaxed front pose.",
     "men": "Face a full-length mirror, phone in one hand, feet comfortably apart. Free hand straightens the kurta hem, collar or jacket placket. Gentle quarter-turn shows shoulder fit, side seam and length; return to front."},
    {"women": "Neckline, sleeve, embroidery or pallu/dupatta border, moving closer while keeping the reflection consistent.",
     "men": "Collar, buttons, cuff, embroidery or jacket texture, moving closer while keeping the reflection consistent."}),
  F("B", "garment_showcase", "Garment-focused showcase",
    {"women": "Direct to camera, full outfit visible. Arms clear of the silhouette; gently spread the pallu/dupatta or smooth the pleats. Small turn reveals the drape or side slit; let the fabric fall naturally.",
     "men": "Direct to camera, full outfit visible. Arms relaxed and slightly clear of the torso; touch the collar or straighten a cuff. Small turn shows the kurta slit, jacket profile and trouser fit."},
    {"women": "Worn close-up of print, border, pleats or sleeve finish.",
     "men": "Worn close-up of placket, cuff, fabric weave or an actual jacket pocket."}),
  F("C", "walk_pause_turn", "Walk, pause and turn",
    {"women": "Two short natural steps straight ahead (feet never cross, soles land flat), pause, then a quarter-turn made with two small steps (never pivoting on one foot). Lightly hold a loose pallu/dupatta only if needed. Let the fabric settle; finish with one foot slightly forward.",
     "men": "Two natural steps with relaxed shoulders, pause and quarter-turn. Briefly straighten the hem or jacket after stopping; finish in a comfortable stance."},
    {"women": "Hem/border or dupatta fall, then a stable detail.", "men": "Kurta hem/side slit or collar/cuff."}),
  F("D", "finishing_touches", "Getting-ready finishing touches",
    {"women": "Outfit already worn. Settle the dupatta or pallu, or adjust a sleeve/waist pleat. Briefly angle towards a mirror, then reveal the full outfit facing camera.",
     "men": "Outfit already worn. Straighten the collar, touch an actual button, adjust a cuff or settle an included Nehru jacket. Brief mirror check, then full-outfit reveal."},
    "The adjusted feature, hands moved enough to keep it visible. No long dressing sequence."),
  F("E", "held_to_worn", "Held-up garment to worn reveal",
    {"women": "Worn from the first frame (no hanger, no cut): one hand holds the dupatta/pallu border up at chest height to show its print, lets it settle back on the same shoulder, then a small side turn made with small steps.",
     "men": "Worn from the first frame (no hanger, no cut): one hand lifts the kurta's or jacket's front edge a little to show the fabric, lets it fall, then straightens the collar."},
    {"women": "Match the print/border/embroidery from the held-up view to the worn product.",
     "men": "Match the collar/buttons/texture from the held-up view to the worn product."}),
 ], constraints=[
  "Any hanger view (approach E, and any before-shot on a hanger): " + HANGER_PHYSICS,
  "Saree actions only for sarees; dupatta actions only when a dupatta is included; jacket actions only when the jacket belongs to the listing.",
  "Use a pocket pose only if the pocket actually exists.",
  "Mirror approach (A) intentionally shows the phone; direct-camera approaches never introduce an unexplained phone or mirror.",
  "MIRROR-SELFIE PHONE (user 23-Nov): when she holds a phone as if filming herself in a mirror, the CAMERA IS THE MIRROR: the phone's BACK (its camera lenses) faces the camera and the screen faces HER - the phone screen is NEVER shown to the camera; she holds it at chest-to-face height in one hand, looking at its screen or at the camera-mirror; no mirror frame or reflection is drawn.",
  "Approach E: EVERY product gets its own brief held-up-to-worn sequence (overrides the old one-hanger-per-reel rule for E only).",
  "Clothing is WORN for its main presentation and its detail; a held-up view never replaces the worn view.",
  "Reference looks: Ritu = casual full-length mirror-selfie saree try-on (A); Aishwarya = direct garment showcase, shoulder-to-feet, small turns (B).",
 ]),

 "footwear": dict(framing="knee-down (both knees always in frame so the legs are visibly attached; push-in goes closer)", formats=[
  F("A", "standing_fit", "Standing fit check",
    "Standing still, both soles flat, feet parallel and pointing straight at the camera; the weight shifts slowly from one foot to the other and the toes of one foot lift a little with the heel down, then settle. No turning, rotating or angling of any foot.",
    "Toe shape, strap, upper or fastening."),
  F("B", "walk_stop", "Step and stop",
    "ONE short straight step forward (at most 25 cm) toward the camera, then both soles flat; no turning, no crossing feet.",
    "Side of the sole and heel edge."),
  F("C", "seated_adjustment", "Seated adjustment",
    "Seated ON the room's sofa or chair (seat visible under the person, hips on it, knees about 90 degrees, both feet flat): do ONLY what the slot's ALLOWED ACTIONS line allows - tie a lace or fasten a strap that is shown open first; for slip-ons and anything with nothing to fasten keep both feet in the pair and only lift the toes of one foot a little and lower them; the hand reaches the foot on its own side; both feet end flat.",
    "Fastening, stitching and material."),
  F("D", "side_back", "Weight shift",
    "Standing with feet shoulder-width apart, both soles flat and pointing forward; the weight shifts slowly from one foot to the other and the heel of the unloaded foot lifts a little with the toes down. No turning of the body, legs or feet.",
    "Heel counter, back strap or outsole edge as the heel lifts."),
  F("E", "held_to_worn", "Seated show (pair worn)",
    "Seated with the pair already worn, both hands resting on the knees, feet flat: the toes of one foot lift a little with the heel down, then lower (one continuous take; no hand reaches down; the shoes never leave the feet).",
    "The upper and toe of that foot."),
  F("F", "pov_look_down", "Wearer's look-down (POV)",
    "Camera at the wearer's eye line looking down at the feet on the floor: both feet planted and parallel; the toes of one foot lift a little and settle. No turning.",
    "Top-down view of the toe, vamp and strap or lace pattern."),
  F("G", "step_up", "Step up a single stair or threshold",
    "One foot steps straight up onto a single low step or threshold that already exists in the room (at most 20 cm high), the weight shifts onto it and the other foot follows straight up; no turning, no twisting, the legs stay parallel.",
    "Side of the sole, heel and grip on the step."),
  F("H", "full_look_to_feet", "Full look to the feet",
    "Standing straight, the whole outfit in frame from head to feet, the weight shifting once from one foot to the other; no turning.",
    "The shoes with the hem of the outfit."),
  F("I", "tap_and_settle", "Toe tap and settle",
    "Standing, the heel of one foot stays on the floor while its toes lift a little and tap down once, then the foot settles flat; weight stays on the other foot; nothing leaves the floor; no turning.",
    "Front three-quarter of the toe and upper."),
  F("J", "pair_on_floor_step_in", "Pair worn, toe lift",
    "Both feet already in the pair, standing still; the toes of one foot lift a little with the heel down and lower once; nothing is put on or taken off.",
    "The pair side by side."),

  # ---- 22-Nov DISPLAY approaches K-V (user): the footwear is NOT worn; held in the hand or turned on a platform. Person's legs never move.
  F("K", "hold_turn_30", "Hold and turn 30 degrees",
    "Waist-up. ONE shoe of the pair is held in her/his right hand by the heel counter at chest height, toe to the camera, the other hand relaxed at the side. The WRIST (hand and shoe together) turns the shoe slowly 30 degrees to the left, then back through the front to 30 degrees to the right, ending toe-to-camera. The shoe never leaves the hand; no flip.",
    "Toe box and upper.", display=True),
  F("L", "platform_turn", "Pair on a turning platform",
    "Waist-up, the person standing beside a waist-high table or dresser, the far arm relaxed at the side, looking at the camera. The PAIR stands upright on a small round turntable (30 cm wide, 5 cm high, plain neutral top) on that surface, fixed on it. Her NEARER hand rests two fingertips on the turntable's rim and turns it by hand, slowly: 30 degrees to the left, then back through the front to 30 degrees to the right, the shoes turning with it at the same speed; the platform moves ONLY while her hand pushes it; table, room and camera do not move.",
    "The pair's toe and side profile.", display=True),
  F("M", "pair_two_hands", "Pair held in both hands",
    "Waist-up. One shoe in each hand, each held by its heel counter at chest height side by side, toes to the camera, elbows close. Both wrists turn the shoes together 20 degrees outward, then back to the front. Nothing leaves the hands.",
    "The pair side by side.", display=True),
  F("N", "shoe_on_palm", "Shoe on the open palm",
    "Waist-up. ONE shoe rests on her/his open right palm at chest height in side profile, toe to the left of the frame, the fingers flat and not gripping. The palm tilts 15 degrees so the toe rises, then returns level. The other hand hangs relaxed.",
    "Side profile of the upper and sole edge.", display=True),
  F("O", "presenting_palm", "Pair on a table, presenting hand",
    "Waist-up, beside a waist-high table or dresser with the PAIR standing on it, upright, still. The nearer hand, palm up, glides slowly 20 cm from the heel side to the toe side 15 cm ABOVE the pair, never touching it, while the person looks at the camera; the shoes never move.",
    "The pair's toe and front.", display=True),
  F("P", "lift_and_turn_one", "Lift one and turn it",
    "Waist-up, beside a waist-high surface with the PAIR on it. The nearer hand lifts ONE shoe straight up 15 cm by the heel counter to chest height, then the wrist turns it 20 degrees to the left to show its side; the other shoe stays on the surface, the other hand rests at the side.",
    "Side of the lifted shoe.", display=True),
  F("Q", "toe_tilt", "Heel hold, toe tilt",
    "Waist-up. ONE shoe held at chest height by the heel counter in the right hand, toe to the camera; the wrist tilts the toe 20 degrees up, then back level. No turning, no flip.",
    "Toe cap and vamp.", display=True),
  F("R", "bring_forward", "Hold and bring forward",
    "Waist-up. ONE shoe held at chest height in the right hand, side profile; the arm moves it 15 cm straight toward the camera and holds it there, the elbow staying bent; the body does not lean.",
    "The side of the shoe, close.", display=True),
  F("S", "heel_to_camera", "Heel to camera, wrist turn",
    "Waist-up. ONE shoe held by the toe box in the right hand at chest height, heel to the camera; the wrist turns it 25 degrees to the right, then back to the front. The shoe never leaves the hand; no flip.",
    "Heel counter and back of the shoe.", display=True),
  F("T", "shelf_point", "Pair on a shelf, pointing hand",
    "Waist-up, beside a shoulder-height shelf or dresser top with the PAIR standing on it, upright, still. The nearer hand points with the index finger and moves 20 cm slowly along the pair, 10 cm in front of it, never touching it, while the person looks at the camera; the shoes never move.",
    "The pair on the shelf.", display=True),
  F("U", "sole_tilt", "Sole to camera, tilt",
    "Waist-up. ONE shoe is already held at chest height in the right hand with its sole facing the camera from the first frame (never flipped on screen); the wrist tilts it 15 degrees up, then back to the front.",
    "Sole pattern and heel.", display=True),
  F("V", "platform_turn_one", "Single shoe on a turning platform",
    "Waist-up, beside a waist-high table or dresser, the far arm relaxed at the side. ONE shoe stands upright on a small round turntable (30 cm wide, 5 cm high), fixed on it. Her nearer hand rests two fingertips on the turntable's rim and turns it by hand, slowly: 30 degrees to the left, then back through the front to 30 degrees to the right, the shoe turning with it; the platform moves ONLY while her hand pushes it; table, room and camera do not move.",
    "The shoe's side profile.", display=True),
 ], constraints=[
  "DISPLAY APPROACHES K-V (22-Nov): the footwear is NOT worn - it is held in a hand or stands on a table or turntable; the person's legs and feet stay still and the camera stays above the waist; ONLY a shoe (wrist turn of at most 30 degrees) or a platform that HER HAND turns (at most 30 degrees left and right) moves; NOTHING moves on its own. The shoe is never flipped, thrown, spun, worn, put on or taken off; sealed boxes stay closed; a hand-held shoe is gripped by the heel counter or toe box, never by the laces.",
  "Adapt to the actual footwear type: not every women's shoe has a heel, not every men's shoe has laces.",
  "LEGS NEVER ROTATE (user 21-Nov, the #1 footwear defect; approaches A-J, worn): no leg, knee, ankle or foot turns, pivots, twists, swings or angles; every foot points the way its shin and knee point, as in the first frame; both knees stay in frame; movements are only toes up, heel up, a weight shift, a straight slide of at most 10 cm, or one straight step of at most 25 cm.",
  "ANATOMY (user 20-Nov, Day 5): ankles, knees and toes move only within their normal range; no backward knees or extra joints. Every leg attached to a visible body; any foot not stepping rests on the floor with weight and contact shadow - nothing hovers, slides or levitates. Exactly two legs and two feet, one shoe on each foot.",
  "SAME BACKGROUND (user 20-Nov): every shot in the SAME room and on the SAME floor as the rest of the reel; the room/floor in every plate is an edit of the reel's first plate.",
  "CLIENT 16-Nov: construction EXACTLY as the listing (toe post vs slide vs toe loop vs ankle strap vs crossed/single band, heel, sole colour, buckle side); a slide is never a thong.",
  "CLIENT 16-Nov: feet anatomy - BOTH big toes on the INNER side of the feet, little toes on the OUTER sides, 5 toes; the two shoes a mirrored identical pair.",
 ]),
 "everyday_clothing": dict(framing="full outfit; waist-to-feet prominent for bottoms", formats=[
  F("A", "mirror_fit", "Mirror fit check",
    {"women": "Phone in one hand; free hand smooths the top/dress at the side. Gentle quarter-turn, then a relaxed front pose.",
     "men": "Phone in one hand; free hand straightens the shirt/T-shirt hem. Gentle quarter-turn, then a relaxed front pose."},
    {"women": "Neckline, sleeve or waist construction.", "men": "Collar, sleeve or fabric."}),
  F("B", "direct_fit", "Direct fit showcase",
    {"women": "Front view then a small side turn made with small steps (no pivot on one foot); arms clear of the silhouette.",
     "men": "Front view then a small side turn; arms relaxed with the garment visible."},
    "Seam, print, fastening, placket or material."),
  F("C", "walk_settle", "Walk and settle",
    {"women": "Two short straight steps (feet never cross, soles land flat), pause with one foot slightly forward; let the garment settle.",
     "men": "Two short straight steps (feet never cross, soles land flat), pause comfortably; let the garment settle."},
    "Hem, trouser leg or fabric fall as relevant."),
  F("D", "finishing_touches", "Finishing touches",
    {"women": "Adjust an actual sleeve, collar or waistband detail; finish facing camera.",
     "men": "Adjust the cuff, collar or overshirt front; finish facing camera."},
    "The adjusted construction feature."),
  F("E", "held_to_worn", "Held-up to worn",
    "Garment worn from the first frame: seated on the sofa edge, the person stands up and lets the garment settle, then a small side angle (one continuous take, no hanger).",
    "Match print, seam or construction to the opening view."),
 ], constraints=[
  "Any hanger view (approach E, and any before-shot on a hanger): " + HANGER_PHYSICS,
  "Top listings: keep the supporting bottoms consistent across the reel. Bottom listings: waist-to-feet framing prominent.",
  "Do not invent pockets, fastenings or extra garments.",
  "Mirror approach (A) intentionally shows the phone; other approaches never show an unexplained phone or mirror.",
  "MIRROR-SELFIE PHONE (user 23-Nov): when she holds a phone as if filming herself in a mirror, the CAMERA IS THE MIRROR: the phone's BACK (its camera lenses) faces the camera and the screen faces HER - the phone screen is NEVER shown to the camera; she holds it at chest-to-face height in one hand, looking at its screen or at the camera-mirror; no mirror frame or reflection is drawn.",
 ]),

 "fashion_wearables": dict(framing="by subtype: ankle-level anklets, ear-level earrings, wrist-level watches, waist-level belts; small items kept prominent", formats=[
  F("A", "worn_check", "Worn styling check",
    {"women": "Eyewear: slight head turn. Watch: turn wrist towards camera. Earrings: tuck hair behind the ear. Necklace: keep the neckline unobstructed. Bag: angle shoulder/forearm. Belt: small waist-level turn.",
     "men": "Eyewear: slight head turn. Watch: turn wrist towards camera. Chain: keep the neckline visible. Bag: angle shoulder/body. Belt: small waist-level turn."},
    "Frame, dial, jewellery setting, buckle or bag hardware as appropriate."),
  F("B", "put_on_reveal", "Put on and reveal",
    {"women": "Put on glasses, slip on a suitable bracelet or lift the bag onto the shoulder. Complex clasp: show only the final adjustment.",
     "men": "Put on glasses, settle the watch or lift the bag onto the shoulder. Complex fastening: show only the final adjustment."},
    "Fit and fastening with fingers clear of the feature."),
  F("C", "feature_closeup", "Feature close-up",
    {"women": "Worn item: gently rotate the wrist, angle the eyewear or hold the jewellery steady.",
     "men": "Worn item: rotate the wrist, angle the eyewear or hold the accessory steady."},
    "Dial, frame, clasp, stones, buckle or zip as listed."),
  F("D", "natural_use", "Natural-use moment",
    {"women": "Bag: reach for the handle. Watch: glance at the wrist. Eyewear: look towards the window. Earrings: tuck hair back.",
     "men": "Bag: reach for the handle. Watch: glance at the wrist. Eyewear: look towards the window. Belt: move the shirt clear of the buckle."},
    "The actual feature revealed by that action."),
  F("E", "held_to_styled", "In-hand to styled",
    "Already worn or carried from the first frame: one hand touches it to show its shape (lifts the bag a little by its handle, turns the watch face to camera, touches the frame of the glasses), then a relaxed pose (one continuous take).",
    "Match the held feature to the styled item."),
 ], constraints=[
  "Resolve the action from each product's actual subtype; for unlisted subtypes derive a physically appropriate action, never an unrelated one.",
  "One plain supporting outfit for the whole reel unless the listing itself requires a change.",
 ]),

 "home_decor": dict(framing="the person and the item in ONE frame: camera fixed 2-2.5 m from the wall or surface, level, the item life-size beside the person; the push-in goes closer", formats=[
  F("A", "palm_glide", "Palm glide (feel the finish)",
    "Close-up BESIDE the wall item (never in front of it, never pointing at it): the item fills the right two-thirds of the frame, she stands at the left edge in profile, shoulder and side of the face visible, her flat right palm resting on the item's surface; the palm glides slowly 10 cm across it and back to exactly where it started, feeling the finish. A non-wall item: the same on its own surface.",
    "The item's finish and pattern under the palm."),
  F("B", "fingertip_trace", "Fingertip trace",
    "Same close-up beside the item: her right index fingertip rests on one line of the design and traces slowly 8 cm along it and back to the start, in contact all the time. A non-wall item: traces one edge or pattern line on its surface.",
    "The traced line of the design."),
  F("C", "edge_feel", "Feel the edge",
    "Same close-up beside the item: her right thumb and index fingertip rest on one edge or corner of the item and smooth slowly 4 cm along it and back to the start. A non-wall item: feels its rim or edge.",
    "The edge and its finish."),
  F("D", "back_of_hand", "Back of the fingers",
    "Same close-up beside the item: the backs of her right fingers brush lightly 10 cm across the surface and back to the start, feeling the texture. A non-wall item: the same across its surface.",
    "The surface texture."),
  F("E", "press_feel", "Press and feel",
    "Same close-up beside the item: her right fingertips press lightly 1 cm into the surface and ease off, the palm then resting flat for a moment; the hand ends exactly where it started. A non-wall item: the same on its surface.",
    "The surface where the fingertips rest."),
 ], constraints=[
  "HOME DECOR (user 22-Nov): the item is life-size and ALREADY in place - never peeled, applied, hung, unrolled, unpacked, held up as a sheet or faded in; a sticker set is shown INSTALLED in the arrangement of the listing photo.",
  "WALL ITEMS ARE SHOWN BY TOUCH IN A CLOSE-UP (user 22-Nov): the camera is 1.0 m from the wall facing it straight on, the item fills the right two-thirds of the frame and the person stands at the LEFT edge in profile BESIDE it (never in front of it, never pointing at the wall); only her shoulder, the side of her face and her right arm are visible, the arm joined to the shoulder; one hand touches the item and feels it in ONE way (palm glide, fingertip trace, edge feel, back of the fingers, press); the movement goes out and comes back exactly; contact stays on the surface all the time; the other arm hangs straight down out of frame.",
  "NO BACKING SHEET: a decal is only its printed artwork stuck on the wall - no white board, paper or frame around it; the white of the listing photo is not part of the product.",
  "ONE ITEM, ONE WALL: only this product is on its wall; the same wall, furniture and light all reel; no mirror. Real size: compare the item with the person (a 12 cm butterfly decal is palm-sized; a 60 x 90 cm decal reaches from her shoulder to above her head).",
 ]),
 "home_furnishing": dict(framing="the textile large and edge-to-edge where installed", formats=[
  F("A", "spread_smooth", "Spread and smooth", "Smooth the bedsheet, spread the throw, settle the cushion cover or smooth the relevant textile.", "Texture, print or seam."),
  F("B", "before_furnished", "Before to furnished", "The product already installed (on the bed, sofa, window, floor or table): the person steps beside it and looks at it (one continuous take).", "Corner fit, border or finished edge."),
  F("C", "fabric_fall", "Fabric and fall", "Lift and gently release a small textile section; draw a curtain panel slightly aside. Rigid-backed rugs: show edge and surface without pretending they drape.", "Folds, weave or border."),
  F("D", "everyday_use", "Everyday-use view", "Sit beside the cushion, settle the throw on the lap or step naturally onto the rug, as fits the listing.", "Product in ordinary use."),
  F("E", "folded_to_place", "Folded to in place", "The product already in place: one hand straightens one corner or edge; never lifted, folded or shaken (one continuous take).", "Matching print and finish."),
 ], constraints=["Separate actions for curtains, rugs, bedding, throws and cushions.", "No invented performance claims.", "Never shake or spread a sheet in the air."]),

 "kitchen": dict(framing="countertop, product large; hands only", formats=[
  F("A", "counter_demo", "Countertop demonstration", "Place on a clean counter and perform one intended action.", "Handle, lid, rim, control or working surface."),
  F("B", "preparation", "Preparation task", "Mix, scoop, pour, arrange or another actual supported preparation task.", "Product interacting with ingredients or relevant contents."),
  F("C", "access_fill", "Open, fill and close", "Containers/storage: open, add contents and close. Other items: their actual access/load/ready sequence, without inventing a lid.", "Real opening, closure or access feature."),
  F("D", "serve_present", "Serve and present", "Serve with suitable plates, bowls, trays or utensils; for tools/appliances present the result beside the clearly visible tool.", "Shape, finish or working/serving surface."),
  F("E", "stored_to_ready", "Stored to ready", "Take from an appropriate shelf/rack, place on the counter, show it ready for intended use.", "Grip or construction."),
 ], constraints=["Check all five listings against the approach before generating; adapt to their real function.", "No invented airtightness, heat resistance or appliance functionality."]),

 "household_utility": dict(framing="product large in its real utility location; hands only", formats=[
  F("A", "one_task", "One-task demonstration", "Perform one intended wipe, sweep, sort, hold or storage action.", "Working part."),
  F("B", "task_before_after", "Before to completed task", "One continuous take: the product is used once on a small, realistically untidy spot, which visibly becomes clean/tidy only where it was used.", "Product visible in or beside the completed task."),
  F("C", "feature_demo", "Feature demonstration", "Operate a real lid, clip, handle, wheel or folding mechanism.", "Mechanism in action."),
  F("D", "in_place", "In-place usefulness", "Show the product in its laundry, shelf, bathroom or utility location.", "Fit and accessible working parts."),
  F("E", "retrieve_use_return", "Pick up, use and put back", "Retrieve the item, perform one brief action and return it.", "Grip, storage feature or finish."),
 ], constraints=["No invented capacities or dramatic unsupported cleaning transformations."]),

 "baby_care": dict(framing="caregiver's hands; a baby is not required", formats=[
  F("A", "caregiver_inspection", "Caregiver inspection", "Hold steadily and turn to show construction.", "Fabric, fastening, handle or actual component."),
  F("B", "prepare_use", "Prepare for use", "Open the changing mat, prepare the bib or set up the item for its intended task.", "Closure, edge or setup feature."),
  F("C", "nursery_placement", "Nursery placement", "Place it in an appropriate nursery or changing-area location.", "Product clearly visible in the setting."),
  F("D", "feature_demo", "Relevant feature demonstration", "Fasten the bib, open a pocket or demonstrate an actual adjustment.", "Feature in action."),
  F("E", "routine_preparation", "Routine preparation", "Retrieve from an organiser and set it ready for use.", "Product and included accessories only."),
 ], constraints=["Age- and product-appropriate handling; no feeding, medical or developmental claims.", "No loose styling props in an infant sleep space; no unsafe use."]),

 "fragrance": dict(framing="bottle large, label readable", formats=[
  F("A", "bottle_showcase", "Bottle showcase", "Hold around chest level, label facing camera; turn the bottle slightly while keeping the label readable.", "Label, cap and bottle finish."),
  F("B", "getting_ready", "Getting-ready finish",
    {"women": "Pick up from the dressing table, apply appropriately once and lower the hand.",
     "men": "After a brief collar/cuff adjustment, pick up and apply appropriately once."},
    "Bottle upright and readable."),
  F("C", "application", "Application close view", "For a suitable spray, apply towards the wrist once, then lower the arm; adapt for the actual applicator.", "Bottle and its actual atomiser/roll-on/applicator."),
  F("D", "vanity_pickup", "Vanity pick-up", "Reach in, lift the bottle and turn its front towards camera.", "Cap removal or actual applicator."),
  F("E", "ready_to_leave", "Ready-to-leave moment",
    {"women": "Already dressed, apply appropriately, put the bottle down and reach for a bag.",
     "men": "Already dressed, apply appropriately, put the bottle down and reach for keys/bag."},
    "Bottle remains prominent."),
 ], constraints=["Follow the actual product and applicator; not every fragrance is a wrist spray.", "No invented notes, longevity or visible scent effects."]),

 "grooming": dict(framing="tool head / application area large", formats=[
  F("A", "mirror_routine", "Mirror routine", "Perform one appropriate grooming action; slight head turn only when needed to expose the relevant area.", "Tool head, application area or packaging."),
  F("B", "product_to_use", "Product to application", "Show the product, then a small appropriate application or intended use.", "Texture or contact point without obscuring it."),
  F("C", "feature_closeup", "Feature close-up", "Demonstrate the actual control, attachment, comb, cap or dispenser.", "Selected feature operating."),
  F("D", "finishing_touch", "Finishing touch", "Neaten the beard edge, comb hair or use a suitable finishing product.", "Naturally treated area."),
  F("E", "shelf_use_return", "Shelf to use to return", "Pick up from the grooming shelf, perform a brief intended action and return it.", "Label or working head."),
 ], constraints=["Resolve trimmers, razors, beard products, hair products and skincare separately.", "No instant hair-growth, skin-lightening or exaggerated transformation effects."]),
}

LETTERS = "ABCDEFGHIJKLMNOPQRSTUV"
DISPLAY_LETTERS = "KLMNOPQRSTUV"   # footwear approaches where the shoes are not worn (22-Nov)   # A-E for every family; footwear also has F-J (user 20-Nov)


GENERAL = [
    "HOLDING HAND ALWAYS VISIBLE (user 22-Nov): whenever a hand holds, pinches or supports a product, that hand, wrist and forearm are in frame in every frame; never held by a hand outside the frame; no arm enters from the frame edge without a visible shoulder or body.",
    "DISPENSING (user 22-Nov): a pump, squeeze bottle or tube releasing cream, lotion, gel, soap or oil - the other hand is open, palm up, 5-8 cm directly below the nozzle in frame; one pea-size dollop lands in that palm and stays there; never dispensed into the air or onto a surface.",
    "PHYSICS FROM THE DAY 6 REVIEW (user 21-Nov, every vertical): SUPPORT - in every frame each object is gripped by a visible hand (forearm in frame) or rests on a visible surface with a contact shadow, never hanging in the air or held by fingertips alone; before any action that needs both hands the product is first set down on the surface. GRIP - held by its body, fingers never covering the cap, nozzle or label; the SAME hand holds it from the first frame to the last; to show a side the wrist turns (hand and product together, at most 30 degrees), the product never slides inside the grip. PACKAGING - sealed packs, cartons, boxes and wrappers are never opened, torn or unboxed; caps, lids, teats and straps are not taken off unless that is the real-use step, and every part keeps its count. SIZE - life-size; a handheld product under 30 cm is never shown full-body or knee-up. FORM - a roll-on rolls, a spray sprays from 15-20 cm, a cream is rubbed in, on the body area where it is really used. LACES - tied only on a lace-up, starting untied with loose ends, ending with a bow. ONE COPY - exactly one of the product anywhere in the frame. FURNITURE - every surface used is in the room from the first frame; nothing appears. HANDS - exactly two, attached to the person's arms.",
    "FACE (user 21-Nov): at least one product's take in every reel shows the persona's whole face.",
    "NO CUT INSIDE A PRODUCT (user 21-Nov): a product's 4 s take is never cut and never jumps to another scene; every product has its own scene (room + surface) and its own product reference sheet. finish refuses a reel with a cut inside a product.",
    # user 20-Nov, from the Day 5 review (extra limbs, sitting on air, fake lace tying, wrong/duplicate products, outfit popping in, height changes)
    "SAME PERSON, SAME HEIGHT: the persona's height, build and body proportions are identical in every plate and clip of the reel - same head-to-floor size against the same furniture and door frames, same camera height (about chest height, never moving lower or higher between products). Every plate of the reel is an edit of the reel's FIRST full-body plate (person, outfit, room), so scale cannot drift.",
    "BACKGROUND IN PROPORTION: the person and the room keep real-world scale - an adult stands about the height of a door frame minus a head, a sofa seat reaches mid-thigh, a bed edge reaches the knee, floor tiles/planks stay the same size around the feet. Never a huge person in a tiny room or a miniature background behind a giant figure; close-ups crop in on the same-scale scene (the camera moves closer), they never enlarge the person against a shrunken background.",
    "NO REPEATED GESTURES (user 20-Nov): each of the 5 products gets a DIFFERENT hand gesture and body action inside the approach - e.g. one adjusts a cuff, the next smooths the front, the next turns to the side, the next rests a hand on the hip, the next looks down at the product; never the same hand move, pose, turn or walk twice in one reel, and never the same opening pose for two products. Write each slot's gesture in plan.json and check they are all different before generating.",
    "QUALITY (user 20-Nov): sharp focus on the product in every frame, natural phone-camera look, no warping, melting, morphing, smearing or flicker of hands, face, product or background; correct colours and lighting continuity; text/logos on the product stay legible and unchanged; if a plate or clip shows any of these defects, regenerate it before finish.",
    "OUTFIT LOCK: the outfit (top, bottom, hem length, footwear-free legs) is fixed in the first plate and never changes, appears or disappears inside a clip or between products; bare legs never turn into trousers and back.",
    "SEATED SHOTS: a seat (the room's sofa, bed edge, chair or ottoman) must be in the plate and directly under the person BEFORE she/he sits; the body visibly rests on it with weight and contact. Never sit, squat or hover without a seat (no 'sitting on air').",
    "ACTIONS MATCH THE PRODUCT: only do what the listed product physically allows, checked against its PRODUCT SPEC (Closure / Type) and reference sheet: tie laces ONLY if laces are visible; open/close a buckle or velcro ONLY if it has one and it is shown open first; never adjust a flip-flop, slide or clog; a slip-on is slipped on, not tied. If the approach's action does not fit the product, use the approach's standing/worn alternative for that slot.",
    "NO TAKING OFF OR SWAPPING (user 20-Nov): within a clip the slot's product stays on/with the person from the first frame to the last - never removed, never put on mid-clip, never one foot in it and the other foot bare or in a different shoe; both feet always wear the same slot pair.",
    "EACH PRODUCT SHOWN ONCE (user 20-Nov): every product appears ONLY inside its own 4-second take and NOWHERE else in the reel - not in another slot's full-body or wide shot, not on the floor or shelf in the background, not in a mirror, not in the opening or end frame. When slot N starts, the previous slot's product is gone (taken off, out of frame). Footwear/wearables: in slot N the person wears ONLY slot N's pair.",
    "ONE PRODUCT PER SLOT: slot N shows ONLY slot N's listed product (its own reference sheet + listing photo in every plate of that slot); never reuse another slot's product, never show two slots' products in one shot. If two slots carry the same PID, STOP and report the row.",
    "BODY PHYSICS: exactly two arms and two legs, every limb attached; feet planted with weight and contact shadow unless that foot is mid-step; no foot hanging in the air, no leg crossing through the other, no ankle/knee twist beyond natural range. Hands reaching a foot only while seated, from the same-side hand.",
    "ONE approach for the whole reel, applied to ALL FIVE product slots (never one approach per product, never five reels).",
    "Every listed slot is represented: no skipping, deduplicating or substituting. A missing/inaccessible/unsuitable slot -> STOP, report row + slot, do not mark the reel complete.",
    "ONE CONTINUOUS TAKE PER PRODUCT (user 21-Nov): each product is shown in ONE 4 s take with no cut - the presentation/use (0-2.5 s), then the camera pushes in on the detail (2.5-4.0 s). Zoom-in only: never a cut, a second clip or a zoom-out inside a product. Exact listed product (colour, print, shape, material, construction, branding, included parts) - listing photos are the reference.",
    "Natural, brief movements: no full spins, exaggerated poses or unboxing. Product-specific actions beat generic gestures. One clear action per main shot.",
    "BAU home: consistent, tidy, lived-in Indian home, NO festive decor (this also overrides older Diwali decor rules for ethnic). Same persona, room, supporting clothes and light across the reel.",
    "Product large enough to read on a phone. Details show real features only - no invented functions or claims.",
    "Preflight all five products against the approach first; if one cannot be shown faithfully with it, STOP and report (the user picks another letter) - do not invent product functions.",
]


def resolve(vertical):
    return VERTICALS.get(vertical)


def _pick(text, variant):
    return text if isinstance(text, str) else text.get(variant or "women")


SHEET = "row_approaches.csv"   # 02_BAU_DATA/row_approaches.csv: one line per sheet row, column "approach" = A-E or HOLD/empty


def load_sheet(data_dir):
    p = os.path.join(data_dir, SHEET)
    if not os.path.exists(p):
        return {}
    import csv
    return {int(r["row"]): r for r in csv.DictReader(open(p, newline="", encoding="utf-8"))}


ROTATE_WINDOW = 4   # user 21-Nov: a letter may not repeat within the previous 4 rows of the same vertical


def auto_letters(data_dir, rows):
    """Rotation by position inside the vertical (sheet order): A, B, C, D, E, (F-J for footwear), then back to A."""
    sh = load_sheet(data_dir); out = {}
    for row in rows:
        r = sh.get(int(row))
        if not r:
            continue
        n = len(FAMILIES[r["family"]]["formats"]) if r.get("family") in FAMILIES else 5
        same = [k for k, x in sorted(sh.items()) if x["vertical"] == r["vertical"]]
        out[int(row)] = LETTERS[same.index(int(row)) % n]
    return out


def check_rotation(data_dir, row, letter):
    """Refuse a letter already used by one of the previous 4 rows (with a letter) of the same vertical."""
    sh = load_sheet(data_dir); r = sh.get(int(row))
    if not r:
        return
    prev = [x for k, x in sorted(sh.items()) if k < int(row) and x["vertical"] == r["vertical"]
            and (x.get("approach") or "").strip().upper() not in ("", "HOLD")][-ROTATE_WINDOW:]
    clash = [int(x["row"]) for x in prev if x["approach"].strip().upper() == letter]
    if clash:
        raise SystemExit(f"row {row}: approach {letter} was already used by row(s) {clash} of the same vertical - at least 5 "
                         f"different approaches must come before one repeats. Fix: pipeline.py setapproach AUTO {row}")


def set_rows(data_dir, letter, rows):
    """Write the approach letter (A-E) or HOLD for the given rows into row_approaches.csv."""
    import csv
    letter = letter.upper()
    auto = auto_letters(data_dir, rows) if letter == "AUTO" else {}
    if letter not in list(LETTERS) + ["HOLD", "AUTO"]:
        raise SystemExit("use a letter A-E (footwear A-V) or HOLD")
    p = os.path.join(data_dir, SHEET)
    lines = list(csv.DictReader(open(p, newline="", encoding="utf-8")))
    want = {int(r) for r in rows}
    hit = set()
    for r in lines:
        if int(r["row"]) in want:
            r["approach"] = "" if letter == "HOLD" else auto.get(int(r["row"]), "") if letter == "AUTO" else letter
            hit.add(int(r["row"]))
    w = csv.DictWriter(open(p, "w", newline="", encoding="utf-8"), fieldnames=list(lines[0].keys()))
    w.writeheader(); w.writerows(lines)
    for r in sorted(want - hit):
        print(f"row {r}: not in {SHEET} (Makeup or unknown row) - skipped")
    print(f"{len(hit)} rows -> {letter}")


def choose(row, vertical, data_dir, row_dir, override=None):
    """Per-row selection (user 16-Nov): the row's letter in row_approaches.csv. Empty/HOLD = this row is on hold.
    An explicit override (prompt <row> <letter> or FK_APPROACH) runs that letter for this run only."""
    fam = resolve(vertical)
    if not fam:
        raise SystemExit(f"row {row}: vertical {vertical!r} has no approach family")
    family, variant = fam
    letter = (override or os.environ.get("FK_APPROACH") or "").upper()
    from_sheet = not letter
    if not letter:
        letter = (load_sheet(data_dir).get(int(row), {}).get("approach") or "").strip().upper()
    if from_sheet and letter not in ("", "HOLD"):
        check_rotation(data_dir, row, letter)
    if not letter or letter == "HOLD":
        raise SystemExit(f"row {row}: ON HOLD - no approach set in {SHEET} (set one: pipeline.py setapproach <A-E> {row})")
    n = len(FAMILIES[family]["formats"])
    if letter not in LETTERS[:n]:
        raise SystemExit(f"row {row}: family {family} has approaches {LETTERS[0]}-{LETTERS[n-1]} or HOLD, got {letter!r}")
    fmt = FAMILIES[family]["formats"][LETTERS.index(letter)]
    os.makedirs(row_dir, exist_ok=True)
    json.dump(dict(row=int(row), source_vertical=vertical, family=family, variant=variant, letter=letter, id=fmt["id"]),
              open(os.path.join(row_dir, "approach.json"), "w"), indent=1)   # log of what this row was made with
    return family, variant, fmt


PER_PRODUCT = 4.0   # user 16-Nov: EXACTLY 4 s per product (main + detail together), never more
MAIN_S, DETAIL_S = 2.5, 1.5


def timing(endslate_s, fps=24):
    """4 s per product, 5 products = 20 s of product footage + the end slate (~21.6 s reel). Frame-exact (96 frames)."""
    return PER_PRODUCT, MAIN_S, DETAIL_S


def block(row, vertical, products, data_dir, row_dir, endslate_s, override=None):
    family, variant, fmt = choose(row, vertical, data_dir, row_dir, override)
    fam = FAMILIES[family]
    per, main, det = timing(endslate_s)
    slots = "\n".join(f"  slot {i}: {u}" for i, u in enumerate(products, 1))
    who = f" ({variant}'s actions)" if variant else ""
    other = ", ".join(f"{f['letter']}={f['id']}" for f in fam["formats"] if f is not fmt)
    return f"""=== PRESENTATION APPROACH {fmt['letter']} - {fmt['name']} ({family}/{fmt['id']}){who} ===
This reel uses approach {fmt['letter']} ONLY, for all five products (other approaches, not used here: {other}).
FRAMING: {fam['framing']}.
PRESENTATION (0-2.5 s), every product: {_pick(fmt['main'], variant)}
PUSH-IN TARGET (2.5-4.0 s, same take, no cut): {_pick(fmt['detail'], variant)}
Family rules:
""" + "\n".join(f"- {c}" for c in fam["constraints"]) + "\nGeneral rules:\n" + "\n".join(f"- {c}" for c in GENERAL) + f"""
PRODUCT SLOTS (each gets ONE continuous 4 s take, in this order; log subtype per slot in log.md before generating):
{slots}
TIMING (user rule): EXACTLY {per:.0f} s per product, never more = ONE continuous take: {main} s presentation + {det} s camera
push-in (no cut). 5 products = 20.0 s of footage (Product 1 starts at 0 s, title overlaid on it) + the {endslate_s:.2f} s end slate
= {20 + endslate_s:.2f} s reel. Generate ONE 4 s clip per product (360p). plan.json: 5 segments of 4.0 s, each with "slot": N.
finish refuses a reel whose footage is over 20.0 s.
"""
