# Worker brief - batch 6 wave 2 (3-Nov), 6 workers x 3 rows

Make finished Diwali reels for YOUR rows, ONE AT A TIME in order. Finish one row completely (through `pipeline.py finish N`) before starting the next.

For EACH row N:
1. Read the full instructions in 03_WORK/_prompts/row_N.txt and follow them. That file now carries:
   - the ENGINE line: Omni 1.1 360p NEW PROMPT, bulk plates;
   - this row's SHOOTING STYLE (A/B/C/D/E), which wins over the base shot template;
   - the title taken from the sheet;
   - all the rules.
   Then read 03_WORK/NEWPROMPT_360.md and 03_WORK/OMNI720_BRIEF.md (tools, folder, rate limits, bulk plates). Clips are 360p, NOT 720p, with the NEWPROMPT block verbatim.
2. Tools: the TrueFan connector is mcp__<omni-connector>__*. Load these via ToolSearch: generate_nano_banana_image, get_image_status, generate_video, get_generation_status, upload_media, move_to_folder, list_assets.
   - The folder is ALWAYS "Flipkart_Fashion-Rhythm_AI_Profiles". It is already confirmed, so never ask.
   - Move every uploaded reference into that folder.
   - To get a local file in, call upload_media with method "service_command" and run the curl it returns.
3. Bulk plates: make the master plate alone and QC it, then queue all the other plates at once with wait_for_result:false and collect them with ONE get_image_status call.
   - Six workers share TrueFan's 10-image slot, so jobs may sit queued. Never resubmit a queued job.
   - Rate limit: resubmit only the failed ones after about 1 minute. Then wait 5/10/15 minutes. After that, fall back to Higgsfield account 1 nano_banana_2_1, but only while its balance is 20 or more.
   - If you are blocked, log "BLOCKED" with the resume point, move on to your next row, and come back later.
4. Style notes:
   - A: mirror selfie, phone in front of the face, outfit worn. The mirror shows only her; the phone is plain with no logo.
   - B: headless fit check from the neck down. For footwear, knee-down only.
   - C: hands-only demo.
   - D: plain grey courier pouch with no logo, opened by two hands, then the product. Footwear is then worn knee-down.
   - E: room before/after, same framing.
   - Every style: ARM TRACE, product always clearly in frame, nobody speaks, no teeth.
5. Earlier workers found these problems; check for them on every plate and clip:
   - Lit diyas or clay diyas in the decor: remove them.
   - A phone lying on a table or sofa: remove it, except the mirror-selfie phone in style A.
   - Head too high in a full-body plate: pad and outpaint.
   - A hand resting on the belly, which reads as pregnancy: edit or trim it out.
   - A bindi or jewellery appearing mid-clip.
   - Teeth.
   - Duplicate listings, meaning identical photos: show the item once and note it.
6. Finish with `cd "~/Desktop/Flipkart Fashion/01_DIWALI_REELS/02_SKILL_PIPELINE/scripts" && /usr/bin/python3 pipeline.py finish N`. Fill qc/visual_checklist.json only after you have looked at every visual_qc sheet. Then look at qc/final_1fps.jpg and check that the title matches the sheet title in the prompt.
   - Do NOT upload to Drive and do NOT touch the sheet.
   - Never touch rows that are not yours.
7. Start each log.md with "ENGINE: Omni 1.1 360p NEWPROMPT + STYLE <X> (user 3-Nov)".

Report back briefly per row: final 480p path and duration, style, plate source, clip and retake counts, QC issues, distinct outfits or pairs, or the exact BLOCKED point.

## Lessons from wave 2 (apply from wave 3 on)
- NB often adds an UNLIT clay diya on windowsills/rangoli in every plate (even NO_DECOR rooms): check every plate; if NB edits will not
  remove it, fix locally and re-upload (move to the folder).
- Footwear: Omni flips a shoe to show a branded insole near the end of pouch clips -> cut before the flip. Zoom >1.6 crops shoes at the
  sides -> keep footwear zooms 1.15-1.6. Feet crossing / overlapping during heel turns -> trim.
- Hand drifting to the stomach is the #1 defect on women: write "hands never rest on the stomach or belly" into every plate and clip
  prompt; trim any range where it happens.
- Listing photos that show TWO pairs (combo) -> use the pair that matches the listing title/first photo, note it in log.md.
- Style C (hands-only): no face, no body above the forearms; product used/demoed on a table, sofa or bed.
