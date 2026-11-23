> **30-Oct OVERRIDES (read first):** Higgsfield = ACCOUNT 1 (`mcp__higgsfield__*`) for plates + clips; account 2 only as fallback. Home = CLIENT-FINAL row 195 v2 class, a different room per video (realism.HOME_V2 + HOME_V2_ROOMS + HOME_V2_REF as style ref). Paths: see ../SKILL.md (01_DIWALI_REELS/00-04). The worker prompt from `scripts/pipeline.py prompt <row>` wins over anything below.

# Gesture sample (user 30-Oct): yesterday's look + the reference reels' try-on gestures - row 6 Tanya, Women's Ethnic Wear

User: "kal wale hi video rakho, ye pasand nahi aye, aur isme se hand movement aur hand gesture wagera in references se le lo"
then "Yes, make sample". The Pinterest/tripod REF30 look is REJECTED - do NOT use ROOM_A/B/C, REF_REAL, CLIP_TRIPOD or the
sticker opener.

## LOOK = yesterday's NEXT6 (client feedback #3) - follow 01_DIWALI_REELS/02_SKILL_PIPELINE/rules/BATCH_next6.md + rules/BATCH_100.md exactly
- Benchmark: 00_PREVIOUS_VERSIONS/NEXT6_29oct_feedback3_samples/Diwali_row004_Naina_WomensEthnicWear_480p.mp4 (+ 04_DATA/rows/row_004/log.md "NEXT6 29-Oct" for the method).
- Plates: realism.HOME_BG + HOME_VARIANTS[2] (pale-peach wall, dining table, steel-handled wardrobe) + realism.FESTIVE_EXTRAS
  (ethnic = decor ON; no diyas/flames) + PLATE_REALISM + PLATE_GUARD + PLATE_NO_SELFIE. Paste the realism constants VERBATIM
  (the fb#3 definitions at the bottom of realism.py win). Same home, same Tanya face in every shot.
- Clips: realism.CLIP_CAMERA (hand-held by a family member) + CLIP_REALISM + CLIP_NO_TALK + CLIP_HANDS + CLIP_GUARD.
- Do NOT reuse any plate/clip from 01_DIWALI_REELS/04_DATA/rows/row_006 (old look) - all new.

## NEW: GESTURES from the reference reels (realism.REF_GESTURES + realism.CLIP_TRYON_BODY)
One gesture per shot, all different, written into the plate pose AND the clip action:
| Shot | Outfit (check products/) | Gesture |
|---|---|---|
| s1 | p2 white sharara set + floral dupatta | dupatta |
| s2 | p1 maroon sharara set | turn (shows the back) |
| s3 | p4 black kurta + palazzo + dupatta | smooth |
| s4 | p3 purple sharara set | flare |
| s5 | p5 teal sharara set + dupatta | waist |
| s6 | p2 or p5 embroidery, WORN | detail (hand + worn garment close-up, no face) |
Every hand keeps ONE job (CLIP_HANDS); lips closed; clothing always worn.

## Edit
- Shots ~3.5-4 s like yesterday (s6 detail ~2.5 s), ~21 s footage. camera "steady", realism default (no realism_strength override).
- ONE board super: {"board":2,"head":"Diwali Try-On Haul","sub":"Ethnic Wear · Diwali Sale Live","start":0,"end":<footage end>,"x":0.42,"y":0.085,"max_w":0.72}
- Music: batch_100.json row 6 (penny_compounding_bed60.wav, offset 0). logo + endslate true.
- Assemble: BBD_OUT="~/Desktop/Flipkart Fashion/01_DIWALI_REELS/03_WORK/_approved_samples_GEST30" /usr/bin/python3 "~/Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts/assemble_fk.py" 6
  (Flipkart logo + end slate; NOT assemble.py).
- 480p -> 03_WORK/_approved_samples_GEST30/row_006/final/Diwali_row006_Tanya_WomensEthnicWear_GEST_480p.mp4, copy to 01_DIWALI_REELS/01_LATEST_FINAL/.
