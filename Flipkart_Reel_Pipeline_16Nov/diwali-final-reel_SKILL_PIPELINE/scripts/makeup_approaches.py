"""MAKEUP approaches (user 16-Nov): every makeup product TYPE has 5 detailed approaches A-E of applying it.
In a reel ONLY ONE of the five products is applied (Beauty pipeline rule: one application per video); the other four are
shown as hands-only close-ups. The row picks WHICH slot is applied (apply_slot) and HOW (approach letter A-E) in
02_BAU_DATA/row_approaches.csv. Types that cannot go on skin (tools, wipes, kits, bag) get 5 detailed approaches of USING them.

Applicable types share the spec's makeup format IDs (REEL_PRESENTATION_IMPLEMENTATION_SPEC.md section 12):
  A mirror_application  B swatch_to_finish  C direct_application  D held_to_worn  E finishing_touch
Each approach = framing + main action and pose + a separate detail shot, written for that product type.
Product type = first 3 letters of the Flipkart PID (Flipkart category code), checked against live titles on 16-Nov.
"""

LETTERS = "ABCDE"
FMT = {"A": ("mirror_application", "Mirror application"), "B": ("swatch_to_finish", "Swatch to worn finish"),
       "C": ("direct_application", "Direct-camera application"), "D": ("held_to_worn", "Product to worn reveal"),
       "E": ("finishing_touch", "Getting-ready finishing touch")}


def X(framing, main, detail, fid=None, name=None):
    return dict(framing=framing, main=main, detail=detail, id=fid, name=name)


def T(name, group, rules, a, b, c, d, e, own_ids=False):
    out = {}
    for L, ap in zip(LETTERS, (a, b, c, d, e)):
        if not own_ids:
            ap["id"], ap["name"] = FMT[L]
        out[L] = ap
    return dict(name=name, group=group, rules=rules, approaches=out)


MIRROR = "Mirror shot over her shoulder: her reflection face-and-shoulders, the phone NOT visible (camera behind/beside her), reflection and handedness consistent"
FACE = "Direct to camera, face-and-shoulders, eye level, persona centred"
LIPS = "Tight lips-and-chin crop, lips front-facing"
EYE = "Tight one-eye crop, brow to cheekbone, eye open and steady unless stated"
HAND = "Hands-only close-up at chest height over the dressing table, product label to camera"

TYPES = {
 # ================= LIPS =================
 "LSK": T("Lipstick", "lips",
  "Use the listing's real applicator (bullet vs liquid wand). One shade only; lips start bare. Lips front-facing for every lip pass.",
  X(MIRROR, "She uncaps the lipstick with the label toward the mirror, then makes ONE controlled pass: lower lip left-to-right, then the upper lip following the cupid's bow. Lips slightly parted, no pout. Lowers the lipstick to chest height, label still visible.",
    "Cut closer to the reflection: lips front-facing, colour edge and finish (matte/satin/cream) visible, lipstick out of the contact area."),
  X(HAND + " -> " + LIPS, "Hands-only: one short swatch stripe on the back of the hand next to the open lipstick (shade name toward camera). Cut to her lips already wearing that exact shade, front-facing, a soft natural smile.",
    "Hand swatch held up beside the chin so swatch and lips are compared in the same light; no colour shift between them."),
  X(FACE, "Facing camera, she brings the wand/bullet to the centre of the lower lip and makes one slow pass to the corner, then presses lips together once. Head straight, applicator never blocks the contact edge from camera.",
    "Lips-only crop front-facing: crisp edge, real finish, applicator lowered out of frame."),
  X(HAND + " -> " + FACE, "Hands-only: lipstick held upright, cap off, twisted up (bullet) or wand pulled out showing the doe-foot. Cut to her face front-on, lips already wearing the shade, relaxed expression.",
    "Lipstick held beside the lips (not touching) so the bullet/pack shade matches the worn colour."),
  X(FACE + ", rest of the look already complete", "Look already done (eyes, cheeks). She makes one quick centre-lip touch-up on the lower lip, presses lips once and recaps.",
    "Settled lips front-facing, then the lipstick set down near — not covering — the face if space permits.")),
 "LPB": T("Lip balm", "lips",
  "Non-tinted balm shows only a natural sheen; tinted balm only if the listing says tinted. No brightening/SPF results claimed.",
  X(MIRROR, "Uncaps the balm at the mirror, one slow glide across the lower lip then the upper lip, lips relaxed, then a light lip press.",
    "Reflection close: soft healthy sheen on the lips, balm lowered with the label visible."),
  X(HAND + " -> " + LIPS, "Hands-only: a thin glide of balm on the back of the hand catching window light. Cut to the lips with the same sheen.",
    "Hand sheen and lip sheen in the same light; no exaggerated gloss."),
  X(FACE, "Facing camera, one glide over the lower lip, lips stay front-facing; she presses lips together once.",
    "Lips-only crop showing the sheen, applicator out of frame."),
  X(HAND + " -> " + LIPS, "Hands-only: twist up the stick / open the tin showing the balm. Cut to lips with the balm applied.",
    "Balm product held beside the lips (not touching)."),
  X(FACE + ", ready to leave", "Already dressed and ready, she takes the balm from the table, one quick pass, caps it and slips it into her bag.",
    "Lips with sheen, then the balm on the table label-up.")),
 "LLI": T("Lip liner", "lips", "Liner only defines the edge; do not credit a lipstick worn on top to the liner.",
  X(MIRROR, "At the mirror, elbow rested on the dressing table for a steady hand, she traces the cupid's bow in two short strokes, then the lower lip edge corner-to-centre.",
    "Reflection close on the defined lip edge, liner lowered, label visible."),
  X(HAND + " -> " + LIPS, "Hands-only: one thin line swatch on the back of the hand. Cut to lips lined with that exact shade (liner edge only, or lined and filled with the liner itself).",
    "Swatch held by the chin beside the lined lip edge."),
  X(FACE, "Facing camera, she outlines the lower lip in one controlled stroke from the corner to the centre, lips front-facing.",
    "Sharp lip-edge crop, front-facing."),
  X(HAND + " -> " + LIPS, "Hands-only: pencil uncapped, tip shown to camera (sharpened/twist-up as real). Cut to lips lined with it.",
    "Pencil tip held next to the lined edge, matching shade."),
  X(FACE + ", look already complete", "Lips already done; she adds one short defining stroke at one corner of the lower lip and blends inward with a fingertip.",
    "Corner close-up showing the cleaner edge.")),
 "LGS": T("Lip gloss", "lips", "Real shine/tint only, no exaggerated wet look; credit only the gloss's own effect.",
  X(MIRROR, "At the mirror she pulls out the doe-foot, wipes the excess on the neck of the tube, and makes one pass over the centre of the lower lip, then presses lips together.",
    "Reflection close on the glossy lips, gloss tube lowered label-up."),
  X(HAND + " -> " + LIPS, "Hands-only: a small gloss swatch on the back of the hand catching window light. Cut to lips wearing the gloss.",
    "Swatch beside the chin; same shine level on both."),
  X(FACE, "Facing camera, one doe-foot pass over the lower lip, lips front-facing; light lip press.",
    "Lips-only crop showing the real shine/tint."),
  X(HAND + " -> " + LIPS, "Hands-only: tube held upright, doe-foot pulled out showing the gloss colour. Cut to glossy lips.",
    "Tube beside the lips (not touching)."),
  X(FACE + ", look already complete", "Lips already coloured; one gloss pass on the centre of the lower lip as the final step.",
    "Lips close-up, gloss on top, tube set down near the face.")),
 "LSQ": T("Lip & cheek tint", "lips", "Pick lips OR cheek for the one application, not both. Stain finish only.",
  X(MIRROR, "At the mirror, two small dots of tint on the lower lip, pressed together and patted with a fingertip.",
    "Reflection close on the stained lips, bottle lowered label-up."),
  X(HAND + " -> " + "cheek or lips crop", "Hands-only: one tint dot spread into a sheer swatch on the back of the hand. Cut to the same tint on the cheek apple (head turned slightly) or on the lips.",
    "Swatch beside the tinted area in the same light."),
  X(FACE, "Facing camera, one dot on the cheek apple tapped outward with two fingertips in three taps (head turned slightly to show the cheek).",
    "Cheek close-up at a slight angle showing the natural flush."),
  X(HAND + " -> " + FACE, "Hands-only: bottle/stick held up, applicator shown. Cut to the face wearing the tint on the chosen area.",
    "Tint product beside the tinted area."),
  X(FACE + ", look already complete", "Look done; a final tap of tint on one cheek apple to warm the face.",
    "Cheek close-up, settled flush.")),
 # ================= EYES =================
 "MCR": T("Mascara", "eyes", "Never touch the eyeball; eye stability (no fluttering); no length/volume claims beyond the real look; no clumps invented.",
  X(MIRROR, "Leaning slightly toward the mirror, eyes looking down into it, she places the wand at the root of the upper lashes and makes one slow wiggle-up stroke, then a second stroke on the outer lashes. Eye steady.",
    "Reflection close on the eye now open, lashes separated, wand lowered."),
  X(HAND + " -> " + EYE, "Hands-only: wand pulled out of the tube showing the brush and formula to camera (no hand swatch). Cut to the lashes coated.",
    "Wand held near (not at) the eye, brush shape vs finished lashes."),
  X(FACE + " -> " + EYE, "Facing camera, chin slightly up, eyes looking down, one upward stroke on the upper lashes from root to tip.",
    "One-eye crop, eye open, lashes defined, wand out of frame."),
  X(HAND + " -> " + EYE, "Hands-only: tube held label-to-camera, wand twisted out. Cut to the eye with mascara already on, open and steady.",
    "Tube beside the eye (not close to the eyeball)."),
  X(FACE + ", look already complete", "Look done; a final light coat on the outer lashes, then one natural blink.",
    "One-eye crop, lashes finished, eye open.")),
 "KJL": T("Kajal", "eyes", "Waterline only with gentle movement; never touch the eyeball; eye stability.",
  X(MIRROR, "At the mirror, one finger gently pulls the lower lid down a little, she glides the kajal along the lower waterline once from inner to outer, then blinks once.",
    "Reflection close on the lined eye, kajal lowered, label visible."),
  X(HAND + " -> " + EYE, "Hands-only: one short kajal line on the back of the hand showing its depth of black. Cut to the eye lined with it.",
    "Swatch beside the cheek near the lined eye; same black."),
  X(FACE + " -> " + EYE, "Facing camera, eyes looking up slightly, she glides the kajal along the lower waterline once, steady elbow.",
    "One-eye crop, eye open, the line visible."),
  X(HAND + " -> " + EYE, "Hands-only: twist the kajal up showing the tip (or uncap the pencil). Cut to lined eyes.",
    "Kajal held near the temple beside the lined eye."),
  X(FACE + ", look already complete", "Look done; a final pass along the outer third of the lower lash line, softened with the fingertip.",
    "One-eye crop, smudged outer corner.")),
 "ELR": T("Eyeliner", "eyes", "Steady hand (elbow rested), eye stability, nothing touches the eye opening.",
  X(MIRROR, "At the mirror, eye half-closed, she draws one steady stroke along the upper lash line from inner to outer, ending in a small flick.",
    "Reflection close on the eye opening to show the line and wing."),
  X(HAND + " -> " + EYE, "Hands-only: one liner stroke on the back of the hand showing the colour and finish. Cut to the lined lid.",
    "Swatch beside the eye in the same light."),
  X(FACE + " -> " + EYE, "Facing camera, eye half-closed, one outward wing flick at the outer corner, then the eye opens.",
    "Closed-then-open one-eye crop showing the wing."),
  X(HAND + " -> " + EYE, "Hands-only: liner uncapped, felt tip/brush shown. Cut to the finished line, eye open.",
    "Liner beside the eye, tip vs line."),
  X(FACE + ", look already complete", "Look done; she sharpens the wing tip with one tiny stroke.",
    "One-eye crop, crisp wing.")),
 "ESD": T("Eyeshadow palette", "eyes", "Show the real pans; one shade family; do not invent an included brush (use a fingertip if no brush is listed).",
  X(MIRROR, "At the mirror, she picks a shade with a fingertip (or included brush) and pats it once on the centre of the lid, eye closed, then blends to the crease.",
    "Reflection close: lid closed showing the shade, then the eye opens."),
  X(HAND + " -> " + EYE, "Hands-only: two shade swatches side by side on the back of the hand. Cut to the chosen shade on the closed lid.",
    "Swatch beside the closed lid; same colour."),
  X(FACE + " -> " + EYE, "Facing camera, eye closed, one sweep across the lid with fingertip/brush.",
    "Closed-lid crop, then eye opens."),
  X(HAND + " -> " + EYE, "Hands-only: palette opened toward camera showing all pans. Cut to the closed lid wearing one shade.",
    "Open palette beside the face, shade pan next to the lid colour."),
  X(FACE + ", look already complete", "Look done; a final blend at the crease with a fingertip.",
    "Closed-lid crop showing the blended crease.")),
 "SMG": T("Shimmer / glitter eye powder", "eyes", "Keep away from the eye opening; no fallout invented; one shade.",
  X(MIRROR, "At the mirror, eye closed, she presses a little shimmer onto the centre of the lid with a fingertip.",
    "Reflection close: lid catching window light as the eye opens."),
  X(HAND + " -> " + EYE, "Hands-only: a shimmer swatch on the back of the hand tilted into window light. Cut to the lid with that shimmer.",
    "Swatch and lid in the same light."),
  X(FACE + " -> " + EYE, "Facing camera, eye closed, one fingertip press on the lid centre.",
    "Closed-lid crop, shimmer visible."),
  X(HAND + " -> " + EYE, "Hands-only: jar(s) opened showing the shimmer. Cut to the shimmer on the lid.",
    "Jar beside the lid."),
  X(FACE + ", look already complete", "Look done; a tiny dab of shimmer on the inner corner.",
    "Eye crop showing the inner-corner highlight.")),
 "FLS": T("False eyelashes", "eyes", "Glue never near the eye opening; use only included accessories (glue/curler only if listed).",
  X(MIRROR, "At the mirror, she lays a thin glue line on the lash band, waits a beat, and places the strip at the outer lash line with her fingertips, pressing gently.",
    "Reflection close: eye opens, lash band blended."),
  X(HAND + " -> " + EYE, "Hands-only: lash strip lifted from the tray and held up to show its length. Cut to the eye wearing it.",
    "Strip held beside the eye vs worn lashes."),
  X(FACE + " -> " + EYE, "Facing camera, chin slightly up, she places the strip and presses at the outer corner.",
    "Eye-open crop, lash band blended."),
  X(HAND + " -> " + EYE, "Hands-only: open the lash tray showing all pairs (and curler/glue if included). Cut to lashes worn.",
    "Tray beside the face."),
  X(FACE + ", look already complete", "Lashes already on; a final press at the outer corner, one natural blink.",
    "Eye-open crop.")),
 # ================= BROWS =================
 "EBP": T("Eyebrow pencil", "brows", "Use the spoolie only if included; natural hair-like strokes.",
  X(MIRROR, "At the mirror, short hair-like upward strokes along the sparse front of the brow, then the tail.",
    "Reflection close on the filled brow."),
  X(HAND + " -> " + "brow crop", "Hands-only: two short strokes on the back of the hand showing the shade. Cut to the brow filled with it.",
    "Swatch beside the brow."),
  X(FACE + " -> brow crop", "Facing camera, a few feathery strokes in the arch, then brushed through with the spoolie end.",
    "Brow crop, natural texture."),
  X(HAND + " -> brow crop", "Hands-only: pencil shown with its spoolie end. Cut to the defined brow.",
    "Pencil beside the brow."),
  X(FACE + ", look already complete", "Look done; one tidy stroke on the tail, brushed once.",
    "Brow crop.")),
 # ================= FACE BASE =================
 "FND": T("Foundation", "base", "Shade must match the persona's real skin tone; no complexion change, no lightening, no coverage claims; small area only.",
  X(MIRROR, "At the mirror, two small dots on one cheek, blended outward with fingertips in short strokes.",
    "Reflection close on the blended cheek, natural skin texture."),
  X(HAND + " -> cheek crop", "Hands-only: one stripe on the jawline-coloured back of the hand. Cut to a small blended area on the cheek.",
    "Swatch held by the jaw in the same light."),
  X(FACE, "Facing camera, dots on the cheek bounced in with a damp sponge (prop) or fingertips.",
    "Cheek crop at a slight angle, texture intact."),
  X(HAND + " -> " + FACE, "Hands-only: bottle pumped once onto the back of the hand, label to camera. Cut to the face with the blended base.",
    "Bottle beside the cheek."),
  X(FACE + ", look already complete", "Look done; a final small dab on one area blended out.",
    "Cheek crop.")),
 "CLR": T("Foundation stick / concealer", "base", "No skin-lightening, no exaggerated before/after; small area only.",
  X(MIRROR, "At the mirror, one stick swipe on the cheekbone, blended with fingertips.",
    "Reflection close on the blended area."),
  X(HAND + " -> face crop", "Hands-only: stick swatch on the back of the hand. Cut to the blended area on the face.",
    "Swatch beside the cheek."),
  X(FACE, "Facing camera, three dots under one eye tapped in with the ring finger.",
    "Under-eye crop, natural texture."),
  X(HAND + " -> " + FACE, "Hands-only: stick twisted up showing the shade. Cut to the face with the blended area.",
    "Stick beside the cheek."),
  X(FACE + ", look already complete", "Look done; a final dab on one small spot.",
    "Spot crop.")),
 "CMP": T("Compact powder", "base", "Use the included puff/mirror only if the listing has them.",
  X(MIRROR, "At the mirror, she presses the puff into the powder and presses it on the nose and forehead.",
    "Reflection close, matte T-zone, skin texture intact."),
  X(HAND + " -> face crop", "Hands-only: open compact showing the pan and puff. Cut to a matte cheek.",
    "Compact beside the cheek."),
  X(FACE, "Facing camera, one puff press on one cheek, then the nose.",
    "Cheek crop, matte finish."),
  X(HAND + " -> " + FACE, "Hands-only: compact clicked open toward camera (mirror and pan). Cut to the face with the set finish.",
    "Open compact beside the face."),
  X(FACE + ", ready to leave", "Look done; she takes the compact out, one quick press on the nose using its mirror, clicks it shut.",
    "Compact closed in hand, label up.")),
 "PRM": T("Primer / makeup fixer", "base", "Read the listing: CREAM primer -> dab and spread; SPRAY fixer -> arm's length, eyes closed, follow the real directions. No invented glow.",
  X(MIRROR, "Cream: pea-size on a fingertip, spread over the cheek. Spray: at the mirror, eyes closed, bottle at arm's length, one or two mists in an X, holds still.",
    "Reflection close on the fresh finish."),
  X(HAND + " -> face crop", "Cream: a dab on the back of the hand spread thin. Spray: one mist onto the back of the hand. Cut to the finish on the face.",
    "Hand and face in the same light."),
  X(FACE, "Facing camera; cream: dots on the cheek spread with fingertips; spray: eyes closed, one mist, light fingertip pats.",
    "Face crop, fresh finish."),
  X(HAND + " -> " + FACE, "Hands-only: bottle shown, pump/nozzle to camera. Cut to the face after application.",
    "Bottle beside the face."),
  X(FACE + ", look already complete", "Look done; spray: one final mist with eyes closed; cream: a light press over the cheek.",
    "Face crop, settled finish.")),
 # ================= CHEEKS =================
 "BLU": T("Blush", "cheek", "One shade; slight head angle for cheek shots; no exaggerated flush.",
  X(MIRROR, "At the mirror, a light smile, one brush (or fingertip) sweep on the cheek apple toward the temple.",
    "Reflection close at a slight angle on the flushed cheek."),
  X(HAND + " -> cheek crop", "Hands-only: palette swatch on the back of the hand. Cut to the flush on the cheek apple.",
    "Swatch beside the cheek."),
  X(FACE, "Facing camera, head turned slightly, three fingertip taps of blush on the cheek apple.",
    "Cheek crop, natural flush."),
  X(HAND + " -> " + FACE, "Hands-only: palette opened toward camera showing all pans. Cut to the face wearing one shade.",
    "Open palette beside the cheek."),
  X(FACE + ", look already complete", "Look done; a final light sweep, head turned slightly.",
    "Cheek crop.")),
 "HGL": T("Highlighter", "cheek", "No exaggerated glow; real finish only.",
  X(MIRROR, "At the mirror, one glide along the top of the cheekbone, tapped in with a fingertip.",
    "Reflection close turning into window light."),
  X(HAND + " -> cheek crop", "Hands-only: swatch on the back of the hand tilted into light. Cut to the cheekbone.",
    "Swatch beside the cheekbone."),
  X(FACE, "Facing camera, head turned slightly, fingertip taps on the cheekbone top.",
    "Cheekbone crop catching light."),
  X(HAND + " -> " + FACE, "Hands-only: stick/pan shown. Cut to the highlighted cheekbone.",
    "Product beside the cheek."),
  X(FACE + ", look already complete", "Look done; a final dab on the nose bridge.",
    "Nose-bridge crop.")),
 "BRZ": T("Bronzer", "cheek", "Subtle warmth only; no complexion change.",
  X(MIRROR, "At the mirror, one sweep under the cheekbone toward the ear.",
    "Reflection close at a side angle."),
  X(HAND + " -> cheek crop", "Hands-only: swatch on the back of the hand. Cut to the warmed cheek.",
    "Swatch beside the cheek."),
  X(FACE, "Facing camera, light sweep at the temple then the jaw edge.",
    "Side-angle crop."),
  X(HAND + " -> " + FACE, "Hands-only: pan opened showing the shimmer. Cut to the bronzed face.",
    "Pan beside the face."),
  X(FACE + ", look already complete", "Look done; a final light sweep, head slightly turned.",
    "Cheek crop.")),
 # ================= TRADITIONAL =================
 "SIN": T("Sindoor", "traditional", "Respectful, ordinary getting-ready moment in a real home; no festive decor (BAU); a clean thin line only, no spill.",
  X(MIRROR, "Standing at the mirror, she parts her hair with one finger, uncaps the sindoor and draws one short, thin line along the start of the parting with the applicator tip, then lowers the tube label-up.",
    "Reflection close on the parting: clean red line, no powder fallout on the forehead."),
  X(HAND + " -> parting crop", "Hands-only: applicator pulled out showing the colour on the tip, one tiny dot pressed on the back of the hand. Cut to the same red in the hair parting.",
    "Hand dot held near the parting in the same light; same red."),
  X(FACE, "Facing camera, head tilted down a little so the parting shows, one short stroke at the start of the parting, then she lifts her head with a calm expression.",
    "Top-of-head crop on the parting line."),
  X(HAND + " -> " + FACE, "Hands-only: tube held upright, cap off, applicator shown. Cut to her face front-on with the sindoor already in the parting.",
    "Tube held beside the temple, colour matched to the worn line."),
  X(FACE + ", look already complete", "Dressed and ready, sindoor is the last step: one short stroke at the parting, cap back on, she smooths her hair.",
    "Parting crop, then the tube set on the dressing table.")),
 "BIN": T("Bindi", "traditional", "Bindi centred between the brows; sizes/colours only as in the box.",
  X(MIRROR, "At the mirror, she peels one bindi from the flap with a fingertip and presses it between her brows, checking it is centred.",
    "Reflection close on the forehead, bindi centred and flat."),
  X(HAND + " -> forehead crop", "Hands-only: box opened toward camera showing the flaps of sizes, one bindi lifted on a fingertip. Cut to it worn.",
    "Fingertip bindi held beside the worn one; same size and colour."),
  X(FACE, "Facing camera, she peels and presses the bindi between the brows in one move, then relaxes her face.",
    "Forehead crop, bindi centred."),
  X(HAND + " -> " + FACE, "Hands-only: the box held up, cover to camera. Cut to her face front-on wearing the bindi.",
    "Box beside the face."),
  X(FACE + ", look already complete", "Look done; the bindi is the last step: placed, a small check in the mirror, a light smile.",
    "Forehead crop, then the box closed on the table.")),
 # ================= NAILS =================
 "NLP": T("Nail polish", "nails", "Nails and hands match the avatar's skin tone; nails short and neat; shade exactly as the bottle; no chipping or flooding the cuticle.",
  X("Hands-only, left hand flat on the dressing table, nails to camera, bottle beside it",
    "She uncaps the bottle, wipes the brush on the neck, and paints the index nail in three strokes: centre, left side, right side. Hand stays flat and still.",
    "Painted nail next to the bottle, glossy finish, clean cuticle line.", "one_nail", "One-nail paint"),
  X(HAND + ", then fingertips crop", "Hands-only: one stripe of polish on the thumbnail shows the shade. Cut to all five nails painted, fingers fanned beside the bottle.",
    "Fingers fanned beside the bottle so shade and bottle match.", "swatch_to_all", "Stripe to all nails"),
  X("Hands-only, both hands on the table, nails to camera",
    "She paints the index and middle nails of one hand, steady strokes, the other hand holding the bottle upright.",
    "Two painted nails close-up, even coat.", "two_nail", "Two-nail paint"),
  X(HAND, "Hands-only: bottle held up label-to-camera, brush pulled out showing the colour. Cut to painted nails resting next to the bottle.",
    "Bottle and nails side by side, same shade.", "bottle_to_done", "Bottle to done"),
  X("Hands-only, nails already painted", "Nails done; a final top stroke on one nail, then she lifts the hand and gently spreads the fingers to dry (no blowing, no fast waving).",
    "Fingertips close-up in window light.", "finishing_coat", "Finishing coat"),
  own_ids=True),
 # ================= TOOLS =================
 "PFS": T("Makeup sponge / puff", "tool", "The sponge/puff is the listed product; any foundation or powder used with it is a neutral prop and is not credited. Show its real shape, size and colour.",
  X("Face crop at a slight angle", "She holds the damp sponge by its round base and bounces it on two foundation dots on the cheek in small quick taps, never dragging.",
    "Sponge held up beside the cheek showing its shape and colour.", "bounce_blend", "Bounce blend"),
  X("Face crop", "She presses the puff into loose powder (prop), taps off the excess on the back of her hand, and presses it on the nose and forehead.",
    "Puff close-up in the fingers, texture visible.", "press_puff", "Press puff"),
  X(HAND, "Hands-only: the sponge shown dry, then held under a few water drops (prop bowl) and squeezed so it swells slightly, then one bounce on the cheek.",
    "Dry and damp sponge side by side (if two are in the pack) or the damp one beside the pack.", "dry_vs_damp", "Dry vs damp"),
  X("Under-eye crop", "She uses the pointed tip to blend under one eye in tiny taps, eye open and steady.",
    "Tip close-up in the fingers.", "edge_detail", "Edge detail"),
  X("Face crop, look already complete", "Look done; a final soft press over the cheek to smooth, then the sponge set on its pack/case.",
    "Sponge on the pack, label visible.", "finishing_press", "Finishing press"),
  own_ids=True),
 "BAR": T("Makeup brush set", "tool", "Only the brushes in the listing (count and colours as listed); powder used is a prop and not credited.",
  X(HAND, "Hands-only: she fans the brushes in one hand like cards, picks the big powder brush, and makes one light sweep on the cheek.",
    "Bristle heads and handles close-up, set count visible.", "fan_reveal", "Fan reveal"),
  X(HAND, "Hands-only: she runs a fingertip slowly across the bristles of one brush to show softness, then one sweep on the cheek.",
    "Bristles bending softly under the fingertip.", "bristle_touch", "Bristle touch"),
  X(HAND, "Hands-only: she takes a brush out of its roll/pouch (only if included), makes one sweep, and slides it back in.",
    "The roll/pouch with brushes in their slots.", "pouch_to_use", "Pouch to use"),
  X(HAND, "Hands-only: two different brushes held up side by side, then one is used for a single blending sweep.",
    "Two brush heads side by side.", "two_brush", "Two-brush"),
  X("Face crop, look already complete", "Look done; one final dusting sweep with the fluffy brush, then the brush laid back with the set.",
    "The full set laid out on the dressing table.", "finishing_dust", "Finishing dust-off"),
  own_ids=True),
 "NLA": T("Nail-art brush set", "tool", "The brushes are the product; the polish used is a neutral prop. Only the tips in the listing.",
  X("Hands-only, nails to camera", "On an already painted nail she touches the dotting tool once to make one tiny dot near the cuticle.",
    "Dot tip and the dot side by side.", "dot_detail", "Dot detail"),
  X("Hands-only, nails to camera", "With the striping brush she pulls one thin straight line across a painted nail.",
    "Stripe close-up, clean line.", "stripe", "Stripe"),
  X(HAND, "Hands-only: all brush tips fanned toward camera, she picks one and makes one short stroke on a nail.",
    "Tips fanned, each tip shape visible.", "set_reveal", "Set reveal to use"),
  X("Hands-only, nails to camera", "With the fine brush she paints a small swirl on the ring-finger nail.",
    "Swirl close-up.", "swirl", "Swirl"),
  X("Hands-only, nails already designed", "Nails done; one final dot, then the brush laid back in the set.",
    "Finished nail beside the brush set.", "finishing_detail", "Finishing detail"),
  own_ids=True),
 # ================= KITS =================
 "MKT": T("Makeup kit", "kit", "Apply only ONE item from the kit; show the real pans/compartments; no included brush unless listed.",
  X(MIRROR, "At the mirror she opens the kit, picks one item (a lip or cheek shade) and makes one application in a single pass.",
    "Kit pans close-up, then the applied area.", "mirror_one_item", "Mirror, one item"),
  X(HAND, "Hands-only: two shades from the kit swatched side by side on the back of the hand; she applies one of them.",
    "Swatches held beside the applied area.", "swatch_two", "Swatch two, apply one"),
  X(FACE, "Facing camera, the open kit in one hand, she applies one item with the other hand.",
    "Applied-area crop, kit held lower in frame.", "direct_one_item", "Direct, one item"),
  X(HAND + " -> " + FACE, "Hands-only: kit opened toward camera showing all compartments. Cut to the one shade worn.",
    "Open kit beside the face.", "kit_to_worn", "Kit reveal to worn"),
  X(FACE + ", look already complete", "Look done; she uses the kit's lid mirror (only if it has one) for one final touch from the kit.",
    "Kit and the touched-up area.", "finishing_from_kit", "Finishing touch from the kit"),
  own_ids=True),
 "CBK": T("Combo kit", "kit", "Apply only ONE item of the combo; every combo piece must be visible at least once.",
  X(HAND, "Hands-only: all combo pieces laid in a row on the dressing table, one picked up and applied once.",
    "Each combo piece visible in the row.", "layout_apply", "Lay out, apply one"),
  X(LIPS, "She picks the lip item of the combo and makes one pass on the lips.",
    "Lips crop, lip item beside the chin.", "lip_item", "Lip item"),
  X(HAND + " -> " + FACE, "Hands-only: the combo box opened toward camera. Cut to one item worn.",
    "Combo box beside the face.", "combo_to_worn", "Combo to worn"),
  X(HAND, "Hands-only: one item swatched on the back of the hand, then applied.",
    "Swatch beside the applied area.", "swatch_apply", "Swatch then apply"),
  X(FACE + ", look already complete", "Look done; one final touch with one combo item.",
    "Applied-area crop.", "finishing_item", "Finishing touch"),
  own_ids=True),
 # ================= SKINCARE / REMOVAL =================
 "SNR": T("Sunscreen", "skincare", "No whitening/glow claims; SPF only as printed on the pack; no white cast invented; natural skin texture.",
  X(MIRROR, "At the mirror she dots sunscreen on the forehead, both cheeks and chin, then spreads it on one cheek with fingertips.",
    "Reflection close on the cheek, skin texture intact.", "mirror_spread", "Mirror spread"),
  X(HAND, "Hands-only: she squeezes a line along two fingers to measure, then spreads it on the cheek.",
    "Two-finger line close-up beside the tube.", "two_finger", "Two-finger measure"),
  X(FACE, "Facing camera, a small squeeze onto the fingertip and spread on one cheek in outward strokes.",
    "Cheek crop.", "direct_spread", "Direct spread"),
  X(HAND, "Hands-only: tube held up label-to-camera by the window, a little squeezed onto the back of the hand and spread thin.",
    "Tube and hand together.", "tube_to_skin", "Tube to skin"),
  X(FACE, "First step of her morning: sunscreen spread on the face, then a cut to the rest of the look already done.",
    "Tube on the dressing table, label up.", "routine_first", "Routine first step"),
  own_ids=True),
 "MUR": T("Makeup remover wipes", "removal", "No harsh rubbing; never on the open eye; the residue on the wipe is from the shown makeup only.",
  X("Face crop", "She pulls one wipe from the pack, folds it once, and wipes one cheek gently in a downward stroke.",
    "Pack and the used wipe showing light residue.", "pull_wipe", "Pull and wipe"),
  X(HAND, "Hands-only: a lipstick swatch on the back of the hand wiped off in one stroke.",
    "Clean hand and the wipe with the colour.", "swatch_off", "Swatch off"),
  X(HAND, "Hands-only: pack held label-to-camera, flap peeled open, one wipe pulled out, flap pressed shut.",
    "Flap and wipe close-up.", "pack_reveal", "Pack reveal"),
  X(EYE, "She presses the wipe on the closed eye for a second, then wipes down gently.",
    "The wipe with eye-makeup residue.", "eye_off", "Eye makeup off"),
  X("Face crop", "With her makeup on, she wipes one cheek in a single stroke; the wipe shows the residue.",
    "Wipe close-up.", "end_of_day", "End of day"),
  own_ids=True),
 "CNR": T("Micellar water", "removal", "Cotton pad is a neutral prop; never on the open eye.",
  X("Face crop", "She soaks a cotton pad from the bottle and makes one gentle swipe across the cheek.",
    "Bottle label and the used pad.", "pad_swipe", "Pad swipe"),
  X(EYE, "She holds the soaked pad on the closed eye for a second, then wipes down gently.",
    "Used pad with residue.", "eye_hold", "Hold on the eye"),
  X(HAND, "Hands-only: bottle tilted onto a pad, label to camera, the pad soaking.",
    "Bottle and pad together.", "bottle_to_pad", "Bottle to pad"),
  X(HAND, "Hands-only: a lipstick swatch on the hand removed with the soaked pad in one swipe.",
    "Clean hand.", "swatch_off", "Swatch off"),
  X("Face crop", "End of the day, she removes makeup from one cheek in one swipe.",
    "Used pad beside the bottle.", "end_of_day", "End of day"),
  own_ids=True),
 "FLT": T("Cleansing wipes", "removal", "Gentle use only; real pack design.",
  X("Face crop", "She pulls one wipe and wipes one cheek in a gentle downward stroke.",
    "Pack and wipe.", "pull_wipe", "Pull and wipe"),
  X(HAND, "Hands-only: a makeup swatch on the hand wiped off in one stroke.",
    "Clean hand and wipe.", "swatch_off", "Swatch off"),
  X(HAND, "Hands-only: pack label to camera, flap peeled, one wipe pulled out.",
    "Pack flap close-up.", "pack_reveal", "Pack reveal"),
  X("Face crop", "She wipes her forehead in one stroke after a long day.",
    "Wipe close-up.", "forehead", "Forehead wipe"),
  X("Face crop", "End of day: one wipe across the cheek, then the pack set down.",
    "Pack on the table.", "end_of_day", "End of day"),
  own_ids=True),
 # ================= ACCESSORY =================
 "VAN": T("Cosmetic / vanity bag", "accessory", "Not applied; only its real compartments, zips and handles; contents are props.",
  X(HAND, "Hands-only: she places a few makeup items into the open bag and zips it closed in one smooth pull.",
    "Zip pull and teeth close-up.", "pack_it", "Pack it"),
  X(HAND, "Hands-only: she unzips the bag and opens it toward camera showing the compartments.",
    "Compartments and lining close-up.", "open_reveal", "Open reveal"),
  X(HAND, "Hands-only: she lifts the closed bag by its handle off the dressing table.",
    "Handle and material close-up.", "carry", "Carry"),
  X(HAND, "Hands-only: she slots brushes into the elastic holders inside the bag.",
    "Holders filled.", "organise", "Organise"),
  X(HAND, "Hands-only: she places the closed bag into a tote for travel.",
    "Material and logo close-up.", "travel", "Travel"),
  own_ids=True),
}

# 17-Nov user: "fix application of make up and creams" - pasted VERBATIM into the applied slot's keyframe AND clip prompts.
APPLY_PHYSICS = {
 "common": (
  "APPLICATION PHYSICS (one real application, filmed on a phone, continuous take): "
  "START: the target area is BARE in the first frame (no product on it yet); the product is already open (cap off, "
  "applicator out / product on the fingertip) and ALREADY IN PLACE: the applicator / sponge / fingertip is touching the exact spot where the first stroke begins (user 19-Nov) - never raised in the air or held away from the face; the hand is still. "
  "CONTACT: the applicator (or fingertip) visibly TOUCHES the skin/lip - it never hovers or passes through it; the skin "
  "presses very slightly under it. "
  "COMPLETE RESULT: whatever is in frame at the end looks like a finished, natural application (both lips; a whole eye, brow, cheek or nail). A half-done area is never left visible next to its bare twin - frame tightly on the one side instead. "
  "DEPOSIT: product appears ONLY where the applicator has already passed, building gradually along the stroke path at the "
  "speed of the stroke - never all at once, never ahead of the applicator, never on any area it has not touched. "
  "The colour is a trail that grows FROM the applicator tip: its leading edge is always exactly under the tip, and everything "
  "beyond the tip is still bare skin/lip at that moment. No spots, patches, blotches or tint appear anywhere else, before or "
  "after. Write the clip prompt as a PROGRESS MAP: for each beat state which part is coloured and which is still bare "
  "(e.g. 1.0 s: only the centre third of the lower lip coloured, rest of the lower lip and the whole upper lip bare). "
  "STROKES: short, real-speed strokes in the area order given below; the whole application fits the 2.5 s main shot. "
  "SPEED: one slow, smooth, controlled pass at real speed (about 1-2 seconds per stroke), no repeated scrubbing, no speed-up. "
  "END: the hand moves the applicator away, the result stays exactly as applied; she then turns her face to look straight INTO THE CAMERA (user 19-Nov, every product) with a happy smile and holds still for the last second. "
  "SHADE AND FINISH: the applied colour is exactly the product's shade from its pack/bullet/swatch and the finish is the "
  "product's own (matte / satin / gloss / dewy) - it does not shift hue, glow or change between frames. "
  "MOOD (user 19-Nov, every product): she looks HAPPY and pleased the whole time - warm, relaxed, smiling eyes, a soft content smile whenever her mouth is free (during lip strokes the smile shows in her eyes and cheeks only, lips relaxed), ending on a gentle happy smile at camera. Never blank, bored, tense or serious; no exaggerated grin, no laughing, no teeth during lip work. "
  "BODY: head and face stay steady (no bobbing, no turning mid-stroke); exactly one applying hand + at most one steadying "
  "hand, each forearm traced to its own shoulder; natural finger joints; nails as in the persona. "
  "PRODUCT: the same pack, colour, label and applicator as the listing in every frame; it never changes shape, size or "
  "colour, never duplicates, never leaves the hand; the SAME hand that applies it also shows it to camera at the end - it is never passed to the other hand (user 19-Nov). "
  "SKIN: real skin texture and pores stay visible; no beauty filter, no smoothing, no lightening, no complexion change. "
  "CAMERA: ONE continuous take with NO jump cuts, no cuts of any kind, no time skips and no sudden reframing (user 19-Nov) - if a reference clip has cuts, bridge them with a smooth continuous move instead; phone held steady, nearly locked off, at most a 10% slow push-in; light and white balance constant. "
  "No speech, no mouthing words, no on-screen text."),
 "lips": (
  "LIPS (user 19-Nov, tested): head-to-chest framing, start frame with the wand tip ALREADY on the LEFT corner of the bare "
  "LOWER lip (viewer's left). FOUR SEPARATE strokes, each covering only half of one lip and stopping at the centre, with "
  "the wand visibly LIFTING OFF and being placed down again between strokes (otherwise the model merges them into 2): "
  "(1) lower lip left corner to centre, (2) lower lip right corner to centre, (3) upper lip left corner up to the "
  "cupid's-bow peak, (4) upper lip right corner up to the peak; then a clearly visible LIP PRESS (lips squeeze tight and roll slightly inward, one side-to-side "
  "'mm' rub, release back to full shape); then a natural happy face, eyes open, steady hold. 6 s clip: strokes 0.2-3.9 s, "
  "press 3.9-4.7 s, hold 4.7-6.0 s. Colour stays inside the lip border; no teeth, no pout. Liner: outline only in the "
  "same four strokes, no fill. Gloss/balm: one sheer pass per lip half, no thick goo."),
 "eyes": (
  "KAJAL / LINER ON THE WATERLINE (user 19-Nov): the eye reacts like a real eye - two or three quick natural blinks between strokes (pencil lifted slightly away for each blink) and the eye turns a tiny bit watery (thin glossy sheen on the lower lid, slight glisten), no tears running, kajal stays neat. "
  "EYES (ONE eye only, framed so the OTHER eye is out of frame - a tight close-up of one eye and brow; never show one "
  "eye done next to a bare eye): eye stability - the eye does not flutter, roll or blink during the stroke (one natural "
  "blink only after the hand moves away). The applicator never touches the eyeball or enters the eye opening. "
  "Kajal/liner: one continuous line along the lash line/waterline from inner to outer corner, complete to the corner. "
  "Mascara: wand at the lash root, two wiggles upward across the whole lash line, lashes separate and darken only where "
  "the wand passed. Shadow: lid closed during the pat/sweep, the whole lid covered by the end, then the eye opens slowly. "
  "False lashes: strip placed along the lash line in one press, held, then released."),
 "brows": (
  "BROWS (ONE brow, framed so the other brow is out of frame): short upward hair-like strokes from the inner brow "
  "outward to the tail so the WHOLE brow is filled by the end; colour only where the pencil touched; brow hairs stay "
  "natural, shape unchanged."),
 "cheek": (
  "CHEEK (ONE cheek, head turned three-quarters so only that cheek faces camera and the other cheek is hidden): "
  "brush/fingertip touches the cheek apple and sweeps up toward the temple, two short passes; a soft flush appears only "
  "along that path, blended edges, no stripe, no glow beyond the product. Highlighter: top of the cheekbone only."),
 "base": (
  "FOUNDATION (user 19-Nov): applied with a damp pink beauty blender sponge, never fingers - quick light BOUNCING dabs (sponge squashes and springs back, no wiping), area by area (right cheek, left cheek, forehead, nose and chin); by the end it is COMPLETELY blended into the skin: no patches, lines, edges, streaks or cakey areas, jaw seamless into the neck, real pores still faintly visible. VISIBLE PRODUCT COLOUR (user 19-Nov): every patch the sponge touches visibly takes on the product's own shade from the bottle (even if it differs from her skin), so the viewer sees the product being applied; the untouched side keeps her natural tone; she then holds the bottle beside the treated cheek to compare. "
  "CREAMS / BASE (concealer, primer, sunscreen, moisturiser): framing a close-up of ONE side of the face "
  "(head turned three-quarters) so the result looks complete in frame. A small real amount (pea-size or 2-3 dots) on the "
  "fingertip or sponge; dot it on that cheek / under that eye, then spread/blend with 3-4 short outward strokes or taps "
  "until that visible area is evenly covered. The cream is visible as a soft layer that thins and SINKS IN as it is "
  "blended - it does not vanish instantly, does not spread by itself, never appears where it was not touched. No white "
  "cast unless the product leaves one; no instant glow, no skin smoothing, no lightening. Sprays: arm's length, eyes "
  "CLOSED, one or two mists, a fine mist cloud that settles; skin looks fresh, not wet."),
 "nails": (
  "NAILS (ONE nail - the index or middle fingernail - in a tight close-up, other nails bare and out of focus or out of "
  "frame): hand flat on the table, brush wiped on the bottle neck, three strokes centre-left-right covering the WHOLE nail; "
  "colour only where the brush passed, glossy, clean cuticle line, no flooding."),
 "traditional": (
  "SINDOOR / BINDI: sindoor - a thin line drawn once along the hair parting with the applicator or fingertip, colour only "
  "on the parting, no spill onto the forehead. Bindi - picked off the sheet with a fingertip and pressed once at the centre "
  "between the brows, held a moment, straight and centred. Face front-facing for these; head steady."),
}
APPLY_AREA = {"lips": "lips", "eyes": "eyes", "brows": "brows", "cheek": "cheek", "base": "base", "skincare": "base",
              "nails": "nails", "traditional": "traditional", "kit": None, "tool": "base", "removal": None, "accessory": None}


# PANEL REFERENCES (user 19-Nov): a real application frame per product type. Prompts alone did not fix the pose, so the
# start keyframe MUST be generated with this image attached FIRST as the composition reference (framing, camera angle,
# head tilt, eye direction, hand and applicator position), the row persona second and the listing photo third.
# Pinned on Omni, so the asset id never expires; the local copy is in assets/makeup_refs/.
PANEL_REFS = {"KJL": ("assets/makeup_refs/KJL_panel_ref.jpg", "asset_129bb6f2c47944c69ddcef41ea921a23")}


def panel_ref(pid):
    r = PANEL_REFS.get(pid[:3].upper())
    if not r:
        return ""
    return (f"\n      PANEL REFERENCE (mandatory): generate the start keyframe with Omni image {r[1]} ({r[0]}) as IMAGE 1 = "
            "composition reference - copy its exact framing, camera distance and angle, head tilt, eye direction, hand "
            "coming from below and the applicator position; ignore its text sticker and its person. IMAGE 2 = the row "
            "persona (identity), IMAGE 3 = the listing photo (the product in her hand). She is dressed up and ready to go "
            "out with finished makeup; the eye not being worked on already has the product applied." + (" PENCIL GRIP (user 19-Nov): the kajal pencil is ALWAYS held like a pen - between the thumb and index finger near the tip, resting on the middle finger, the barrel angled back along the hand like writing - in the keyframe and in every frame of the clip; never held in a fist, at the far end, or vertically like a stick." if pid[:3].upper() in ("KJL", "ELR", "EBP", "LLI") else ""))


def apply_physics(t):
    area = APPLY_AREA.get(t["group"])
    return APPLY_PHYSICS["common"] + ((" " + APPLY_PHYSICS[area]) if area else "")


SHOWN = ("hands-only close-up at chest height, label/shade to camera, held its own natural way (unique show_device), "
         "opened if that shows the product better - NOT applied; gripped by ONE visible hand (forearm in frame) or resting on "
         "the vanity - never in the air or held by fingertips alone, never passed to the other hand, sealed packaging never "
         "opened, exactly one of the product in frame, life-size")
GROUP_PRIORITY = ["lips", "cheek", "eyes", "brows", "base", "nails", "kit", "traditional", "skincare", "tool", "removal", "accessory"]


def ptype(pid):
    return TYPES.get((pid or "")[:3].upper())


def default_slot(pids):
    """Slot to apply when the row does not say: the most visible application first (lips > cheek > eyes ...)."""
    best = None
    for i, p in enumerate(pids, 1):
        t = ptype(p)
        if t and (best is None or GROUP_PRIORITY.index(t["group"]) < GROUP_PRIORITY.index(best[1]["group"])):
            best = (i, t)
    return best[0] if best else 1


def block(pids, slot, letter, endslate_s=1.583333):
    if letter not in LETTERS:
        raise SystemExit(f"makeup approach must be A-E, got {letter!r}")
    lines = []
    for i, p in enumerate(pids, 1):
        t = ptype(p)
        if not p:
            raise SystemExit(f"slot {i}: no product id in the sheet - fix the sheet before this row (do not skip the slot)")
        if not t:
            raise SystemExit(f"slot {i} pid {p}: unknown makeup type {p[:3]} - add it to makeup_approaches.TYPES")
        if i == slot:
            ap = t["approaches"][letter]
            lines.append(f"  slot {i} [{t['name']}] = THE ONE APPLICATION - approach {letter}: {ap['name']} ({ap['id']})\n"
                         f"      FRAMING: {ap['framing']}\n      MAIN action and pose: {ap['main']}\n"
                         f"      PUSH-IN (end of the same take, no cut): {ap['detail']}" + (f"\n      RULES: {t['rules']}" if t["rules"] else "")
                         + f"\n      Paste VERBATIM into this product's start keyframe AND its application clip prompt:\n      {apply_physics(t)}" + panel_ref(p))
        else:
            lines.append(f"  slot {i} [{t['name']}] = SHOWN only: {SHOWN}; ONE continuous 4 s take - 2.5 s shown, then the camera pushes in on its label/pan/applicator (no cut)")
    per = 4.0   # user 16-Nov: exactly 4 s per product (main + detail), never more
    return f"""=== MAKEUP APPROACH {letter} - one application (slot {slot}) ===
ONLY ONE product is applied in this reel (slot {slot}); the other four are shown, never applied. Same persona, light and colour
treatment throughout so shades stay comparable. Application = a short demonstration in one continuous take, not a full routine. Every slot is ONE continuous take: the action,
then a camera push-in on the detail (user 21-Nov: no cut inside a product, zoom-in only). FACE: the applied product's take
shows the persona's whole face (every reel shows the face at least once). SUPPORT (Day 6): every product is gripped by a
visible hand or rests on the vanity in every frame; nothing floats; the same hand holds it all the way; parts keep their count.
{chr(10).join(lines)}
Rules: no eyeball contact, no skin lightening, no invented coverage/wear-time/SPF claims, no complexion change, natural skin
texture, no beauty filter, never invent an included brush/applicator. If the applied product cannot be applied faithfully with
approach {letter}, STOP and report (user picks another letter or slot).
TIMING (user rule): EXACTLY 4 s per product, never more - the applied slot too: ONE clip per product (2.5 s application or
close-up + 1.5 s camera push-in, no cut). 5 x 4 = 20.0 s footage + the {endslate_s:.2f} s end slate = {20 + endslate_s:.2f} s reel. In assemble.py
set CLIPS to 5 clips of 4.0 s (one continuous take per product). finish refuses a reel whose footage is over 20.0 s.
"""
