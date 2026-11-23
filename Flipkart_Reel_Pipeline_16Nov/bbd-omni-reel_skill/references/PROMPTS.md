# Prompt patterns (Nano Banana plates + Omni 1.1 clips)

## Shot plan by reference format
| Reference format | Shot 1 (0-8 s) | Shot 2 | Shot 3 |
|---|---|---|---|
| talk_to_camera / number callout | persona full-length or mid, says the hook + first product, holding/wearing it | product 2 worn/held, hard-cut feel | product 3 + offer + CTA, smile |
| unboxing / try_on_haul | courier polybag held to camera, opens it, line 1 | wearing product 1, turns, line 2 | product 2/3 + CTA |
| mirror_lookbook (music) | mirror selfie, phone over face, look 1 | look 2 same mirror | look 3, phone lowered, smile |
| grwm | mid-routine at mirror/dresser, states occasion | product going on | final look reveal + CTA |
| fit_check (men) | chin-down/headless shirt-on, buttons, sleeve roll | mirror selfie, hand in pocket | turn + final pose |
| hands_demo / product_hero (home, makeup) | hands open packet / hold product to camera | product in use (bed made, curtain hung, swatch) | styled hero + offer |

Keep one set-up per row (same room) unless the reference cuts between rooms. Our room is an ordinary lived-in Indian flat, never the reference's room.

## Nano Banana plate (9:16)
```
Vertical 9:16 phone photo, first frame of a creator reel. <IMAGE_REF_0> is the creator: keep her/his exact face,
hair, skin tone and body (identity reference only - not the clothes or background). <IMAGE_REF_1> (and _2) are the
product listing photos: the product must match them exactly - colour, print, cut, packaging.
Scene: <one ordinary Indian home setting, time of day, light>. <Persona> is <action + framing copied from the
reference format>, <wearing / holding> the product. <realism.PLATE_REALISM - always, verbatim>
No text, no captions, no logos, no watermark, no other people, hands with five fingers.
```

Plates after s1: add plate s1 as <IMAGE_REF_1> ("the SAME woman/man in this reel's earlier shot: same face shape,
moles, freckles, nose stud, skin texture and tone - do not lighten or smooth") and describe the room as "exactly the
room from <IMAGE_REF_1>"; the product photo moves to <IMAGE_REF_2>.

## Omni 1.1 clip (generate_video)
```
<FIRST_FRAME> is the starting frame of this shot; continue from it exactly - same person, outfit, product, room, light.
<realism.CLIP_CAMERA>, <framing>. <Beat-by-beat action over 8 s with timings, including one small natural imperfection>.
Dialogue (she/he speaks to camera, lips in sync, natural everyday Hinglish, clear Indian accent, native Hindi
speaker, <voice description from personas/voices.json>): "<this shot's line from column K>"
Numbers are spoken as English words; never say a price. Speech starts within the first 0.5 s and ends by 7.5 s; no talking
before or after the line. Background: quiet room tone only, no music.
Keep the product identical to the first frame in every frame: same colour, print and shape. No text on screen, no
logos, no extra people, natural hands.
```
Music rows: replace the Dialogue block with "No speech. The creator does not talk; ambient room sound only."

## Voice descriptions (personas/voices.json)
Write one line per persona the first time it is used, e.g. "warm mid-pitch female voice, late twenties, friendly,
North Indian Hinglish" and reuse it word for word in every clip of every row with that persona.
- Omni 1.1 extension (previous_generation_id) with new dialogue fails: 'unable to process speech edits' -> one plate per spoken shot.

## Dialogue script (user rule, Oct 8)
Hindi words in Devanagari, English words + brand names in Latin, numbers as English words:
"भाई सुनो, Flipkart पर BBD live है, sports shoes का upgrade हो जाए?"
Append to every spoken-shot prompt:
"The Hindi words of the dialogue are written in Devanagari: pronounce them as natural spoken Hindi (e.g. मत = "mut", not the English word "mat"); the words in Latin letters (English words and brand names) are said the way an Indian speaker says them in English. Say every word exactly once, in this order; never repeat a word or phrase and add nothing else."
"Wardrobe stays exactly as in the first frame for the whole shot: same clothes, same shoes, nothing new appears on the clothes or body." (positive wording - naming "microphone" invites one)

## REALISM (permanent, user rule 27-Oct-2026)
"It is too perfect ... it seems AI ... we want it to look like a real person shot that video."
- Plates: append `realism.PLATE_REALISM` verbatim (scripts/realism.py). Room = lived-in, a few everyday objects, mixed light,
  slight tilt/off-centre framing, real skin, flyaway hair, creased fabric, relaxed non-model pose.
- Clips (Omni, Kling, music rows too): camera = `realism.CLIP_CAMERA` (handheld by a friend), end with `realism.CLIP_REALISM`.
  Put one small human imperfection in the beat list (hesitation, brushing hair back, glance off-camera, re-adjusting the product).
- Edit: assemble.py applies `realism.vf()` per segment (micro-shake, exposure/WB drift, grain, phone sharpening). Keep it on.
- Do NOT ask for an empty/plain top band for text - supers are white boxes and read over any background.

## ERROR GUARDS (permanent, user rule 27-Oct-2026)
- Plates: after PLATE_REALISM append `realism.PLATE_GUARD` (anatomy count, safe poses, product big and exact, campaign-fit outfit, no fire handling, fixed room).
- Clips: append `realism.CLIP_GUARD` before CLIP_REALISM. Beats: standing/walking/turning/sitting upright only; show the product, don't light anything.
- QC: `visual_qc.py <row>` then tick qc/visual_checklist.json honestly; assemble refuses otherwise.

## REAL HOME BACKGROUND (permanent, user rule 27-Oct-2026)
- Pass assets/refs/real_home_bg_ref.jpg as a background-style reference in plate s1, and add `realism.HOME_BG` to the prompt.
- The room is an ordinary lived-in Indian living room (cream walls, fan, tube light, wall TV + cables, switchboard, wooden sofa with floral covers, patterned carpet), with flat dim tube-light lighting.
- Festive extras are minimal (one marigold string, a few floor diyas). No decorated sets.
