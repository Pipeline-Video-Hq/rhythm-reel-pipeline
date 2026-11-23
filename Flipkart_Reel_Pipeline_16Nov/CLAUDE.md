# Flipkart Rhythm reel pipeline (merged)

One folder, two pipelines. It turns rows of the Rhythm sheet (`Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv`, tab
`1500_1`) into vertical (9:16) Flipkart reels. Each reel has 5 products, background music only, and gives **exactly 4 s to each product**
(ONE continuous take per product: 2.5 s use + 1.5 s camera push-in, no cut): 20 s of footage + the 1.58 s end slate = **21.58 s**. Generation runs on the TrueFan / Omni MCP: Nano Banana 2 for image plates and
**gemini-omni-1.2-flash, 360p** for clips, always filed in the Omni folder `Flipkart_Fashion-Rhythm_AI_Profiles`.

- **Every vertical except Makeup** goes through the main pipeline, with one of 5 presentation approaches (A-E) per row.
- **Makeup** goes through the Beauty pipeline, with one of 5 application approaches (A-E) per product type. Only one product
  is applied per reel.
- The row sheet `02_BAU_DATA/row_approaches.csv` decides, row by row, which approach is used and which rows are on hold.

## What the folder contains

| Path | What it is |
|---|---|
| `CLAUDE.md` | This file. |
| `README.txt` | Change log of the merge (16-Nov), with the same commands in short form. |
| `REEL_PRESENTATION_IMPLEMENTATION_SPEC.md` | The client spec that the approaches are built from. |
| `diwali-final-reel_SKILL_PIPELINE/` | **Main pipeline.** `scripts/pipeline.py` (entry point), `assemble_fk.py` (assembly, music, logo, end slate), `approaches.py` (A-E for 11 families, 4 s timing), `bgm_rotation.py` (music round robin), `product_spec.py` (product spec sheets), `makeup_approaches.py` (A-E for 32 makeup types), `sheet_to_rows.py` (sheet CSV to row files). Also `SKILL.md`, `rules/`, `briefs/`, `examples/`. |
| `bbd-omni-reel_skill/` | Engine used by the main pipeline: `scripts/` (assemble, realism, visual_qc, products fetcher, board titles), `assets/brand` (Flipkart logo and end slate), `assets/fonts`, `assets/refs`, `personas/` (all 50 sheet personas, `<name>.jpg`). |
| `beauty_pipeline/` | **Beauty (Makeup) pipeline**: `README.md`, `SKILL.md`, `PROMPT_LOCKS.md`, `CATEGORY_RULES.md`, `REALISM_RULES.md`, `PIPELINE_CONCEPT_LAB.md`, scripts (`omni.py`, `generate_clips.py`, `check_actions.py`, `validate_concepts.py`, `product_text.py`, `hands_prompt.py`, `assemble_template.py`), `example_run_ID_4/`. Needs a `.env` holding `OMNI_MCP_URL` and `OMNI_TOKEN`; it is **not in the zip**, so add your own. |
| `assets/music/rhythm_bgm_approved/` | **The only music used**: 22 approved tracks (`RHY_BGM_004 ... 031`). Tracks 001, 002, 003, 011, 013, 014, 017, 019 and 022 are not approved and not included. Handed out by **round robin** (see Music). |
| `assets/music/bgm_rotation.json` | Round-robin state, created on first use: the next track and which track each row got. |
| `assets/brand_beauty/` | Beauty end slate, logo overlay and fonts. |
| `02_BAU_DATA/` | Row data: `row_approaches.csv` (**per-row approach control**), `film_titles.json` (on-screen text per row), `sheet_rows_*.json` (rows for `addrows`), `worker_rules.txt`, `prep_*.sh` / `qc_wear.sh` / `deliver_wear.sh` helpers, batch notes, example prompts. |
| `runs/BAU_1500_1/` | Created on the first run: `03_WORK/row_NNN/` (one work folder per row) and `01_LATEST_FINAL/Day N/<Category>/` (finished 480p reels plus `1080p_masters/`). |

Every path is resolved from this folder, so it can live anywhere. Set `FK_PIPE=<path>` to point at another copy.

## Setup (once per machine)

1. Install Python 3 (with `Pillow` for Beauty), `ffmpeg`/`ffprobe` on the PATH, and `rclone` with a `gdrive` remote (only needed for `upload`).
2. Put `beauty_pipeline/.env` in place (Omni token) and make sure the TrueFan / Omni MCP connector is enabled in Claude.
3. Optionally link the skills so Claude finds them: `diwali-final-reel_SKILL_PIPELINE` -> `~/.claude/skills/diwali-final-reel`
   and `bbd-omni-reel_skill` -> `~/.claude/skills/bbd-omni-reel`. The scripts themselves do not need the links.
4. Always run with `FK_MODE=BAU` (the Rhythm sheet is a BAU job, so no festive decor). All commands below are run from
   `diwali-final-reel_SKILL_PIPELINE/scripts/`.

```bash
cd diwali-final-reel_SKILL_PIPELINE/scripts
export FK_MODE=BAU
```

## Step 1: load rows from the sheet

```bash
python3 sheet_to_rows.py "/path/to/Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv"          # all rows
python3 sheet_to_rows.py "/path/to/....csv" 1002-1020 417                                            # only some rows
python3 pipeline.py addrows ../../02_BAU_DATA/sheet_rows_csv_Makeup.json                             # one vertical at a time
```

`sheet_to_rows.py` writes one `sheet_rows_csv_<Vertical>.json` per vertical and adds each row's "Text for the Film" to
`film_titles.json`. `addrows` registers the rows in `02_BAU_DATA/batch_100.json` and downloads the 5 product listings with
their photos.

Rows with an empty product link are **skipped and listed**. Fix these in the sheet first: 829, 830 (HomeFurnishing), 891, 898
(household kitchen), 951, 957 (Household suppliers), 1025 (Makeup), 1229, 1240, 1242 (women fragrance), 1319, 1331 (Grooming
Men). Each of these rows has slots 2-5 empty.

## Step 2: choose the approach per row (`02_BAU_DATA/row_approaches.csv`)

The sheet has one line per sheet row (1,500 lines) with these columns:
`row, name, vertical, family, approach, apply_slot, options, delivered`.

- `approach`: put **A, B, C, D or E** to make the row with that approach. **Leave it empty (or write HOLD) to keep the row on
  hold**; it will not run. Every row starts on hold.
- `apply_slot` (Makeup only): 1-5, the **one product that gets applied**. The other four are shown only. It is pre-filled with
  the most visible product, ranked lips > cheek > eyes > brows > base > nails > ...
- `options`: what A-E mean for that row's family. For Makeup it lists each slot's product type.
- `delivered`: `yes` for rows already delivered (the first 100 ethnic rows).

You can edit the file in Excel or Sheets, or use these commands:

```bash
python3 pipeline.py setapproach AUTO 467-500      # 21-Nov: rotation per vertical (A, B, C, D, E ... in sheet order)
python3 pipeline.py setapproach B 2 3 10-20       # rows 2, 3 and 10-20 use approach B
python3 pipeline.py setapproach HOLD 15           # put row 15 back on hold
python3 pipeline.py setslot 3 1060                # Makeup row 1060: slot 3 is the applied product
python3 pipeline.py approaches                    # per vertical: how many rows on A-E and how many on HOLD
python3 pipeline.py approaches B                  # ... and list the rows set to B
```

To force a letter for a single run without changing the sheet, use `python3 pipeline.py prompt <row> D` or `FK_APPROACH=D`.
For Makeup, `FK_APPLY_SLOT=2` does the same for the applied slot. Each row logs what it was made with in
`runs/BAU_1500_1/03_WORK/row_NNN/approach.json`.

### Approaches, non-Makeup verticals (`approaches.py`)

One approach per reel, applied to **all five products**. Each product gets a main shot and a separate detail shot. Men's and
women's verticals share the letters but have their own actions.

| Family (sheet verticals) | A | B | C | D | E |
|---|---|---|---|---|---|
| ethnic (Women's Ethnic Wear, Men Ethnic) | mirror_try_on | garment_showcase | walk_pause_turn | finishing_touches | held_to_worn |
| footwear (women Footwear, Men Footwear) | standing_fit | walk_stop | seated_adjustment | side_back | held_to_worn |
| everyday_clothing (Women western, Men casual) | mirror_fit | direct_fit | walk_settle | finishing_touches | held_to_worn |
| fashion_wearables (FashionWearables _Women / _Men) | worn_check | put_on_reveal | feature_closeup | natural_use | held_to_styled |
| home_decor (Home Decore) | place_reveal | before_styled | held_inspection | room_to_detail | styling_adjustment |
| home_furnishing (HomeFurnishing) | spread_smooth | before_furnished | fabric_fall | everyday_use | folded_to_place |
| kitchen (household kitchen) | counter_demo | preparation | access_fill | serve_present | stored_to_ready |
| household_utility (Household suppliers) | one_task | task_before_after | feature_demo | in_place | retrieve_use_return |
| baby_care (baby care) | caregiver_inspection | prepare_use | nursery_placement | feature_demo | routine_preparation |
| fragrance (women fragrance, Men fragrance) | bottle_showcase | getting_ready | application | vanity_pickup | ready_to_leave |
| grooming (Grooming Men) | mirror_routine | product_to_use | feature_closeup | finishing_touch | shelf_use_return |

### Approaches, Makeup (`makeup_approaches.py`)

The product type comes from the first 3 letters of the Flipkart PID. There are 32 types, and each has 5 detailed approaches,
each written as framing + main action/pose + detail shot + type rules.

- **Products applied to skin** (lipstick LSK, lip balm LPB, lip liner LLI, lip gloss LGS, lip & cheek tint LSQ, mascara MCR,
  kajal KJL, eyeliner ELR, eyeshadow ESD, shimmer SMG, false lashes FLS, eyebrow pencil EBP, foundation FND, foundation
  stick/concealer CLR, compact CMP, primer/fixer PRM, blush BLU, highlighter HGL, bronzer BRZ, sindoor SIN, bindi BIN) use
  the spec's makeup formats: **A** mirror_application, **B** swatch_to_finish, **C** direct_application, **D** held_to_worn,
  **E** finishing_touch.
- **Products used rather than applied** (nail polish NLP, sponge PFS, brush set BAR, nail-art brushes NLA, makeup kit MKT,
  combo kit CBK, sunscreen SNR, remover wipes MUR, micellar water CNR, cleansing wipes FLT, vanity bag VAN) have 5 named
  use-approaches each, for example `one_nail`, `bounce_blend`, `fan_reveal`, `pull_wipe`, `pack_it`.
- In a reel **only the `apply_slot` product is applied**, with the row's letter. The other four get a hands-only close-up
  (label to camera, each held a different way) plus a detail clip.

## OpenAI key (21 Nov)

The OpenAI API key is in this folder's `.env` (`OPENAI_API_KEY`), copied from `~/Downloads/flipkart-pipeline-final/.env`.
- **Never use it without the user's explicit yes for that specific run.** The only code that uses it is the product
  planner, and only with `--confirmed`. A plain `plan` is a dry run that sends nothing.
- **Never print, show, copy elsewhere or send the key.** `.env` is never put in a zip; the zip build excludes it.
- **Never re-send a failed OpenAI request automatically:** report it and ask.

## Step 2b: plan the row with OpenAI (required for every non-Makeup row, 21 Nov)

Every non-Makeup row is now made from **product plans**. `prompt` refuses a row that has no plan
(`FK_LEGACY=1` prints the old prompt, for emergencies only).

```bash
python3 pipeline.py plan 593              # dry run: lists exactly what would be sent to OpenAI - nothing is sent or paid
python3 pipeline.py plan 593 --confirmed  # after the user's yes: one request per product without a saved plan
python3 pipeline.py shots 593             # rebuild the reel plan + every prompt from the saved plans (no OpenAI call)
```

**What goes to OpenAI:** only the product. That is the listing title, brand, specifications, description and up to 3
listing photos, plus our rule book and the approach letter's text. Never the persona, the sheet, the client or the
project. The exact request text is saved in `row_NNN/planner_requests/`.

**What comes back** (one plan per product + approach, saved in `02_BAU_DATA/product_plans/` and reused by every row that has
that product):
- **The product:** what it is and how people really use it every day.
- **Life size:** real dimensions and how big it looks against the body.
- **Prerequisites:** for example, a razor needs stubble and shaving foam already on the cheek; laces are tied only on a
  lace-up.
- **The scene:** room, surface, life-size props, and what must NOT be in it.
- **3 shot variants:** each with the start and end state, the framing, the push-in target, and timed beats. Every beat says
  which body part moves (her/his own left or right), direction, distance in cm, speed, contact and what stays still.

**Checked by code before anything is generated** (`product_planner.validate`). A plan with errors blocks the row:
- **Timing:** beats run without gaps from 0 to 4 s, the action finishes by 2.5 s, and only the camera moves after that.
- **Movement:** at most 3 movements, head turns at most 30 degrees, a step at most 30 cm.
- **Not allowed:** a cut, a flip, a zoom-out, taking off or putting on footwear, rolling or lifting large textiles, a
  mirror in frame, or a product appearing from nowhere.
- **Matches the listing:** laces, buckles and velcro are used only when the listing has them; slip-ons are never adjusted.
- **Prerequisites:** a razor needs foam and stubble; a trimmer needs a beard.
- **Hands off worn slip-ons (21 Nov, after the first real plans):** worn footwear with nothing to fasten is shown only with
  small foot movements. The hands never smooth, rub, tap, pinch or "seat" it; QC had flagged "sandals are getting fixed".
- **Rejected plans:** a saved plan that fails the checks is re-requested on the next `plan --confirmed`. The old file is
  kept in `02_BAU_DATA/product_plans/rejected/`. `prompt` re-checks every plan and rebuilds the prompts each time, so a
  worker never gets a stale or failing plan.

**The reel planner** (`reel_planner.py`, no cost):
- **Rooms:** picks the fewest rooms (1, at most 2) that fit all 5 products.
- **Background bible:** a fixed list per room of walls, floor, light, and every piece of furniture and background prop with
  its real size and place. It goes into every prompt, so the background and props never change.
- **Same-category items:** removed from the room (a rug product means no other rug), or kept plain and swapped for the
  product only in its own slot (bedsheet, curtains, cushions, towel).
- **Camera:** fixed positions per framing, always facing the same back wall.
- **Person lock:** height in cm against the door, seat and counter, plus outfit and hair (`02_BAU_DATA/personas_body.json`).
- **Order:** products are ordered so the person's state stays logical (the beard is shaved only after the beard oil).
- **Movement:** picks one shot variant per product so no two products repeat a movement.

**The shot builder** (`shot_builder.py`) writes every prompt into `row_NNN/shots/`. The worker pastes them verbatim:
- **Room master:** one image per room. It fixes the room, the props, the light and the person's size.
- **Per product:**
  - a **start still** (an edit of the room master);
  - an **end still** (an edit of the start still, with the correct result and the camera pushed in);
  - a **clip:** Omni 1.2 first/last-frame, 4 s, 360p, 9:16, between the two stills.
- **plan.json:** a skeleton with 5 segments of 4.0 s, in the planned order.

`finish` checks a planned reel automatically before assembling it. This is not QC; it runs in seconds. It requires exactly
5 products, one 4.0 s take each in the planned order, digital zoom 1.0, and no cut, black or frozen frames inside a take.
It refuses the reel and names the slot to regenerate.

## Step 3: make a row

```bash
python3 pipeline.py new 417            # work folder runs/BAU_1500_1/03_WORK/row_417 (brief, products, folders)
python3 pipeline.py prompt 417         # prints the worker prompt for the row's approach (refuses HOLD rows)
```

Give the printed prompt to a Claude worker; this repo used one worker per row, with 6 running at a time. The worker builds
the plates and clips on Omni 1.2 at 360p, writes `plan.json`, and runs `finish`. **There are no QC stages** (see below).

```bash
python3 pipeline.py finish 417         # assembles, music, logo, end slate -> 480p in 01_LATEST_FINAL/Day N/<Category>/
python3 pipeline.py upload 417         # copies the 480p to Drive BAU_1500_1/Day N/<Category>/ and records the link
python3 pipeline.py status             # which rows are finished
```

- **Makeup rows** work the same way. `new` also lays out the Beauty run folder. `prompt` prints a Beauty worker prompt with
  the makeup approach block. The worker follows `beauty_pipeline/README.md` minus its checks: concept card, action JSONs +
  `clip_frames.json`, then `generate_clips.py --confirmed` directly (Omni 1.2, 360p). It copies `assemble_template.py` to
  the row folder as `assemble.py` with `OUT = final/<out name>`. `finish` runs that `assemble.py` and files the result the
  same way as every other vertical.
- **Timing, 4 s per product (never more), ONE continuous take per product (21 Nov).** Every product, the applied makeup one
  included, gets a single 4 s clip: 2.5 s use or presentation, then 1.5 s camera push-in on the detail. There is no cut, no
  second clip and no zoom-out inside a product, and the digital zoom stays 1.0. This goes in `plan.json` (or the Beauty
  `assemble.py` CLIPS list) as 5 segments. `finish` refuses any reel
  longer than 20 s + the end slate (21.58 s, plus 0.1 s for encode rounding).

## Product specs (every vertical except Makeup)

For each of the 5 products on display, `product_spec.py` reads the public Flipkart listing and writes a spec sheet:
`runs/BAU_1500_1/03_WORK/row_NNN/specs/slot_N.json` holds the title, brand, price, every listed specification and the
description. `slot_N.txt` is the **PRODUCT SPEC block**. Colour, pattern, fabric/material, type, style, parts and pack
contents come first, then the remaining specs.

- `new <row>` builds the 5 sheets. `prompt <row>` builds any that are missing and puts all 5 blocks in the worker prompt.
- The worker pastes slot N's block **verbatim into every plate and every clip prompt for that product** (main and detail
  shots), alongside its listing photos as the image reference. This keeps the generated product true to the listing.
- Makeup rows don't use this; the Beauty pipeline has its own `product_text.json`.

```bash
python3 product_spec.py --pid SARHQNNCEKZFDEZR ./out     # test one product: prints the JSON and the PRODUCT SPEC block
python3 product_spec.py ../../runs/BAU_1500_1/03_WORK/row_002   # all 5 slots of a row
```
`02_BAU_DATA/example_specs/row_002/` holds the 5 sheets made for row 2 (sarees) as an example.

### Product reference sheets (6-angle image per product)

Before any plate, the worker makes a **product reference sheet** for each of the 5 products: one 3:2 image on white with 6
equal panels (front, three-quarter front-left, three-quarter front-right, left side, rear, and open or top-down). Rules are in
`diwali-final-reel_SKILL_PIPELINE/rules/PRODUCT_REFERENCE_SHEET.md`, including how to present each product type (clothes on
an invisible ghost mannequin, footwear as a pair with the soles, wearables, decor, furnishings, kitchen, fragrance,
grooming, baby care, multi-piece sets).

1. Look at the main listing photo (`products/p<N>_1.jpg`, called Image 1) and write `specs/slot_<N>/product_caption.json`
   (schema: `rules/PRODUCT_CAPTION_SCHEMA.md`). Every sticker, price/barcode label, badge, protective film, tag, wrap,
   overlay graphic, watermark, food/content and prop goes in `unwanted_elements` and is **removed** from the sheet. A mark that
   changes between listing photos is a sticker.
2. Write `specs/slot_<N>/sheet_prompt.json` (`prompt` + `excluded_elements`). Never put the brand, model or listing name in
   the prompt; refer to "the <product type> in Image 1".
3. Run `python3 product_spec.py --check-sheet <row folder> <N>`. It must print OK (every caption key present, no brand/model
   name, Image 1 referenced, removed elements listed).
4. Generate it with Nano Banana 2 at 3:2 with Image 1 attached, one take, and save it as
   `specs/slot_<N>/reference_sheet.png`.

Every plate of that product then gets its reference sheet as an image reference plus its PRODUCT SPEC text, and every clip
starts from such a plate. Example inputs, a 3-cooker set with its red paper labels removed:
`02_BAU_DATA/example_specs/row_852_slot1/`.

### Same product in every shot (identity lock)

Fix for a product changing between its main and detail shots (a kurta came out with a different hem, pattern and placket):
- `--check-sheet` also writes `specs/slot_<N>/identity_lock.txt`. It is built from the photo caption and lists the exact cut,
  hem shape, base colour and pattern, trims, every button (count and placement), pockets and every piece of the listing.
  For clothing the caption must record all of these (`rules/PRODUCT_CAPTION_SCHEMA.md`).
- The **main** plate of a product uses its reference sheet + listing photo, and its prompt carries the PRODUCT SPEC and
  IDENTITY LOCK.
- **Every other plate** of that product, for every vertical and every approach A-E, is never generated fresh. That covers the
  detail close-up, the held-up / hanger / in-hand / folded view, the before or empty-spot view, and the put-on, open or
  closed state. Each one is an **edit of that product's main plate** (main plate first in the references): "the same
  <product> - <the change>; the product itself does not change". Make the main plate of each product first, then its edits.
- **Makeup** follows the same rule: each product's first keyframe comes from its listing photo, and its other keyframes are
  edits of it.
- Tested 17-Nov on a Men Ethnic kurta (row 417 slot 1): the main and detail plates show the same kurta. See
  `02_BAU_DATA/example_specs/row_417_slot1_identity_test/main_vs_detail.jpg`.
- Every clip prompt carries the identity lock plus "the product stays exactly as in the starting frame; it never changes,
  morphs or swaps".
- Clothing main shots wear the exact listing outfit (all its pieces). If the listing is only a top, the bottom is plain,
  neutral and the same in that product's main and detail shots.

### Hanger shots (clothing)

Fix for hanger shots that came out physically wrong: a top hanging sideways with its collar off the hook, trousers not held
by the hanger, hooks hanging from nothing. Every clothing approach (ethnic, women western, men casual) now carries a
`HANGER PHYSICS` rule (`approaches.py`), pasted into every plate and clip prompt that shows a hanger:
- the hanger is held by the hand by its hook, or hooked over a real rail, rod or door hook;
- tops hang upright and symmetric, with the hanger arms inside both shoulders, the collar centred under the hook and the
  sleeves falling straight;
- bottoms hang on their own hanger, clipped level at the waistband or folded evenly over the bar;
- a set (top + bottom) goes on ONE hanger: the top hung on it and the bottom folded over the same bar under it (two hangers
  in one hand made the second one float in testing); a saree is folded over the bar;
- exactly two hands: one on the hook, the other relaxed at the side or holding the hem on its own side;
- nothing floats, twists or hangs sideways.
- Tested 17-Nov (row 417 kurta set): `02_BAU_DATA/example_specs/row_417_slot1_identity_test/hanger_v1_vs_v2.jpg`.

### Makeup and cream application

`makeup_approaches.py` has `APPLY_PHYSICS`, pasted word for word into the applied product's start keyframe **and** its
clip prompt. It has a common block plus an area block for lips, eyes, brows, cheek, base/creams or nails.
- **Start:** the target area is bare and the product is already open and loaded.
- **Contact:** the applicator visibly touches the skin or lip; it never hovers or passes through.
- **Deposit:** colour or cream appears only where the applicator has passed, gradually, at the stroke's speed.
- **Stroke:** one slow pass at real speed; the result holds at the end.
- **Shade and finish:** exactly the product's own, with no glow or flicker.
- **Face and body:** head steady, no teeth or talking, eyes stable, exactly two hands.
- **Look:** no beauty filter or skin lightening; camera nearly locked off.
- **Creams:** a pea-size amount on one small area, blended in 3-4 strokes, thinning and sinking in, never vanishing
  instantly; sprays with eyes closed.

The clip prompt is written beat by beat (0-0.5 s start, the strokes, the press, the final hold). Example:
`02_BAU_DATA/example_specs/makeup_lip_application_test/`.

## No QC stages (user 17-Nov)

QC was removed because it slowed everything down. Workers make **one take per plate and per clip** and go straight to
`finish`. The removed steps are:

- Main pipeline: the visual-QC hard gate in the engine's `assemble.py` (switched off by `assemble_fk.py`), `visual_qc.py`
  sheets, `qc/visual_checklist.json`, ARM TRACE / teeth / 1 fps checks, retake rounds, and the `qc/final_1fps.jpg` review
  tile after `finish`.
- Beauty: the frame gate, `check_actions.py` (no longer run by `generate_clips.py`; pass `--check` to run it again),
  `validate_concepts.py`, `product_text.py check`, and the `--dry` review round.

The quality rules (physics, two arms, product in frame, no decor) are still **written into every generation prompt**; they
are just not checked afterwards. The 4 s timing check in `finish` stays, because it is instant. Backups of the files before
this change end in `.bak_17nov_qc`.

## Music: 22-track round robin

Every reel, across all verticals and both pipelines, gets its track from its **row number** (20-Nov): track =
approved[(row - 1) % 22]. Row 1 gets RHY_BGM_004, row 2 gets 005, ... row 22 gets 031, and row 23 starts again at 004. This
used to be a per-machine counter, which repeated tracks when several machines worked in parallel; now every machine gives a
row the same track, and neighbouring rows never share one. A row keeps its track, so rerunning `finish` on it never changes
the music.

Also from 20-Nov, in every non-Makeup prompt (`approaches.py` `GENERAL`):
- **No repeated gestures:** each of the 5 products gets a different gesture and pose, written into `plan.json`.
- **Quality:** sharp product; no warping, morphing or flicker; product text stays legible.

`prompt` also prints a **warning** when a product is used in other rows too, so that reel's shots of it look different.
- Non-Makeup rows: the track is assigned by `assemble_fk.py` when the row is finished.
- Makeup rows: the track is assigned when `prompt` runs and written into the worker prompt (`MUSIC = ...` for `assemble.py`).
  The Beauty concept check accepts repeats from this pack.

```bash
python3 bgm_rotation.py status        # next track + how many reels each track has been used on
python3 bgm_rotation.py get 417       # show (or assign) row 417's track
```
To restart the rotation from track 004, delete `assets/music/bgm_rotation.json`.

## Rules that apply to every row

- BAU: a real, tidy, lived-in upper-middle-class Indian home with **no festive decor** (no diya, rangoli, marigold or lights).
  The same persona, room and light are kept through the whole reel.
- All 5 product slots are shown, as the exact listed product. Nothing is skipped, deduplicated or substituted; if a slot
  can't be shown, the worker stops and reports it.
- Movements are natural and brief: no spins, no unboxing, no invented features or claims. Makeup has no skin lightening, no
  eyeball contact, and no coverage, wear-time or SPF claims.
- Use the TrueFan / Omni MCP only, with folder `Flipkart_Fashion-Rhythm_AI_Profiles` on every call. On a rate limit, wait once and
  check once; never loop-poll. Never delete files (move them to `work/junk`). No Drive uploads or sheet edits by workers.
- Music comes only from `assets/music/rhythm_bgm_approved`, in round-robin order.

## Day 5 fixes (19-20 Nov)

The Day 5 review found extra limbs, twisted legs, feet hanging in the air, people sitting on air, lace tying on shoes without
laces, wrong or duplicate products, clothes appearing mid-clip, and people out of scale with the room. The fixes:

- **General rules** (`approaches.py` `GENERAL`, pasted into every non-Makeup worker prompt):
  - **Same person, same height:** same build and proportions, camera at the same height.
  - **Every plate an edit of the first:** every plate of a reel is an edit of its first full-body plate.
  - **Background in proportion:** door frame, sofa, bed and floor tiles keep real-world scale against the person.
  - **Outfit lock:** the outfit never appears, disappears or changes.
  - **Seated shots:** a real seat must be in the plate and under the person.
  - **Actions match the product:** see "Allowed actions" below.
  - **One product per slot:** a slot never shows another slot's product.
  - **Body physics:** two arms and two legs, feet planted with weight, no twists.
- **Allowed actions per slot (footwear):** `pipeline.py` `footwear_actions()` reads each slot's listing (Closure, title) and
  adds a line to the prompt:
  - **lace-ups:** may tie the laces;
  - **velcro, buckle or zip:** may fasten it;
  - **slip-ons, flip-flops, slides, clogs, mules:** never tie, buckle or adjust anything;
  - **unknown:** shown worn only.
- **Duplicate products:** `prompt` refuses a row that has the same PID in two slots.
- **Footwear approaches:**
  - **A-J:** footwear rows accept A-J; every other family still accepts only A-E.

    | Letter | Approach | What it shows |
    |---|---|---|
    | F | `pov_look_down` | the wearer looking down at their own feet |
    | G | `step_up` | stepping up onto a step or threshold |
    | H | `full_look_to_feet` | the full outfit, then a tilt down to the shoes |
    | I | `tap_and_settle` | a toe tap, then the foot settles flat |
    | J | `pair_on_floor_step_in` | the pair on the floor, then stepping in |

  - **Safer B and D:** B is two straight steps with no turning or crossing feet. D turns in small steps in place, never
    pivoting on the ankle.
  - **Anatomy rule:** joints stay within their natural range, feet never float, and there is exactly one shoe on each foot.
  - **Same background:** every shot stays in the reel's room and on its floor.
- **Redo list:** `02_BAU_DATA/day5_redo_list.csv` has 15 rows with the slots to regenerate, about 104 s at 360p. Their work
  folders are not on this machine.

## Day 6 fixes (21 Nov) - every vertical

Problems found in the 20 Day 6 reels, and the fix now in the pipeline. Rows are sheet rows.

| Problem (rows) | Fix |
|---|---|
| One frame dropped or held at every product cut (all reels) | **Cause:** a silent audio track delayed each segment by 0.021 s. **Fix:** music reels now assemble video-only segments (`assemble.py`), so cuts are frame-exact. |
| A cut between two products with the same framing looks like a jump or morph (498, 500) | Every product ends on a close push-in and the next starts wider; the reel planner avoids the same framing on both sides of a cut. |
| Products hanging in the air (1177, 1181, 1183) | **Rule and check:** every beat names the hand or surface holding the product. A two-hand action happens only after the product is set down. |
| Packs torn, boxes opening by themselves, unboxing (1178, 1190, 1195) | Forbidden in the rule book and rejected by the check. |
| Product turning inside the grip, hand flipping (1187) | Turned only with the wrist, so hand and product turn together (checked). |
| Third hand (1185, 1243) | Exactly two hands. Every product's first image is an edit of the room master, never of another product's image. |
| Small parts duplicated or changed: teats, lids, straps (1185, 1198-1201) | Parts are listed with counts in the product lock and are never taken off unless that is the real-use step. |
| Furniture appearing mid-shot (1190, 1195, 1200) | The surface is in the room bible and visible from the first frame. |
| Small product morphing in a full-body shot (1225) | Handheld products under 30 cm start waist-up or closer; fingers never cover the cap or label. |
| Roll-on spraying mist; wrong body area (1228) | A roll-on rolls and a spray sprays (checked); deodorant goes on the underarm. |
| Hand swapped (1240) | One continuous take, plus a same-hand check. |
| Size mismatch or extra copies (1246, 1225, 1228, 1177) | Exactly one copy anywhere in the frame, plus the life-size lock. |
| Laces mimed on an already-laced shoe (486) | Only on lace-ups: tying starts untied with loose ends and ends with a visible bow (checked). |
| Reel too short, a product missing its detail (1183) | `finish` requires 5 takes of 4 s each. |

These rules are in the planner's rule book and checks, the shot physics text, the old-style prompts (`approaches.GENERAL`) and
the Makeup prompts.

**Also new (21 Nov):**
- **Face:** every reel shows the persona's whole face at least once. The reel planner refuses a reel without it; the rule book
  asks for one face-showing variant per product.
- **Repeated movements:** a movement type (turn, heel lift, slide ...) may appear in at most 2 products of a reel.
- **Approach rotation:** `setapproach AUTO <rows>` gives each vertical A, B, C, D, E (A-J for footwear) in sheet order.
  `prompt` refuses a letter already used by one of the previous 4 rows of the same vertical, so at least 5 different
  approaches come before one repeats.
- **`finish` refuses:**
  - a cut inside any product, in every vertical including Makeup. The check is instant: a real cut scores 0.2-0.9, while a
    continuous take stays under 0.05; the threshold is 0.15.
  - a missing product sheet: the spec sheet for every product, and outside Makeup the 6-angle reference sheet too.
- **Every product has its own scene** (room and surface, from its plan) and its own product sheet.

## Holding hand, dispensing and home decor (22 Nov)

- **The holding hand is always visible.** Whenever a hand holds, pinches or supports a product, that hand, wrist and forearm
  are in frame in every frame. Code: the first frame must name the holding hand, and a held product never starts or ends at
  `macro` (it would crop the hand out). No arm enters from the frame edge without a visible shoulder or body.
- **Dispensing.** A pump, squeeze bottle or tube releasing cream, lotion, gel, soap, shampoo or oil: the other hand is open,
  palm up, 5-8 cm directly below the nozzle, in frame. One press gives one small dollop that lands in that palm. Code: a
  dispensing beat without "palm" and "below" is rejected.
- **Home decor** (`approaches.py` and a family block added to the OpenAI request). The old instructions left depth and size
  open; the three reviewed wall-decor reels showed stickers bigger than the person, her reaching to a far wall from mid-room, arms
  coming from the frame edge with no body, a sticker sheet fading in, and the room changing between products.
  - The item is already in place and life-size. Wall decals are never peeled, applied or faded in, and sheets are never held up.
  - **`scene.mount`:** the item's real width and height, its height from the floor, its gap to the furniture, and how far the
    person stands from it. A wall item uses surface kind `wall` (the room's back wall).
  - **Depth:** the person stands 30-60 cm from the item, parallel to it, body turned about 45 degrees, so shoulder, arm and hand
    form one line. The camera is fixed 2-2.5 m from the wall.
  - **Limbs:** the shot starts with the upper body in frame, at most one hand touches the item, the other arm hangs.
  - **Approaches A-E** are rewritten with these exact positions; only items under 30 cm are ever picked up.
  - Code checks `scene.mount` numbers, the 20-70 cm distance, the `wall` surface and the starting framing.

## Surfaces: no table appears out of nowhere (21 Nov)

Day 6 reels had tables fading in mid-shot and packs hanging in the air. The OpenAI planner now plans the surface:
- **`scene.surface`** in every new plan: the one surface the product rests on or is set down on. It has a kind (table,
  counter, dresser, bed, sofa, shelf, stool, desk, cabinet_top, floor, lap, or none_held), a real size, an exact place in
  the room and what is already on it.
- **Checked in code:** `start_state` must name the surface, and it must be in the start framing (a surface above the floor
  needs waist_up, knee_up, full_body, hands_close or product_close; sofa, bed and stool also allow knee_down). Any other table,
  shelf, tray, stool, counter or bench that appears later in the shot is rejected.
- **In the room from the first image:** the reel planner puts every product's surface into the room's background bible. If
  the room template has no such furniture, it adds it. The room master image is generated from the bible, and every later image
  is an edit of it, so the surface exists in every frame and nothing is added.
- **In the prompts:** the start still and the clip prompt both name the surface ("in the frame from the first frame to the
  last; nothing appears or changes").
- Plans made before 21 Nov have no surface: the planner derives it from the anchor and shows a warning. New plans need
  `schema_version` 2.

## Footwear: legs never rotate (21 Nov)

QC: "in shoes the main major issue is the legs rotating". The video model rotates legs whenever a plan says turn, pivot, angle
outward or walk-and-turn. The fix removes rotation completely:
- **Allowed movements only:** toes up (heel down), heel up (toes down), a weight shift, a straight slide of at most 10 cm,
  ONE straight step of at most 25 cm, a toe tap, or tying laces while seated on a lace-up.
- **Checked in code** (`product_planner.validate_shot`): a footwear plan is rejected if a leg or foot beat says turn, rotate,
  pivot, twist, angle, outward, inward, sideways, cross, swing, kick or sweep, gives degrees, or moves more than 10 cm
  (25 cm for a step); its `movement_type` must be one of the allowed words; and it must start with both knees in frame.
- **Approaches** (`approaches.py`): footwear A-J are rewritten without any turning. D is now a weight shift, B is one straight
  step, and J is the pair worn with a toe lift.
- **Prompts:** every footwear image and clip prompt says every foot points the way its shin and knee point in every frame.
- **Old saved footwear plans** that use turns now fail the check and need re-planning (OpenAI, after the user's yes).

## Makeup application rules (17-20 Nov, `makeup_approaches.py`)

### Rules for every applied product
- **Start frame:** the applicator is already touching the spot where the first stroke begins.
- **Expression:** she looks happy throughout.
- **One take:** no jump cuts.
- **Same hand:** the hand that applies the product also shows it to camera.
- **Ending:** she looks straight into the camera with a smile.

### Lips
1. **Start frame:** head-to-chest framing, with the wand on the left corner of the bare lower lip.
2. **Strokes:** four separate strokes, each covering half of one lip and stopping at the centre, with the wand lifting off
   in between.
3. **Lip press:** a visible lip press after the strokes.
4. **Timing:** a 6-second clip.

### Kajal
- **Grip:** held like a pen, always. The same pen grip applies to eyeliner, eyebrow pencil and lip liner.
- **Start frame:** made from the panel reference `assets/makeup_refs/KJL_panel_ref.jpg` (pinned on Omni as
  `asset_129bb6f2c47944c69ddcef41ea921a23`), then the row's persona, then the listing photo.
- **Look:** she is dressed up, with the other eye already lined.
- **Tested method (row with Sunita):**
  1. **Strokes:** an edit of the uncut 3-second reference clip (`KJL_motion_ref_clean3s.mp4`) with the persona and product
     swapped in.
  2. **Ending:** a 2-second continuation where she shows the pencil to camera with the same hand.

### Foundation
- **Applicator:** a damp beauty blender, bounced, never wiped.
- **One side only:** applied to one side of the face, shown in the product's own shade so the change is visible.
- **Ending:** she shows the bottle to camera.

### Primer and fixer
- **Two kinds under one code:** `PRM` covers both. A title with "fixer", "setting spray" or "spray" is a fixer.
- **Fixer:**
  1. She shows off the can, then gives one test pump into the air.
  2. She turns to side view and the can is held still for 3 pumps, with her eyes closed and the mist landing on her whole face.
  3. She turns back and shows the can, smiling.
- **Action file:** the example is `02_BAU_DATA/example_specs/makeup_fixer_test/A1_fixer_apply_row1045.json`.
- **Product spec:** the spec block from `product_spec.py --pid` is pasted into the prompt.

### Reference files
- **Product types:** `02_BAU_DATA/makeup_product_types.csv` lists all 32 types, with 21 applied and 11 used.
- **Reference frames and clips:** stored in `assets/makeup_refs/`.

## Known gaps

- The 12 rows with empty product links listed above.
- `batch_100.json` is not shipped; Step 1 rebuilds it on each machine.
- `.env` (Omni token) and the rclone config are machine-specific and not in the zip.
- No video has been generated with the new approaches yet. They are tested at prompt level only.
- The OpenAI planner (21 Nov) is tested offline only, with synthetic test plans. No real OpenAI request has been sent yet,
  and no reel has been made with the planned flow.
- Makeup application tests needed 5-6 s for the applied product, but the reel rule is still 4 s per product. This is not
  decided yet.
- The team copy (`Flipkart_Reel_Pipeline_20Nov_day5fixed.zip`) does not have the planner.
- Row 593 (Nisha, the first planned row): its 5 OpenAI plans are saved, but none of their variants shows the face (all are
  knee-down). It needs one slot re-planned (1 OpenAI request, after the user's yes) before it can be made.

## Scale and lids (22 Nov)

- **Scale lock:** `shot_builder.scale_text` turns the plan's real `dimensions_cm` into numbers against the person (longest side as % of height, in hand-lengths, head heights and foot lengths) and puts them in every product lock, so every start still and clip carries them.
- **Lid / cap state:** new plan field `part_states` (every removable lid, cap, cover: start and end state, and the hand action if it changes). A part needed open for use is already open in the first frame; a lid never opens, closes or moves by itself. Rules 25 and 26 in `product_planner.py`; a state change without a hand action is an error, a missing field is a warning.
- **Old plans** have no `part_states`: prompts then say "every lid keeps the state of the start still"; re-plan (OpenAI, after the user's yes) to get the per-part states.

## Detailed actions (22 Nov)
Planner rule 27: every beat is written like a director's note (start position, path, direction, cm, speed, fingers/grip, wrist/elbow, product movement, contact and pressure, end position); `movement` asks for 25+ words and `action_summary` for 2-3 sentences. A beat under 20 words gives a warning (old plans stay valid; re-plan after the user's yes to get the richer text).

## Footwear display approaches K-V (22 Nov)
Footwear rows now accept A-V (22 letters, rotation covers all). **K-V show the shoes NOT worn** (held in a hand or on a table/turntable); the person's legs stay still, camera waist_up or closer, face in frame. K hold_turn_30 (wrist turns shoe 30 left/right), L platform_turn (pair on a 30 cm turntable, 30 left/right), M pair_two_hands, N shoe_on_palm, O presenting_palm, P lift_and_turn_one, Q toe_tilt, R bring_forward, S heel_to_camera, T shelf_point, U sole_tilt, V platform_turn_one.
- Planner: `FOOTWEAR_DISPLAY_RULES` are added to the OpenAI request only for these letters; `validate` switches to `footwear_display` (worn-footwear and leg checks off; new checks: no wearing/put-on/take-off, no flip/spin/throw/hand swap, legs never move, every turn at most 30 degrees, start framing waist_up or closer, allowed movement_type words).
- Reel planner: same movement in all 5 products is allowed for these letters (by design); `shot_builder` uses `footwear_display` physics (heel/toe-box grip, wrist-only turn, turntable in frame from the first frame, only it turns).
- New letters need new plans (plan files are per approach letter): `plan <row> --confirmed` after the user's yes.

## Open box spec and looked-up dimensions (22 Nov)
- **Open state:** plan field `open_state_spec` (rule 28). A shot that opens a lidded box/product or takes it out of a box must set `used: true` and describe the open state (contents, parts and counts, how opened, where the lid goes). `shot_builder` adds an OPEN-STATE SPEC to the product lock and a separate open-state reference sheet (`specs/slot_N/open_sheet.png`, made by `run_row.py`, required by `finish`); it is an extra reference on the product's start still. Tearing or unsealing packaging stays forbidden.
- **Dimensions from OpenAI:** rule 26 makes the planner look up real dimensions with the web search tool (listing first), with `parts_cm` and `dimensions_source`; "typical" sizes give a warning. These numbers feed the scale lock.
- Old plans lack both fields; re-plan after the user's yes.

## Limbs every second, nothing moves alone, product-photo shots (22 Nov)
- **Limbs per beat (planner rule 29, `schema_version` 3):** inside the action every beat is at most 1.0 s and fills `limbs` for left hand+arm, right hand+arm, left leg+foot, right leg+foot, head/gaze and torso, plus `arms_in_frame`, `hands_in_frame`, `legs_in_frame` (max 2 each). Missing limbs, a beat over 1.0 s, or a count over 2 is an error for version-3 plans (a warning for older plans). `shot_builder.beats_text` pastes the limbs into the clip timeline.
- **Nothing moves on its own (rule 30):** an object moves only because a named limb moves it. A beat where no limb moves but something sways, flutters, rotates, slides or floats is rejected. The turntable approaches L and V are now turned by her hand (two fingertips on the rim, 30 degrees left then right); the prompt says the platform moves only while her hand pushes it.
- **Product-photo shots (home_decor, home_furnishing, kitchen, household_utility):** one of the 3 variants is `no_person: true`: the cleaned ORIGINAL LISTING PHOTO is the first frame (`plate_cleanup` says what to remove and how to extend to 9:16), no person, hand or arm, only the camera pushes in (photo_wide/photo_mid/photo_close), `ambient` is always `none`. The reel planner uses at most 3 such shots (decor prefers them) and always keeps at least one avatar shot with the face. `shot_builder.photo_slot_files` builds their prompts from the listing photo, not the room master.
- Existing plans have none of these fields; re-plan after the user's yes.

## Nothing appears out of nowhere, lid lock (22 Nov)
- **Planner rule 31 + check:** every table, shelf, stool, tray, box, prop or product used at any point is already in the first frame (named in `start_state` or `scene`). A shot that names one later (end_state, contact, support, product_state) that the first frame lacks is rejected ("appears out of nowhere"). The `CONTINUITY` text in every clip prompt says the same.
- **Lid lock:** a lid/cap/cover changing state is rejected unless `part_states` declares it and a named hand does it; plans without `part_states` get a hard "never opens, closes or turns" line in every prompt.
- `prompt`/`shots` re-validate every saved plan, so these checks also apply to plans saved earlier.

## Generation hardening (22 Nov) - why a paid run no longer wastes money
Found in the first real runs (rows 508, 510, 1181) and fixed in `run_row.py` v2 / `pipeline.py` / `shot_builder.py`:
- **Checks never block a paid reel:** `FK_LAX=1` (default in `run_row.py`) turns every `finish` check and plan finding into a printed/logged warning; the reel is always finished and filed. Without it, a strict check after paid generation left a finished set of clips with no reel.
- **No double sends:** one lock per row; ONE shared 2-second request clock for all rows running in parallel; a failed request is never re-sent by the script (only a rate-limit rejection waits once); a timeout is never re-sent (Omni may have accepted it); a clip's `generation_id` is saved the moment it is queued, so a resume polls it instead of paying again.
- **Stops cleanly:** any failure writes `row_NNN/STOPPED.json` (what failed + ready fallbacks) and keeps everything made so far. Fallbacks need the user's yes: `--sheet-alt=<slot>:<k>` (another listing photo), `--sheet-pro=<slot>` (Nano Banana Pro), `--sheet-photo=<slot>` (listing photo as reference, free), `--local-photo=<slot>` (photo-only shots built locally, free).
- **Free pre-flight:** `run_row.py <row> --dry` walks the whole run offline (every reference resolves, prompt sizes, placeholders) and prints the exact number of images/clips it would send (resume-aware). Use it to quote the exact list before asking for the user's yes. `run_row.py status` shows every row in one line; `run_row.py launch <rows> --confirmed` starts rows in parallel, detached, Mac kept awake.
- **Plan changes can't leak:** every asset stores a hash of the prompt it was made from; a changed plan never silently reuses an old asset. All `shots/` files are read once at the start.
- **Clips:** downloads are verified and retried (free); each clip is trimmed/padded to exactly 4.000 s (original kept as `.orig.mp4`).
- **Prompts:** listing legal text (importer/packer/manufacturer addresses, model numbers) is removed from the product spec in prompts; pronouns are rewritten to the persona's gender; the open-state sheet is now named (IMAGE_REF_3 / IMAGE_REF_1) in the still prompts; prompts are checked against Omni's 20,000-character limit before sending (current ones are 12-14k).

## Video-generation errors: what causes them and the permanent fixes (22 Nov)
Clips are first/last-frame interpolations: the model morphs from picture 1 to picture 2, so ANYTHING that differs between them (a limb, a prop, a sleeve, the light, the scale) cross-fades or melts, and anything wrong in picture 1 is carried through the whole clip.
- **Extra limbs (permanent, layered):** (1) *Prevent:* one acting limb; the other arm hangs STRAIGHT DOWN, identical in the first and last frame; no crossing limbs; small net movement (planner rules 32-33, `PHYSICS`). (2) *Detect before paying:* `limbguard.py` (Apple Vision hand/face/body count, free, local) runs on every person still; more than 2 hands / 1 face / 1 body stops the row BEFORE the clip is paid for, with ready options `--accept-limbs=<name>`, `--regen=<name>` (1 new request), `--candidates=2` (best-of-N renders, each billed). Product-photo stills must show no person. (3) *Report:* 5 frames of every finished clip are counted; `limbs_report.json` / `run_row.py status` show limb flags (never blocks). Validated on 22 Nov: it caught 3 hands in row 510 slot 1 (a real extra arm).
- **Frame-to-frame continuity:** optional pixel-locked end frame (`FK_END_MODE=composite`, `continuity.py`): the edit model changes only the action with the camera NOT moving, then the changed region (exposure-matched) is pasted onto the start frame and the push-in is a crop of the same pixels. Everything outside the action is identical in both frames. Not the default until tested on a real pair (1 image + 1 clip).
- **Nothing appears / slides / floats:** planner rule 31 + checks (an object not in the first frame, a table or object that "slides/rolls/is carried in", anything floating/hovering) + the `CONTINUITY` text in every clip prompt.
- **Scale:** the product's size is also given as a share of the PICTURE WIDTH (`onscreen_text`), next to the cm / % of height / hand-lengths. Wall decals are only the printed artwork (no white backing sheet, never in front of the person).
- **Product-photo shots are preferred for decor** (no person = no extra limb, no scale error); the photo-shot validator no longer rejects them for artwork words (girl/face) or camera "no roll/tilt" wording; a photo-only shot needs no reference sheet.
- **Prompt wording that causes errors:** banned-object lists were replaced by a positive style line (naming "diya, rangoli" primes the model to draw them); left/right always mean the person's own; steady tripod camera, constant light, slow even pace, closed mouth.
- **Clutter:** one cloth prop and one container prop per room (4 muslin cloths on one table cannot be redrawn consistently).
- **Blocked products:** sensitive products (breast pump, intimate, medicines, anything used on a child) are shown only as an object held away from the body, never with a baby (rule 34, `BABY_RULES`).

## First frame / last frame, touch close-ups for wall decor (22 Nov, after rows 1181 and 510)
What went wrong in those reels: the cap of the nibbler (1181 slot 3) came off and a second cover faded in, because the plan's part_states told every prompt "cap closed -> off"; the first and last pictures were two separate generations, so every difference between them morphed or appeared out of nowhere; 510 slot 1 had a third arm and the decal drawn as a giant white board.
Fixed (home families: home_decor, home_furnishing, kitchen, household_utility, baby_care):
- **Nothing changes state inside a clip:** parts keep their FIRST-frame state (a part that must be open is open from the first frame); no set down / pick up / lift off / open / pour (rules 25, 28, 33 + `STATE_CHANGE` check). `part_states` changes and `open_state_spec` are ignored for these families.
- **Last frame made from the first frame:** default `locked` mode (`FK_END_MODE`): the last frame is a local crop of the first frame (free, cannot morph). When the OpenAI plan has a `last_frame` with ONE change (rule 36: one limb at most 10 cm, or the product turned at most 20 degrees, plus `identical`, `limbs_end`, `push_in.zoom` 1.2-1.6, `edit_prompt`), the change is made as an edit of the first frame, pasted onto the first frame pixel for pixel (`continuity.composite_zoom`) and cropped. The edit is hand-counted (`limbguard`) before its clip is paid for.
- **Person visible from the first frame:** start framing full_body / knee_up / waist_up / shoulders_up / wall_close, never hands_close (no arms from nowhere).
- **Built-in safe shots** (`product_planner.safe_shot`) when no OpenAI variant passes: one out-and-back movement of one limb, everything else still (held: wrist turn / tilt / still; surface: hand toward and back; wall decor: 5 touch close-ups).
- **Wall decor = touch close-up (user 22-Nov):** framing `wall_close` (camera 1.0 m from the wall, item in the right two-thirds, avatar at the left edge in profile BESIDE it, never in front, never pointing); she feels it in a different way per product: palm glide, fingertip trace, edge feel, back of the fingers, press. Decor approaches A-E were rewritten to these touches. Product-photo shots (no person) are still preferred for up to 3 products.
- **Cost:** no end-still generation in locked mode - a home reel is 11-12 images + 5 clips (was 16-19 + 5).
- **Redo one slot:** `run_row.py <row> --confirmed --only=<slot> --redo=<slot>` (old pictures/clip moved aside, never deleted). `--dry --fresh` counts a full run.
- Old OpenAI plans have no `last_frame`; re-plan (after the user's yes) to get planned last frames - until then safe shots and locked crops are used.
- **Supports in the first picture (user 22-Nov):** every start picture and clip prompt lists the shot's surface, anchor furniture, props and any table/chair/stool/stand the beats use as "SUPPORTS ALREADY IN THIS FIRST PICTURE"; nothing is added later. With the locked last frame (a crop of the first) nothing can appear between the frames either.
- **Locked last frame everywhere (22-Nov):** product-photo shots and every family now use the crop-of-the-first-frame last frame (only shots whose action travels - step, slide, walk, weight shift - keep an edited end frame). A home reel is now 8-12 images + 5 clips. `FK_END_MODE=push` brings back the old edited end frames.
- Tested 22-Nov on row 1181 slot 3 and row 510 slot 1 (`--only/--redo`): both reels reassembled.
- **The camera moves, not the person (row 510 slot 5, 22-Nov):** in the old clip she walked toward the camera instead of a push-in (an old separately generated last frame). Every clip prompt now says she stays on the same floor spot, feet planted, only the camera comes closer (rule 37), and a plan beat that steps, walks or comes closer is rejected outside footwear.
- **Baby care review (22-Nov):** "diapers too big" -> baby sizes in `BABY_RULES` (pack 30-45 cm shown closed, folded diaper palm-sized ...), a size check (a diaper item over 60 cm or a small baby product over 70 cm is rejected), and every product lock now says the listing photo and reference sheet are close-ups whose size must never be copied. "Lid opens on its own" -> no state change inside a clip + locked last frame (earlier 22-Nov fixes). "Things grew on their own" -> every clip prompt says everything grows together with the push-in and nothing changes size relative to the hand; the locked last frame is a uniform crop, so the two frames agree.
- **Finger and camera detail (user 22-Nov):** every beat now has `fingers` for both hands, finger by finger (rule 38, `schema_version` 5 = required, older plans = warning), pasted into the clip timeline; every clip prompt has a CAMERA PLAN (locked until the action ends, then one straight constant-speed dolly-in to the last frame; no pan, tilt, roll, zoom-lens, focus pull or shake), plus the plan's own `camera_plan` when it has one. The built-in safe shots carry both.
- **Clip prompt size:** the clip prompt only names the person and room (both are in the two frames) instead of repeating the full room list and person lock, so it stays near 13-15k of Omni's 20k limit.
- **Everything, every beat (user 22-Nov, rule 39, `schema_version` 6):** each beat has an `everything` checklist of 21 parts - head, eyes, mouth, hair, shoulders, torso, hips, both arms, both hands' fingers, both legs/feet, clothing, product, product parts, props, surface, background, light, camera - each "still", "out of frame" or the exact movement. The clip timeline prints every moving part in full and names every still part ("COMPLETELY STILL: ..."); anything not described as moving must not move. Required for new plans, a warning for older ones; the built-in safe shots fill all 21.
- **Listing photos are close-ups (user 22-Nov):** every OpenAI request now says so and asks the planner to web-search the exact product's real dimensions, weight, pack contents, parts, how people hold and use it, and real-life photos (listing, brand site, other retailers, reviews), naming the sources. The generation prompts say the same (size only from the numbers, against her hand).

## Serper key (22 Nov)
`SERPER_API_KEY` (Google search through serper.dev) is in this folder's `.env` next to the OpenAI key, with the same rules: never printed, shown, copied elsewhere or put in a zip; used only inside `plan <row> --confirmed` after the user's yes; a failed search is never retried (the plan is then made with OpenAI's own web search). For every product that is not searched yet, 2 Google searches are made with ONLY the product title/brand ("<title> dimensions size cm", "<brand> <title> how to use"); the answer box, knowledge graph and top 6 results of each are added to that product's OpenAI request, and cached in `02_BAU_DATA/product_plans/serper/<PID>.json` so a product is never searched twice. The dry run (`plan <row>`) shows how many searches would be made. One-off check: `python3 product_planner.py serper-test "<query>"` (1 search).

- **22-Nov (user's explicit request):** `ryhtm_pipeline.zip` now INCLUDES the pipeline's root `.env` (OpenAI + Serper keys). Anyone who gets that zip can use both keys - share it only with people who should. `beauty_pipeline/.env` (Omni token) is still left out.
- **Size stays the same across the clip (22-Nov):** every product lock has a SIZE LOCK ACROSS THE CLIP line (the product keeps its size relative to her hand, body and room in every frame; only the push-in enlarges everything together), next to the clip-wide "nothing grows or shrinks" line, and the locked last frame is a uniform crop. `sizecheck.py` (OpenCV, free) measures every finished clip: the product's scale vs the scene's scale (or the planned push-in when the background has too few features); more than 12 % difference is written to `size_report.json` and the row log (report only). Tested on row 1181: the redone slot 3 grows exactly with the push-in (1.35 vs 1.35).

## NO AUTOMATIC CHECKS OR QC IN GENERATION (user 22-Nov, final)
`run_row.py` and `finish` run no checks: the hand counter on pictures (limb guard), the clip hand and size reports, best-of-N, and the finish checks (planned takes, cuts, sheets, duration) are switched off. Sections above that describe them are history. Still in place (they are how the video is made, not checks): the prompt rules, the locked last frame (a crop of the first frame), and the planner's rules that pick a usable action. `limbguard.py` is still used only to centre the push-in.
- **Hero - show what it is FOR (user 22-Nov, rule 40, `schema_version` 7):** "it is a nibbler - what will I do with the front view?". Every plan has `hero` (main_thing, ready_state, must_see, never). The product is in its ready / in-use state from the first frame (nibbler: cap off beside it, sac filled with fruit visible through the mesh), nothing is prepared inside the clip, the main thing faces the camera and the push-in ends on it; a plain front view of an unused product is never the shot. The product lock carries it into every picture and clip prompt; the built-in safe shots use it. Old plans have no hero and must be re-planned (after the user's yes).
- **Parallel planning (user 22-Nov):** `plan --confirmed` sends every product's Serper searches and OpenAI request AT THE SAME TIME (one thread per product), so a row plans in one request's time; failures are still never retried.
- **Parallel generation (user 22-Nov: minimum time, same output):** inside a row, all product sheets and the first room picture are made at the same time, then every product's first picture, last frame and clip at the same time (`run_row.py` `par()`); a second room waits for the first. Every send still waits its turn on the shared 2-second clock, and the first failure stops the row.
- **23-Nov:** the shared gap between sends is 1 second (was 2). `run_batch.py` plans ahead: every row is planned at once in the background and a row generates as soon as its plan is ready (`--parallel N` generation places); `--plan-only` plans in advance (overnight), `--generate-only` generates rows planned earlier. `PROMPT_FOR_EDITOR.md` is the prompt a teammate pastes into Claude Code to run rows.
- **Same avatar in every product (row 1183, 23-Nov):** every first picture passes the persona sheet AND says the same face, skin tone on face/arms/hands, build, height, hair and jewellery as the persona sheet and room master; waist-up and wider shots keep her whole head and face in the frame. (The clip itself can only take its first and last frame, so identity is fixed in the first picture.)
- **Not stationary (user 23-Nov, rule 41):** the camera glides in smoothly for the whole 4 s (no locked start); the person is alive (breathing, blinks, eyes between product and lens, small head movement, softly changing smile) - only objects stay still; the built-in actions are bigger (30-degree turn each way, 25-degree tilt, 10 cm lift toward the camera, 10-12 cm palm/fingertip glide) and the "hold and blink" action is gone; an OpenAI action that is tiny/slight/subtle or under 5 cm and 15 degrees is not used. Built-in actions are rebuilt from the current code every time.
- **OpenAI wait (23-Nov):** a planning request now waits up to 25 minutes for OpenAI's answer (was 10); two requests with web search ran past 10 minutes and were lost.
- **Real, not a studio (user 23-Nov, rule 42):** the push-in is now 1.15-1.3x (was up to 1.6-2x) and the clip prompt says it ends with the product large AND the room still visible. The no-person shot is no longer the white listing photo: it is an edit of the room master WITHOUT the person, with the product in its real place (decal on the wall, lotion on the dresser), the room clearly visible around it, then the same gentle push-in.
- **Alive and engaged (user 23-Nov):** she looks mostly at the product and glances at the camera once (never a fixed stare), shifts her weight, moves naturally; warm lived-in daylight style; the camera move gives natural depth (background shifts slightly behind her). Objects still never move by themselves.
- **Closed unless used (user 23-Nov):** a cream/lotion/pump product is CLOSED (cap shut, pump locked) and NO cream is on any hand unless the shot's action is the press; `shot_builder.closed_unless_used` strips every 'dollop on her hand / cap open / pump unlocked' text from the plan, the ready state, prerequisites, part states, push-in target and beats for every other shot, and the dispensing rule text is only sent with a shot that presses. BABY_RULES no longer asks for a dollop on the hand.
- **Zoom always toward the product (user 23-Nov):** every first picture is composed with the product at a known place (the centre; beside-the-wall shots: 60% across), and the locked last frame is cropped around the product - found by matching its listing photo / reference sheet in the picture (OpenCV SIFT), else its planned place. Never toward her face or hands.
- **Zoom made IN the video (user 23-Nov, default `FK_END_MODE=first`):** each clip now gets ONLY its first picture; the video model films a real camera dolly-in toward the product (about 25% closer, natural depth - the product grows a little faster than the wall), never a crop or digital zoom. No end picture is generated or cropped. `FK_END_MODE=locked` brings back the cropped last frame.
- **No post-production zoom (user 23-Nov, rule 43):** the only zoom is the camera move filmed in the clip; OpenAI plans it per shot in `camera_plan` (start, the dolly toward the product in cm and speed, end about 15-30% closer with the room visible) and it is the clip prompt's CAMERA instruction; assembly forces digital zoom 1.0 on every segment.
- **Team review 23-Nov (floating products, wrong use, product changing, oversized):** the no-change / closed-unless-used / hero rules now also cover grooming, fragrance and fashion wearables (`LOCK_FAMILIES`). Planner rule 44 + prompt text: a held product is GRIPPED between chest and waist height, never over the face, never balanced on a palm or hanging under a hand, nothing (product, cap, dropper, shoe) floats; tools are used where they are used (brush in the hair, comb in the beard, perfume at the wrist); the product is AS SOLD with one of each part (no loose dropper or spare cap); size against her hand and forearm, plus its share of the picture height. A pair of shoes held up is gripped by ONE hand at both heel straps. **Every clip now gets the product's reference sheet, its listing photo and the persona picture as reference images** next to the first frame (Omni allows up to 7), with an "identical in every frame" instruction, so the product and the avatar cannot change between frames; the long listing spec is dropped from the clip prompt (the images carry it), and repeated per-beat body text is shortened.

## EVERY RULE COVERS EVERY CATEGORY (user 23-Nov)
`LOCK_FAMILIES` and `PHOTO_FAMILIES` now hold all 11 families, so these apply to every category: nothing changes state or appears inside a clip; closed unless used (rule 45, general); the hero / ready state; the person's body in frame from the first frame (footwear may start knee-down); actions big enough not to look stationary (footwear excepted, its moves are small by rule); the planned last frame; the no-person shot = the product in the room; built-in safe shots, now also for WORN products (footwear: toe up / heel up / weight shift, knee-down; clothing and wearables: palm smoothing the fabric, fingertips feeling an edge, a 15-degree shoulder turn). Everything in the prompts (held right, as sold, size, nothing floats or appears, alive, camera toward the product, supports, reference images in every clip) was already general. Still category-specific by nature: footwear legs/laces/display rules, wall-decor touch close-ups, baby-care "no baby in frame", decor preferring photo shots.
- **No-person room shot: HOME only (user 23-Nov):** `PHOTO_FAMILIES` = home_decor, home_furnishing, kitchen, household_utility.
- **Size checked against Google in code (option 4, 23-Nov):** `product_planner.serper_size(pid)` reads the saved Serper results and finds the size most sources agree on (packaging, shipping-box and rolled-tube sizes are ignored; mm and inches converted). When at least 2 sources agree and OpenAI's size differs by more than 30 %, Google's size is used for every scale line in the prompts (noted in the plan warnings); otherwise the match is noted. Free - it uses the cached searches.
- **Reference sheet shows the real size (option 3, 23-Nov):** new product sheets put a plain 30 cm ruler with cm marks beside the product in panel 6, at the same scale, so the image and video models SEE the real size; every prompt says the ruler is only a size guide and never appears in the scene or the video. Sheets made before keep no ruler.
- **Faster planning (user 23-Nov, options 1 + 3):** OpenAI's own web search is OFF by default (`OPENAI_WEB_TOOL=web_search` turns it back on); to keep the plans as well informed, Serper now makes up to 4 Google searches per product (size, how to use, review/in-hand size, box contents/parts; 10 results each, top 8 sent), and only the searches a product has not had yet are made. `run_batch.py` makes each row's 5 product sheets (`run_row.py <row> --confirmed --sheets-only`, sized from the Google results) AT THE SAME TIME as OpenAI plans the row, so generation starts with the sheets ready. (In home rows a product that becomes a no-person shot may get a sheet it does not use.)
- **Mirror-selfie phone (user 23-Nov, every category):** in a mirror-selfie shot the camera IS the mirror - the phone's back (lenses) faces the camera, its screen faces her, the screen is never shown to the camera; in the approach constraints, the prompts' PHYSICS text and planner rule 46.
- **Faster OpenAI plans (user 23-Nov, options 1+2):** OpenAI writes 2 person variants (home: + 1 product-in-room variant) instead of 3, and in each beat only the parts that MOVE or TOUCH something (fingers only for a hand that holds/touches/moves); `product_planner.fill_routine` fills every part it left out as still, so every prompt still gets the full 21-part checklist, both hands' fingers and all six limbs. Reasoning effort is 'low' (`OPENAI_REASONING=medium` or `high` for more care).
- **Serper REMOVED (user 23-Nov):** no Serper calls are made and its key is gone from `.env`; OpenAI's own web search (`OPENAI_WEB_TOOL`, on by default) finds the real size, use and parts. The ruler on product sheets made during planning takes its size from the listing's own Width/Height/Depth specs (`listing_size`); the old Serper functions stay in the code unused and the saved search results are no longer read for sizes.
- **Product size vs box size (user 23-Nov):** plans now give `dimensions_cm` = the product itself OUT OF ITS BOX (used for drawing) and `package_cm` = the box/pack size (never used for drawing), with `size_check` saying how they were told apart (rule 26); the listing-size reader skips package/box/shipping fields.
- **Use the right part (user 23-Nov, rule 47, `schema_version` 8):** plans list every part in `parts_role` (applicator / container / closure / spare / accessory / packaging), whether it is USED in the shot, where it is in the first frame and the one movement; e.g. a serum is applied with its dropper, the bottle only holds it. Every picture and clip prompt gets 'PARTS - USE / DO NOT USE'; a used applicator keeps the product open (closed-unless-used respects it) and is already in its use position in the first frame.
- **Not used is not hidden (user 23-Nov):** each part in `parts_role` also has `shown` - an unused part (the bottle, the box, a spare) can stand in the shot, visible and untouched, where the plan says; prompts say 'SHOW but do NOT use ...'; only second copies are forbidden.
- **Output cap (user 23-Nov):** every OpenAI planning request has `max_output_tokens` 18000 (thinking + answer; saved plans used 5.8k-15k); `OPENAI_MAX_OUTPUT` changes it. A plan that hits the cap comes back cut off and fails (not re-sent).
- **Loose parts never hover (user 23-Nov, cap floating in front of her):** a shown-but-unused part must lie ON a named surface that is in the start framing (in front of or beside her), with a contact shadow; a part with no such surface in its plan is left out of the picture; every prompt has a LOOSE PARTS line; products with loose parts are filmed with her behind the counter/table they lie on.
- **Support chain (user 23-Nov, every object):** every product, part, prop, cloth, mat, tray or box rests on something that rests on furniture or the floor, with a contact shadow; a cloth lies flat on a table/counter/bed before anything rests on it (planner rule 48, the prompts' PHYSICS text and the background bible); a plan prop whose placement names nothing it rests on is dropped from the room.
- **Stands or leans for real (user 23-Nov, sandals upright on their toes):** an object stands upright only if it can stand on its own base; anything else lies on its natural side (shoes ON THEIR SOLES) or leans against a real object in the frame that touches it (wall, box, stand - listed as a prop); a hand resting on top is not support (planner rule 49, PHYSICS text, footwear display rules).
- **No leaning against walls (user 23-Nov):** something that cannot stand on its own lies on its natural side, or leans on a stand / easel / riser / its own box that the plan puts in scene.props behind it, touching it - never against a wall.
