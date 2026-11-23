# OMNI 720p worker brief (user 3-Nov: "baki ki 9 videos truefan mcp omni 1.1 720p pe bana do")

Make ONE Diwali row end to end, same approved look and rules as the Kling pipeline, but the CLIPS are made on
TrueFan Omni 1.1 at 720p instead of Higgsfield Kling.

1. Get the row's full instructions: `cd "~/Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts" && python3 pipeline.py prompt <ROW>`.
   Follow it for everything (docs, shot plan, plates, plate QC, trims, zooms, title, QC, finish) EXCEPT the clip engine and the
   account rules below. Read the row's existing `03_WORK/row_<ROW>/log.md` and `work/` first: earlier workers already wrote shot
   plans, plate prompts, clip prompts and TrueFan reference asset ids - reuse them, do not redo the planning.
2. PLATES: TrueFan Nano Banana 2 (folder "Flipkart_Fashion-Rhythm_AI_Profiles", never test-test_diwali). TrueFan has been rate-limiting
   (IMAGE_RATE_LIMITED). Retry the same call after waiting 5, then 10, then 15 minutes. Only after that, fall back to Higgsfield
   ACCOUNT 1 `nano_banana_2_1` (mcp__higgsfield__*) and only while `mcp__higgsfield__balance` >= 20 credits; log every fallback.
   If both are unavailable, log "BLOCKED: plates" with the resume point and stop cleanly.
3. CLIPS: TrueFan `generate_video` (mcp__<omni-connector>__generate_video; load via ToolSearch):
   model "gemini-omni-1.2-flash", resolution "720p", aspect_ratio "9:16", folder "Flipkart_Fashion-Rhythm_AI_Profiles",
   duration_seconds = the planned beat length (3 / 4 / 5 s, finale 5 s), image_asset_ids = [the shot's plate asset id]
   (a TrueFan Nano Banana image_asset_id can be used directly; a Higgsfield plate must be uploaded to TrueFan first).
   Prompt = the planned clip prompt, starting with "The first image is the starting frame <FIRST_FRAME>." and adding
   "No speech, no dialogue, lips stay closed, no teeth. No on-screen text. Exactly two hands per person. Keep the product,
   face, outfit and room exactly as in the starting frame." Submit all clips in parallel; poll get_generation_status.
   A rate-limited Omni job is retried by the server - never resubmit it. Download to clips/s<N>.mp4.
   Max 2 retakes per shot, only for real defects (extra hand, broken feet/limbs, product changed, teeth, face change).
   NO Higgsfield/Kling clips at all.
4. QC exactly as the pipeline says (visual_qc.py sheets + checklist, 5 fps mouth crops, final_1fps.jpg). Omni clips carry
   their own audio: the finish step uses category music only, so make sure no Omni audio is left in the final.
5. Finish with `python3 pipeline.py finish <ROW>` (final 480p goes to 01_LATEST_FINAL as usual). Add a line "ENGINE: Omni 1.1 720p"
   at the top of log.md. Do NOT upload and do NOT touch the sheet (the main session does both).
6. Report briefly: final path + duration, Omni clips/seconds, retakes, plate source (TrueFan / Higgsfield fallback), QC issues.
7. Omni test lessons (row 100, 3-Nov): add "one continuous take, no cuts, no dissolves, no double exposure" to every clip prompt
   (a ghost cross-fade happened once); Omni walks more, so for worn/zoom shots ask "she stays on the same spot, small step only,
   feet fully in frame". ARM TRACE rule from the pipeline prompt applies to every plate and clip.
8. FOLDER (user 3-Nov: "jo folder diya tha usi main save karna image and video"): EVERY TrueFan image AND video goes in
   "Flipkart_Fashion-Rhythm_AI_Profiles". generate_* calls pass folder=...; files you upload_media (persona, listing photos, padded
   plates, Higgsfield plates) do not get a folder by themselves - right after uploading, call move_to_folder with their asset ids
   and that folder. Never leave any of our assets outside it.
9. BULK PLATES (user 3-Nov: "Haan, bulk karo"): make the master plate alone and QC it, then queue ALL remaining plates at once
   (generate_nano_banana_image wait_for_result:false, one call per plate, no waits between) and collect them with ONE
   get_image_status call over every image_job_id. Up to 10 render at once; never resubmit a queued/running job. Resubmit only
   the ones that come back IMAGE_RATE_LIMITED, after ~1 min; use the 5/10/15-min waits only if they keep failing. The Gemini rate
   limit is shared with other TrueFan projects on the account (e.g. Bajaj-BFL_ORM bulk runs).
