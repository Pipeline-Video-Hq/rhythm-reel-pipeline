"""Fetch the row's real Flipkart products (name, price, MRP, photos) from the listing pages.

    python3 products.py <row>      -> row_NNN/products.json + row_NNN/products/p1_1.jpg ...

Public product pages with a normal browser user agent, 2 s apart. Search-result URLs are skipped.
"""
import html, json, os, re, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128 Safari/537.36"


def get(url, binary=False):
    time.sleep(2)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-IN,en"})
    with urllib.request.urlopen(req, timeout=40) as r:
        b = r.read()
    return b if binary else b.decode("utf-8", "ignore")


def parse(page):
    out = {}
    for blob in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S):
        try:
            data = json.loads(blob)
        except Exception:
            continue
        for d in data if isinstance(data, list) else [data]:
            if isinstance(d, dict) and d.get("@type") == "Product":
                out["title"] = html.unescape(d.get("name", ""))
                img = d.get("image")
                out["images"] = img if isinstance(img, list) else [img] if img else []
                off = d.get("offers") or {}
                if isinstance(off, list):
                    off = off[0] if off else {}
                out["price"] = off.get("price")
    m = re.search(r'"mrp"\s*:\s*\{?[^}]*?"value"\s*:\s*(\d+)', page) or re.search(r'"mrp"\s*:\s*(\d+)', page)
    if m:
        out["mrp"] = m.group(1)
    if not out.get("images"):
        out["images"] = list(dict.fromkeys(re.findall(r'https://rukminim\d\.flixcart\.com/image/\d+/\d+/[^"\s]+?\.jpe?g', page)))[:4]
    out["images"] = [re.sub(r"/image/\d+/\d+/", "/image/832/832/", u) for u in out["images"]][:3]
    return out


def main():
    row = int(sys.argv[1]); d = row_dir(row)
    brief = load(os.path.join(d, "brief.json"))
    if not brief:
        raise SystemExit("run row.py first")
    os.makedirs(os.path.join(d, "products"), exist_ok=True)
    prods = []
    for i, url in enumerate(brief["product_urls"], 1):
        if "/search?" in url or "/p/" not in url:
            prods.append(dict(url=url, skipped="search URL, not a product")); continue
        try:
            p = parse(get(url))
        except Exception as e:
            prods.append(dict(url=url, error=str(e)[:200])); continue
        files = []
        for j, im in enumerate(p.get("images", []), 1):
            fn = os.path.join(d, "products", f"p{i}_{j}.jpg")
            try:
                open(fn, "wb").write(get(im, binary=True)); files.append(fn)
            except Exception:
                pass
        prods.append(dict(url=url, title=p.get("title"), price=p.get("price"), mrp=p.get("mrp"), photos=files))
        print(i, (p.get("title") or "?")[:60], p.get("price"), p.get("mrp"), len(files), "photos")
    save(prods, os.path.join(d, "products.json"))


if __name__ == "__main__":
    main()
