# BBD reel worker brief (rows assigned in your prompt)

You make finished BBD reels with the bbd-omni-reel skill (the folder this file is in).
Read first: SKILL.md (all of it - standing rules + "Run steps - one-shot recipe"), references/PROMPTS.md, references/PLAN.md, references/QC_BRIEF.md.
Always `export BBD_OUT=<your output folder>` (the coordinator gives it) before running scripts. SK=<skill>/scripts.
The user approved this batch: generate without asking. Work row by row, finish one before starting the next.

## Hard rules
- ONE generation per shot (generations:1). Re-generate a shot only after it fails a gate; max 2 re-takes per shot, then mark the row BLOCKED in row_NNN/log.md and move on.
- Up to TWO video generations (Omni or Kling) in flight from you at a time - e.g. generate shots 1 and 2 together, or overlap the next row's plates with this row's clips (7 other workers share the accounts; if a generation fails as rate-limited, wait 60 s and retry). Nano Banana: one at a time; on IMAGE_RATE_LIMITED wait ~60 s and retry.
- NO PRICES anywhere: never spoken, never on screen (no rupee amounts, MRP, strike-through, "from Rs", "under Rs"). Product labels = name only. If column I (hook) or a [Music only] super contains a price, drop the price part.
- Dialogue: Hindi words in Devanagari, English words/brand names in Latin, numbers as English words. Voices: use data/voices.json exactly (key = persona name, title case). Do not edit voices.json.
- Prompts never contain the words microphone/mic/lav. Describe wardrobe positively.
- Plate checklist (SKILL.md step 4) on EVERY plate before any clip: persona identity (= plate s1); persona's own shoes/clothes/bag plain and unbranded (zoom on feet - no swoosh/"N"/letters); same outfit + same shoes on the feet as plate s1 (footwear rows: products are HELD, never worn); product held at waist/side so the chest is visible; product matches listing photo side by side (two products in one plate -> colours in CAPS); no text, no extra people.
  * Apparel rows (Men's Western Wear, Women's Ethnic Wear): the persona WEARS that shot's product garment; face, hair, jewellery, footwear, setting stay identical to plate s1 - only the garment changes.
- Pick up to 3 products (clearest listing photos) per row; set shots.json "products" to their 1-based indices in products.json; one product per shot.
- Never open Instagram. Do not touch Google Drive, the Google Sheet, or Chrome - delivery is done by the coordinator. Do not edit the skill's scripts; if a script fails, work around it in your row folder and say so in your report.
- No AI model names in output file names.

## Voice rows (column D "Voice") - Omni with lip-sync
Follow the one-shot recipe exactly: row.py -> products.py -> shotplan.py -> fill shots.json (voice from voices.json, wardrobe, setting, hook = column I without prices, dialogue_dev, action, framing, products) -> plates (TrueFan generate_nano_banana_image, 9:16 2K, persona + listing photos uploaded via upload_media method service_command; the returned curl `ut=` token works for several files ~15 min) -> promptgen.py -> generate_video per prompts.json entry (model gemini-omni-1.2-flash, 720p, 9:16, the entry's duration and image) -> download to clips/sN.mp4 -> clipcheck.py <row> <N> (RETAKE = regenerate that shot) + qc.py <row> clips/sN.mp4 and LOOK at the sheet (mic/badge appearing, wardrobe or shoes changing, product morphing, face drift, hands) -> autoplan.py -> assemble.py -> qc.py <row> (no_repeats must be true) -> read every master sheet.

## Music rows (column D "Background music") - Kling, no lip-sync
Script = "[Music only] Super 1: ... | End: ...". Make 3 visual beats that follow column J (HOOK / PRODUCTS / CLOSE) with the row persona and products. Plates exactly as above. Clips: Higgsfield MCP `generate_video` with params {model:"kling3_0_turbo", sound:"off", aspect_ratio:"9:16", duration:5-7, medias:[{role:"start_image", value:<media_id>}], prompt:<motion beat, natural phone-camera UGC, persona does not speak, no text, product identical to the start image, natural hands>}. Get the media_id with `media_import_url` on the plate's TrueFan image URL. Poll with `jobs_wait`, download the result video URL to clips/sN.mp4. Visual check with qc.py <row> clips/sN.mp4. Write plan.json by hand (references/PLAN.md): audio {"mode":"music"}, supers = the [Music only] lines (outline/pill, TOP of frame y 0.07-0.13, never on product or face, badge corner x>0.74,y<0.16 kept clear), last super = the End line text (no price), logo true, endslate true. Then assemble.py, qc.py, read the master sheets.

## QC (every row)
Self-QC strictly against references/QC_BRIEF.md (all 12 rules + no prices) on the master sheets and transcript; write qc/verdict.json {"verdict":"PASS"|"FAIL","issues":[...]}. Fix FAILs (re-trim / move super / re-take shot) before moving on. Log every generation id and every re-take reason in row_NNN/log.md.

## Report (final message, under 150 words)
One line per row: PASS / BLOCKED (reason), final length, clips generated. Plus any script problems.

## Update (Higgsfield concurrency - shared with other people, max 7 per person)
- Kling on Higgsfield: at most ONE Kling job in flight from you at a time.
- Extra plate source: ONLY the workers for rows 8-13 and rows 20-25 may ALSO make plates on Higgsfield `generate_image` model `nano_banana_2` (params resolution "2k", aspect_ratio "9:16", medias role "image_references"), at most ONE Higgsfield image job in flight at a time, alternating with TrueFan Nano Banana when TrueFan is rate-limited. References: `media_import_url` on a public https URL (TrueFan plate URLs, Flipkart listing image URLs) or `media_upload` + curl PUT + `media_confirm` for local files (persona jpg). Same plate checklist. The plate must then be uploaded to TrueFan (upload_media service_command curl) before it can be a <FIRST_FRAME> for Omni.
- Everyone else: TrueFan Nano Banana only for images.
