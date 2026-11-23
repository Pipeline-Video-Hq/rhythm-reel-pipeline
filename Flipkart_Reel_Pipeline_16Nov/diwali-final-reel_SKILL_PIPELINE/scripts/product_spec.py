"""PRODUCT SPECS (user 17-Nov, every vertical except Makeup/Beauty): build a spec sheet for each product on display, then
send it as the reference for that product's plate and clip generation.

    python3 product_spec.py <row_folder>         # all 5 slots of a row (reads products.json for the urls)
    python3 product_spec.py --pid <PID> [out]    # one product (testing)

Per slot it writes <row>/specs/slot_N.json (title, brand, price, every listed specification, the colour/material/pattern/
type fields picked out, description) and <row>/specs/slot_N.txt = the PRODUCT SPEC block that goes VERBATIM into every
image and clip prompt for that product. Data comes only from the public listing page (no invented features).
"""
import html, json, os, re, sys, time, urllib.request

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"
# spec keys that describe what the product LOOKS like - these lead the prompt block (others follow, capped)
VISUAL = ["Color", "Colour", "Pattern", "Fabric", "Material", "Outer Material", "Upper Material", "Sole Material", "Type",
          "Sari Style", "Style", "Blouse Piece", "Neck", "Neck Type", "Sleeve", "Sleeve Length", "Length", "Fit", "Closure",
          "Occasion", "Ideal For", "Shape", "Frame Color", "Lens Color", "Dial Color", "Dial Shape", "Strap Color",
          "Strap Material", "Heel Height", "Heel Type", "Toe Shape", "Base Material", "Finish", "Size", "Dimensions",
          "Width", "Height", "Depth", "Weight", "Capacity", "Number of Contents in Sales Package", "Sales Package",
          "Pack of", "Model Name", "Model Number", "Brand Color", "Embroidery Type", "Print Type", "Ornamentation"]
SKIP = {"Fabric Care", "Wash Care", "Net Quantity", "Manufacturer", "Importer", "Packer", "Generic Name", "Country of Origin",
        "Seller", "Style Code", "Model ID", "Warranty", "Domestic Warranty", "Warranty Summary", "Covered in Warranty", "Not Covered in Warranty"}


def fetch(pid):
    req = urllib.request.Request(f"https://www.flipkart.com/product/p/itme?pid={pid}",
                                 headers={"User-Agent": UA, "Accept-Language": "en-IN,en"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "ignore")


_NOT_LEN = re.compile(r"weight|wt\b|capacity|volume|quantity|qty|pack|count|pieces|pcs|price|mrp|spf|ml\b|litre|liter", re.I)
_UNIT = {"mm": 0.1, "cm": 1.0, "m": 100.0, "in": 2.54, "inch": 2.54, "inches": 2.54, '"': 2.54, "ft": 30.48, "feet": 30.48}


def cm_values(text):
    """23-Nov: the LENGTHS (in cm) in a free-text size like 'width 110, height 100, weight 245 g' -> [110.0, 100.0].
    Weights, volumes, counts and other units are dropped (before this, 245 g and 150 ml were read as 245 cm / 150 cm).
    A bare number counts as cm (the field is dimensions_cm); mm / m / inch / ft are converted."""
    out = []
    for part in re.split(r"[,;/\n]|\bx\b|×", str(text or "")):
        label = re.sub(r"[\d.]+.*", "", part)
        if _NOT_LEN.search(label):
            continue
        for num, unit in re.findall(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|inches|inch|in|ft|feet|\"|g|gm|gms|kg|ml|l|ltr|%|pcs|pc)?(?![a-z])",
                                    part, re.I):
            f = _UNIT.get(unit.lower() if unit else "cm")
            if f and float(num) > 0:
                out.append(round(float(num) * f, 2))
    return out


def _u(x):
    """Decode JSON escapes like \\u0026 -> &."""
    try:
        return json.loads('"' + x.replace('"', '\\"') + '"')
    except Exception:
        return x


def parse(page, pid=""):
    spec = {"pid": pid}
    for blob in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S):
        try:
            data = json.loads(blob)
        except Exception:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get("@type") == "Product":
                spec["title"] = html.unescape(d.get("name", ""))
                b = d.get("brand")
                spec["brand"] = html.unescape(b.get("name", "") if isinstance(b, dict) else b or "")
                off = d.get("offers") or {}
                off = off[0] if isinstance(off, list) and off else off
                spec["price"] = off.get("price") if isinstance(off, dict) else None
    if not spec.get("title"):
        m = re.search(r"<title>(?:Buy )?(.*?)(?: Online @ Best Price| \| Flipkart)", page, re.S)
        spec["title"] = html.unescape(m.group(1)).strip() if m else ""
    # specifications grid: {"label_1":{"value":{"text":["v1","v2"]}},"label_0":{"value":{"text":"Key"}}}
    rows = {}
    for vals, key in re.findall(r'"label_1":\{"value":\{"text":\[((?:"[^"]*",?)+)\]\}\},"label_0":\{"value":\{"text":"([^"]{1,60})"\}', page):
        v = ", ".join(html.unescape(_u(x)) for x in re.findall(r'"([^"]*)"', vals) if x.strip())
        key = html.unescape(_u(key)).strip()
        if key and v and key not in rows and key not in SKIP:
            rows[key] = v
    spec["specifications"] = rows
    m = re.search(r'"contentTitle":"Description".{0,4000}?"text":"([^"]{40,1200})"', page, re.S)
    spec["description"] = html.unescape(_u(m.group(1))).replace("\\n", " ").strip() if m else ""
    return spec


def block(spec, slot=None):
    """The PRODUCT SPEC text that is pasted verbatim into every plate/clip prompt of this product."""
    s = spec["specifications"]
    lead = [(k, s[k]) for k in VISUAL if k in s]
    rest = [(k, v) for k, v in s.items() if k not in dict(lead)][:8]
    lines = [f"PRODUCT SPEC{f' (slot {slot})' if slot else ''} - reproduce EXACTLY, from the listing {spec['pid']}:",
             f"  Product: {spec.get('title', '')}" + (f" | Brand: {spec['brand']}" if spec.get("brand") else "")]
    lines += [f"  {k}: {v}" for k, v in lead + rest]
    if spec.get("description"):
        lines.append(f"  Listing description: {spec['description'][:300]}")
    lines.append("  Show only what is listed: same colour, print/pattern, material look, shape, parts and pack contents; "
                 "never add or change a feature.")
    return "\n".join(lines)


def make(pid, outdir, slot=None):
    os.makedirs(outdir, exist_ok=True)
    spec = parse(fetch(pid), pid)
    if not spec.get("title") or not spec.get("specifications"):
        # 23-Nov: a bot-block / changed page gives an empty listing; never cache it and never let the planner guess the product
        raise SystemExit(f"slot {slot} {pid}: the Flipkart listing came back empty (title={spec.get('title')!r}, "
                         f"{len(spec.get('specifications') or {})} specs) - nothing saved; run again later")
    name = f"slot_{slot}" if slot else pid
    json.dump(spec, open(os.path.join(outdir, name + ".json"), "w"), indent=1, ensure_ascii=False)
    open(os.path.join(outdir, name + ".txt"), "w").write(block(spec, slot) + "\n")
    return spec


def for_row(row_dir, urls=None):
    """Specs for the row's 5 slots (urls given, else brief.json product_urls). Missing pid -> stops (never skip a slot)."""
    urls = urls or json.load(open(os.path.join(row_dir, "brief.json")))["product_urls"]
    out = os.path.join(row_dir, "specs")
    for i, u in enumerate(urls, 1):
        m = re.search(r"pid=([A-Za-z0-9]+)", u)
        if not m:
            raise SystemExit(f"slot {i}: no pid in {u} - fix the sheet (slot is not skipped)")
        jp = os.path.join(out, f"slot_{i}.json")
        if os.path.exists(os.path.join(out, f"slot_{i}.txt")) and os.path.exists(jp):
            try:
                old = json.load(open(jp))
            except ValueError:
                old = {}
            if old.get("pid") == m.group(1) and old.get("title") and old.get("specifications"):
                continue      # 23-Nov: reuse only when it is THIS slot's product (a sheet change refetches) and not empty
            print(f"slot {i}: saved spec is for {old.get('pid')!r} or empty - refetching {m.group(1)}")
        sp = make(m.group(1), out, i)
        print(f"slot {i}: {sp.get('title', '?')[:60]} | {len(sp['specifications'])} specs")
        time.sleep(2)
    return out


CAPTION_KEYS = ["product_type", "selected_piece", "silhouette", "colours_materials", "features", "display_controls", "printed_branding",
                "openable_parts", "visible_view", "unwanted_elements"]


def check_sheet(row_dir, slot):
    """Product reference sheet inputs for one slot (rules/PRODUCT_REFERENCE_SHEET.md): caption has every key, and the sheet
    prompt never names the brand / model / listing title (Image 1 must stay the ground truth). Returns a list of problems."""
    d = os.path.join(row_dir, "specs", f"slot_{slot}")
    bad = []
    try:
        cap = json.load(open(os.path.join(d, "product_caption.json")))
    except Exception as e:
        return [f"slot {slot}: product_caption.json missing/invalid ({e})"]
    bad += [f"slot {slot}: caption missing '{k}'" for k in CAPTION_KEYS if k not in cap]
    try:
        sp = json.load(open(os.path.join(d, "sheet_prompt.json")))
    except Exception as e:
        return bad + [f"slot {slot}: sheet_prompt.json missing/invalid ({e})"]
    spec = json.load(open(os.path.join(row_dir, "specs", f"slot_{slot}.json")))
    prompt = sp.get("prompt", "").lower()
    printed = " ".join(b.get("text", "") for b in cap.get("printed_branding", [])).lower()
    sp_ = spec["specifications"]
    generic = " ".join(str(sp_.get(k, "")) for k in ("Material", "Type", "Color", "Colour", "Fabric", "Outer Material")).lower()
    names = [spec.get("brand", "")]
    for k in ("Model Name", "Model Number"):   # listings often put plain words here ("stainless steel") - only real names count
        for part in re.split(r"[|/,]", str(sp_.get(k, ""))):
            part = part.strip()
            if part and part.lower() not in generic and (any(c.isdigit() for c in part) or part[:1].isupper()):
                names.append(part)
    for n in filter(None, (x.strip().lower() for x in names)):
        # allowed only inside a quoted printed-branding text; any other mention = the model draws its own idea of the brand
        if n in prompt.replace(f'"{printed}"', "") and n not in printed:
            bad.append(f"slot {slot}: sheet prompt names '{n}' - refer to 'the <product type> in Image 1' instead")
    if cap.get("selected_piece") and "only" not in prompt:
        bad.append(f"slot {slot}: sheet prompt must say only the selected piece is shown (one product per sheet)")
    if "image 1" not in prompt:
        bad.append(f"slot {slot}: sheet prompt never points at Image 1")
    if cap.get("unwanted_elements") and not sp.get("excluded_elements"):
        bad.append(f"slot {slot}: caption lists unwanted elements but excluded_elements is empty")
    return bad


def identity_lock(row_dir, slot):
    """IDENTITY LOCK (user 17-Nov: apparel changed between main and detail shots even with the spec): the visual details the
    photo caption recorded - silhouette, every colour/material part, every feature with its position - as hard 'must stay
    exactly' lines. Written to specs/slot_N/identity_lock.txt and pasted into every plate and clip prompt of that product."""
    cap = json.load(open(os.path.join(row_dir, "specs", f"slot_{slot}", "product_caption.json")))
    L = [f"IDENTITY LOCK (slot {slot}) - this exact {cap.get('product_type', 'product')}, identical in every shot; changing ANY of these "
         "is a different product:"]
    if cap.get("silhouette"):
        L.append(f"  - Shape / cut: {cap['silhouette']}")
    if cap.get("proportions"):
        L.append(f"  - Proportions: {cap['proportions']}")
    for c in cap.get("colours_materials", []):
        L.append(f"  - {c.get('part')}: {c.get('colour')}, {c.get('finish')}")
    for f in cap.get("features", []):
        L.append(f"  - {f.get('name')} at {f.get('position')}: {f.get('detail')}")
    if cap.get("display_controls") and cap["display_controls"] != "none":
        L.append(f"  - Controls / display: {cap['display_controls']}")
    for b in cap.get("printed_branding", []):
        L.append(f"  - Printed text \"{b.get('text')}\" at {b.get('position')}")
    L.append("  Do not simplify, restyle, add or remove anything: same pattern, same hem/edge shape, same buttons and their count, "
             "same trim colours, same pieces. If a close-up crops part of it, what is visible must match these lines exactly.")
    txt = "\n".join(L)
    open(os.path.join(row_dir, "specs", f"slot_{slot}", "identity_lock.txt"), "w").write(txt + "\n")
    return txt


if __name__ == "__main__":
    if sys.argv[1] == "--check-sheet":       # --check-sheet <row_dir> <slot>
        probs = check_sheet(sys.argv[2], int(sys.argv[3]))
        if not probs:
            identity_lock(sys.argv[2], int(sys.argv[3]))   # written as soon as the caption is valid
        print("\n".join(probs) if probs else "OK"); sys.exit(1 if probs else 0)
    if sys.argv[1] == "--pid":
        sp = make(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else ".")
        print(json.dumps(sp, indent=1, ensure_ascii=False)); print(); print(block(sp))
    else:
        for_row(sys.argv[1])
