"""PIXEL-LOCKED CONTINUITY (22-Nov). A first/last-frame video model morphs between its two images, so anything that differs
between them - a prop, the face, a sleeve, the light - morphs, melts or cross-fades in the clip. An image-edit model never
keeps the untouched parts of a picture exactly, and a 'camera pushed in' edit even re-draws the room.
Fix: the END frame is built from the START frame by a local, free step:
  1. the edit model changes ONLY the action result with the camera NOT moved (the 'action end' image);
  2. composite_zoom(): exposure-match it, find where it really differs from the start frame (the acting hand/limb/product),
     paste ONLY that region onto the start frame (everything else stays the start frame's own pixels), then
  3. crop + resize that picture towards the push-in target (the push-in is a plain zoom of the same pixels).
Result: the two frames are identical except the action and the zoom - nothing can morph that should not."""
import numpy as np
from PIL import Image, ImageFilter


def composite_zoom(base_path, edit_path, out_path, zoom=1.0, thresh=34, grow=19, feather=9, max_changed=0.55):
    a = Image.open(base_path).convert("RGB")
    b = Image.open(edit_path).convert("RGB").resize(a.size, Image.LANCZOS)
    A = np.asarray(a).astype(np.float32); B = np.asarray(b).astype(np.float32)
    ratio = np.clip(np.median((A + 1) / (B + 1), axis=(0, 1)), 0.85, 1.18)      # same exposure / colour as the start frame
    B = np.clip(B * ratio, 0, 255)
    d = np.abs(A - B).max(axis=2)
    dm = np.asarray(Image.fromarray(np.clip(d, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(4)))
    m = dm > thresh
    mi = Image.fromarray((m * 255).astype("uint8"))
    for _ in range(max(1, grow // 8)):
        mi = mi.filter(ImageFilter.MaxFilter(9))
    frac = float((np.asarray(mi) > 127).mean())
    info = dict(note="", changed=round(frac, 3), ratio=[round(float(x), 3) for x in ratio], zoom=zoom, skipped=False)
    if frac > max_changed:        # the edit shifted the whole picture: pixel-locking would be wrong, use the edit as it is
        out = B; info["skipped"] = True
    else:
        mask = np.asarray(mi.filter(ImageFilter.GaussianBlur(feather))).astype(np.float32)[..., None] / 255.0
        out = A * (1 - mask) + B * mask
    ys, xs = np.where(np.asarray(mi) > 127)
    W, H = a.size
    cx, cy = ((xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2) if len(xs) > 200 and not info["skipped"] else (W / 2, H / 2)
    if frac > 0.30 and not info["skipped"]:
        info["note"] = "LARGE CHANGE between the first frame and the action-end picture - something may have appeared or moved"
    img = Image.fromarray(out.astype("uint8"))
    if zoom > 1.001:
        cw, ch = W / zoom, H / zoom
        x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), H - ch)
        img = img.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
        info["crop_center"] = [int(cx), int(cy)]
    img.save(out_path, quality=95)
    return info


def push_center(base_path):
    """Where the push-in goes: the middle of the hands and the main subject (Apple Vision, free), else the middle of the picture."""
    try:
        import limbguard
        i = limbguard.scan([base_path])[0]
        pts = [(hb[0] + hb[2] / 2, 1 - (hb[1] + hb[3] / 2)) for hb in (i.get("hand_boxes") or [])]
        if i.get("sal"):
            sx, sy, sw, sh = i["sal"]; pts.append((sx + sw / 2, 1 - (sy + sh / 2)))
        if pts:
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    except Exception:
        pass
    return (0.5, 0.5)


def zoom_only(base_path, out_path, zoom, center=None, cap=1.3):
    """LOCKED END FRAME: the last frame is the first frame, only closer - a pure crop of the same pixels. Nothing can appear,
    change or move between the two frames; the push-in is the only difference."""
    a = Image.open(base_path).convert("RGB"); W, H = a.size
    zoom = min(max(zoom, 1.0), cap)
    c = center or push_center(base_path)
    if isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], tuple):
        c = c[0]
    cx, cy = c[0] * W, c[1] * H
    cw, ch = W / zoom, H / zoom
    x0 = min(max(cx - cw / 2, 0), W - cw); y0 = min(max(cy - ch / 2, 0), H - ch)
    img = a.crop((int(x0), int(y0), int(x0 + cw), int(y0 + ch))).resize((W, H), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2, percent=55, threshold=2))
    img.save(out_path, quality=95)
    return dict(zoom=zoom, center=[round(c[0], 3), round(c[1], 3)])


def product_center(base_path, product_paths):
    """23-Nov (user: the zoom ALWAYS goes toward the product): find the product in the picture by matching it with its listing photo /
    reference sheet (OpenCV SIFT + homography, free, local). Returns the product's centre (x, y as 0-1) or None."""
    try:
        import cv2
        img = cv2.imread(base_path, cv2.IMREAD_GRAYSCALE)
        H, W = img.shape
        sift = cv2.SIFT_create(3000)
        kb, db = sift.detectAndCompute(img, None)
        best = None
        for pp in product_paths or []:
            ref = cv2.imread(pp, cv2.IMREAD_GRAYSCALE) if pp else None
            if ref is None or db is None:
                continue
            s = 800 / max(ref.shape); ref = cv2.resize(ref, None, fx=min(1, s), fy=min(1, s))
            ka, da = sift.detectAndCompute(ref, None)
            if da is None or len(ka) < 10:
                continue
            m = [a for a, b in cv2.BFMatcher().knnMatch(da, db, k=2) if a.distance < 0.75 * b.distance]
            if len(m) < 12:
                continue
            src = np.float32([ka[x.queryIdx].pt for x in m]).reshape(-1, 1, 2); dst = np.float32([kb[x.trainIdx].pt for x in m]).reshape(-1, 1, 2)
            Hm, inl = cv2.findHomography(src, dst, cv2.RANSAC, 6.0)
            if Hm is None or inl is None or inl.sum() < 10:
                continue
            pts = dst[inl.ravel() == 1].reshape(-1, 2)          # the matched product points in the picture
            cx, cy = float(np.median(pts[:, 0])), float(np.median(pts[:, 1]))
            if 0 <= cx < W and 0 <= cy < H and (best is None or inl.sum() > best[0]):
                best = (int(inl.sum()), cx / W, cy / H)
        return (best[1], best[2]) if best else None
    except Exception:
        return None


def color_center(base_path, product_paths):
    """Fallback for clear / plain products: where the product's own colours are in the picture (colour back-projection, free)."""
    try:
        import cv2
        img = cv2.imread(base_path); hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); H, W = img.shape[:2]
        best = None
        for pp in product_paths or []:
            ref = cv2.imread(pp)
            if ref is None:
                continue
            rh = cv2.cvtColor(ref, cv2.COLOR_BGR2HSV)
            mask = ((rh[..., 1] > 60) & (rh[..., 2] > 40)).astype("uint8") * 255      # the product's coloured parts, not the white background
            if mask.sum() < 255 * 500:
                continue
            hist = cv2.calcHist([rh], [0, 1], mask, [30, 32], [0, 180, 0, 256]); cv2.normalize(hist, hist, 0, 255, cv2.NORM_MINMAX)
            bp = cv2.GaussianBlur(cv2.calcBackProject([hsv], [0, 1], hist, [0, 180, 0, 256], 1).astype("float32"), (0, 0), W / 30)
            y, x = np.unravel_index(int(bp.argmax()), bp.shape)
            if best is None or bp.max() > best[0]:
                best = (float(bp.max()), x / W, y / H)
        return (best[1], best[2]) if best and best[0] > 5 else None
    except Exception:
        return None


def product_zoom_center(base_path, product_paths):
    """The product's centre; if it cannot be matched, the hand holding/touching it, then the main subject."""
    c = product_center(base_path, product_paths)
    if c:
        return c, "product (matched with its listing photo)"
    c = color_center(base_path, product_paths)
    if c:
        return c, "product (found by its colours)"
    try:
        import limbguard
        i = limbguard.scan([base_path])[0]
        hb = i.get("hand_boxes") or []
        if hb:
            hb = max(hb, key=lambda b: b[2] * b[3])          # the biggest hand = the one holding / touching the product
            return (hb[0] + hb[2] / 2, 1 - (hb[1] + hb[3] / 2)), "the hand at the product"
    except Exception:
        pass
    return push_center(base_path), "main subject"
