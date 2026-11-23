# Category rules: what to do for different products

Sources: (1) the Flipkart Diwali export `~/Downloads/Diwali_Pipeline_Export_6Nov2026` (SKILL.md sections 3 and 9, `memory/shooting-styles-rule.md`, the category notes in `memory/`), (2) the rules built in this pipeline (PROMPT_LOCKS.md, PIPELINE_CONCEPT_LAB.md, REALISM_RULES.md). The export runs on a different engine (Higgsfield/Kling plates and clips, 22-24 s reels); this repo runs on Omni at 360p with first frames only. The CATEGORY ideas below carry over; engine details do not.

Priority when two rules conflict: the newest user rule wins. In this repo: one application per video, creator face in at most 2 clips, hands-only close-ups for the rest, home setting (never a kitchen), 10 percent push-in at most, 30 s maximum, no opencv overlay.

## Shooting styles (export, user 3-Nov): one style per video, music only
A mirror selfie (phone over the face) | B headless fit check | C hands-only product demo | D courier pouch unboxing | E room before/after.
Pairs per category (alternate row by row): Ethnic + Western A,B | Women footwear B (knee down), D | Men footwear B (knee down), C | Kids clothing, Kids footwear, Kitchen, Household, Baby care, Toys, Fragrance C,D | Fashion wearables B (wrist/neck close), D | Home decor + Furnishing E,C | Makeup C,D.
Conflict to know: the export's `shooting-styles-rule.md` also says 'Makeup C only ... no pouch/box opening in any shot'. In this repo products are opened only as pre-opened (cap already off) and never with an opening action, so use C (hands-only close-ups) plus the creator hook and the one application.

## Per category
| Category | What to show and how |
|---|---|
| Makeup (lips, eyes, cheek, face) | Creator face only in the hook and the ONE application (that product already open, first frame bare, mark must really appear, lock 8c/15). Every other product is a hands-only close-up, held in a different natural way (hands_prompt.py), label to camera. Eye products: eye stability (lock 8). No price on screen. Never a kitchen. |
| Fragrance | Same budget. The one application is ONE spray on the inner wrist or collarbone with the bottle already open (nozzle at the target, no mist in the first frame, never sprayed on the head). Bottles are gripped by ONE hand wrapped around the body, upright, label to camera, never in cupped palms (no diya hold). Exactly one of each bottle. |
| Skincare, Grooming | Same budget. The application is a fingertip dab and spread on the cheek or back of the hand with the jar/tube already open; the others are close-ups held at the edges. |
| Apparel: ethnic, western, kids | Every outfit is WORN by the avatar (one product = one worn shot = one outfit change); never laid on a bed or sofa, never only held up, never on a hanger as the main shot. Allowed before-shot (<=2 s, hands only): a packet open or a hanger (at most 1 hanger). Worn shot with a gesture, then a close-up of a worn detail (print, embroidery, border) with the face out of frame. Kids: the mother's hands. Diwali decor only in ethnic wear and home decor. Campaign-fit outfit (festive but simple for Diwali). |
| Footwear (women, men, kids) | Every pair is first SHOWN (two hands turning one shoe, hands only), then WORN in a tight or knees-down shot (the footwear fills the frame), at least 2 hands-only turn shots. Groomed person and neat, clean feet (realism.FOOTWEAR_BEAUTY in the export). No packet and no shoe box. No notebook, list, paper or pen in any shot. Avoid floor or cross-legged poses. Hands-only prompts stay short (body words trigger NSFW flags). |
| Home decor | A calm reveal: carry each product in and PLACE it (before to after), then a close-up of the placed product, plus 2 close-ups. Keep each product centred in its frame. Diwali decor (marigold, rangoli, warm lights, a toran) only in this category and ethnic wear, inside a real home; still no lit diyas unless the product is a diya. |
| Home furnishing (bedsheets) | Folded in hands or packet open or pick up, then the sheet ALREADY laid on the made bed (edge to edge over the whole mattress, matching pillow covers), a hand smoothing it, then print and fabric close-ups. NEVER shake, unfold or spread it in the air (it reads tiny). |
| Fashion wearables (watch, jewellery) | Style B/D: wrist or neck close-up, box open or shown, then worn. |
| Kitchen, Household | Hands-only demo (C) in the right room type; shown, packet or box open, pick up, then used. (In this repo never use a kitchen as the background.) |
| Baby care, Toys | Mother's hands, shown or packet open, then used; style C,D. |
| Pets | Always OUTDOORS on the home's green lawn (same lawn spot in every shot, house wall or verandah behind), never a living room. Shampoo or bathing happens on the grass with a tub or towel. |
| Any category | The product is clearly visible and big in every shot (the face is optional). Exactly two hands maximum, each forearm traced to a frame edge (lock 18 and the export's no-extra-hands rule). No fire handling, no lit diya in anyone's hand. No price or percent on screen unless verified. Objects stay consistent across shots. |

## Variety (export, user 30-Oct)
Each video mixes 2-3 ways of bringing the products in (shown, picked up, placed, worn) and never the same intro three times in a row. In this repo that is the unique `show_device` per product (check_actions.py enforces it).

## Edit and delivery (export)
Footage <= 24 s (this repo: 30 s with the 1.58 s end slate), pieces of 1.5-4 s, hard cuts, one title or header for the whole film, Flipkart logo and end slate, music only, no price and no percent, finished 480p copy for review.
