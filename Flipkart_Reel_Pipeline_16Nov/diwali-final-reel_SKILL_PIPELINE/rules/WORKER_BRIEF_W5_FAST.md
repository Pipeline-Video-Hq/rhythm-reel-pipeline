# Worker brief - W5 FAST (user 6-Nov: "qc was not good and was taking long, so do not qc, only take blunders in consideration for the regenerations")

Same pipeline as WORKER_BRIEF_W4.md (read it once for tools, folder, plates, clips, finish, usage rules) - ONLY the QC changes:

## QC = BLUNDERS ONLY (no full QC pass)
- Do NOT run the detailed QC: no visual_qc.py contact-sheet study per shot, no mouth/hand crops, no checklist ticking, no nitpicking
  (small lighting/colour drift, slight softness, minor shoe detail, background objects, a short smile = all ACCEPTED, keep going).
- Look ONCE at each plate (one glance at the image) and ONCE at qc/final_1fps.jpg after `pipeline.py finish N`.
- Regenerate (max 1 retake per shot) or trim ONLY for a BLUNDER:
  1. Extra or missing limbs / hands / feet (3 arms, 3 legs, a shoe on one foot only, fused feet).
  2. The product is missing, wrong (not the listing pair at all) or not visible in the shot.
  3. Face melts / turns into another person, or a body horror morph.
  4. Fire, diya or candle flame; nudity; readable garbage text big on screen.
  5. Final: wrong or missing title, missing Flipkart logo or end slate, final shorter than ~20 s.
- Anything else is NOT a reason to regenerate. Trim a bad second instead of re-rolling when possible.

## Everything else unchanged
Style per row (the prompt says it), Omni 1.1 360p NEWPROMPT clips, Nano Banana 2 plates, folder Flipkart_Fashion-Rhythm_AI_Profiles, footwear = every pair shown in
two hands then worn (knees-down, feet + shoes big), no unboxing, title = sheet text exactly, no upload, no sheet edits, one row at a time.
Rate limit: ONE timed wait (5/10/15 min) then check once; never loop-poll. If blocked twice, log BLOCKED + resume point and report.

Report per row in 3 lines: final path + duration, style, blunders fixed (or "none").

## NO ZOOM (user 6-Nov, PERMANENT, overrides "zoom punch-in" anywhere in the template/SKILL.md)
The zoom punch-in is a crop made at assembly (assemble.py "zoom"), and cropping a 360p clip makes it blurry. So: every plan.json segment
zoom 1.0, no zoom/zoom_y, never the same clip twice as a punch-in. Show the product big in the PLATE itself (knees-down framing, feet + shoes large)
or with a separate close-up clip. Keep the final >= 24 s with more/longer clips.

## NO PACKET / BOX OPENING (permanent - unboxing retired 3-Nov)
Ignore any "PACKET OPEN" / "BOX OPEN" intro in the row prompt's VARIETY line. Intros only: SHOWN in two hands, PICK UP from counter/shelf, or a use beat.
