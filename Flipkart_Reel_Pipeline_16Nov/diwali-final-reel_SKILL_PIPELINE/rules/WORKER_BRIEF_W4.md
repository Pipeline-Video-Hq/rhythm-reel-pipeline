# Worker brief - wave 4 (short version; same quality, same rules)

You make finished Diwali reels for YOUR 3 rows, ONE AT A TIME (finish row 1 through `pipeline.py finish` before row 2).

For EACH row N:
1. Read 03_WORK/_prompts/row_N.txt (the full instructions: shooting STYLE, title, rules) and 03_WORK/NEWPROMPT_360.md. Read 03_WORK/row_N/log.md first; reuse anything that passes QC.
2. TrueFan tools (load via ToolSearch: generate_nano_banana_image, get_image_status, generate_video, get_generation_status, upload_media, move_to_folder, list_assets). The connector may be named mcp__764b4a1c-...; use whichever TrueFan connector this session exposes.
   - Folder ALWAYS "Flipkart_Fashion-Rhythm_AI_Profiles" on every generate call; after every upload_media call move_to_folder the new ids there.
3. Plates: master plate alone first + QC, then the other plates queued together (wait_for_result:false) and collected with one get_image_status. Rate limit: wait 1 / 5 / 10 / 15 min, then Higgsfield account 1 nano_banana_2_1 only if its balance >= 20. If blocked, log BLOCKED + resume point and move on.
4. Clips: Omni gemini-omni-1.2-flash, 360p, 9:16, the NEWPROMPT block verbatim, folder as above. Submit all clips at once, collect with get_generation_status.
5. HARD RULES: NO unboxing / pouch / box opening anywhere (style D is retired); product clearly in frame in every shot; ARM TRACE every plate and clip (each hand -> its own forearm and sleeve, max 2 per person, no arm from a side edge); nobody speaks; no teeth; no diya, no phone lying around; footwear zoom 1.15-1.6, knee-down means feet + shoes big; title = the sheet text in the prompt; duplicate listings shown once.
6. QC cheaply: ONE combined contact sheet per shot (visual_qc.py output) + mouth/hands crops only where a face/hands show. Trim bad seconds instead of retaking; max 1 retake per shot.
7. Finish: `cd "~/Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts" && /usr/bin/python3 pipeline.py finish N`, tick qc/visual_checklist.json only after looking at the sheets, look at qc/final_1fps.jpg (title matches sheet, logo, white end slate, product in frame).
8. Do NOT upload to Drive, do NOT touch the sheet, never touch other rows. Never delete files that are not yours (move them aside instead).
9. log.md starts with "ENGINE: Omni 1.1 360p NEWPROMPT + STYLE <X>"; write "ARM TRACE: PASS sN" per shot.

Report in 6 lines per row: final path + duration, style, plate source, clips/retakes, QC issues, distinct pairs.

## USAGE RULES (user 3-Nov, permanent)
A. Row workers run on the cheaper model (Sonnet). The strongest model (Opus) is used ONLY for the final QC pass (main session or one Opus QC agent), never for making rows.
B. Rate limit / queue waiting: do NOT poll. When a TrueFan call is rate-limited or a job is queued, wait with ONE timed sleep (use `sleep 300`-style waits via a background command or the wait tool, 5 / 10 / 15 min) and check ONCE after it. Never check status over and over in a loop. Resubmit failed jobs once per wait, never a queued one.
10. LENGTH: each final >= 24 s total (>= 22 s footage + end slate): at least 2 shots per distinct pair (main + detail/zoom). Check final duration before reporting.
