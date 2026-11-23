# Pipeline changes, 23 Nov 2026

Base: Madhav's code, including his fixes of 23 Nov (commits a7c016b and 910fe26: product sheets made while planning runs,
`fill_routine`, rules 44-49, `listing_size`). The table lists what was still wrong after that, and what changed today.

**How to test a change:** never on a batch. Test 3-4 rows, each from a different category (for example baby care,
fragrance, footwear, home decor), and check every reel before a batch.

| # | Area | Error before | Effect seen | Change now | Where | How checked |
|---|---|---|---|---|---|---|
| 1 | Finish checks | All finish checks were switched off on 22 Nov (5 products, 4 s takes, black / frozen / cut frames, length) | Broken, frozen or 4-product reels were filed with no warning | Checks are back on. A failing reel gets `qc/FAILED.json` naming the slot to redo and is not filed | `pipeline.py` `finish` | Test clips: a cut, a short clip, black and frozen frames were caught; good clips passed |
| 2 | Upload | Upload sent the first file it found, with no check | A failed or stale reel could reach Drive | Upload sends only the exact file that passed finish (`qc/pass.json`) | `pipeline.py` `upload` | Code read |
| 3 | Plan checks | `FK_LAX=1` was on by default and turned every plan error into a warning; a "fewest errors" fallback used failing plans | Rows 1228 ("Application issue") and 1185 ("Three hands") were made from plans that had failed | A plan with errors stops the row before anything is paid for | `pipeline.py`, `product_planner.py`, `run_batch.py`, `run_row.py` | Day 6 saved plans compared with the QC notes |
| 4 | Product size | Every number in the size text was read as cm (150 ml -> 150 cm, 245 g -> 245 cm) | Products drawn far too big (Day 6 "size" notes) | Sizes are read with their units; the plan must agree with the listing's stated size within 25% | `product_spec.py` `cm_values`, `product_planner.py`, `shot_builder.py` | 7 of 52 saved plans corrected (for example a bottle from 150 cm to 20 cm) |
| 5 | Camera move | The timeline said "camera locked", then a separate push-in in the last 1.5 s | A hard cut about 2 s into a take in 30 of 39 flagged Day 6 reels ("transition jerk") | Every beat carries one slow, even camera move; it ends only 15-25% closer | `shot_builder.py` `beats_text` | Measured on the 39 reels; prompt change, needs one paid test row |
| 6 | Handling | The "no state change" check read only the last frame and missed wipes, twisting and pumps | Floating products, caps opening wrongly, wipes hovering (baby care, fragrance) | Rule 50: nothing is picked up, put down, opened or pulled out inside a take, checked on every beat; grip lock in the clip prompt | `product_planner.py` `handling_errors`, `shot_builder.py` | 52 saved plans: 17 of 237 shot options rejected, every product keeps a clean option |
| 7 | Duplicate products | The duplicate check read a field that does not exist | The same product could appear twice in a reel | Exactly 5 different products on every route | `pipeline.py` `planned_inputs` | Code read |
| 8 | Listings | An empty Flipkart page (bot block) was saved and never fetched again | The planner guessed the product | An empty listing is refused and not saved; a changed product is fetched again | `product_spec.py` | Code read |
| 9 | Product change | Pictures and sheets were keyed by slot, not by product | After a sheet fix the old product could be generated | Every slot's assets belong to one product ID; a changed product's assets are moved aside and made again | `run_row.py`, `pipeline.py` `new` | Code read |
| 10 | Personas | An unknown name silently became a 160 cm woman | Wrong body or height | An unknown persona stops the row | `reel_planner.py` | All 50 Day 6 personas are present |
| 11 | On-screen text | The title and the "under Rs X" claim were never checked | A wrong title or price claim could ship | The title must equal the sheet text; "under Rs X" is checked against the listing prices | `pipeline.py` `check_text` | Code read |
| 12 | Makeup names | The product names on screen were typed by hand from a template | Template names could ship | Names are checked against `product_text.json` | `pipeline.py` `finish_beauty` | Code read |
| 13 | Rate limits | A second rate-limit reply stopped the whole row | About 12.5 min of each 23 min reel was lost (speed note, 62 reels) | One shared, adaptive picture queue for all rows; a rate-limited picture waits for its turn | `imgqueue.py`, `run_row.py` | Offline test against a fake Omni server |
| 14 | Planning | Planning blocked generation | Picture capacity sat idle | Planning pool (10 rows) separate from generation; rows generate in plan-ready order | `run_batch.py` | Offline test |
| 15 | Network | A network drop failed every running row (173 rows on 23 Nov) | Rows lost | Requests that never left the Mac wait for the network; a request sent with no answer is never re-sent | `netwait.py`, `run_row.py`, `product_planner.py` | Offline test |
| 16 | Double billing | Makeup clips retried on any error, including ones Omni may have billed; a rerun re-submitted clips | Paying twice | Retry only when Omni certainly did not take the job; a rerun collects submitted clips | `beauty_pipeline/generate_clips.py` | Code read |
| 17 | Paid ids | Several threads changed the asset-id file without a lock; Omni replies were not checked | A crash could lose a paid id | Thread-safe id file; every reply is checked and a bad one stops the row cleanly | `run_row.py` | Race reproduced, then fixed |
| 18 | Image model | No model name was sent | A server default change could swap the model | `gemini-3.1-flash-image` pinned; switch with `FK_IMAGE_MODEL=<id>`; `omni_models.py` lists what Omni accepts (free) and a run stops before any paid picture if the model is not accepted | `run_row.py`, `omni_models.py` | Omni tool model list checked |
| 19 | Video model | Docs and one script still said Omni 1.1 | A worker could generate on 1.1 | Omni 1.2 everywhere | `SKILL.md`, `rules/*.md`, `promptgen.py` | grep |
| 20 | Portability | Paths from other people's Macs; shell scripts ran on after errors | Broke on other Macs | Paths removed; scripts stop at the first error | `common.py`, `make_zip.sh`, `prep_*.sh` | Syntax checks |
| 21 | Short clips | A short clip was silently shortened in assembly | A product cut short, later beats shifted | Assembly refuses a short clip | `bbd-omni-reel_skill/scripts/assemble.py` | Test clip |
| 22 | Clip reports | The free hand and size reports on finished clips were never called | No warning | They run on every clip and show at finish as warnings | `run_row.py`, `pipeline.py` | Code read |

## Not changed yet
- No automatic check looks at the finished clip for product changes, floating items or extra hands (a vision check is proposed).
- Footwear leg movement needs real reference clips.
- The first 2 frames of each product are frozen (they come from Omni).
