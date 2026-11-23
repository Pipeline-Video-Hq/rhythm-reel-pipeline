---
name: diwali-final-reel
description: The CLIENT-APPROVED pipeline for Flipkart Diwali Phase_1 reels - since 3-Nov-2026 made fully on the TrueFan MCP (Nano Banana 2 plates in bulk, Omni 1.1 360p clips with the user's CAMERA/LIGHT/MOTION/FRAMING prompt), one shooting style per video (A mirror selfie / B headless fit check / C hands-only demo / D pouch unboxing / E room before-after, 2 per category alternating by row), real lived-in home, music only, Flipkart logo + end slate, delivered to Drive + sheet col P + purple row colour. Use for any new or redone Diwali row ("make row N", "Diwali batch", "next wave", "aage continue karo"), and whenever someone asks how the Diwali videos are made.
---

# Diwali final reel - approved pipeline (30-Oct-2026)

The client approved this style on 30-Oct ("client says videos is good"). The approved examples are in
`01_DIWALI_REELS/01_LATEST_FINAL/`: rows 6 ethnic, 195 western, 256 kids, 65 footwear and 444 home decor. Each is ~24 s at 480p,
with 1080p masters in `1080p_masters/`. Everything older is in `00_PREVIOUS_VERSIONS/`, and none of it is the reference any more.


## FINAL UPDATES - saved 3-Nov-2026 NIGHT ("pipeline save kar do"); these win over the section below where they differ
- **NO UNBOXING (user 3-Nov ~16:00):** style D (courier pouch unboxing) is RETIRED, never show a pouch/box/package opening. New style pairs
  (pipeline.py STYLES): Ethnic/Western A,B | Women FW B,C | Men FW B,C | Kids clothing B,C | Kids FW B,C | Kitchen + Household C,E |
  Baby Care, Toys, Fragrance, Makeup C only | Fashion wearables B,C | Home Decor + Furnishing E,C.
- **ARM TRACE (row 100 had 3 arms):** every hand -> its own forearm -> its own sleeve; hands = forearms = sleeves, max 2 per person; no arm from a
  side edge when both sleeves are at the bottom; check the PLATE at full size before animating; doubt = remake the plate; log "ARM TRACE: PASS sN".
- **LENGTH:** each final >= ~24 s total (>= 22 s footage + end slate): >= 2 shots per distinct pair (main + detail/zoom). Duplicate listings shown once.
- **TrueFan folder ALWAYS Flipkart_Fashion-Rhythm_AI_Profiles** for every image AND video; uploads (upload_media) must be moved there with move_to_folder.
- **USAGE RULES (user 3-Nov):** row workers on SONNET (Agent model: sonnet); the strongest model only for the final QC pass. On a rate limit / queued
  job: ONE timed sleep (5/10/15 min) then check ONCE, never loop-poll. 3-6 workers at a time, short brief rules/WORKER_BRIEF_W4.md.
- **SY ROWS (other person's, marked "SY" in sheet col Q "Assign to"): NEVER make them.** 185-187, 230-249, 287-311, 348-349, 415-436, 475-502.
  CSV for that person: ~/Desktop/Flipkart_Transfer_Kit/SY_100_rows_for_other_person.csv. Never clear the marks.
- **PER FINISHED ROW (main session):** look at the contact sheet -> `pipeline.py upload N` (Drive only) -> add the link to sheet col P with the browser
  Name-box paste (verify name col C and that P is empty first; verify via CSV export afterwards that the link is in exactly that cell and the rows above/below
  are unchanged). Purple row colour needs the Google Sheets connector (browser paint-format misclicks - do not use it).
- **ENGINE QUALITY:** Omni 360p (360x640 scaled up; softer than Kling 720p - row 100 test in 05_TESTS). Omni 720p ~Rs390/video, 360p ~Rs160. Higgsfield acct1 is nearly empty.
- **Status 3-Nov night:** 585 videos on Drive (batch 5 = 100, batch 6 waves 1-6 = all of rows 46-63, 101-125, 162-184 and 350-367). Wave 7 (368-373 Kids FW + 412-414
  Fashion Wearables SAMPLE, show the first wearables video to the user before more) was prepared but NOT started (stopped). Next open rows after that: skip SY.
- **Second Mac:** ~/Desktop/Flipkart_Transfer_Kit (INSTALL_on_second_mac.sh + README_FIRST.md); give that Mac different rows from this one.

## CURRENT PIPELINE (saved 3-Nov-2026 evening - "pipeline save kar lo"; this section wins over anything older below)
Approved by the user on 3-Nov after the samples (05_TESTS/Sample_row045_Shruti_NEWPROMPT_OMNI360_480p.mp4).
1. ROWS: next open rows of sheet 'Diwali Phase_1' (col P empty, >= 2 real pids, 'upto'->'AT' in pids). EXCLUDED: Makeup 698-747,
   Fragrance 868-907 (user re-confirmed 3-Nov) and row 45 (sample, user sends it personally - never link/colour it).
   Read the sheet with the Google Sheets connector (get_values 'Diwali Phase_1'!C2:P910). Write 04_DATA/sheet_rows_<batch>.json,
   then `pipeline.py addrows <json>` (5-12 min, run in background), `new N`, `prompt N > 03_WORK/_prompts/row_N.txt`.
   Titles: 04_DATA/film_titles.json has the sheet "Text for the Film" (col I) for every open row - add new rows there if missing
   (a missing title made workers use the default "Diwali Try-On Haul"; fix with `pipeline.py retitle N`).
2. ENGINE (TrueFan MCP only, mcp__d8f678e4-...): plates Nano Banana 2 in BULK (master alone + QC, then all other plates queued with
   wait_for_result:false and one get_image_status), clips Omni gemini-omni-1.2-flash 360p 9:16 with the NEW PROMPT block verbatim
   (rules/NEWPROMPT_360.md). Folder ALWAYS Flipkart_Fashion-Rhythm_AI_Profiles (uploads moved there). Higgsfield only as plate fallback
   (account 1, balance >= 20) after 5/10/15-min waits. No Kling clips.
3. SHOOTING STYLE per video (only change vs the old pipeline): A mirror selfie (phone over face) | B headless fit check | C hands-only
   demo | D courier pouch unboxing | E room before/after. Pairs: Ethnic+Western A/B, Women FW B(knee-down)/D, Men FW B(knee-down)/C,
   Kids clothing/Kids FW/Kitchen/Household/BabyCare/Toys C/D, Fashion wearables B(wrist/neck)/D, Home Decor+Furnishing E/C.
   Even row = first, odd row = second. pipeline.py STYLES/STYLE_TXT prints it into every worker prompt.
4. RULES on top of section 7: product clearly in frame every shot (face optional); no twirls (Omni over-rotates); unboxing only in
   style D; hands never on the stomach; no diyas (also unlit clay ones on sills), no phones lying around; footwear zoom 1.15-1.6.
5. WORKERS: 6 general-purpose agents x 3 rows each, one row at a time, brief rules/WORKER_BRIEF_W2.md (with wave-2 lessons).
   ~14-15 min per video per worker, ~18-20 videos/hour with 6 workers, ~3.5 GB disk per 18 videos (check
   `df -h /System/Volumes/Data` first; never delete without the user's OK). Workers never upload or touch the sheet.
6. MAIN SESSION per finished row: look at qc/final_1fps.jpg (title = sheet, logo, end slate, product in frame) ->
   `pipeline.py upload N` (rclone copy to Drive, link into 04_DATA/drive_links_final.json) -> Sheets connector: get_values C<N> (name
   check) + P<N> (must be empty) -> update_values P<N> = Drive link -> colour B:P of row N light purple (rgb .85/.82/.96,
   update_spreadsheet repeatCell, sheetId 583191233, columns 1-16; never A or Q) = "made on TrueFan".
7. Cost (Google public rates): 360p ~$0.03/s -> ~$1.70-2.00 per video; 720p ~$0.10/s -> ~$3.70-4.40 per video.
Snapshot of the scripts at this point: scripts_snapshot_3nov/.

## Folder layout (01_DIWALI_REELS/)
| Folder | What |
|---|---|
| `00_PREVIOUS_VERSIONS/` | everything OLD - never a reference: 28-29 Oct batch finals, NEXT6 feedback-3 samples, rejected Tier-2 / Pinterest (REF30) samples, older cuts, old docs + old batch bookkeeping (queue, drive links, link drip) |
| `01_LATEST_FINAL/<Category>/` | FINAL videos (480p) per category + `1080p_masters/`. Only finished, checked videos go here. |
| `02_SKILL_PIPELINE/` | this file, `scripts/pipeline.py` (new / prompt / finish / status), `briefs/` (BRIEF, BRIEF2, BRIEF3), `rules/` (BATCH_100.md, BATCH_next6.md = all permanent rules), `examples/row_NNN/` (plan.json + log.md of each approved video), `scripts_snapshot_30oct/` (frozen copies, reference only) |
| `03_WORK/row_NNN/` | work folders of rows being made now (plates, clips, qc, plan.json, final). `03_WORK/_approved_samples_GEST30/` = work of the 5 approved samples |
| `04_DATA/` | `batch_100.json` (persona, vertical, home_variant, music, products per row), `BATCH_100_table.md`, `rows/row_NNN/` (source data per row: products/, brief.json, products.json; old clips/finals inside are previous versions) |

The LIVE scripts are in `~/.claude/skills/bbd-omni-reel/scripts/` (realism.py, assemble.py, board_title.py, visual_qc.py,
products.py) and `Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts/assemble_fk.py`. Always run them with `/usr/bin/python3` (Homebrew
python has no Pillow) and `nice -n 19`.

## 1. Look (client feedback #3 - unchanged)
- **Home:** a REAL lived-in Indian home (realism.HOME_BG + HOME_VARIANTS[n]). It is nice and tidy, with a few everyday things
  (charger, bottle, tilted cushion). It is NOT a showroom and NOT the Pinterest/tripod look (REJECTED 30-Oct). CLIENT-FINAL HOME (30-Oct): the row 195 v2 CLASS of home - "isi category ka background, but same background na" - realism.HOME_V2 + one of HOME_V2_ROOMS (8 different rooms: living rooms, bedrooms, living-dining, balcony-door corner) + HOME_V2_REF (examples/home_umc_preview/home_v2_style_FINAL.png) as STYLE reference only. A different room per video, the same room inside one video. The grey upper-middle-class room (HOME_UMC_LIVING) is superseded.
- **Camera, light, colour:** the phone is hand-held by a family member (realism.CLIP_CAMERA). Normal home light, normal phone colour.
- **People:** real skin, natural expression, lips closed.
- **Diwali decor:** ONLY for Women's Ethnic Wear and Home Decor (realism.FESTIVE_EXTRAS: marigold, rangoli, fairy lights,
  toran). There are NEVER lit diyas, candles or flames. Every other category gets realism.NO_DECOR.

## 2. Body language - the reference gestures (NEW, approved)
Every worn/face shot gets ONE gesture from `realism.REF_GESTURES`, and each shot uses a different one. Add realism.CLIP_TRYON_BODY:
`turn` (shows the back) - `dupatta` (lifts the edge) - `smooth` (kurta front, looks down then up) - `waist` (hand on the
waist, sway) - `look_down` (cuff) - `flare` (half-twirl) - `detail` (hand shows the work on the WORN garment) - `foot_show`.

## 3. Shot grammar per category (mix it - each video gets its own rhythm)
- **Apparel (ethnic, western, kids):** 5 outfits, all WORN. Mix these:
  - BEFORE -> WORN (user 30-Oct night: "kuch hanger pe kuch packing open karte huye, taki ek jaise na lage" + "hanger pe kam
    dikhana"). Two kinds, mixed so videos don't look alike:
    - PACKET OPEN -> WORN: ~2 s, hands only, two hands open a plain courier pouch on the bed/table and slide out the exact folded
      outfit. At least 1 per video.
    - HANGER -> WORN: ~2 s of the exact outfit on a plain hanger, held at the hook by one hand. AT MOST 1 per video (often none).
    Hands only; for kids, the mother's hands. Cut straight to the same outfit worn with a gesture. The packet/hanger moment is
    allowed ONLY as this "before" shot.
  - WORN with a gesture, plus a ZOOM punch-in (see 4).
  - CLOSE-UP of the worn detail (print, embroidery, mirror work, border). Her hand shows it; the face is out of frame.
- **Footwear:** EVERY pair is first SHOWN (two hands turning one shoe, hands only), THEN WORN.
  - Worn shots are a full body wide shot -> a zoom punch-in on the feet (zoom 2.1-2.4, zoom_y 1.0), plus knees-down shots.
  - Model: realism.FOOTWEAR_BEAUTY (attractive, groomed, pedicured feet). Write "phone held very low, about 40 cm from her feet".
  - Hands-only prompts stay short and about the product only; body or nail words cause false NSFW flags.
- **Home Decor:** a calm reveal. She carries each product in and PLACES it (before -> after), then a zoom punch-in on the
  product (zoom ~1.7, zoom_y 0.85-0.9), plus 2 close-ups. Keep each product centred horizontally in its plate so the crop lands on it.
- **Length:** ~22-24 s of footage (pieces of 1.5-3.5 s) + end slate.

## 4. Edit
plan.json is the same format as `examples/row_*/plan.json`.
- **Zoom punch-in:** put the SAME clip twice in a row: the wide part, then the continuation with `"zoom": 1.7-2.4,
  "zoom_y": 0..1` (anchor height: 0 = top, 0.5 = centre, 1 = bottom). For cloth, use zoom 1.8 with zoom_y >= 0.7 so the face
  is never cut mid-way.
- **Title:** ONE `board` super for the whole footage, `{"board":0-7,"head":..,"sub":..,"start":0,"end":<footage>,"x":0.42,
  "y":0.085,"max_w":0.72}`. Rotate the board font between videos. On light walls use a panel style (1, 2, 4, 5, 6, 7), not the white
  shadow styles 0/3. No price and no %.
- **Music:** the row's batch_100 music from 0. Settings: `camera: steady`, `logo: true`, `endslate: true`.
- **Assemble ONLY with the Flipkart wrapper** (plain assemble.py burns the old BBD badge and the "Starts 9th October" slate):
  `BBD_OUT="<work root>" /usr/bin/python3 "~/Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts/assemble_fk.py" <row>`
- **480p:** `ffmpeg -i master -vf scale=480:854:flags=lanczos -c:v libx264 -crf 23 -c:a aac -b:a 128k -movflags +faststart`.
  Name it `Diwali_rowNNN_<Name>_<Category>_480p.mp4` and copy it to `01_LATEST_FINAL/`.

## 5. Generation
- **Plates:** TrueFan `generate_nano_banana_image` (Nano Banana 2, 9:16), ALWAYS `folder="Flipkart_Fashion-Rhythm_AI_Profiles"` (user 2-Nov;
  never test-test_diwali). Fall back to Higgsfield `nano_banana_2_1` on ACCOUNT 1 only after 2 TrueFan failures for a plate.
  - Pass the persona photo plus 2-3 listing photos.
  - From shot 2 on, also pass the first plate (same home, same face).
  - Paste the realism constants VERBATIM.
  - Write "no tripod or phone visible".
- **Clips:** Higgsfield ACCOUNT 1 (`mcp__higgsfield__*`, user 30-Oct; account 2 `mcp__523fc806-...` only as fallback when account 1 is empty - media ids do not cross accounts). `kling3_0_turbo`, 720p, 5 s, 9:16, sound off, count 1
  (7.5 cr each). Decline preset suggestions. Up to 3-4 in flight.
  - Prompt order: CLIP_CAMERA + gesture text + CLIP_TRYON_BODY + CLIP_REALISM (or CLIP_REALISM_CHILD) + CLIP_NO_TALK +
    CLIP_HANDS + CLIP_GUARD. Keep it under 2500 chars by shortening only the gesture text.
- **Persona:** the persona from the sheet (batch_100.json name). Exception: row 65 uses Zoya.
- **Cost:** about 65-95 credits per video. A video takes ~30-45 min (one worker per row; run 2-3 rows in parallel).

## 6. QC gate (never skip)
1. `visual_qc.py <row>` with BBD_OUT. LOOK at the hands (6 fps), limbs and full sheets plus face/lip crops.
2. Check every frame for:
   - ARM TRACE (3-Nov, row 100 s9 had 3 arms): follow every hand to its forearm and sleeve; hands = forearms = sleeves, max 2 per person; no arm from a side edge when both sleeves are at the bottom. Check the PLATE at full size before animating; doubt = remake the plate.
   - exactly 2 hands, 2 legs/feet;
   - the same face;
   - outfit/pair/product = listing (the hanger/shown item = the worn item);
   - lips closed (teeth smiles = retake or trim);
   - no flames;
   - the room unchanged;
   - the gesture actually happens.
3. Trim bad seconds instead of re-rolling when possible.
4. After assembly, LOOK at the 1 fps sheet of the 480p:
   - Flipkart "f" logo top-right;
   - white Flipkart end slate;
   - title readable and never over the face;
   - zoom crops clean.

Common faults seen:
- Teeth grins late in a clip.
- A hand resting on the belly (re-plate it to the side of the waist or hip).
- An earring or watch appearing.
- A hanger spinning.
- Shoes flattening or changing colour.
- An open-back mule instead of a closed jutti.
- A tripod/phone drawn into the plate.

## 7. Hard rules (all still permanent)
- SHOOTING STYLES (user 3-Nov ~14:45, only the shooting style changes): one style per video, alternating row by row within the
  category (even row = first, odd row = second). A mirror selfie (phone in front of the face) | B headless fit check | C hands-only
  product demo | D courier pouch unboxing | E room before/after. Ethnic + Western: A,B | Women FW: B (knee-down), D | Men FW: B
  (knee-down), C | Kids clothing, Kids FW, Kitchen, Household, BabyCare, Toys, Fragrance: C,D | Fashion wearables: B (wrist/neck
  close), D | Home Decor + Furnishing: E,C | Makeup: C,D (after the other categories). Engine: Omni 1.1 360p NEW PROMPT
  (03_WORK/NEWPROMPT_360.md). pipeline.py STYLE_TXT/STYLES print it into every worker prompt.
- PRODUCT ALWAYS IN FRAME (user 3-Nov, PERMANENT): "har shot me product clearly dikhna chahiye. Avatar ka face na dikhe to bhi
  chalega (mirror selfie me phone face ke aage, ya sirf haath me product), par product hamesha frame me ho." = In EVERY shot the
  product is clearly visible, large and sharp. The avatar's face is optional: a face-less shot is fine (hands-only with the product,
  or a mirror selfie where the phone covers the face), but the product must be in frame the whole used range. Any clip range
  where the product is hidden, cropped out or too small = trim it or retake. The old "no mirror selfie" line is relaxed ONLY to
  this case (phone in front of the face, product clearly shown); a selfie that hides the product is still banned.
- No selfie (a mirror selfie only per the rule above: phone over the face, product clearly in frame).
- Each hand has one job.
- Clothing is always worn: packet-open or hanger only as the ~2 s before-shot (max 1 hanger per video).
- No notebook, paper or pen.
- No price and no %.
- Every distinct product shown (duplicate listings once).
- No Drive upload or sheet edits unless the user asks.
- No AI model names in file names.

## 0. HOW TO RUN (the gesture version is FINAL - user 30-Oct: "gesture wala final, usi ko continue karna hai")
Work root for every new or redone row: `01_DIWALI_REELS/03_WORK/row_NNN` (BBD_OUT = 03_WORK).
```
H=~/Desktop/Flipkart\ Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts/pipeline.py
/usr/bin/python3 "$H" status            # final vs open rows per category (reads 01_LATEST_FINAL)
/usr/bin/python3 "$H" new 374 375        # set up 03_WORK/row_NNN (brief.json, products/, folders, log.md)
/usr/bin/python3 "$H" prompt 374         # the full worker prompt: category template, home, decor, title board, music
/usr/bin/python3 "$H" finish 374         # assemble_fk -> 480p -> 01_LATEST_FINAL (+1080p master) -> qc/final_1fps.jpg
```
Main session: `new` the rows, start ONE background worker per row with the `prompt` text (2-3 rows in parallel), and check
each finished video's frames before telling the user. Category templates (in pipeline.py):
- apparel / kids apparel / footwear / home decor = APPROVED samples.
- wearables (watches, bags) and home furnishing = built from the same grammar, not yet seen by the client. Show the first one
  to the user before batching.

## 8. Worker prompt template (pipeline.py prompt generates the full version)
"You are worker X making ONE Diwali reel: row N (<persona>, <category>) in the approved final style. READ
02_SKILL_PIPELINE/SKILL.md fully, then briefs/BRIEF.md + BRIEF2.md (+ BRIEF3.md for footwear/home decor) and the closest
examples/row_*/log.md. Work in <work root>/row_NNN (copy brief.json + products/ from 01_DIWALI_REELS/04_DATA/rows/row_NNN, set out_name).
Run scripts with BBD_OUT=<work root>. Plates -> clips -> QC (look at every sheet) -> plan.json with zoom punch-ins ->
assemble_fk.py -> 480p -> 01_LATEST_FINAL/. Log everything in row_NNN/log.md. Report: path, duration, shot list, credits,
retakes, doubts."

## 9. Variety in every category (user 30-Oct night: "is tarah sari categories main kar dena, mtlb same na lage")
Every video mixes 2-3 ways of bringing products in; `pipeline.py prompt` adds a VARIETY line per category and picks a different
opener for neighbouring rows (row % 3):
- Apparel: PACKET OPEN (at least 1) / HANGER (at most 1) -> worn.
- Footwear: SHOWN in two hands only -> worn, as in row 65 (user 31-Oct: "jaise pahele dikhate the, packet se nahi nikalo" - no packet, no shoe-box).
- Wearables: BOX OPEN / SHOWN / PACKET OPEN -> worn.
- Home Decor: CARRY IN + place / UNBOX from a carton + place / FINISHING TOUCH on a placed piece.
- Home Furnishing: FOLDED in hands / PACKET OPEN / PICK UP -> then the sheet ALREADY LAID on the made bed. NEVER shake/unfold/spread it in the air (user 31-Oct: looks tiny).
- Kitchen, Household, Makeup, Grooming, Baby, Toys, Pets: SHOWN / PACKET-or-BOX OPEN / PICK UP from shelf or counter -> used.
Rules: at least 2 intro types and 1 packet/box opening per video, never the same intro 3 times in a row. The shot framing stays as in the approved template (user: "shot mat badlna") - only the intro varies.
