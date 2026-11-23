> **30-Oct OVERRIDES (read first):** Higgsfield = ACCOUNT 1 (`mcp__higgsfield__*`) for plates + clips; account 2 only as fallback. Home = CLIENT-FINAL row 195 v2 class, a different room per video (realism.HOME_V2 + HOME_V2_ROOMS + HOME_V2_REF as style ref). Paths: see ../SKILL.md (01_DIWALI_REELS/00-04). The worker prompt from `scripts/pipeline.py prompt <row>` wins over anything below.

# NEXT 6 rows (29-Oct-2026): the row after each approved sample = 4, 81, 170, 272, 425, 473
Per-row data: batch_next6.json (name, vertical, theme, decor, title, font, treatment, music, hv = home_variant, persona link, products). brief.json is in each row_NNN/.
ALL rules of BATCH_100.md apply (worn clothing, every distinct product shown, footwear format + FOOTWEAR_BEAUTY, no paper, 2 hands / no selfie, lips closed, no price/%, 480p, title rules, QC gate, assemble command). Look benchmark = the 6 client-approved samples (rows 3, 80, 169, 271, 424, 472: see their plan.json/log.md; frame sheets in SAMPLES_29oct/approved6_frames/).

## NEW CLIENT FEEDBACK #3 (29-Oct, PERMANENT) - "make sure AI video na lage, real lage"
realism.py now holds it (HOME_BG, HOME_VARIANTS, PLATE_REALISM, CLIP_CAMERA, CLIP_REALISM, CLIP_REALISM_CHILD were redefined at the bottom of the file). Paste them VERBATIM. In short:
- HOME: a REAL LIVED-IN home, decent and nice, between the approved samples' middle-class home and the polished Tier-2 home. Simple almari, ordinary curtains, a plain wall. NOT designer headboard + frames + plants + cove lights all together. A FEW everyday things lying around (charger, bottle, tilted cushion, cloth on a chair), but not clutter. Use HOME_VARIANTS[hv].
- LIGHT: normal home light (window daylight / ceiling bulb), with natural shadows and uneven light. Not even studio light, not dark.
- PERSON: natural expression (soft half-smile, glances to the side, as if mid casual chat but LIPS DO NOT MOVE), NOT a fixed model smile or pose. REAL skin (pores, uneven tone, no glow/airbrush). Natural hair, not perfectly set. Home-worn clothes with creases. Relaxed hands holding the product casually, never standing stiff.
- CAMERA: phone held in hand, light shake, subject a little off-centre, not cinematic. NORMAL phone colours: no saturation boost, no HDR, no glossy grade. (assemble's vf now adds a slightly stronger handheld shake.)
- Decor: as in batch_next6.json (decor true only for 4 Ethnic and 473 Home Decor: small, ordinary, no lit diyas). Otherwise NO_DECOR.
- Do NOT reuse any old plate/room of row 4 (move old plates/clips to old_pre_fb3/).

## Clips
- Higgsfield SECOND account ONLY: mcp__<omni-connector>__* (load via ToolSearch). Never the mcp__higgsfield__* tools (empty account).
- Model: kling3_0_turbo, 720p, duration 5, 9:16, sound off, count 1, use_unlim false. Trim each to about 3.5-4 s. Max 2 jobs in flight per worker. Decline preset suggestions.
- Plates: TrueFan generate_nano_banana_image first (free). If rate-limited, use the second-account Higgsfield nano_banana_2_1.
- Budget: max 80 credits per row.

## Persona
~/.claude/skills/bbd-omni-reel/personas/<name>.jpg. Rishi (row 170) is missing: download it from the persona link (Drive uc?export=download&id=...) and save it as personas/rishi.jpg.

## Kids rows
- Row 170 (Rishi, an adult man) shows KIDS' running shoes: he HOLDS and shows each pair, never wears them, and the close-ups are hands-only (like approved row 169).
- Row 272 (Diya, a child) WEARS each outfit; use CLIP_REALISM_CHILD.

## Output
- row_NNN/final/<out_name> plus the _480p.
- Copy the 480p to NEXT6_29oct/ (not to FINAL_480p_category_wise).
- No Drive upload, no sheet edits.
- Log everything in row_NNN/log.md under "## NEXT6 29-Oct".
- Report each finished row to main: path, credits, doubts.
