"""Per-product label text, given to every image prompt so packaging text renders correctly (user 2026-11-05).
Each run keeps <run>/product_text.json: {"P1": {"brand": "...", "name": "...", "variant": "...", "front_lines": ["exact text line 1", ...], "colour": "...", "pack": "..."}, ...}
front_lines = the exact words printed on the front of the pack/bottle, read from the product photo (not invented).
Usage: python3 product_text.py <run folder> [check]   -> prints the PRODUCT TEXT block to paste into every frame prompt; 'check' fails if any product is missing text."""
import json, sys, os
def block(run, ids=None):
    d = json.load(open(os.path.join(run, "product_text.json"), encoding="utf-8"))
    out = ["PRODUCT TEXT (print exactly these words, spelled exactly, same font style as the reference photo, nowhere else on the product, no invented text):"]
    for k, v in d.items():
        if ids and k not in ids: continue
        lines = " / ".join(v["front_lines"])
        out.append(f"- {v['brand']} {v['name']} ({v.get('variant','')}): front reads: {lines}; {v.get('colour','')}; {v.get('pack','')}")
    return "\n".join(out)
if __name__ == "__main__":
    run = sys.argv[1]
    p = os.path.join(run, "product_text.json")
    if not os.path.exists(p): print("MISSING product_text.json"); sys.exit(1)
    d = json.load(open(p, encoding="utf-8")); bad = [k for k, v in d.items() if not v.get("front_lines") or not v.get("brand")]
    if len(d) < 5: bad.append("fewer than 5 products")
    if len(sys.argv) > 2 and sys.argv[2] == "check":
        print("OK" if not bad else "FAIL: " + ", ".join(bad)); sys.exit(1 if bad else 0)
    print(block(run))
