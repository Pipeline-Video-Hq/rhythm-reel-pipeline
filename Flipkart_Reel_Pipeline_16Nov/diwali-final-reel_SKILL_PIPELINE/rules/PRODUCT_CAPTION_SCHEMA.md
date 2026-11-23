# product_caption.json (input to PRODUCT_REFERENCE_SHEET.md)

Written by the worker for each product slot after looking at its primary listing photo (Image 1 = `products/p{N}_1.jpg`)
and the other listing photos. Describe only what is visible; never add details from memory of the brand or model.
The listing spec (`specs/slot_N.json`) may confirm colour/material names, but Image 1 wins where they differ.

```json
{
  "product_type": "air fryer",
  "selected_piece": "the only piece (for a set/pack: which ONE piece the sheet shows, e.g. 'large cooker, top right of Image 1')",
  "silhouette": "upright rounded-square box, slightly taller than wide, flat top, pull-out drawer in the lower half",
  "proportions": "about 1.1 : 1 height to width; drawer is the lower 45% of the front",
  "colours_materials": [
    {"part": "body sides and top", "colour": "matte black", "finish": "fine brushed texture"},
    {"part": "front control panel and drawer front", "colour": "silver", "finish": "brushed stainless steel"}
  ],
  "features": [
    {"name": "drawer handle", "position": "centre of the drawer front", "detail": "black, vertical, curves outward and down"},
    {"name": "dial", "position": "centre of the control panel", "detail": "round, silver"}
  ],
  "display_controls": "black glass panel across the top front: digital display top centre showing 00:20 and 400F, two columns of touch buttons left and right, silver dial in the middle",
  "printed_branding": [
    {"text": "<exact text as printed>", "position": "top centre of the control panel, white"}
  ],
  "openable_parts": ["pull-out drawer with basket"],
  "visible_view": "front, slightly from the left; sides, back and top not visible",
  "unwanted_elements": [
    {"what": "white price sticker with barcode", "where": "lower right of the drawer front", "replace_with": "plain brushed silver drawer front"},
    {"what": "clear protective film with a peel tab", "where": "over the control panel glass", "replace_with": "clean black glass"},
    {"what": "fried food in the basket", "where": "inside the open drawer", "replace_with": "empty, clean basket"}
  ]
}
```

The example is an appliance; the same keys work for every product. For clothes `features` lists neckline, sleeves, print,
border, embroidery, buttons and pieces of the set; for footwear upper, straps/laces, heel, toe shape and sole; for wearables
dial/frame/clasp/stones/buckle; `display_controls` is "none" when there are none.

CLOTHING - these become the IDENTITY LOCK, so be exact (user 17-Nov: a kurta changed between shots): `silhouette` states the
length and the HEM SHAPE (straight / curved / asymmetric / high-low / side slits); `colours_materials` names the base colour
AND the pattern (plain / self-design woven grid / print with motif and scale / embroidery and where); `features` lists the
collar/neckline, the placket (colour, edge trim, length), every button (count, colour, placement - centre or angled/side),
pockets and pocket squares, cuffs, borders, and every other piece of the listing (dhoti, pyjama, churidar, jacket, dupatta)
with its colour and style.

Rules:
- `printed_branding` holds only text that is printed, moulded or engraved on the product or its retail packaging, exactly as it reads.
- `unwanted_elements` lists every sticker, label, badge, film, tag, wrap, overlay graphic, watermark, food/content and prop
  (see the sticker section of PRODUCT_REFERENCE_SHEET.md), each with where it is and the clean surface that replaces it.
  Use an empty list when there are none.
- `openable_parts` is empty when nothing opens (the sheet then uses a top-down view for panel 6).
