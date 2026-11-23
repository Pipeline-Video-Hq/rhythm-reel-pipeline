# Pipeline preflight and product inputs

Generation or regeneration requires the user's confirmation for the specific job. Do not submit a generation job to create a reference or a video without it. The `--confirmed` flag records that the operator obtained that confirmation; it does not replace asking the user. This CLI requires a passing preflight, uses 360p and portrait, and accepts only action files inside the validated run.

Create `pipeline_products.json` in the run folder. List **every** product once, including the product being applied. Each product must have a different `show_device` chosen from `open_palm`, `eye_level_turn`, `cheek_match`, `mirror_reflection`, `fabric_comparison`, `size_comparison`, `unbox_reveal`, `table_flourish`, `fan_or_stack`, `collarbone_cradle`. Each device is a distinct staging concept; invent and review the actual gesture and framing so they look distinct. A product can be marked `opens: false` if it cannot or should not open on camera.

For each product that opens, write a product-specific `closed_spec`, `open_spec`, and `opening_action`, based on its actual listing references. The open specification must describe the visible contents, shape, colors, number of parts and cap or lid position. Provide paths to existing closed and open reference images relative to the run folder and set `references_approved` to true only after the user has approved both. Creating reference images requires separate user confirmation. This manifest records and checks references; it does not create or upload them or attach them to the Omni request. Verify the supported Omni image-input schema and explicitly attach the approved references before relying on image-to-video. The generation client blocks any run containing an opening product until that is implemented; it cannot silently proceed without references.

Example (illustrative paths, not actual assets):

```json
{"products": [{"id":"P01", "show_device":"open_palm", "opens":true,
 "opening_action":"Pull cap straight off and hold it in the left hand",
 "closed_spec":"Red tube with cap fitted", "open_spec":"Red tube, exposed lipstick bullet, cap separate",
 "closed_reference":"assets/plates/P01_closed.png", "open_reference":"assets/plates/P01_open.png",
 "references_approved":true}]}
```

Each product action JSON must carry `product_id`, matching `show_device`, and `beat_type` (`show` or `apply`). For an opening product, set `opens_on_camera: true` and mark the actual opening step with `opening_step: true` and describe it in `what_happens`. Non-product hook or b-roll actions may use `product_showcase: false`. Every step must have `camera: "locked_off"`; avoid contradictory camera movement instructions in all plan text. Exactly one application beat is required.

Run `python3 pipeline_preflight.py RUN_FOLDER` for a local read-only check. Once the user confirms a specific clip and its approved image inputs can be supplied, the command shape is `python3 omni.py --run RUN_FOLDER --action RUN_FOLDER/04_actions/SCENE.json --confirmed`. Do not run this command as a test.

Preflight checks metadata, paths and distinct device labels; it cannot judge whether specs match the real product, whether gestures are meaningfully different, or whether a model follows the prompt. Review product references, the planned motions and every generated clip for product accuracy, distinct presentation, opening, and unwanted camera movement before assembly. If review fails, request confirmation before any regeneration.
