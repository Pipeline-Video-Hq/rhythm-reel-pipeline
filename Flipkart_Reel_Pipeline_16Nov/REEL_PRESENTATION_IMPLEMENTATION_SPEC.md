# Flipkart BAU reel presentation specification

## Task for Claude

Implement this specification in the existing reel pipeline. Inspect the current code and its callers before editing. This document specifies the requested behavior; it does not claim that these changes are already implemented.

Use the current pipeline's product ingestion, persona identity, generation, assembly, branding and export integrations. Extend those mechanisms rather than building a separate pipeline. Preserve unrelated behavior.

## Non-negotiable requirements

1. Cover all 17 source verticals listed below, **including Makeup**. The user's latest instruction adds Makeup to this rollout and supersedes the earlier exclusion.
2. Each category family has **five alternative presentation formats**. Men's and women's versions share format IDs and concepts, but have explicitly different garment-appropriate actions, turns, poses and detail instructions.
3. Choose **one format per reel**, then apply that format to **all five listed product slots**. Do not assign one of the five formats to each of the five products. Do not generate five reels per row unless separately requested.
4. Every listed product slot must be represented. Do not silently skip products, deduplicate slots or replace a product with a different item. If a slot is missing, inaccessible or unsuitable, report the row and slot for correction; do not mark an incomplete reel complete.
5. The **entire final reel must be no longer than 30 seconds, including the end clip**, transitions and every other visual segment.
6. Each product gets a main presentation and a separate detail shot. Clothing must be worn for its main presentation and worn detail; a held-up introduction does not substitute for the worn view.
7. Keep the exact listed product: colour, print, shape, material appearance, construction, branding and included components. Use the listing images as the product reference.
8. Use natural, brief movements. No full spins, exaggerated poses or unboxing. Product-specific actions take precedence over generic gestures.
9. For BAU, use a consistent, tidy, lived-in Indian home with no festive decorations. Preserve persona, room continuity, supporting clothing and lighting within a reel, except for the listed products that change.
10. Keep the product large enough to read on a phone screen. Details should show real product features, not invented functionality or performance claims.

## Exact source labels and routing

Preserve these CSV labels at ingestion. Add explicit internal aliases where needed; do not rely on loose substring matching that can confuse women and men.

| CSV vertical | Shared format family | Action variant |
|---|---|---|
| Women's Ethnic Wear | ethnic | women |
| Men Ethnic | ethnic | men |
| women Footwear | footwear | women |
| Men Footwear | footwear | men |
| Women western | everyday_clothing | women |
| Men casual | everyday_clothing | men |
| FashionWearables _Women | fashion_wearables | women |
| FashionWearables _Men | fashion_wearables | men |
| Home Decore | home_decor | product-specific |
| HomeFurnishing | home_furnishing | product-specific |
| household kitchen | kitchen | product-specific |
| Household suppliers | household_utility | product-specific |
| baby care | baby_care | caregiver-led, product-specific |
| women fragrance | fragrance | women |
| Men fragrance | fragrance | men |
| Grooming Men | grooming | men, product-specific |
| Makeup | makeup | product-specific application and framing |

Use aliases for existing normalized names such as `Men's Ethnic Wear`, while retaining the original source label in logs.

## Timing and assembly

The following is a default budget, not permission to assume the actual end-clip duration.

| Segment | Start (s) | End (s) | Budget (s) |
|---|---:|---:|---:|
| Product 1 | 0 | 5.5 | 5.5 |
| Product 2 | 5.5 | 11 | 5.5 |
| Product 3 | 11 | 16.5 | 5.5 |
| Product 4 | 16.5 | 22 | 5.5 |
| Product 5 | 22 | 27.5 | 5.5 |
| End clip | 27.5 | 30 | 2.5 |

- Probe the actual end clip before planning: `product_budget = (30 - actual_end_clip_duration - other_nonoverlapping_overhead) / 5`.
- Prefer no separate opening segment: begin Product 1 immediately, with any title overlaid on the footage.
- At the default 5.5 seconds, allocate roughly 3.5 seconds to the main presentation and 2 seconds to detail. These are editable planning values, subject to the total duration limit.
- Fit turns, actions and cuts within those budgets. Use one clear action per main shot; the tables below describe the action vocabulary, not a requirement to perform every gesture in one short shot.
- A held-up-to-worn format may subdivide the main budget into a very brief held-up view and a worn view. Preserve the separate worn detail shot.
- Transitions must fit within the planned timeline. Account for overlap and any extra frames in the actual assembled output.
- If the end clip is longer, reduce each product slot equally. If the resulting budget cannot support a legible main and detail view, report the timing conflict instead of dropping a product or truncating the end clip silently.
- Validate both the rendered timeline and final encoded file duration. Use frame-aware budgeting so rounding cannot push the output past 30 seconds. Trim planned footage or adjust the timeline rather than unnaturally speeding up gestures.

## 1. Ethnic wear — women and men

Shared IDs: `mirror_try_on`, `garment_showcase`, `walk_pause_turn`, `finishing_touches`, `held_to_worn`.

| Format | Women's main action and pose | Men's main action and pose | Detail shot |
|---|---|---|---|
| Mirror-selfie try-on | Face a full-length mirror, phone in one hand, one foot slightly ahead. Free hand smooths the kurta front or lightly lifts pallu/dupatta edge. Gentle quarter-turn shows side drape; return to a relaxed front pose. | Face a full-length mirror, phone in one hand, feet comfortably apart. Free hand straightens kurta hem, collar or jacket placket. Gentle quarter-turn shows shoulder fit, side seam and length; return to front. | Women: neckline, sleeve, embroidery or pallu/dupatta border. Men: collar, buttons, cuff, embroidery or jacket texture. Move closer while maintaining reflection consistency. |
| Garment-focused showcase | Direct camera, full outfit visible. Keep arms clear of silhouette; gently spread pallu/dupatta or smooth pleats. Small turn reveals drape or side slit; let fabric fall naturally. | Direct camera, full outfit visible. Arms relaxed and slightly clear of torso; touch collar or straighten cuff. Small turn shows kurta slit, jacket profile and trouser fit. | Worn close-up. Women: print, border, pleats or sleeve finish. Men: placket, cuff, fabric weave or actual jacket pocket. |
| Walk, pause and turn | Take two short natural steps, pause and quarter-turn. Lightly hold loose pallu/dupatta only if needed. Let fabric settle; finish with one foot slightly forward. | Take two natural steps with relaxed shoulders, pause and quarter-turn. Briefly straighten hem or jacket after stopping; finish in a comfortable stance. | Women: hem/border or dupatta fall, then a stable detail. Men: kurta hem/side slit or collar/cuff. |
| Getting-ready finishing touches | Outfit already worn. Settle dupatta or pallu, or adjust a sleeve/waist pleat. Briefly angle towards a mirror, then reveal the full outfit facing camera. | Outfit already worn. Straighten collar, touch an actual button, adjust cuff or settle included Nehru jacket. Brief mirror check, then full-outfit reveal. | The adjusted feature with hands moved enough to keep it visible. No long dressing sequence. |
| Held-up garment to worn reveal | Briefly hold kurta on hanger or folded saree with border visible. Cut to that exact item worn, front-facing. Lightly lift the relevant fabric edge or make a small side turn. | Briefly hold kurta or included jacket on hanger, front visible. Cut to that exact item worn, front-facing. Adjust collar/hem or make a small side turn. | Match the print/border/embroidery or collar/buttons/texture from the held-up view to the worn product. |

Ethnic-specific constraints:
- Saree actions apply only to sarees; dupatta actions only when included; jacket actions only when the jacket belongs to the listing.
- Pockets must actually exist before using a pocket pose.
- Mirror format intentionally shows the phone; direct-camera formats do not introduce an unexplained phone or mirror.
- The current requirement applies the chosen format to all five products. For `held_to_worn`, each product therefore receives its own brief held-up-to-worn sequence. Replace any older conflicting rule limiting the reel to one held-up introduction for this format only.
- Ritu reference: casual full-length mirror-selfie saree try-on, phone obscuring much of the face, free hand showing pallu and drape.
- Aishwarya reference: direct garment-focused saree showcase, largely shoulder-to-feet framing, small turns and closer pallu/border views.

## 2. Footwear — women and men

Frame mainly knee-down. Adapt to the actual footwear type rather than assuming all women's shoes have heels or all men's shoes have laces.

| Format ID / format | Women's main action | Men's main action | Detail shot |
|---|---|---|---|
| standing_fit / Standing fit check | Pair worn; one foot slightly forward, angle outward, then lift heel slightly if stable. | Pair worn; one foot forward, angle outward and gently shift weight. | Women: toe shape, strap or upper. Men: toe box, upper or fastening. |
| walk_stop / Walk and stop | Two short steps, stop with one foot ahead. | Two natural steps, stop in relaxed stance. | Side profile, heel/sole construction. |
| seated_adjustment / Seated adjustment | Adjust an actual strap, buckle or lace while seated; place both feet down. | Adjust lace/strap or settle loafer onto foot while seated; place feet down. | Fastening, stitching and material. |
| side_back / Side-and-back view | Reposition feet from side profile to rear view without twisting the ankle. | Reposition feet from side profile to rear view. | Rear strap, heel counter or outsole edge as applicable. |
| held_to_worn / In-hand to worn | Hold one shoe by its sole briefly; cut to pair worn and angle one foot. | Hold one shoe by its sole briefly; cut to pair worn and angle one foot. | Match the feature shown in hand to the worn shoe. |

No unstable heel balancing, exaggerated ankle twists or unsupported flexibility demonstrations.

## 3. Everyday clothing — Women western and Men casual

| Format ID / format | Women's main action and pose | Men's main action and pose | Detail shot |
|---|---|---|---|
| mirror_fit / Mirror fit check | Phone in one hand; free hand smooths top/dress at the side. Gentle quarter-turn, then relaxed front pose. | Phone in one hand; free hand straightens shirt/T-shirt hem. Gentle quarter-turn, then relaxed front pose. | Women: neckline, sleeve or waist construction. Men: collar, sleeve or fabric. |
| direct_fit / Direct fit showcase | Front view then small side turn; arms clear of silhouette. | Front view then small side turn; arms relaxed with garment visible. | Seam, print, fastening, placket or material. |
| walk_settle / Walk and settle | Two steps, pause with one foot slightly forward; let garment settle. | Two steps, pause comfortably; let garment settle. | Hem, trouser leg or fabric fall as relevant. |
| finishing_touches / Finishing touches | Adjust actual sleeve, collar or waistband detail; finish facing camera. | Adjust cuff, collar or overshirt front; finish facing camera. | The adjusted construction feature. |
| held_to_worn / Held-up to worn | Brief hanger view, cut to garment worn, then small side angle. | Brief hanger view, cut to garment worn, then small side angle. | Match print, seam or construction to the opening view. |

For top listings, keep supporting bottoms consistent. For bottom listings, make waist-to-feet framing prominent. Do not invent pockets, fastenings or extra garments.

## 4. Fashion wearables — women and men

Use the same five formats for both, but resolve the action from the actual product subtype. Keep small items prominent. Use ankle-level framing for anklets, ear-level for earrings, wrist-level for watches and waist-level for belts.

| Format ID / format | Women's actions | Men's actions | Detail shot |
|---|---|---|---|
| worn_check / Worn styling check | Eyewear: slight head turn. Watch: turn wrist towards camera. Earrings: tuck hair behind ear. Necklace: keep neckline unobstructed. Bag: angle shoulder/forearm. Belt: small waist-level turn. | Eyewear: slight head turn. Watch: turn wrist towards camera. Chain: keep neckline visible. Bag: angle shoulder/body. Belt: small waist-level turn. | Frame, dial, jewellery setting, buckle or bag hardware appropriate to the item. |
| put_on_reveal / Put on and reveal | Put on glasses, slip on suitable bracelet or lift bag onto shoulder. Complex clasp: show final adjustment only. | Put on glasses, settle watch or lift bag onto shoulder. Complex fastening: show final adjustment only. | Fit and fastening with fingers clear of the feature. |
| feature_closeup / Feature close-up | Worn item: gently rotate wrist, angle eyewear or hold jewellery steady. | Worn item: rotate wrist, angle eyewear or hold accessory steady. | Dial, frame, clasp, stones, buckle or zip as listed. |
| natural_use / Natural-use moment | Bag: reach for handle. Watch: glance at wrist. Eyewear: look towards window. Earrings: tuck hair back. | Bag: reach for handle. Watch: glance at wrist. Eyewear: look towards window. Belt: move shirt clear of buckle. | Actual feature revealed by that action. |
| held_to_styled / In-hand to styled | Hold item to show shape, then cut to it worn or carried; use subtype-appropriate pose. | Hold item to show shape, then cut to it worn or carried; use subtype-appropriate pose. | Match the held feature to the styled item. |

For subtypes not explicitly listed, derive a physically appropriate action from the product. Do not substitute an unrelated action. Keep one plain supporting outfit unless the listing itself requires a change.

## 5. Home decor

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| place_reveal / Place and reveal | Place on an appropriate shelf, console or table and withdraw hand. | Surface finish, pattern or decorative feature. |
| before_styled / Before to styled corner | Brief empty spot, matched cut to product placed there. | Product in final position. |
| held_inspection / In-hand inspection | Gently turn a small item; keep large/fragile objects supported and change viewing angle instead. | Texture, edge or workmanship. |
| room_to_detail / Room view to close view | Establish its room placement, then cut closer. | Defining design feature. |
| styling_adjustment / Final styling adjustment | Straighten frame, slightly rotate vase or position decorative object. | Finished arrangement with listed item prominent. |

Supporting props must not imply that unlisted flowers, stands or accessories are included.

## 6. Home furnishing

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| spread_smooth / Spread and smooth | Smooth bedsheet, spread throw, settle cushion cover or smooth the relevant textile. | Texture, print or seam. |
| before_furnished / Before to furnished | Matched cut from plain bed/sofa/window to product installed. | Corner fit, border or finished edge. |
| fabric_fall / Fabric and fall | Lift and gently release a small textile section; draw a curtain panel slightly aside. For rigid-backed rugs, show edge and surface without pretending they drape. | Folds, weave or border. |
| everyday_use / Everyday-use view | Sit beside cushion, settle throw on lap or step naturally onto rug, according to listing. | Product in ordinary use. |
| folded_to_place / Folded to in place | Brief folded/rolled textile view, then cut to it spread or installed. | Matching print and finish. |

Use separate actions for curtains, rugs, bedding, throws and cushions. Do not invent performance claims.

## 7. Household kitchen

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| counter_demo / Countertop demonstration | Place on clean counter and perform one intended action. | Handle, lid, rim, control or working surface. |
| preparation / Preparation task | Mix, scoop, pour, arrange or perform another actual supported preparation task. | Product interacting with ingredients or relevant contents. |
| access_fill / Open, fill and close | For containers/storage, open, add contents and close. For other items, show their actual access/load/ready sequence without inventing a lid. | Real opening, closure or access feature. |
| serve_present / Serve and present | Use suitable plates, bowls, trays or utensils to serve; for tools/appliances, present the result beside the clearly visible tool. | Shape, finish or working/serving surface. |
| stored_to_ready / Stored to ready | Take from appropriate shelf/rack, place on counter, show ready for intended use. | Grip or construction. |

Check all five listings against the selected format before generation. Adapt actions to their real function, or select another compatible format. Do not invent airtightness, heat resistance or appliance functionality.

## 8. Household utility (source: Household suppliers)

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| one_task / One-task demonstration | Perform one intended wipe, sweep, sort, hold or storage action. | Working part. |
| task_before_after / Before to completed task | Show a small, realistically untidy area, then the result of actual intended use. | Product visible in or beside completed task. |
| feature_demo / Feature demonstration | Operate real lid, clip, handle, wheel or folding mechanism. | Mechanism in action. |
| in_place / In-place usefulness | Show product in its laundry, shelf, bathroom or utility location. | Fit and accessible working parts. |
| retrieve_use_return / Pick up, use and put back | Retrieve item, perform one brief action and return it. | Grip, storage feature or finish. |

No invented capacities or dramatic unsupported cleaning transformations.

## 9. Baby care

Caregiver-led demonstrations; a baby is not required. Use age- and product-appropriate handling without inventing feeding, medical or developmental claims.

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| caregiver_inspection / Caregiver inspection | Hold steadily and turn to show construction. | Fabric, fastening, handle or actual component. |
| prepare_use / Prepare for use | Open changing mat, prepare bib or set up item for its intended task. | Closure, edge or setup feature. |
| nursery_placement / Nursery placement | Place in appropriate nursery or changing-area location. | Product clearly visible in setting. |
| feature_demo / Relevant feature demonstration | Fasten bib, open pocket or demonstrate an actual adjustment. | Feature in action. |
| routine_preparation / Routine preparation | Retrieve from organiser and set ready for use. | Product and included accessories only. |

Do not put loose styling props in an infant sleep space or demonstrate an unsafe use.

## 10. Fragrance — women and men

| Format ID / format | Women's main action | Men's main action | Detail shot |
|---|---|---|---|
| bottle_showcase / Bottle showcase | Hold around chest level, label facing camera; turn bottle slightly while keeping label readable. | Hold around chest level, label facing camera; turn bottle slightly while keeping label readable. | Label, cap and bottle finish. |
| getting_ready / Getting-ready finish | Pick up from dressing table, apply appropriately once and lower hand. | After a brief collar/cuff adjustment, pick up and apply appropriately once. | Bottle upright and readable. |
| application / Application close view | For suitable perfume spray, apply towards wrist once, then lower arm; adapt for actual applicator. | For suitable perfume spray, apply towards wrist once, then lower arm; adapt for actual applicator. | Bottle and actual atomiser/roll-on/applicator. |
| vanity_pickup / Vanity pick-up | Reach in, lift bottle and turn front towards camera. | Reach in, lift bottle and turn front towards camera. | Cap removal or actual applicator. |
| ready_to_leave / Ready-to-leave moment | Already dressed, apply appropriately, put bottle down and reach for bag. | Already dressed, apply appropriately, put bottle down and reach for keys/bag. | Bottle remains prominent. |

Follow actual product instructions and applicator. Do not assume every fragrance is a wrist perfume. No invented notes, longevity or visible scent effects.

## 11. Men's grooming

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| mirror_routine / Mirror routine | Perform one appropriate grooming action; slight head turn only when needed to expose relevant area. | Tool head, application area or packaging. |
| product_to_use / Product to application | Show product, then a small appropriate application or intended use. | Texture or contact point without obscuring it. |
| feature_closeup / Feature close-up | Demonstrate actual control, attachment, comb, cap or dispenser. | Selected feature operating. |
| finishing_touch / Finishing touch | Neaten beard edge, comb hair or use suitable finishing product. | Naturally treated area. |
| shelf_use_return / Shelf to use to return | Pick up from grooming shelf, perform brief intended action and return. | Label or working head. |

Resolve trimmers, razors, beard products, hair products and skincare separately. No instant hair-growth, skin-lightening or exaggerated transformation effects.

## 12. Makeup

Use all five listed products in each reel under one selected format, within the same 30-second total budget including the end clip. Keep the same persona, lighting and camera colour treatment so shades and finishes remain comparable. Resolve the actual subtype before choosing the application area or gesture.

| Format ID / format | Main action for each product | Detail shot |
|---|---|---|
| mirror_application / Mirror application | Hold the product briefly with label visible, then perform one short application in a mirror. Lip product: one controlled lip pass. Blush: light cheek placement. Eye product: a brief appropriate eye-area action. Base: dab and blend a small area. | Stable close-up of the applied area and visible finish; move the hand/tool out of the way. Keep reflection and handedness consistent. |
| swatch_to_finish / Swatch to worn finish | Show one small swatch of a suitable colour cosmetic on the back of the hand or forearm, then cut to that exact shade worn in its intended area. For a tool, demonstrate its pickup/blending action instead of inventing a pigment swatch. | Applied colour/texture in consistent light, without beauty filters or colour shifts. For clear products, show the actual visible finish without exaggerating it. |
| direct_application / Direct-camera application | Face the camera and perform one product-appropriate application action. Turn the head slightly to expose the cheek or eye area when needed; keep lips front-facing for lip products. Keep tools clear of the camera's view of the contact point. | Close-up of the application edge, blend or finish. No full-face transformation within the short slot. |
| held_to_worn / Product to worn reveal | Hold packaging with the shade/label facing camera; briefly reveal the real applicator or pan. Cut to the product already worn, using a front view for lips or a slight head angle for cheek/eye products. | Match the shown product/shade to its worn result; show the relevant area rather than an unrelated full-face pose. |
| finishing_touch / Getting-ready finishing touch | With the rest of the look already complete, apply one final touch: lip touch-up, small powder press, light blush blend or another intended action. For setting spray, follow its actual directions and keep eyes closed during application. | Brief settled result on the relevant area, followed by the product visible near—but not covering—the face if space permits. |

Makeup-specific constraints:
- Lipstick/gloss: lips and actual applicator. Blush/highlighter: cheek area. Foundation/concealer: a small relevant face area. Eye shadow/liner/mascara: the intended eye area with controlled movements. Powder: suitable brush/puff contact. Tools: their actual intended application or blending function.
- Select a format compatible with all five listings; do not force a swatch, spray or eye-area action onto an unsuitable product. Use the general compatibility preflight below.
- If the five products are alternative shades of the same type, use separate matched shots with the previous shade removed/reset between products. Do not stack five lipsticks or foundations and imply each final colour is independently accurate.
- If products are complementary steps, a cumulative routine is allowed only when consistent with the selected format and intended use. Each product still needs its own visible action and detail shot; do not credit one product with the combined result.
- Keep skin texture natural. No skin-lightening effects, invented coverage/wear-time claims or exaggerated before-and-after results. Do not simulate a different complexion to make a shade appear to match.
- No applicator contact with the eyeball, implausible hand movements or unsupported uses. Do not invent an included brush, applicator or component; distinguish supporting tools from the listed product.
- Application is a short demonstration, not a requirement to complete an entire makeup routine in 5.5 seconds. A pre-applied matched result can be shown after a cut.

## Implementation guidance

### Inspect these existing locations first

- `diwali-final-reel_SKILL_PIPELINE/scripts/pipeline.py`: source category routing, folder aliases, STYLES, BAU templates, prompt assembly and final assembly timing.
- `diwali-final-reel_SKILL_PIPELINE/scripts/assemble_fk.py`: normalized category handling, branding, music routing and final output assembly.
- `diwali-final-reel_SKILL_PIPELINE/SKILL.md` and applicable rule files: update active documentation where it conflicts with this specification. Do not rewrite historical snapshots or example logs as if they used the new behavior.

Existing line numbers may move; find symbols and their callers rather than hard-coding line offsets.

### Recommended configuration structure

Represent the following explicitly, using repository conventions:

- Source vertical -> family + action variant + supported aliases.
- Family -> five stable format IDs with product-subtype compatibility.
- Format -> framing, main action, pose/turn, detail action and constraints for each applicable variant.
- Reel plan -> selected format, persona, five source product slots, actual end-clip duration and per-shot timing.
- Product shot plan -> source slot/PID, subtype, references, main action, detail action, shot durations.

Do not put the whole specification into one undifferentiated prompt. Resolve category, format, variant and subtype before generating each product's instructions.

Support an explicit format override. Otherwise use a stable, logged selection across the five compatible alternatives, so reruns preserve the same format. Balance variety across rows without changing format in the middle of a reel.

Preflight all five products for compatibility. If necessary, select another common compatible format before generating any shots. If no format can be used faithfully, report the incompatibility rather than inventing product functions.

### Conflict resolution

These current requirements take precedence over earlier pipeline defaults for this rollout:

- 30 seconds includes the end clip; it is not 30 seconds of product footage plus branding.
- Five listed product slots must be represented; older deduplication/skip rules must not silently remove slots.
- The chosen format applies to every product; five formats are alternatives, not five successive reel segments.
- A held-up format repeats the brief held-up-to-worn sequence for all five clothing products, replacing the earlier one-hanger-per-reel restriction for that format.
- Explicit mirror-selfie formats permit a visible phone; do not combine them with contradictory no-selfie prompts.
- BAU has no festive decor, including ethnic wear; older Diwali decor rules do not override this.
- Makeup is included by the user's latest instruction; remove rollout exclusions that would prevent its five formats from being used.

### Required verification

1. Routing: all 17 included exact CSV labels resolve, including Makeup; men's and women's labels are not confused; existing normalized aliases work.
2. Coverage: each family offers exactly five named alternatives, with shared format IDs across gender variants.
3. Actions: inspect representative women's and men's ethnic, footwear, everyday clothing, wearable and fragrance plans; verify variant-specific actions and product-subtype constraints. For Makeup, check lip, eye, base/cheek and tool actions, shade resets and appropriate framing.
4. Product completeness: every reel has all five source slots, each with a main presentation and separate detail shot. Duplicate source slots remain traceable; missing slots stop completion with a clear reason.
5. Format consistency: one selected format across all five products; deterministic reruns; explicit override supported.
6. Timing: test default 2.5-second end clip and a longer end clip. Verify per-product budgets adjust and the final encoded duration remains <= 30 seconds.
7. Conflict cases: held-to-worn across five products, mirror phone visibility, BAU no-decor and Makeup inclusion overriding its earlier exclusion. Check that incompatible makeup actions are rejected and alternate shades are not stacked without resetting.
8. Visual QA: product identity, natural anatomy and gestures, consistent persona/room, legible detail framing, accurate reflection where used, complete end clip and no omitted products.

After implementation, report changed files, validation performed and any blocked product/format combinations. Do not claim video generation or visual QA was completed unless it actually ran.

## Source context

- Vertical labels: `Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv`, supplied by the user.
- Creative formats and timing: this conversation; 30 seconds **including** the end clip, all five products. The user's latest scope update includes Makeup, superseding the earlier instruction to skip it.
- Visual references: `BAU1500_row002_Ritu_WomensEthnicWear_480p.mp4` and `BAU1500_row003_Aishwarya_WomensEthnicWear_480p.mp4` in Downloads.

This is an implementation specification only. No production code or videos have been changed by creating this file.
