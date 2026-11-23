"""Clip check (23-Nov plan, step 1): does the finished clip still show THE product, held or resting for real, with a normal body?

For one product clip: 5 frames (0.2, 1, 2, 3, 3.8 s of the take) + the listing photo -> ONE vision call (OpenAI, JSON mode).
The model answers fixed yes/no questions per frame; the verdict is computed HERE from those answers (not left to the model):

    FAIL if any frame shows: a different product than the photo (colour / print / label / shape), the product changing between
    frames, an object floating (not in a hand, not on a surface), an object appearing or vanishing, more than 2 hands,
    a hand or arm not joined to a body, or more than 5 fingers on a hand.

    python3 clip_check.py <clip.mp4> [listing_photo.jpg] [--start S] [--product "text"]   one clip, prints JSON
    from clip_check import check_clip                                                     used by pipeline.finish

Paid: one small vision request per product clip (model OPENAI_QC_MODEL, default gpt-5-mini). Never re-sent automatically."""
import base64, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import product_planner as PP   # noqa: E402  (key loading, call(), response_text())

QC_MODEL = PP.env("OPENAI_QC_MODEL", "gpt-5-mini")
TIMES = (0.2, 1.0, 2.0, 3.0, 3.8)
QUESTIONS = (
    "For EACH frame answer with booleans only:\n"
    "  same_product: the main product is the SAME item as in the PRODUCT PHOTO (same colour, print, label text, shape)\n"
    "  product_unchanged: the product looks the same as in frame 1 (no morphing, no change of size, colour, label or parts)\n"
    "  supported: every object is held in a hand or rests on a surface (nothing floats in the air)\n"
    "  no_appearing: no object appears or vanishes compared with frame 1\n"
    "  hands_ok: at most 2 hands, every hand and arm joined to the body, at most 5 fingers per hand\n"
    "If no product is visible in a frame, set same_product and product_unchanged to true for that frame and say so in note.\n"
    "Return JSON only: {\"frames\": [{\"t\": <seconds>, \"same_product\": bool, \"product_unchanged\": bool, \"supported\": bool, "
    "\"no_appearing\": bool, \"hands_ok\": bool, \"note\": \"<=15 words, only if something is false\"}]}")
KEYS = ("same_product", "product_unchanged", "supported", "no_appearing", "hands_ok")
LABEL = {"same_product": "not the listed product", "product_unchanged": "product changes during the clip",
         "supported": "object floating", "no_appearing": "object appears or vanishes", "hands_ok": "hands / fingers wrong"}


def _b64(path):
    return "data:image/jpeg;base64," + base64.b64encode(open(path, "rb").read()).decode()


def frames(clip, start=0.0, times=TIMES, width=480):
    tmp = tempfile.mkdtemp(prefix="clipcheck_")
    out = []
    for t in times:
        p = os.path.join(tmp, f"f_{t:.1f}.jpg")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start + t:.3f}", "-i", clip, "-frames:v", "1",
                        "-vf", f"scale={width}:-2", "-q:v", "3", p], check=True)
        if os.path.exists(p):
            out.append((t, p))
    return out


def check_clip(clip, photo=None, start=0.0, product=""):
    """-> {"verdict": PASS|FAIL, "issues": [...], "frames": [...], "usage": {...}}  (raises on a failed request: never re-sent)"""
    fr = frames(clip, start)
    if not fr:
        return {"verdict": "FAIL", "issues": ["clip cannot be read"], "frames": []}
    content = [{"type": "input_text", "text": (f"PRODUCT: {product}\n" if product else "") +
                ("Image 1 is the PRODUCT PHOTO from the listing. " if photo else "There is no listing photo: judge consistency only. ") +
                f"The next {len(fr)} images are frames of ONE 4-second video clip at {', '.join(f'{t:g} s' for t, _ in fr)}.\n"
                + QUESTIONS}]
    if photo and os.path.exists(photo):
        content.append({"type": "input_image", "image_url": _b64(photo)})
    content += [{"type": "input_image", "image_url": _b64(p)} for _, p in fr]
    body = {"model": QC_MODEL, "input": [{"role": "user", "content": content}], "reasoning": {"effort": "low"},
            "text": {"format": {"type": "json_object"}}, "max_output_tokens": 4000}
    resp = PP.call(body)
    ans = json.loads(PP.response_text(resp))
    rows = ans.get("frames") if isinstance(ans, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"clip check reply has no frames: {str(ans)[:200]}")
    issues = []
    for r in rows:
        for k in KEYS:
            if r.get(k) is False:
                issues.append(f"{r.get('t', '?')} s: {LABEL[k]}" + (f" ({r['note']})" if r.get("note") else ""))
    return {"verdict": "FAIL" if issues else "PASS", "issues": issues, "frames": rows, "model": QC_MODEL,
            "usage": resp.get("usage")}


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a:
        raise SystemExit(__doc__)
    st = float(a[a.index("--start") + 1]) if "--start" in a else 0.0
    pr = a[a.index("--product") + 1] if "--product" in a else ""
    pos = [x for i, x in enumerate(a) if not x.startswith("--") and (i == 0 or a[i - 1] not in ("--start", "--product"))]
    print(json.dumps(check_clip(pos[0], pos[1] if len(pos) > 1 else None, st, pr), indent=1, ensure_ascii=False))
