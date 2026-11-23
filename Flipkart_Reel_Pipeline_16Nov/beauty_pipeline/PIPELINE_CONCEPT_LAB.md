# Pipeline stage 0: CONCEPT LAB (mandatory, runs before any storyboard or generation)

Why: rows were coming out as the same video with different faces and products (same vanity, same fairy lights, same maroon kurta, same one-product-at-a-time showing). This stage makes that impossible.

## Steps
1. Read `concept_registry.json` (every concept already used) and the other rows in the same batch.
2. For each row write THREE different concepts with different archetypes (below). Each concept fills every field of the concept card.
3. Run `python3 validate_concepts.py concepts_batch.json`. It fails if any concept repeats a set, wardrobe colour, structure archetype, light, hook device or palette from the registry or from another row in the batch, or if the structure is a serial one-by-one showing.
4. The user picks one concept per row. Only then write the storyboard. After the video is approved, add the concept to the registry.

## Concept card (all fields required)
`row, persona, archetype, hook_device, set (location), wardrobe (colour + garment), light (time of day + colour), palette, camera_language, product_interaction (how products appear: combined, layered, packed, mixed ... never serial one-by-one), signature_moment, music_mood, ending`

## Archetypes (pick one; a serial showing of one product per beat is NOT allowed)
- **Layered look build**: one look built layer by layer from several products (liner + lipstick + gloss), looks combine products.
- **Day to night**: the same face, three looks, time and outfit change through match cuts and light changes.
- **Pack with me**: she packs a Diwali gift hamper in the Flipkart bag; kits and products are handled together, one lip look at the end.
- **Mix and match**: two shades blended on the lips or a palette made on her fingertip; combinations are the point.
- **Mirror reveal**: before and after in one continuous mirror move.
- **Shade roulette**: a game structure with a twist (used once for Ritu, now in the registry; do not repeat).
- **Festive moments**: each product lives in a different festive moment (a different room, outfit and light per moment).
- **Close-up film**: pure macro lip, skin and texture, with the avatar in two or three wide cutaways.

## Hard rules (also enforced at review)
- Different set, wardrobe, light, palette, structure and hook device per row; the hook line from the sheet stays verbatim.
- Products appear combined, layered, packed or in motion, not one after another with the same framing.
- No jump cuts inside a clip under 3 s; the application shot is at least 2.4 s and continuous; use push-ins and pans, not cuts.
- Portrait 9:16 only (the b-roll plate for the ffmpeg pan is the only landscape exception); camera movement stated for every step; both first and last frames generated; face-forward, avatar prominent; product scale and count checked across frames.
- Music only unless the row says voiceover. Max 30 s including the end slate. Ask before any generation.

## Stage 0b: action sanity check (mandatory, after the concept, before the storyboard)
List every action in the storyboard and justify each as a natural everyday gesture. Then run `python3 check_actions.py <run folder>`. It fails any phrase like "above her head" / "over her head" / "arm raised". Fix the storyboard until it passes.

## Prompt locks (mandatory)
Every image and video prompt carries the three locks in `PROMPT_LOCKS.md`: PROPORTION LOCK (her face and every product keep identical proportions), NO DUPLICATES (a product in her hand is never also on the table; exact product count), NATURAL GESTURE. `omni.py` adds them to every clip prompt automatically.

## Application budget (mandatory, user rule 2026-11-04)
Each video contains exactly ONE application of ONE product (the hero beat): one lip swipe, one cheek blend, one spray. Every other product beat is a SHOW beat: she only presents the product: holds it up and turns the label to the camera, tilts it to show size and shape, brushes a fingertip along the bottle or tube, opens the lid or twists the bullet up, rests it in her palm, sets it down in a row. No second application, no swatch, no spray, no blend for any other product.
- Concept cards carry `application_count` (must be 1), `apply_product` (which product is applied) and `show_device` (how the other products are shown). `validate_concepts.py` rejects any other count.
- Action files carry `"beat_type": "show"` or `"apply"` per clip. `check_actions.py` fails a run unless exactly one clip is `apply` and every clip has a beat_type.
- The single application gets the full cinematic treatment (stroke-in-progress first frame, 2.4 s or more, constant-speed push-in). Show beats stay calm: one product at a time in her hand, held still or slowly turned, with natural gestures only.

## Zoom limit (user 2026-11-04)
The push-in during an application is small: total framing change at most about 20 percent, constant speed, no extreme close-up or macro (the older 'push-in to an extreme close-up' wording is retired). Her face and the area being worked on stay in view. Lock 4 in PROMPT_LOCKS.md; `omni.py` adds it to every clip prompt.

## Canonical product plates (user feedback 2026-11-04, the set of 10 box)
A complex or multi-part product (a gift set, a kit, a box with a separate lid and tray) gets ONE canonical plate before any frame uses it: a product-only image on a clean background that matches the listing photos exactly (parts, colours, count, label), approved by the user. Every frame then uses that plate as its reference, never the raw listing photo, and the product appears exactly once per frame (never a second box or a second copy). Without an approved plate, a complex product is not generated in any frame.

## Open it on camera (user 2026-11-04)
Anything that comes closed is opened by her on camera before it is shown open or used: she lifts the box lid, pulls the cap off and holds it, twists the bullet up. The first frame shows the product closed (cap or lid on); the open end state is written in the prompt; each opening is one smooth natural gesture. For the single application she uncaps or twists up the product first. Complex products need a canonical plate in BOTH states (closed and open) that match exactly.

## Open-state spec (user 2026-11-04)
Every clip whose action opens something (lid, cap, bullet) must carry `opens` (what opens) and `open_state_ref` (an Omni asset id of an open-state image of that exact product: the open canonical plate for sets, or one generated open-state frame for a tube) in its action JSON. The clip prompt lists the open end state and the open-state asset is attached as a second reference alongside the first frame. Generating an open-state image costs one extra image per openable product and needs user approval first. check_actions.py fails any clip with `opens` but no `open_state_ref`.

## Distinct show devices (user 2026-11-04: "each product should be shown and flaunted in a different way, that's the kick")
Every show beat uses a DIFFERENT way of presenting its product. No two products in a video are shown with the same gesture, pose or camera framing. Pick one device per product from this catalog (or invent a new one), never repeat a device inside a run:
- balanced on her open palm, tilted toward the camera, a fingertip gliding along it
- held between two fingers at eye level, turned slowly to catch the light
- cradled against her collarbone or cheek like a treasured thing
- opened on camera: lid lifted, cap twisted off horizontally with both hands, bullet twisted up
- held up beside her face as a colour match to her skin, lips or outfit
- lifted out of its box or pouch and shown as a reveal
- fanned or stacked with its siblings in her hands
- shown against her outfit or a swatch of fabric
- set down into a row on the table with a small flourish of the hand
- a size comparison: held next to her fingers, palm or a flower
- shown through a mirror reflection
Concept cards carry `show_devices` (one entry per product, all different). `validate_concepts.py` rejects duplicates; action files carry `show_device` and `check_actions.py` rejects a run where two show clips share one. The first frame of each show clip must already stage its own device (different pose, different framing, different hand), so clips do not look alike.


## Framing lock and duplicate gate (user 2026-11-05)
Hook and later frames share one camera framing (PROMPT_LOCKS.md lock 5). Each frame lists held products and the table products; count each product once before any clip is generated, and re-roll the frame (user approval) if one is duplicated. Prefer a hook that lays out fewer products so removing the held one is unambiguous.


## Room setting is always selected (user 2026-11-05)
Every run starts by choosing ONE room setting (the card's `set` field: room type, wall colour, window side, furniture, props, light) from the catalog below or a new one, unique across the registry (validate_concepts.py already rejects repeats). It is then locked: generate ONE empty-room plate (no person, no products, the table or surface in the exact camera framing used by every frame) and use it as the base reference of every keyframe, together with a per-frame table plate listing exactly which products sit on the table. Never take the room from the hook frame or an earlier frame (the model copies stray objects such as a chair or the held product back in). Catalog: terracotta art studio with paint-splattered wood table; festive vanity corner with fairy lights; sunlit rooftop terrace with rangoli; marble hall with chandeliers; white-tile balcony with plants; cosy bedroom dressing table; bright kitchen counter with brass diyas.


## Different BGM every run (user 2026-11-05)
Each run uses a track no earlier run used. Tracks come from the zip packs in <pipeline folder>/assets/music/rhythm_bgm_approved (Rhythm sheet: ONLY these approved RHY_BGM tracks, bgm_pack = rhythm_bgm_approved) (unzip into the run's assets/bgm, keep the pack and file name). Record the choice as `bgm` in the concept card and concept_registry.json and check the registry before picking. Used so far: "Diwali Celebration A" (ID_1, ID_35, ID_45). Pick the pack by mood (festive, fashion/upbeat, acoustic/playful), then a track not in the registry.


## Background is always a home (user 2026-11-05)
Every room setting is a real lived-in HOME interior (living room, bedroom dressing table, home kitchen counter, study desk, home balcony or sit-out), with believable home props (sofa, curtains, family photos, plants, lamps, cushions, tea cups). No studio sets, halls, rooftops, venues or showroom looks. Pick a different home setting per run from this list, locked with the empty-room plate. The earlier catalog entries that are not homes (art studio, marble hall, rooftop terrace) are retired.


## Creator budget (user 2026-11-05, tested on ID_16)
The creator's face is on screen in at most 2 clips: the hook and the one application. The product used for the application is already OPEN before the clip (cap off, tip at the skin, stroke in progress) so there is no opening action. Every other clip is a tight product close-up (top-down, close framing from the start, zoom <= 10 percent) with the product held in her hands (hands and forearms only, face not visible, same outfit), each held a different way (show_device). Home setting, empty-room plate for the two creator frames, close-ups on the same cloth.


## Product text input (user 2026-11-05)
Packaging text rendered by the image model comes out garbled. So every run carries `product_text.json` (see product_text.py): for each product the brand, product name, variant and the EXACT words printed on the front of the pack, read from the product photo (never invented), plus colour and pack type. The generated PRODUCT TEXT block is pasted into EVERY frame prompt that shows a product, next to the product reference photo; the prompt says to print those words only, spelled exactly. `python3 product_text.py <run> check` must pass before any frame is generated (a run without it is blocked). Close-up frames (where the label is large) use only the front_lines of the product shown. If the text still renders wrong after one retry, the label is composited in post (ffmpeg/PIL) from the product photo crop instead of re-rolling.

## Same-surface rule (user 2026-11-05)
Creator and products share ONE table in every creator frame (PROMPT_LOCKS.md lock 11). The empty-room plate is generated with that table (a desk, dining table or console, not a low coffee table in front of a sofa) and the creator's seat behind it.


## No kitchen (user 2026-11-05)
NEVER use a kitchen (counter, stove, kitchen set) as the setting. Allowed home rooms only: living room, bedroom dressing table, study desk, home balcony or sit-out, dining table. The 'home kitchen counter' entries in the catalogs above are removed. validate_concepts.py rejects any card whose `set` contains 'kitchen'.


## Hands match the avatar, no diya hold (user 2026-11-05)
Every run writes `skin_tone` and `nails` (from the avatar photo) into the concept card and the character bible; they go into every frame prompt together with the avatar references, so hands-only close-ups match the creator. Bottles are gripped by one hand around the body, never held in two cupped palms (see PROMPT_LOCKS.md locks 13b and 14). validate_concepts.py rejects a card without `skin_tone`.


## No opencv label overlay (user 2026-11-05)
Do NOT use overlay_label.py (opencv tracked label overlay) on any run. Printed text is handled by the product-text input to the image prompts only; clips go to assembly as generated. The script stays in the repo but is not part of the pipeline.


## Clips: submit all at once, then wait (user 2026-11-05)
Clip generation for a run goes through `python3 generate_clips.py <run>`: all clips of the run are submitted to Omni together (one take each, 360p, first frame only), then the script waits for every job and downloads the mp4s. Requires <run>/clip_frames.json (clip name -> first-frame asset id) and one 04_actions JSON per clip; `--dry` prints every prompt and the total seconds without submitting or spending. If the Omni service is flaky use `--stagger 15` (all-at-once failed during an outage, staggered submits went through). A failed submit is logged in <clip>.submit_error.txt and retried at most once after 60 s; clips whose mp4 exists are skipped. Do not hand-roll per-clip submit scripts any more.


## Music is always upbeat (user 2026-11-06)
Every run's BGM comes from an UPBEAT pack in <pipeline folder>/assets/music/rhythm_bgm_approved (Rhythm sheet: ONLY these approved RHY_BGM tracks, bgm_pack = rhythm_bgm_approved): upbeat-bright, upbeat-fashion, fashion-upbeat, happy, groovy, funky-groovy, playful, cool-beat, fashion-shoot, indian-festive, stylish, diwali-music, diwali. Never from slow or soft packs (home, acoustic-happy, acoustic kids, pets, little-toy-house, indian-wedding). Still a different track every run (not in concept_registry.json). Record `bgm_pack` (the pack folder name) and `bgm` (the track) in the concept card; validate_concepts.py rejects a card whose bgm_pack is not in the upbeat list. Pick the 30 Sec / Short versions first so the music length fits the reel, trim to the reel length with a fade-out. Use the full-energy section (start at the beat, not a quiet intro): in assemble.py set the music start offset past any slow intro.
