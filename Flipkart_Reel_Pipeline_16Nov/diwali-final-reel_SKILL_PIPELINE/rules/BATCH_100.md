> **30-Oct OVERRIDES (read first):** Higgsfield = ACCOUNT 1 (`mcp__higgsfield__*`) for plates + clips; account 2 only as fallback. Home = CLIENT-FINAL row 195 v2 class, a different room per video (realism.HOME_V2 + HOME_V2_ROOMS + HOME_V2_REF as style ref). Paths: see ../SKILL.md (01_DIWALI_REELS/00-04). The worker prompt from `scripts/pipeline.py prompt <row>` wins over anything below.

# Diwali Phase_1: 97-row batch (the 100 minus pilots 126, 193, 73), 28-Oct-2026

The client approved the pilots. Work in `~/Desktop/Flipkart Fashion/diwali_reels_kling/`.

- **Per-row data:** `batch_100.json` (keyed by row): name, vertical, folder, theme, beats, decor, camera, home_variant, title, font, treatment, music, music_offset, products (5 listing links).
- **Readable table:** `BATCH_100_table.md`.
- **Worker split:** `workers_100.json`.
- **Approved examples to copy the flow from:** `row_080/` (log.md, plan.json) and `row_193/`.
- **Pipeline docs:** `~/.claude/skills/bbd-omni-reel/SKILL.md` + references/PROMPTS.md. Use `/usr/bin/python3` for every skill script (Homebrew python has no Pillow).

## HARD RULES (all from the user today; every one is permanent)
1. **ALL VIDEOS INDOORS IN A HOME.**
   - No canteen, park, lane, stairs, terrace or office.
   - Use realism.HOME_BG + realism.HOME_VARIANTS[home_variant], with neat middle-class homes, a different home per row.
   - Never use realism.LOCATION_VARIANTS.
2. **Theme** = batch_100.json[row].theme / beats (all set inside the home). Follow the beats. Use 3 shots, or 4 when a close-up adds value; footwear and wearables always get one tight product close-up.
3. **Decor** only when decor = true (realism.FESTIVE_EXTRAS: small marigold/unlit diyas/rangoli). When decor = false, put realism.NO_DECOR in the plate prompt.
   - The outfit suits the product: festive Indian wear only for ethnic/puja themes; modern everyday wear for western, sports and casual.
   - The same outfit appears in every shot.
4. **Camera:**
   - steady (CLIP_CAMERA, plan "camera":"steady") for everything except camera = "tilt" rows.
   - Tilt rows use CLIP_CAMERA_TILT + plan "camera":"tilt". It must still be filmed BY A FRIEND, never a selfie.
5. **NO LIP MOVEMENT** (music only, no lip-sync): realism.CLIP_NO_TALK goes in every clip prompt. Lips stay closed or a closed-mouth smile.
6. **EXACTLY 2 HANDS, NO SELFIE** (row 73 had a 3rd hand):
   - PLATE_GUARD + PLATE_NO_SELFIE on every plate. CLIP_HANDS on every clip.
   - Each hand has ONE fixed job; no touching hair or face; no waving while holding something.
7. **Other guards:**
   - PLATE_GUARD/CLIP_GUARD: exact limbs, product identical to the listing, no fire, no lit diyas (Kling lights diyas: keep diyas out of shots where possible).
   - PLATE_REALISM/CLIP_REALISM.
   - Child personas: CLIP_REALISM_CHILD.
   - An adult showing kids' products HOLDS them, never wears them.
8. **QC gate:**
   - Run `visual_qc.py <row>` and LOOK at the full, limbs AND hands (6 fps) sheets of every clip.
   - Tick hand_count_ok, lips_not_moving and the rest only after looking. assemble.py refuses otherwise.
   - Retake any failing clip, or trim it to the clean part.
9. **Title:** ONE constant title for the whole video = batch_100.json[row].title (already cleaned: no price, no %).
   - Convert it with `title_styles.style(text, font)[0]`. style() returns a TUPLE: take [0].
   - Treatment by batch_100 treatment:
     - box → style "box"
     - pill → "pill"
     - outline → "outline", line_gap 0.05
     - outline+bg → "outline", line_gap 0.05, bg [0,0,0,110]
   - Size about 46-52 (superscript is auto ×1.8), top of the frame (y ≈ 0.09), NEVER over the face or the product. Move it left/right, or to 3 lines, if needed.
   - Never bold fraktur or fraktur, never a solid black bar, never dark text with an outline.
10. **Music:** batch_100.json[row].music, starting at music_offset s.
    - assemble has no offset key: if offset > 0, pre-trim a copy into row_NNN/work/.
    - Do not change the music choice: it is the user's "7 tracks + 4 repeats per niche, no back-to-back" plan.
11. **NO price and NO "% off"** anywhere: title, plates, product shots. No AI model names in file names.
12. **Output:** 480p ONLY for delivery.
    - The final master goes in row_NNN/final/. Make the 480p (`-vf scale=480:854:flags=lanczos -c:v libx264 -crf 23 -c:a aac -b:a 128k -movflags +faststart`) as row_NNN/final/Diwali_rowNNN_<Name>_<Category>_480p.mp4.
    - Copy that 480p into `FINAL_480p_category_wise/<folder>/` (folder from batch_100.json).
    - **Do NOT upload anything to Drive** (user).

## TOOLS
- **Products:** products.py (listing photos). Pick the 2-4 clearest listings; skip combo or unclear ones.
- **Persona:** ~/.claude/skills/bbd-omni-reel/personas/<name>.jpg.
  - If it is missing, download it from the row's persona Drive link (batch_100.json persona_link), following the SKILL.md / row.py note (Drive download + b64save.py).
  - Save it to personas/<name>.jpg for the other workers.
- **Plates:** TrueFan generate_nano_banana_image (9:16, 2K).
  - **TrueFan is RATE-LIMITED today** (shared quota). On IMAGE_RATE_LIMITED or a timeout, do NOT wait-loop: switch at once to **Higgsfield generate_image**.
  - On Higgsfield, import the refs with media_import_url / media_upload, and pick an edit model with references via models_explore(action:'recommend', query:'edit image with reference images, keep person identity'). Use 9:16.
  - Record which one you used in log.md.
- **Clips:** Higgsfield generate_video `{"model":"kling3_0_turbo","resolution":"720p","duration":6,"aspect_ratio":"9:16","sound":"off","count":1,"use_unlim":false,"medias":[{"role":"start_image","value":<media_id>}],"prompt":...}`.
  - Use media_import_url for TrueFan URLs; a Higgsfield image job id/media works directly.
  - If a preset_recommendation comes back, resubmit with declined_preset_id.
  - At most 2 Kling jobs in flight per worker. Wait with jobs_wait.
- **Colour tags:** assemble.py strips colour tags. Still check the final 1 fps contact sheet: logo + title on every second, end slate clean.
- **Assemble:** `BBD_OUT="$PWD" /usr/bin/python3 "~/Desktop/Flipkart Fashion/diwali_reels/assemble_fk.py" <row>`, run from diwali_reels_kling/.

## REPORTING
- Keep row_NNN/log.md updated: assets, jobs, retakes.
- After EACH row, SendMessage to "main" with: row, 480p path, length, retakes, anything doubtful.
- Then start the next row. Do not stop until all your rows are done.
- If something blocks a row for more than 20 minutes, skip it, note it, and come back to it at the end.

## ADDED 28-Oct ~15:10 (reviewer): product presentation
- The product must be the HERO of every shot: worn, held up toward the camera, or a tight close-up. Never ONLY lying on a bed or sofa, half cut off by the frame edge, while the person looks at something else (row 13 did this; it is weak).
- On the shopping-list theme: she ticks the list in ONE beat at most. In the other beats she holds up or wears the item.

## ADDED 28-Oct ~15:25, USER RULE: footwear "hands-only" shot (format for slippers / sandals / clogs / flats / any footwear)
User: "slippers ko next shot main haath main lekar show kare, sirf haath dikhe - ye slipper ke liye format rahega".
- In EVERY footwear row (men_fw, kids_fw and any footwear), right AFTER the shot where the person wears the slipper, add ONE shot that shows ONLY HANDS holding the slipper.
- Framing: a tight close-up; the frame shows only the two hands/forearms and the slipper. NO face, no body, no legs.
- Action: the hands slowly turn the slipper to show its top, straps and sole. Use one slipper in two hands, or the pair with one in each hand.
- Background: the same home, softly out of focus.
- Plate prompt: PLATE_GUARD + PLATE_REALISM + "only two hands in frame". Clip prompt: CLIP_HANDS (both hands stay on the slipper) + CLIP_GUARD + CLIP_REALISM.
- Product identical to the listing (straps, sole, buckle, print).
- QC: the hands sheet must show exactly 2 hands in every frame.
- This is an extra 4th shot, so trim each shot to about 4.5 s to keep the reel around 20 s.

## ADDED 28-Oct ~15:40, USER RULE: SHOW EVERY PRODUCT OF THE ROW
User: "if the sheet has 4 products, show all four in the video. Row 189 showed only 2, but there were more products."
- Every distinct product in the row's product list (usually 4-5) must appear in the video as the hero of at least one shot: worn, held up, or a close-up.
- Skip a listing ONLY if it is a near-duplicate of another one or is unusable (dead link or no clear photo). Note the reason in log.md.
- Use more, shorter shots: one shot per product, Kling clips of duration 5, trimmed to about 3.5-4 s each. Target 18-24 s of footage (up to about 26 s with the footwear hands-only shots).
- Footwear: each pair gets a worn shot. The hands-only shot (rule above) follows the worn shot. For 4-5 pairs, give the hands-only shot to at least 2 pairs, or show 2 pairs in hands in one shot (one in each hand).
- Same person, same outfit and same home in every shot. The theme's beats are a guide: repeat or extend them per product.
- User clarification 28-Oct: if products are the SAME (duplicate listings), show that product only ONCE; if all five are different, show ALL FIVE.

## CREDITS (user 28-Oct ~15:50): "make as many as the credits allow, it will be recharged later"
- Higgsfield had 6,645 credits at 15:45. Keep making NEW rows with all products. Do NOT redo old rows for now.
- If Higgsfield says insufficient credits: STOP submitting. Finish assembling any row whose clips are all done. Write the exact resume point in each unfinished row's log.md (which plates and clips exist, which are missing). SendMessage main "OUT OF CREDITS" with your list of unfinished rows. Do not switch to another paid service.

## DISK (28-Oct ~16:20): the Mac's disk filled up. After a row's 480p is copied to FINAL_480p_category_wise and checked, delete that row's work/*.mp4 (seg, body and main intermediates; assemble rebuilds them). Do not delete clips, plates or finals.

## ADDED 28-Oct ~16:30, USER RULE (PERMANENT): CLOTHING IS ALWAYS WORN BY THE AVATAR
User (row 13): "cloth bed pe kyun rakhe hai, avatar ko pahenana hai. ye mistakes kisi bhi video main nahi karna hai, avatar pahen ke dikhayega."
- For EVERY apparel product (ethnic, western, kids clothing, lehenga, kurta, dress, saree, night suit...), the avatar WEARS the product in its shot. One product = one worn shot = one outfit change.
- NEVER lay the garment on a bed/sofa, NEVER only hold it up on a hanger or against the body, NEVER show it on a hanger as the hero. Her "own plain outfit" + the product beside her is BANNED.
- The shopping-list / unboxing theme beats are adapted: she is already WEARING the product while she ticks the list or poses.
- The "same outfit in every shot" rule does not apply to apparel rows: each shot shows a different worn product; keep the same face, hair and home.
- Plate prompt: "she is wearing <exact product description from the listing photo>", with the product listing photo as reference; QC: the garment must match the listing (colour, print, border, dupatta).

## ADDED 28-Oct ~17:20, USER RULE (PERMANENT): NO NOTEBOOK / LIST / PAPER ANYWHERE + FOOTWEAR FORMAT ENFORCED
User (row 64): "notebook kyun pakdi hai, notebook kahin nahi hona chahiye" and "slipper wala rule apply nahi kiya ... lag nahi raha ye slipper ka hai".
- NO notebook, notepad, diary, shopping list, paper slip, pen or clipboard in ANY plate or clip. The shopping_list theme is REMOVED (themes.py); batch_100.json rows that had it now have new themes (8, 13, 64, 74, 131, 192, 252, 258, 314, 382, 439, 444, 523, 528, 533). realism.NO_PAPER is now inside PLATE_GUARD and CLIP_GUARD. Plates already made with a list/notebook for pending rows must be REDONE.
- FOOTWEAR rows must clearly read as a footwear video: EVERY distinct pair worn in a shot where the feet/footwear fill most of the frame (knees-down or tight), PLUS the hands-only turn shot (rule of 15:25) for at least 2 pairs. A medium shot where the slipper is tiny does not count as showing it.

## ADDED 28-Oct ~17:30, USER RULE (PERMANENT): FOOTWEAR MODEL MUST LOOK BEAUTIFUL
User: "footwear wale video main model dikhne main sahi ho, dikhne main beauty ho".
- Every FOOTWEAR row (women, men, kids): append realism.FOOTWEAR_BEAUTY to every plate prompt; in clip prompts add "well-groomed, beautiful pedicured feet".
- The person looks attractive and well groomed (styled hair, light makeup, warm smile, flattering outfit), and the feet look beautiful in the close-ups (clean, smooth, neat pedicure, no cracked heels). Still a real person in a real home.
- QC: reject dull, tired or unkempt looks and rough or dirty feet.
- User 28-Oct ~17:45: "footwear wale main ladki ho ya ladka dikhne main khoobsurat ho": the rule applies equally to MEN (handsome, fit, stylish haircut, groomed, clean feet) and women. Men footwear rows 126-135 are included.
- User 28-Oct ~17:50: "footware wale main age dhyan rakhna". Before any footwear row, LOOK at the persona photo; if the person would not look attractive and well groomed on camera, message main to propose another persona before making plates.

## ADDED 28-Oct ~18:00, USER: "row 66 is good video, i want like that" = THE FOOTWEAR LOOK REFERENCE
Reference: ~/.claude/skills/bbd-omni-reel/assets/refs/footwear_good_row066*.jpg/.mp4 (row 66 Naina, Women's Footwear).
Copy its LOOK in every footwear row: attractive, fresh, well-groomed model; bright soft natural daylight (no dim or dull rooms); a simple, neat, well-fitted outfit in a soft colour; a clean, bright, uncluttered home; steady camera; a full-body shot where she walks or turns confidently; a BIG close-up of the feet walking on the floor with neat painted toenails; an accessory such as a sling bag is fine.
Keep the newer rules on top of it: show EVERY distinct pair (row 66 showed only 2 of 5), add hands-only turn shots, no notebook.
Pass the row 66 plate frame (footwear_good_row066_3s.jpg) as a STYLE reference for light, framing and grooming only, never to clone the face or room.
- User 28-Oct ~18:05: "model change hota rahe but isi style main". Use a DIFFERENT model in every footwear video (never the same persona in back-to-back footwear rows), all in the row-66 style (bright, fresh, groomed, big feet close-ups). If a sheet persona does not suit that look, propose a swap from personas/ that is not used in the neighbouring rows.
- User 28-Oct ~18:10: "Persona sheet wala rakhna". ALWAYS use the persona from the sheet (batch_100.json name / persona_link). Do NOT swap personas on your own and do not propose swaps. The model changes from video to video because the sheet already gives each row its own persona. Only exception: row 65 (the user asked for Zoya). Make every sheet persona look her/his best in the row-66 style through grooming, light and outfit.

## WORKER TIPS (learned 28-Oct, W3/W7)
- Kling turbo takes ~8-12 min per clip with 1 in flight, so an 8-shot footwear row takes ~1.5 h.
- Footwear plates: write "phone held very low, about 40 cm from her feet", otherwise the shoes come out small.
- Hands-only shot prompts: keep them short and product-only ("two hands holding the shoe, turning it"). Words about nails, body or legs got a false NSFW flag.
- Helpers: scratchpad/getclip.sh (download clip), scratchpad/qc1.sh (QC sheets for one clip), scratchpad/w3/mkplan.py (plan.json), combo.py, plates.py. Read before use.
- Context: deliver at most 3 rows per worker run, then report and stop at a row boundary (main starts the next worker).

## ADDED 30-Oct (user, PERMANENT): REFERENCE GESTURES, YESTERDAY'S LOOK
The client's Pinterest-room / tripod samples (REF30, SAMPLES_30oct) were REJECTED: "kal wale hi video rakho". The look stays
client feedback #3 (lived-in home, phone hand-held by a family member, normal light; NEXT6_29oct = the benchmark).
ADOPT ONLY the try-on body language of the client's 5 reference reels: every apparel/footwear clip prompt gets ONE gesture from
realism.REF_GESTURES (turn / dupatta / smooth / waist / look_down / flare / detail / foot_show), different gestures across the
reel, plus realism.CLIP_TRYON_BODY. CLIP_HANDS, CLIP_NO_TALK, worn-only, no selfie and every other rule stay. Still banned from
the refs: mirror selfie with a phone, garment held up out of a bag, hangers.
- User 30-Oct (gesture samples): "kabhi hanger dikhaye phir pahen ke ... aur kabhi close dikha diya shot". HANGERS are now
  allowed ONLY as a short hands-only "before" shot of the exact outfit, IMMEDIATELY followed by the same outfit WORN. Also mix in
  close-ups of the worn outfit's detail. Spec: GEST30/BRIEF2.md. An outfit shown only on a hanger is still banned.

## 30-Oct FINAL PIPELINE (user: "ab sari videos aise hi banengi")
All new or redone videos follow 02_SKILL_PIPELINE/SKILL.md (skill diwali-final-reel). Finals go to 01_LATEST_FINAL/. Older outputs are in 00_PREVIOUS_VERSIONS/.

## ADDED 3-Nov, USER RULE (PERMANENT): PRODUCT ALWAYS CLEARLY IN FRAME
- PRODUCT ALWAYS IN FRAME (user 3-Nov, PERMANENT): "har shot me product clearly dikhna chahiye. Avatar ka face na dikhe to bhi
  chalega (mirror selfie me phone face ke aage, ya sirf haath me product), par product hamesha frame me ho." = In EVERY shot the
  product is clearly visible, large and sharp. The avatar's face is optional: a face-less shot is fine (hands-only with the product,
  or a mirror selfie where the phone covers the face), but the product must be in frame the whole used range. Any clip range
  where the product is hidden, cropped out or too small = trim it or retake. The old "no mirror selfie" line is relaxed ONLY to
  this case (phone in front of the face, product clearly shown); a selfie that hides the product is still banned.
