> **30-Oct OVERRIDES (read first):** Higgsfield = ACCOUNT 1 (`mcp__higgsfield__*`) for plates + clips; account 2 only as fallback. Home = CLIENT-FINAL row 195 v2 class, a different room per video (realism.HOME_V2 + HOME_V2_ROOMS + HOME_V2_REF as style ref). Paths: see ../SKILL.md (01_DIWALI_REELS/00-04). The worker prompt from `scripts/pipeline.py prompt <row>` wins over anything below.

# 2 more samples, FAST (client waiting) - footwear row 65 (Zoya) + home decor row 444 (Kavya)
Same theme as the approved-direction GEST samples (rows 6 / 195 / 256 in 01_LATEST_FINAL): yesterday's NEXT6 look (feedback #3:
lived-in home, phone hand-held by a family member, normal light, real skin) + REF_GESTURES body language + "before -> after"
pairs + close-ups. Read 03_WORK/_approved_samples_GEST30/BRIEF.md and BRIEF2.md; their rules apply. SPEED: plates straight on Higgsfield nano_banana_2_1
(TrueFan has been rate-limited all day), up to 4 Kling jobs in flight, ~22 s footage, no gold-plating - but QC is NOT skipped.

## Row 65 Zoya - Women's Footwear (juttis) - folder 03_WORK/_approved_samples_GEST30/row_065
- Persona personas/zoya.jpg (user's choice for row 65). Every footwear rule: every distinct pair BIG, hands-only turn shots,
  realism.FOOTWEAR_BEAUTY (attractive, groomed, clean pedicured feet), "phone held very low, about 40 cm from her feet".
- 4 distinct pairs: pearl-scallop jutti (p1 = p2), gold embroidered jutti (p3), cream jutti with multicolour stripes (p4),
  maroon velvet jutti with gold/teal embroidery (p5). Check products/.
- Outfit: one simple pastel kurta + cropped pants (ankles + juttis visible), same in every shot. Footwear = NO decor.
  Home = HOME_BG + HOME_VARIANTS[<batch_100 row 65 home_variant>].
- Shots (~8 clips): s1 full body, she wears the pearl pair, gesture foot_show | s2 knees-down pearl, steps | s3 BEFORE: two
  hands hold the gold pair (hands-only, turning it) -> s4 knees-down gold pair worn, toe tap | s5 knees-down cream pair, heel
  turn | s6 BEFORE: hands hold the maroon pair -> s7 knees-down maroon worn, steps | s8 close-up of the maroon embroidery on
  the worn foot (optional if credits allow).
- Title board 0 (Baloo, white + shadow; switch to board 3 Lobster if unreadable on the wall): head "Diwali Jutti Edit",
  sub "Women's Footwear · Sale Live". Music = batch_100 row 65.

## Row 444 Kavya - Home Decor - folder 03_WORK/_approved_samples_GEST30/row_444
- Persona personas/kavya.jpg. Home Decor = Diwali DECOR ON (realism.FESTIVE_EXTRAS: marigold, rangoli, fairy lights, toran).
  Home = HOME_BG + HOME_VARIANTS[<batch_100 row 444 home_variant>]. Benchmark: 00_PREVIOUS_VERSIONS/NEXT6_29oct_feedback3_samples/Diwali_row473_Aanya_HomeDecor_480p.mp4.
- Products (check products/ + products.json): p1 pair of wooden Swastik/Om shadow diya holders, p2 set of 3 gold metal urli
  stands with flower bowls, p3 gold metal taper candle stand set of 6, p4 glass mosaic tealight holder, p5 pair of gold iron
  pedestal stands. ALL UNLIT: no flames anywhere (Kling lights them; flames = retake). Candle stands hold plain unlit
  candles or stay empty; diya holders empty.
- Gestures adapted to decor (hands keep ONE job each): she carries the product in with both hands and PLACES it (before ->
  after: in her hands -> placed on the console/shelf/floor), arranges / turns it to the light, fills the urli with marigold
  petals, steps back and looks at it with a soft smile; close-ups of each product's detail (cut-out shadow, mosaic glass,
  gold finish) with her hand near it.
- Shots (~7 clips): one hero shot per product (5) + 2 close-ups (p1 swastik cut-out, p4 mosaic).
- Title board 6 (Kalam note): head "Diwali Decor Edit", sub "Home Decor · Diwali Sale Live". Music = batch_100 row 444.

## Both
- Assemble with 01_DIWALI_REELS/02_SKILL_PIPELINE/scripts/assemble_fk.py (BBD_OUT=".../01_DIWALI_REELS/03_WORK/_approved_samples_GEST30"), NOT assemble.py. 480p ->
  03_WORK/_approved_samples_GEST30/row_NNN/final/ + copy to 01_LATEST_FINAL/. Budget ~75 credits each.
