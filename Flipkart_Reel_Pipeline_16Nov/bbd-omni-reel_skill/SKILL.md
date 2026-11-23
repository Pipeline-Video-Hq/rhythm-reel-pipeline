---
name: bbd-omni-reel
description: Make finished Flipkart Big Billion Days (BBD) reels (9:16, ~20 s, Hinglish) on Omni 1.1 720p from rows of the "BBD" tab of the "Ai requirements- Truefan" sheet - one video per row, made with the row's persona avatar, its column-K script, the client's HOOK/PRODUCTS/CLOSE brief (column J), real Flipkart products (columns L-Q) and the client's BBD logo on every frame. Use when the user says "make BBD row N", "BBD rows N-M", "make the BBD videos", "BBD batch", "status of BBD reels" or "redo BBD row N".
---

# BBD row -> Omni 1.1 720p reel

```
SK=<this skill folder>/scripts      # e.g. .claude/skills/bbd-omni-reel/scripts
OUT=$BBD_OUT (default Flipkart/bbd_reels or ~/bbd_reels)            # row_NNN/ folders
DATA=<skill>/data   # bbd.csv snapshot, scripts_out/out_B*.json (column K), persona_ids.json, refs.json (optional)
```
`python3 $SK/status.py 2-501` shows where every row is. Work in batches; never ask per reel.

## Standing rules (user decisions - do not re-ask)

| Rule | Detail |
|---|---|
| Model | (user, 8-Oct-2026) **Lip-sync videos -> Omni; videos with no lip-sync -> Kling.** A video needs lip-sync when the persona speaks the script on camera (Voice rows). Omni: TrueFan MCP `generate_video`, `model: gemini-omni-1.2-flash`, `resolution: 720p`, `aspect_ratio: 9:16`, 3-10 s per clip, at most 2 in flight. No lip-sync (music-only rows, kids rows where a parent voice speaks off camera, any video with no on-camera speech): Kling 3.0 via the Higgsfield MCP `generate_video` (start frame = the same Nano Banana plate; check `models_explore` for the current Kling id; no generated dialogue - music bed, or an ElevenLabs voice-over from the approved roster laid in the edit). Plates for both: TrueFan `generate_nano_banana_image`. Never mix models inside one video. |
| Spend | Before the first paid call of a batch, state rows x clips x seconds and wait for a yes, unless the user already approved that batch. Re-rolls after a QC fail inside an approved batch need no new yes. |
| One take | ONE generation per shot (`generations: 1`). Re-generate a shot only when it fails QC, and log why in `row_NNN/log.md`. Never queue 2-3 takes to choose from. |
| REAL HOME BACKGROUND (permanent, user 27-Oct-2026) | "Video background should look like this, very real": every plate s1 passes assets/refs/real_home_bg_ref.jpg (upload it once, pin it) as a loose BACKGROUND-SPIRIT reference ("only the kind of middle-class home and light - NOT this room, NOT the person") plus one of `realism.HOME_VARIANTS` so every video is a different middle-class home (user: "same copy mat karo", "customer is middle class not premium") and the prompt includes `realism.HOME_BG`: ordinary middle-class Indian living room, plain cream walls, ceiling fan, tube light, wall TV with cables, switchboard, old wooden sofa with floral covers, patterned carpet, flat dim uneven light. Festive props stay small and ordinary. Never a decorated set, showroom, bokeh or studio light. Later plates reuse plate s1 for the room. (29-Oct: a "Tier 2 well-off home" version was tried and the CLIENT REJECTED it - do not use.) |
| ERROR GUARDS + VISUAL QC GATE (permanent, user 27-Oct-2026) | After row 79 shipped with 3 legs, casual clothes in a Diwali video, face drift, a morphed sandal, a tiny product, a lit diya on a sofa and a fake matchstick: every plate prompt also ends with `realism.PLATE_GUARD`, every clip prompt with `realism.CLIP_GUARD` (promptgen adds it). Poses: standing / walking / sitting upright with feet flat - never cross-legged, floor-sitting, crossed legs or bending. No fire handled by the persona. Before assembling: `visual_qc.py <row>` makes 4 fps full + zoomed lower-body sheets per clip and qc/visual_checklist.json; LOOK at every sheet and tick each item (limb count, face, product match, product size, outfit, room, actions, text/logos/people, looks real). `assemble.py` REFUSES to build until every item is true. A false item = regenerate that clip. |
| FOOTWEAR MODEL LOOKS BEAUTIFUL (permanent, user 28-Oct-2026) | "footwear wale video main model dikhne main sahi ho, dikhne main beauty ho". In every footwear row append realism.FOOTWEAR_BEAUTY to every plate prompt (and say "well-groomed, pedicured feet" in clip prompts): an attractive, well-groomed person (styled hair, light makeup, warm smile), and beautiful clean feet with a fresh pedicure. Realism stays (real home, phone look), but the person must look good. QC rejects dull, tired or unkempt looks and rough feet. |
| NO PAPER + FOOTWEAR FORMAT (permanent, user 28-Oct-2026) | Row 64: "notebook kahin nahi hona chahiye" and "lag nahi raha ye slipper ka hai". No notebook, notepad, list, paper slip, pen or clipboard in any shot: realism.NO_PAPER is inside PLATE_GUARD/CLIP_GUARD, and the shopping_list theme was removed from themes.py. Footwear rows: every distinct pair worn in a tight or knees-down shot where it fills the frame, plus hands-only turn shots (only two hands + the slipper) for at least 2 pairs. A medium shot with a tiny slipper does not count. |
| CLOTHING IS WORN (permanent, user 28-Oct-2026) | Row 13 showed the lehengas lying on the bed while the avatar wore her own kurta, and the user rejected it: "avatar pahen ke dikhayega". For every apparel product the avatar WEARS it in its shot: one product = one worn shot = one outfit change. Never lay a garment on a bed or sofa, never only hold it up, never show it on a hanger as the hero. Theme beats (list tick, unboxing) happen while she is already wearing it. QC fails any apparel shot where the product is not worn. |
| REALISM (permanent, user 27-Oct-2026) | Videos must NOT look AI-perfect - they must look like a real person filmed them on a phone. Every plate prompt ends with `realism.PLATE_REALISM`; every Omni/Kling clip prompt uses `realism.CLIP_CAMERA` (handheld, never tripod-locked) and ends with `realism.CLIP_REALISM` (promptgen.py adds both automatically; add them by hand to hand-written and music-row prompts). `assemble.py` adds handheld micro-shake, exposure/white-balance drift, phone grain and light sharpening to the footage only (plan.json `"realism": true` is the default; supers/logo/end slate stay clean). Never ask for a "plain wall in the top 20%" - it makes a fake flat/blurred band; ask for a natural, fully detailed room. QC fails anything that looks glossy, CGI, symmetrical-model-posed or studio-lit. |
| Persona | Every video is made with the row's persona (column C name; image from the column-B Drive link). The optional column-T reference (often non-Indian) is for FORMAT ONLY: hook, beat order, shot types, text style. Never copy the reference person, room, outfit or logo. |
| Products | The row's real Flipkart SKUs (`products.py`), photos passed as references in every plate. Colour, print, shape and packaging must match the listing. A product that morphs = QC fail. |
| Script | Column L is the script. Voice rows: Omni speaks the lines on camera (native lip-sync). Music rows (`music_only`): no speech; the `[Music only] Super ...` lines become the supers. |
| No repeats | Omni often says a phrase twice or ad-libs after the last line. `qc.py` (clip and master) flags back-to-back repeated words (turbo transcript, confirmed by whisper large-v3). A 2+ word repeat = FAIL: trim or jump-cut to keep one copy (or re-take). The master must show `checks.no_repeats: true`. |
| Wardrobe continuity | The persona wears the SAME clothes, shoes, bag and accessories in every shot of a reel (only the product being shown changes). Every plate after s1 uses plate s1 as reference and the prompt says "same outfit and same shoes on his/her feet as <IMAGE_REF_1>". A change = FAIL -> fix the plate and re-take the shot. |
| Devanagari dialogue | (user, Oct 8) In every Omni `Dialogue` line write the Hindi words in Devanagari and keep English words and brand names in Latin letters, e.g. "ओए, scroll मत करो, Flipkart पर BBD live है". Romanised Hindi gets mispronounced ("mat karo" said like the English "mat"). Add the PRON sentence from references/PROMPTS.md. The sheet script stays romanised; convert only inside the prompt. |
| No prices | (user, 8-Oct-2026) **No prices anywhere**: never spoken, never on screen (no rupee amounts, no MRP / strike-through, no "from Rs", no "under Rs"), not in scripts, not in supers. Product labels show the product name only. An offer may be referred to without an amount ("offer live hai", "sale live hai"). QC fails any price. |
| Voice consistency | Omni voices each clip independently. Use the identical voice description in every clip; if QC hears a different voice in one shot, re-generate that shot. |
| Speech | Natural everyday Hinglish with a clear Indian accent (native Hindi speaker, never American/British). Numbers are spoken as English words ("three", "thirteen"). Keep each persona's voice description identical in every clip (`personas/voices.json`). |
| Supers | Copy the reference reel's text look (style, position, case, emoji habits). Text NEVER overlaps the product or the face in any frame (QC red boxes). 8 words max per super. Text must contrast with what is behind it (white plain text on a cream wall is unreadable - use `color: #1c1c1c`, outline or pill). Skin-tone/ZWJ emoji are drawn as their base emoji. |
| CTA | The column-K ending (see Script endings) is the spoken CTA; the end super repeats it or the offer. Never "link in bio", "comment", "DM", "follow". Never Meesho/Amazon/Myntra. |
| Client-facing | No AI model names in file names, sheet cells or Drive (say "Final video", not "Omni"). Sheet: write only our columns (L, S, T and the delivery columns U-V); never touch A-K, M-R. |
| Instagram | Never open Instagram in any browser or account. Reference material is already on disk (`brief.json -> reference.image`). |


## BBD-specific rules (client, 8-Oct-2026)
| Rule | Detail |
|---|---|
| Volume | Client wants 250 outputs per day. Run rows in parallel (several Claude sessions / machines each own a row range); Omni is the bottleneck. Keep each reel to 2-3 clips. |
| BBD logo | `assets/brand/bbd_logo_overlay.png` (Flipkart + Big Billion Days badge, top-right) on EVERY frame; end card `bbd_endslate.mp4` (BBD lockup "Starts 9th October"). Keep supers out of the top-right corner. |
| Script endings | (user, Oct 8 v2 - replaces Poonam's 6 fixed endings) The script ENDS on a generic shop-on-Flipkart line built around Big Billion Days, worded differently in every video, e.g. "Toh chalo Flipkart pe, Big Billion Days mein shoes ki shopping karte hain!" / "Flipkart BBD aa gaya, toh sports shoes ki shopping ab banti hai!". Music rows: End super like "Shop shoes at Flipkart Big Billion Days". Column K (`data/scripts_out/out_B_v2.json`) already has them; generator `Flipkart/endings_v2/gen.py`. Never "link", "comment", "DM", "follow". Speak the ending exactly as written. |
| Format | Column J (HOOK / PRODUCTS / CLOSE / TONE) is the format brief; the optional reference (T/U) only adds look. HOOK = shot 1 with the persona, PRODUCTS = 2-3 products (pick the 3 with the clearest listing photos of the 6 links), CLOSE = persona on camera with the column-K Big Billion Days ending. |
| Personas | Resolved by Drive file id (`data/persona_ids.json`); names in column C have typos (Aditiya, laksha). Kids (Advik, Aarush, Reyansh, Vivaan, Diya, Navya, Myra, Ira): the child wears/uses the product on camera, a parent's voice speaks off camera (voice-over line, child does not lip-sync). |
| Electronics / mobiles / appliances | Keep the product as in its listing photo; no close-ups of screens with readable UI or of small printed text; avoid hands operating buttons (Omni morphs them) - hold up, turn, place on table. |
| Delivery | Drive folder `Flipkart BBD - Final videos` with one subfolder per category (column F vertical); each video goes in its category folder and its Drive link goes in column R "Delivery Url". Column V already has each row's category folder link. Column S is the team's status column - never write it. Never edit A-J or L-Q. |

## Run steps - one-shot recipe (every step below exists because a re-take was paid for once)

`$SK` = this skill's `scripts/`. Shots 2 in flight on Omni; never queue several takes of one shot.

1. **Brief + products.** `row.py <row>` -> `brief.json` (download any missing persona via the Drive connector + `b64save.py`); `products.py <row>` -> `products.json` + photos. Read the photos.
2. **Shot plan.** `shotplan.py <row>` -> `shots.json`: the column-K script split in order into shots (new shot per product, <= 20 words), **clip length sized to the line** (`ceil(words/2.7 + 0.9)`, 4-10 s - spare seconds are what make Omni repeat or ad-lib), coverage asserted (no script word can be lost).
3. **Fill shots.json** (you write this, once per row):
   - `voice` - one description reused word for word in every shot; `wardrobe` - the persona's own clothes, shoes on feet, bag, written positively ("the same plain grey hoodie with only its drawstrings, black joggers, plain worn grey trainers on his feet"); `setting`; `hook` (column I).
   - per shot: `dialogue_dev` = the line with **Hindi words in Devanagari, English words/brands in Latin, numbers as English words** ("ओए, scroll मत करो, Flipkart पर BBD live है"); `action` (0-x s beats, product held at chest/waist, a smile/nod at the end); `framing`; `plate` (asset id, step 4); optional `products` (1-based indices of the listings actually shown) and `pill_names`.
4. **Plates** (Nano Banana, 9:16 2K; s1 first, s1 passed as identity + wardrobe reference to every later plate). Before using a plate, zoom and tick ALL:
   - [ ] face = persona (and = plate s1)
   - [ ] the persona's own shoes/clothes/bag are **plain and unbranded** - zoom on the feet: no swoosh, "N", stripes-logo, letters
   - [ ] **same outfit and same shoes on the feet as plate s1**; the shown product is only in the hands, never worn unless it is worn in every shot
   - [ ] product held at **waist/side height with the chest visible** (a product hiding a hoodie/shirt front made Omni add a clip-on mic 4 times)
   - [ ] product = listing photo side by side (colour, print, logo patch, sole); two products in one plate are described by colour in CAPS
   - [ ] no text, no extra people, five fingers
5. **Prompts.** `promptgen.py <row>` -> `prompts.json`. It refuses until: Devanagari present and no romanised Hindi left, every script word still in `dialogue_dev`, voice/wardrobe/setting set, plates set, and no "microphone/mic/lav" words (naming them invites one). Send each entry to `generate_video` exactly as written (`model`, `resolution`, `aspect_ratio`, `duration_seconds`, `image_asset_ids`, `prompt`). Download to `clips/s<N>.mp4`; record ids in `gens.json`.
6. **Clip gate (automatic).** `clipcheck.py <row> <N>` per clip: both Whisper models + a script-vs-speech comparison ->
   - `PASS` (one trim span) / `FIX` (repeat or ad-lib cut out at the nearest silence, the cut audio re-transcribed and verified) - no human listening needed;
   - `RETAKE` = scripted words missing -> regenerate that shot only (same prompt), log why.
   Then `qc.py <row> clips/s<N>.mp4` and look at the sheet for the visual gate: mic/badge appearing, wardrobe/shoes changing, product morphing, face drift, hands. Any of these = RETAKE (fix the plate first if the plate caused it).
7. **Edit.** `autoplan.py <row>` -> `plan.json` from the verified keep spans (2nd+ span of a shot = 1.06 punch-in), hook top for 3.2 s, **one product-name pill (no price) per shown product at the TOP of frame during its shot, ending before the cut**, end super over the closing shot, badge corner kept clear. `assemble.py <row>`, `qc.py <row>` (master must show `no_repeats: true`), read the master sheets, then the independent QC agent (references/QC_BRIEF.md).
8. **Deliver** (references/DELIVERY.md): via Claude in Chrome; `small.sh` copy -> `Flipkart BBD - Final videos/<vertical>/` (ids in `data/drive_folders.json`, folder is anyone-with-link Editor) -> column R; verify; `delivery.json`.

Music-only rows / no lip-sync: skip 2-3 and 5-6 speech parts; Kling clips from the same checked plates, supers from the `[Music only] Super ...` lines, end super = the column-K End line.

On the one-shot path a reel needs ~24-28 s of Omni + 4-5 plates; a re-take only when the visual gate fails.

## Status words for the user
Report per batch: rows done / failed-QC-being-fixed / blocked (why), clips generated, and the Drive links.
