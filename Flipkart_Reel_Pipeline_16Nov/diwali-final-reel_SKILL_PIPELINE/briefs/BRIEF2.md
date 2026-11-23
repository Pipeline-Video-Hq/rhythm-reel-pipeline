> **30-Oct OVERRIDES (read first):** Higgsfield = ACCOUNT 1 (`mcp__higgsfield__*`) for plates + clips; account 2 only as fallback. Home = CLIENT-FINAL row 195 v2 class, a different room per video (realism.HOME_V2 + HOME_V2_ROOMS + HOME_V2_REF as style ref). Paths: see ../SKILL.md (01_DIWALI_REELS/00-04). The worker prompt from `scripts/pipeline.py prompt <row>` wins over anything below.

# 2 more gesture samples (user 30-Oct): HANGER -> WORN + CLOSE-UPS - rows 195 (Kavya, Western dresses) and 256 (Myra, Kids)

User: "do aur bana do jisme kabhi hanger dikhaye phir pahen ke, is theme par jo abhi banaya hai, aur kabhi close dikha diya
shot, is tarah se do aur bana do". The theme = 03_WORK/_approved_samples_GEST30/row_006 (approved direction): yesterday's NEXT6 look + REF_GESTURES.

Everything in 03_WORK/_approved_samples_GEST30/BRIEF.md applies (look = rules/BATCH_next6.md / feedback #3 constants verbatim, hand-held phone by a family
member, REF_GESTURES one per worn shot + CLIP_TRYON_BODY, CLIP_NO_TALK, CLIP_HANDS, CLIP_GUARD, assemble_fk.py, Flipkart
logo + end slate, 480p to 01_LATEST_FINAL). Look at the frames of 01_LATEST_FINAL/Diwali_row006_Tanya_WomensEthnicWear_GEST_480p.mp4 first.

## NEW shot grammar (mix it - not the same pattern for every outfit)
- HANGER shot (~2 s, the "before"): the exact outfit on a plain hanger, held up by ONE hand at the hook in front of the
  wardrobe/wall/curtain of the same home, the whole garment visible and still, a slight natural sway; the other hand out of
  frame or lightly spreading the hem. Hands only (no face). Phone hand-held, same light. IMMEDIATELY followed by
  -> WORN shot (~3-3.5 s): she is wearing that same outfit, with a REF_GESTURES gesture.
  (The user now allows hangers ONLY as this "before" shot directly followed by the worn shot. A hanger-only outfit is still banned.)
- CLOSE shot (~2 s): a close-up of the WORN outfit's detail (neckline / print / embroidery / sleeve / hem flare), her hand
  lightly showing it ("detail" gesture), face out of frame or cropped at the chin.
- Plain WORN shots with a gesture.
Suggested order (5 outfits, ~22-24 s footage, ~9 clips):
  O1 hanger -> worn | O2 worn -> close | O3 hanger -> worn | O4 worn | O5 worn -> close
Change the order if a product suits it better (e.g. the most detailed outfit gets the close-up). Every distinct product WORN.

## Row 195 (Kavya, Women's Western Wear)
- Persona personas/kavya.jpg. Home = realism.HOME_BG + HOME_VARIANTS[1] (light-blue wall, sofa with printed throw, floral
  curtains, wall clock, TV unit). NO decor (realism.NO_DECOR). Modest, everyday styling; simple flats/block heels.
- Dresses (check products/): p1 champagne satin cowl midi, p2 sage-green bodycon maxi, p3 printed satin maxi, p4 denim shirt
  dress with embroidery, p5 brown mermaid maxi. Close-ups: e.g. p4 embroidery, p1 cowl neckline / p3 print.
- Title board 1: head "Diwali Dress Edit", sub "Western Dresses · Sale Live". Music = batch_100.json row 195.

## Row 256 (Myra, a girl of ~7, Kids Clothing)
- Persona personas/myra.jpg. Home = realism.HOME_BG + HOME_VARIANTS[0] (cream wall, brown wooden wardrobe, grey sofa). NO
  decor. realism.CLIP_REALISM_CHILD (playful, filmed by a parent). Hanger shots: an adult's hand (mother) holds the hanger.
- Sets (check products/): p1 teal palazzo + printed long jacket, p2 orange set + jacket, p3 navy palazzo + printed jacket,
  p4 yellow mirror-work top + magenta sharara + dupatta (listing is on a hanger -> perfect for the hanger -> worn pair),
  p5 red peplum sharara set + dupatta. Close-ups: mirror work (p4), jacket print (p1/p3), peplum embroidery (p5).
- Title board 7: head "Kids' Diwali Looks", sub "Kids Clothing · Sale Live". Music = batch_100.json row 256.

## Folders
03_WORK/_approved_samples_GEST30/row_195/ and 03_WORK/_approved_samples_GEST30/row_256/ (brief.json with out_name ..._GEST.mp4, products/). Run scripts with
BBD_OUT="~/Desktop/Flipkart Fashion/01_DIWALI_REELS/03_WORK/_approved_samples_GEST30". Never touch 01_DIWALI_REELS/04_DATA/rows/row_NNN/ or REF30/.
Budget ~75 credits per row (Kling turbo 7.5 each). TrueFan plates first; Higgsfield nano_banana_2_1 if rate-limited.
