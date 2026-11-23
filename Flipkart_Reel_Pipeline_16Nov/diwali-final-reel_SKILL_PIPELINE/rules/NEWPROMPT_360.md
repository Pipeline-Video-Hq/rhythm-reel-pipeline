# NEW PROMPT + 360p (user 3-Nov ~13:45: "Ye new prompt ke sath 360p pe continue karo")
Approved sample: 05_TESTS/Sample_row045_Shruti_NEWPROMPT_OMNI360_480p.mp4 (work: 05_TESTS/np_work/row_045, plan.json there).

CLIPS: TrueFan Omni "gemini-omni-1.2-flash", resolution "360p", 9:16. Every clip prompt =
"The first image is the starting frame <FIRST_FRAME>." + the block below VERBATIM + "ACTION: <one slow gesture>" + the usual
no-speech / two-hands / keep face-outfit-room / one continuous take / same spot lines.

CAMERA: Recorded on a recent flagship phone's main 1x camera in standard video mode. Not portrait mode, not cinematic mode, no beauty filter, no HDR glow. Deep focus: the creator, the outfit and the room are all equally sharp. Crisp edges on embroidery, fabric weave and prints clearly visible. Clean, high-contrast image with true colours; no haze, no soft focus, no glow, no grain, no motion blur.
LIGHT: bright, even natural window daylight on the creator from the front or side. No dim rooms, no backlight, no fairy-light-only scenes.
MOTION: phone propped or held steady with only slight natural hand movement. No walking shots, no fast pans, no spins, no swishing the dupatta. The creator moves slowly: gentle half-turns, small hand gestures. For every outfit, stand still facing the camera for at least one second with the product fully in frame.
FRAMING: the product is clearly visible in every shot. Prefer mid shots and close-ups over wide shots. The creator's face may be hidden (phone held in front of the face, mirror selfie, only hands holding the product) as long as the product is shown.

ACTIONS: slow only - stand still 1 s facing camera, then ONE of: gentle half-turn and back, lift dupatta/edge a little, smooth the
front, trace embroidery with a hand (close-up), hold hem edges (close-up), hand at hanger hook. NO twirl/flare spins (Omni
over-rotates: row 45 s8 did a full turn -> trimmed). Hands-only and hanger shots get the CAMERA/LIGHT/MOTION/FRAMING lines too.
PLATES: same pipeline, but write the LIGHT line into every plate prompt (bright window daylight on her, no fairy-light-only look)
and prefer mid shots / close-ups over very wide shots.
SHOT GRAMMAR: follow the row's SHOOTING STYLE (pipeline.py prompt prints it; user 3-Nov ~14:45). Packet/courier-pouch unboxing ONLY
in style D videos; in A/B/C/E videos no unboxing. Max 1 hanger. Close-ups + zooms as before.

## SHOOTING STYLES (user 3-Nov ~14:45) - one style per video, alternate row by row (even row = 1st, odd row = 2nd)
"pipeline me sirf shooting style badalna hai, baaki sab same. Saari videos music-only hai (koi bolta nahi)"
A mirror selfie (phone face ke aage) | B headless fit check | C sirf haath se product demo | D courier pouch unboxing | E room before/after
Ethnic + Western: A, B | Women FW: B (knee se neeche), D | Men FW: B (knee se neeche), C
Kids clothing, Kids FW, Kitchen, Household, BabyCare, Toys, Fragrance: C, D | Fashion wearables: B (wrist/neck close), D
Home Decor + Furnishing: E, C | Makeup: C, D (baaki categories ke baad)
Full style text: pipeline.py STYLE_TXT / STYLES (printed into every worker prompt).
