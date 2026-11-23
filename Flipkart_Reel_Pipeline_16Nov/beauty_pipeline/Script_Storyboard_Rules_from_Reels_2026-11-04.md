# Script and storyboard rules from 3 newly downloaded reels (2026-11-04)

Reels read from contact sheets (12 frames each) plus cut detection. Only 3 of the 5 requested were in Downloads. Combine with `Reference_Reels_Analysis_2026-11-02.md` (11 reels).

| # | Reel | Length | Cuts | Face | Hook (on first frame, stays all reel) |
|---|---|---|---|---|---|
| A | Mamaearth Mocha Nude lipstick (@shubhisrivastava__) | 20 s | 6 | yes, talking | "This is the only lipstick you need" |
| B | MARS lip combo (@shop_withjoy1) | 10 s | 1 | no, hands only | "MARS Lip Combos" |
| C | Minara eyeshadow combo (@liferesetblog) | 48 s | 1 | no, hands only | "FLIPKART / Eyeshadow Combo Under ₹160" |

## What each one does

**A, one product, three uses.** Shows the tube, applies to lips, then blush on the cheek, then an arm swatch. Same product, new use every ~3 s. The hook is a claim ("only lipstick you need"), and each beat proves it.

**B, hold the set, then one beat per item.**
- Opens holding the full combo to camera and keeps it for the first ~4 s.
- Then one beat per product: the lipstick close-up with a chip ("Rich · Matte · Pigmented"), the liner close-up with its shade name, and a back-of-hand swatch.
- Closes on a re-hold of the set with a "Perfect Berry-Brown Combo" label and "Comment for Link".
- Product hero shots are very tight (tube fills the frame).
- Label chips sit low in the frame, not over the product.

**C, Flipkart packet to payoff.**
- Opens by tearing the Flipkart packet.
- A Flipkart listing card (Bestseller, rating, ₹155) and an "Order Confirmed" screenshot pop in as trust beats.
- Slow unwrap, then open the palette, then hand swatches, then a top-down shade grid.
- The long take works because something visibly changes every 2–3 s.

## Hard limit: cost
**Maximum 30 s of footage per video, end slate included.** Generation cost scales with seconds, so the storyboard must total at most 30 s. Target 15–25 s (the reels run 10–20 s). Budget with clips, not scenes: **clip length is dynamic**, set by how much action the clip holds (typically 4–6 s, several actions per take, e.g. two swatches with a product swap). Avoid many 2–3 s clips; they cut too often.

## Rules for the script writer
1. **Hook:** one line, on the first frame, on screen the whole film. It must be a claim, a price shock or a set name. It must not be a greeting.
2. **One idea per film.** For a set, the idea is "all of these, one look". For a single product, it is "one product, three uses".
3. **One beat per product, 2-3 s, one proof each.** The proof is a swatch, a close-up with a 3-word chip, or a use. A product never gets a beat with nothing visible changing.
4. **No spoken line is ever acted out.** Voiceover is separate from the picture. Chips carry the words, so each chip is at most 4 words: brand + shade or a 3-word spec (e.g. "Rich · Matte · Pigmented").
5. **Claims:** use only listing facts (shade name, "matte", Bestseller). Do not invent benefits.
6. **End:** the whole set shown together, then a "Shop Now on Flipkart" or "Comment for Link" style call to action.

## Rules for the storyboard writer
1. **Order:** hold the full set first, then one beat per product, then re-hold the set with the call to action.
2. **Shot size:**
   - Medium: the set held to camera.
   - Extreme close-up: each product hero. The tube fills the frame.
   - Macro top-down or 45-degree: swatches.
3. **Swatch beats:** one stroke per beat, on the back of the hand or inner forearm. Each swatch is edited from the previous plate so earlier swatches persist, building to a final row.
4. **Flipkart trust beats** (use 1–2, not all): packet tear opener; listing card with rating; order-confirmed card. Cards are overlays and never AI-generated text.
5. **Pace:** a visible change every 2–3 s. Long takes are fine only if the content changes (a stroke being drawn, a blend).
6. **Overlays:** the hook stays on the whole film. Chips sit in the lower third and never cover the product label. Use one accent colour for chips.
7. **Every scene gets an `action_input.json`** (see `action_input.example.json`) describing each hand movement step by step, so Omni does not improvise.
8. **Hands:** two hands maximum; one operates the product and the other is the passive target. Nails identical across all scenes.

## What to change in the current Ritu and Aishwarya storyboards
- The Ritu storyboard (S01–S07) uses the face as the hero. Reels B and C are hands-only, which also avoids face/lip-sync artefacts. Convert the lip product beats to hand swatches, and keep Ritu for the opener and call to action only.
- It has no set hold or re-hold on the product for the call to action. Add both.
- It has no Flipkart packet or listing-card trust beat. Add one.
- Chips are written as full product names. Cut them to at most 4 words.

## Application-shot rule (generalised, user feedback 2026-11-04)
Show every product being USED on the body part it is made for, as a cinematic close-up, not as a swatch on the arm or hand. The arm swatch is only a secondary proof when the product cannot be shown in use.

| Product type | Hero application shot (cinematic extreme close-up, shallow depth, slow motion) |
|---|---|
| Lipstick, lip liquid, lip liner | the tip gliding across the lower lip, then the finished lip colour with a closed smile |
| Foundation, concealer, cushion | a slow blend on the cheek, skin evening out |
| Blush, highlighter | a sweep on the cheekbone catching the light |
| Eyeshadow palette | a fingertip or brush sweeping colour onto the closed eyelid |
| Kajal, eyeliner | a single line drawn along the lash line |
| Mascara | the wand through the lashes, eyes wide |
| Nail paint | a brush pulling colour across the nail, the finished nail held to the light |
| Skincare (cream, serum) | a fingertip touch and a spread across the cheek, glow on the skin |

For a set with several products, each product gets its own application beat; the finished look of the previous beat carries into the next.

## Mandatory b-roll (user feedback 2026-11-04)
Every video includes one product b-roll clip, 3-5 s, with no avatar: a slow cinematic macro pass over all the products so each one is seen in detail (shape, colour, label). Count it in the 30 s cap.

## Other standing rules
- One product on the table per round; never a crowded row except the hook and b-roll frames.
- First and last frame generated for every clip; each frame generated fresh with the identity sheet, the master face frame and the product photo attached.
- Keep the same side of the hand or arm toward the camera in every frame if an arm is shown.

## Camera direction rule (mandatory, every clip)
Every video prompt and every action file states a camera movement for EVERY step: shot size, angle, movement (push-in, pull-back, lateral dolly or pan, rack focus, locked off), speed, and where the camera ends. Never leave the camera to the model. Typical moves: slow push-in on faces, hard cut to an extreme macro with a slow lateral drift for application shots, a constant-speed lateral pan for product b-roll, lock off on the last frame. In `action_input.json` each step has a `camera` field, and the prompt builder prints it first.

## Portrait only (mandatory)
Every image and every video is 9:16 portrait. Never generate a 16:9 or any landscape image, not even as a source plate for crops.

## B-roll rule (updated, portrait)
Generate ONE portrait 9:16 master image showing all the products in detail at their true relative sizes (for example the tubes standing in a back row and a long flat tray lying across the front). The clip's first frame is the full master and its last frame is a zoomed window cut from the same master (ffmpeg crop, upscaled), so the camera does a slow push-in plus lateral drift across the products. Never generate separate b-roll images per product group: they drift in size and shape.

## Product scale and shape consistency (new)
Before approving any frame set, check each product's size, shape and orientation against its listing photo AND against every other frame where it appears (for example a set of 10 minis is one long flat tray with ten minis, in every shot). A product must not change size or shape between clips. Check dimensions and orientation, not only colour and label.

## Cuts inside a clip (user feedback 2026-11-04)
No jump cuts inside a clip at intervals under about 3 s. Prefer one continuous camera move (for example a smooth push-in from a medium-close to a macro on the lips) over cutting between shots. An application shot (the product on the lips, cheek, eye) lasts at least 2.4 s and is continuous. Cuts belong between clips, roughly every 4 s or more. The clip's last frame is the tight finished-look shot, not a return to the wide shot.

## No product morphing, no swaps (user feedback 2026-11-04)
Products must never rotate, slide, swap hands or turn into different bottles inside a clip. A hook or b-roll clip holds its products perfectly still and only the camera and the person's expression move. Do not write steps like "slides two products forward" or "passes the second product into the same hand". If two products must be used in one look, use one clip per product, each with its own first frame, or keep the second product out of the action.

## B-roll (final rule)
No landscape plate and no ffmpeg pan. Generate ONE portrait 9:16 master image of all products in the row's own set, then ONE Omni clip from that first frame only (no last frame), with a camera-only move (slow push-in and lateral drift over still products).

## Last frames (final rule)
Do not send last-frame images to Omni (they cause a visible snap in the final frames). Send the first frame only and describe the end state in the prompt. If an older clip already has the snap, trim its last 3 frames in assembly.

## Showing products vs using one (user clarification 2026-11-04)
When the avatar presents or shows the products (hook, close, b-roll), ALL the row's products stay on the table, exactly five, never just one. During a single lip application only the product in use moves; the other products stay in the frame, perfectly still, and are never removed.

## Keyframes: first frames only (final, user 2026-11-04)
Never generate a last-frame image. The keyframe set is: one master face frame, one FIRST frame per clip (its start state: product in hand, lips in their pre-application state), and one portrait b-roll master. The end state of each clip is described in the prompt text only. This saves images and removes the snap at the end of clips.

## Application clips: stroke-in-progress first frame (CONFIRMED by the user's test on ID 50 lips, 2026-11-04; standing rule for every row)
Problem seen in ID 50: with a first-frame-only clip the product is either never applied (the clip is spent on the approach) or looks already applied. Fix: the first frame shows the product ALREADY touching the skin with only a short trail of colour laid down (the first centimetre of the swipe), the rest of the zone clean; the clip starts mid-gesture (approach at most 0.3 s); the prompt says colour builds only along the path of the tip and clean skin ahead of the tip stays clean until the tip reaches it. Prefer high-contrast zones (lips, eyelid); show cheek colour as a clearly visible stripe that gets blended. One take per clip only; never queue multiple takes.

## Generation cost (user 2026-11-04)
Never increase generation cost: one take per clip (generations = 1), no extra variants or re-rolls unless the user asks, no extra images beyond the planned set.

## CTA timing (user 2026-11-04)
"Shop Now on Flipkart" appears only in the last 2 s of footage, right before the end slate, never earlier.

## Proportions, duplicates, natural gestures (user feedback 2026-11-04, ID 51)
- PROPORTION LOCK: her face, head size and body proportions, and every product's size, stay identical across all frames of a run (see PROMPT_LOCKS.md); frames are generated from the master frame crop plus the identity sheet so the face does not drift.
- NO DUPLICATES: a product she holds is not also on the table; each product appears once; the visible count is exact.
- NATURAL GESTURES: no spraying or applying on the head, no arm above the head. Fragrance spray targets: inner wrists, neck and collarbone, clothes or dupatta, or a mist in front of her chest that she steps into.

## ONE application per video (user 2026-11-04, supersedes "show every product on its body part")
She applies a product ONCE AND ONLY ONCE per video. All other products are only SHOWN (held up, label turned to camera, tilted, opened, fingertip brushed along, laid in a row). See "Application budget" in PIPELINE_CONCEPT_LAB.md. Applies to every row and every category (lip, cheek, eye, fragrance).

## Zoom during application (user 2026-11-04, supersedes the extreme close-up and macro rules above)
No extreme close-ups. During an application the camera tightens by at most about 20 percent, at constant speed, from a medium-close to a close-up of the face; her face and the applied area both stay in view. Wherever older rules say 'push-in to an extreme close-up' or 'macro', use this instead.

## Canonical plates for complex products (user 2026-11-04)
Sets, kits and boxes (for example the Just Herbs set of 10) change shape, colour and count from frame to frame when each frame redraws them from a listing photo, and sometimes appear twice. Fix: one approved canonical plate per complex product, used as the reference in every frame; exactly one instance per frame; see PIPELINE_CONCEPT_LAB.md.

## Open the product on camera (user 2026-11-04)
For realism the avatar opens boxes, caps and bullets herself: lid lifted, cap removed and held, bullet twisted up. First frame closed, end state open in the prompt. A set or kit has two canonical plates (closed, open) of the same object.

## Zoom minimum (user 2026-11-04, supersedes the 20 percent rule)
Camera movement is kept to a minimum: nearly locked off, at most a barely noticeable push-in of about 10 percent over a clip. No zoom, no macro.

## Each product shown in a different way (user 2026-11-04)
No two products in one video are shown with the same gesture or framing; see "Distinct show devices" in PIPELINE_CONCEPT_LAB.md. The single application is also its own distinct beat.
- Open-state spec (user 2026-11-04): clips that open something carry opens + open_state_ref; see PIPELINE_CONCEPT_LAB.md.


## Creator budget (user 2026-11-05, tested on ID_16)
The creator's face is on screen in at most 2 clips: the hook and the one application. The product used for the application is already OPEN before the clip (cap off, tip at the skin, stroke in progress) so there is no opening action. Every other clip is a tight product close-up (top-down, close framing from the start, zoom <= 10 percent) with the product held in her hands (hands and forearms only, face not visible, same outfit), each held a different way (show_device). Home setting, empty-room plate for the two creator frames, close-ups on the same cloth.
