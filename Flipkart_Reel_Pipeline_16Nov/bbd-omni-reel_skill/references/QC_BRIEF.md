# Independent QC of one BAU reel

You are the QC reviewer for `row_NNN`. You did not make this video; look for problems, not reasons to pass it.
Read: `brief.json` (persona, script, offer, products), `products.json` + the product photos, the persona image,
`plan.json`, `qc/report.json`, and EVERY `qc/master_sheet_*.png` (4 frames/s; red boxes = where supers sit).
Optionally extract audio and listen via a transcript.

FAIL the reel (with timecodes and the shot to fix) if any of these is true:
1. Text over the product or the face in any frame (a red box touching either).
2. The person is not the persona (face/hair/skin drift between shots counts).
3. A product differs from its listing photos (colour, print, shape) or changes during a shot.
4. Any morph, melt, extra/missing fingers, warped face, flicker, frozen frames, or glitchy cut.
5. Voice rows: lips move without speech or speech without lips; words cut mid-word; a line missing vs the script;
   a non-Indian accent; the voice changes between shots; numbers not spoken as English words; ANY price spoken or shown on screen (rupee amount, MRP, strike-through) = FAIL.
6. Music rows: anyone speaking.
7. Any on-screen gibberish text, logos other than Flipkart's, Meesho/Amazon/Myntra, "link in bio"/"comment"/"DM".
8. Offer missing or wrong; CTA missing; end slate missing; loudness outside -16..-12 LUFS or true peak above -1 dB.
9. Length outside 15-35 s.
10. A super that is hard to read against what is behind it (e.g. white text on a cream wall): use a darker colour or the outline/pill style.
11. A word or phrase said twice in a row ("ek dum ready, ek dum ready", "bye bolo, bye bolo") or an ad-lib after the
    script's last line. `qc/report.json -> speech.repeats` lists machine-found repeats (FAIL level = must fix) and
    `qc/words_master.txt` has the word-timed transcript: read it against the script yourself as well.
12. The persona's own outfit, shoes, bag or accessories change between shots (e.g. grey trainers on his feet in
    s1-s2, white sneakers in s3). Look at the feet and clothes in every shot. Only the PRODUCT being shown may change.

Write `qc/verdict.json`: {"verdict": "PASS"|"FAIL", "issues": [{"t": "7.25-8.00", "shot": "s2", "what": "...",
"fix": "re-trim | move super | regenerate s2"}]}. Reply with the verdict and the issues in 5 lines or fewer.

13. LIMB COUNT (user 27-Oct-2026, row 79 had 3 legs at 14 s): in EVERY frame exactly 2 arms, 2 hands x 5 fingers, 2 legs, 2 feet - use the zoomed qc/vqc_sN_limbs.jpg sheets. Extra/merged/missing limb = FAIL, regenerate the clip.
14. Product shape in EVERY frame equals the listing (straps, toe-post, ornaments, print) and the product is large in frame.
15. Outfit fits the campaign (festive wear for Diwali) and the face is the same person in all shots.
16. Room continuity (no picture/idol/furniture appearing in one shot only) and plausible actions (no matches/lighters, no diya on cloth).
qc/visual_checklist.json must have every item true for every clip (assemble.py enforces it).
