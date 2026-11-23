---
name: beauty-flipkart-reel
description: Make a finished Flipkart Diwali ad reel (portrait 1080x1920, at most 30 s, music only) for one sheet row of five products, at 360p video generation, using the Omni connector. Use for any new or redone row, for makeup, fragrance, skincare, apparel, footwear, decor, furnishing and other categories, and whenever someone asks how these reels are made.
---

# Beauty / Flipkart reel pipeline (Omni, 360p)

One run = one sheet row (persona + avatar link + hook text + 5 Flipkart product ids + music only) = one finished reel.
Read first: `HOW_TO_RUN_THE_PIPELINE.md` (steps), `PROMPT_LOCKS.md` (locks 1-18), `PIPELINE_CONCEPT_LAB.md` (concept and creator-budget rules), `REALISM_RULES.md`, `CATEGORY_RULES.md` (what to do per product category).

## Standing rules (short)
- At most 30 s of footage including the 1.58 s Flipkart end slate; portrait 9:16 only; video generated at 360p only (upscaled to 1080x1920 in assembly); images gemini-3.1-flash-image 1K 9:16; model gemini-omni-1.2-flash; folder `Flipkart_Fashion-Rhythm_AI_Profiles`.
- Never generate anything without the user's approval; one take per image and per clip; never a last frame (first frame only); never pass a flawed frame as a reference.
- Creator budget: the creator's face in at most 2 clips (hook + the one application); every other clip is a hands-only product close-up, each product held a different natural way (unique show_device). Exactly ONE application per video; the application product is already open, the first frame has nothing applied, and the mark must really appear.
- Real, ordinary, neat middle-class HOME (never a kitchen, never a decorated set), a different room every video, a casual phone-video look (REALISM_RULES.md, lock 16/17). Hands match the avatar's skin tone, enter from the bottom or sides, one visible holding hand preferred, bottles gripped around the body (no diya hold), exactly two hands.
- Product text is an input (`product_text.json`, `product_text.py`); no opencv overlay; hard cuts only; CTA 'Shop Now on Flipkart' only in the last 2 s; no unverified prices or percentages on screen; camera nearly locked off with at most a 10 percent push-in.
- Music is ALWAYS upbeat and a different track every run: from an upbeat pack only (see PIPELINE_CONCEPT_LAB.md), recorded as `bgm_pack` and `bgm` in `concept_registry.json`.

## Stages
0. Concept card (`validate_concepts.py`) -> registry. 1. Products: manifest, claim check, `product_text.json`. 2. Avatar identity sheet + face anchor, empty-room plate. 3. Keyframes (hook, application, hands-only close-ups with `hands_prompt.py`, b-roll), gate every frame. 4. Action JSONs + `clip_frames.json`, `check_actions.py`. 5. `generate_clips.py <run> --dry` then `--confirmed` (all clips submitted together, then wait). 6. Assemble (`assemble_template.py`), hard cuts. 7. Log and copy the master to the output folder.

## Categories (details in CATEGORY_RULES.md)
- **Makeup** (lips, eyes, cheek, face), **Skincare, Grooming:** the creator hook, one application (product pre-opened), the rest hands-only close-ups.
- **Fragrance:** one spray on the wrist or collarbone, bottle pre-opened; bottles gripped by one hand around the body.
- **Apparel** (ethnic, western, kids): every outfit worn by the avatar; before-shot only a packet open or one hanger.
- **Footwear:** each pair shown in two hands then worn; no packet, no shoe box, no paper.
- **Home decor:** carry in and place; Diwali decor only here and in ethnic wear. **Home furnishing:** folded in hands, then the sheet already laid on the bed; never spread in the air.
- **Fashion wearables:** wrist or neck close-up, shown, then worn. **Kitchen, Household, Baby care, Toys:** hands-only demo, shown, picked up, used. **Pets:** outdoors on the home's lawn.
- Every category: the product is big and visible in every shot; two hands maximum; no fire handling.

## Commands
`python3 validate_concepts.py concepts_batch.json` | `python3 product_text.py <run> check` | `python3 hands_prompt.py <hold> [right|left]` | `python3 check_actions.py <run>` | `python3 generate_clips.py <run> --dry` | `python3 generate_clips.py <run> --confirmed [--stagger 15]`
