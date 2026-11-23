Flipkart reel pipeline export - 16-Nov-2026
diwali-final-reel_SKILL_PIPELINE/  = the approved pipeline (SKILL.md, scripts/pipeline.py + assemble_fk.py, rules/, briefs/, examples/)
                                     Install: link it as ~/.claude/skills/diwali-final-reel
bbd-omni-reel_skill/               = engine scripts used by it (assemble.py, realism.py, visual_qc.py, products.py, board_title.py),
                                     brand assets (Flipkart logo + end slate), personas/. Install as ~/.claude/skills/bbd-omni-reel
02_BAU_DATA/                       = BAU tab 1500_1 data + helpers: worker_rules.txt (worker brief), prep_*.sh (fetch products +
                                     build prompts), qc_wear.sh / deliver_wear.sh (QC tile + Drive upload), film_titles.json, sheet row
                                     files, queues, batch logs, example worker prompts.
Run: FK_MODE=BAU /usr/bin/python3 pipeline.py addrows <rows.json> | new N | prompt N | finish N | upload N
Engine: TrueFan MCP (Nano Banana 2 plates + gemini-omni-1.2-flash 360p clips), folder Flipkart_Fashion-Rhythm_AI_Profiles.
Not included: music library (Desktop/Flipkart Fashion with Music), rclone config, work folders/videos. Paths inside the scripts point
at this Mac (~/...) - change them on another machine.

16-Nov: MAKEUP -> BEAUTY PIPELINE
beauty_pipeline/                   = the Beauty pipeline (copied from ~/Downloads/Beauty_Pipeline; holds .env with the Omni token - keep private).
Rows whose Vertical is "Makeup" (BEAUTY_VERTICALS in pipeline.py) are routed automatically, same commands as every other row:
  new N    -> row folder also gets the Beauty run layout (04_actions/, assets/*, exports/, 01_product_manifest.md, 08_run_log.md)
  prompt N -> Beauty worker prompt (sheet film text as header, BAU no-decor + real-home rules, assemble OUT = final/<out_name>)
  finish N -> runs the row's assemble.py (from beauty_pipeline/assemble_template.py), then the usual 480p + 01_LATEST_FINAL/Day N/Makeup
  upload N -> unchanged.
Override the Beauty folder with FK_BEAUTY_DIR=<path>. To route more verticals later, add them to BEAUTY_VERTICALS.

16-Nov: ONE PIPELINE FOLDER (no more ~, ~/.claude/skills or ~/Downloads paths)
Everything resolves from this folder (override with FK_PIPE=<path>):
  diwali-final-reel_SKILL_PIPELINE/  main pipeline (pipeline.py, assemble_fk.py)
  bbd-omni-reel_skill/               engine scripts + brand assets + personas (all 50 sheet personas present)
  beauty_pipeline/                   Makeup route
  assets/brand_beauty/               Beauty end slate, logo overlay, fonts (was ~/Downloads/flipkart-pipeline-final/assets)
  assets/music/rhythm_bgm_approved/  the ONLY music used: 22 approved RHY_BGM tracks (ask the team for the music folder).
                                     NOT approved, not downloaded: 001 002 003 011 013 014 017 019 022. Rotated by row.
  02_BAU_DATA/                       row data (pipeline.py DATA in FK_MODE=BAU)
  runs/BAU_1500_1/                   work folders (03_WORK) + finals (01_LATEST_FINAL) - created on first run
Still outside: ffmpeg, rclone (on PATH), the Omni token in beauty_pipeline/.env.
Backups of every edited file: *.bak_16nov_onefolder / pipeline.py.bak_16nov_beauty.

16-Nov: PRESENTATION APPROACHES A-E (REEL_PRESENTATION_IMPLEMENTATION_SPEC.md; Makeup skipped for now - Beauty route)
diwali-final-reel_SKILL_PIPELINE/scripts/approaches.py = every vertical family's 5 approaches, lettered A-E in the spec's order,
with women/men actions where the spec gives them. One approach per reel, applied to all 5 products (main + detail shot each),
30 s INCLUDING the end slate (per-product budget computed from the real end slate; finish refuses a file > 30 s).
  PER ROW (choose what each row uses): 02_BAU_DATA/row_approaches.csv - one line per sheet row (1400 rows, Makeup excluded),
               columns row,name,vertical,family,approach,options,delivered. Put A-E in "approach"; empty or HOLD = row on hold.
               Edit it in Excel/Sheets, or:
               FK_MODE=BAU python3 pipeline.py setapproach C 417 418 420-430   -> those rows use approach C
               FK_MODE=BAU python3 pipeline.py setapproach HOLD 425            -> row 425 on hold
               FK_MODE=BAU python3 pipeline.py approaches [C]                  -> per vertical: rows per letter + on hold [rows on C]
               FK_MODE=BAU python3 pipeline.py prompt <row>  -> refuses a HOLD row; prompt <row> D forces D for one run
               Each made row logs its letter in row_NNN/approach.json.
  Letters per family:
    ethnic            A mirror_try_on  B garment_showcase  C walk_pause_turn  D finishing_touches  E held_to_worn
    footwear          A standing_fit   B walk_stop         C seated_adjustment D side_back         E held_to_worn
    everyday_clothing A mirror_fit     B direct_fit        C walk_settle      D finishing_touches  E held_to_worn
    fashion_wearables A worn_check     B put_on_reveal     C feature_closeup  D natural_use        E held_to_styled
    home_decor        A place_reveal   B before_styled     C held_inspection  D room_to_detail     E styling_adjustment
    home_furnishing   A spread_smooth  B before_furnished  C fabric_fall      D everyday_use       E folded_to_place
    kitchen           A counter_demo   B preparation       C access_fill      D serve_present      E stored_to_ready
    household_utility A one_task       B task_before_after C feature_demo     D in_place           E retrieve_use_return
    baby_care         A caregiver_inspection B prepare_use C nursery_placement D feature_demo      E routine_preparation
    fragrance         A bottle_showcase B getting_ready    C application      D vanity_pickup      E ready_to_leave
    grooming          A mirror_routine B product_to_use    C feature_closeup  D finishing_touch    E shelf_use_return

16-Nov: MAKEUP APPROACHES (makeup_approaches.py)
32 makeup product types (from the PID's first 3 letters: LSK lipstick, KJL kajal, FND foundation, MCR mascara, PRM primer/fixer ...),
each with 5 approaches A-E of APPLYING it (tools/wipes/kits/bag: 5 ways of USING it). Per reel ONLY ONE product is applied;
the other four are shown as hands-only close-ups.
  Per row in 02_BAU_DATA/row_approaches.csv (Makeup rows 1002-1101): "approach" = A-E (empty = HOLD), "apply_slot" = 1-5 =
  which product is the applied one (pre-filled: the most visible type, lips > cheek > eyes > brows > base ...). "options" lists
  each slot's type.
    FK_MODE=BAU python3 pipeline.py setapproach B 1002 1010-1020   -> approach B
    FK_MODE=BAU python3 pipeline.py setslot 3 1060                 -> slot 3 is the applied product
    FK_MODE=BAU python3 pipeline.py prompt 1060 [E]                -> Beauty worker prompt with the makeup approach block
  Row 1025 has no PID in slots 2-5 - fix the sheet; the prompt refuses it.
