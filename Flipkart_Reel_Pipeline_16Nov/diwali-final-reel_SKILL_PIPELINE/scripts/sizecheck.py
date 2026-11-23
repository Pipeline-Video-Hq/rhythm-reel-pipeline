"""SIZE CHECK (22-Nov, user: "the dimensions must stay the same across the video"). Free and local (OpenCV).
For sampled frames of a clip it measures two scales against the clip's first frame with feature matching:
  - the scene scale (everything outside the product box: the camera push-in), and
  - the product scale (features inside the product box).
If the product grows or shrinks more than 12 % relative to the scene, the product changed size on its own -> flagged."""
import cv2, numpy as np


def _frame(path, t):
    cap = cv2.VideoCapture(path); cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000); ok, f = cap.read(); cap.release()
    return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) if ok else None


def _scale(a, b, mask):
    orb = cv2.ORB_create(1500)
    ka, da = orb.detectAndCompute(a, mask); kb, db = orb.detectAndCompute(b, None)
    if da is None or db is None or len(ka) < 12:
        return None
    m = sorted(cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True).match(da, db), key=lambda x: x.distance)[:300]
    if len(m) < 12:
        return None
    pa = np.float32([ka[x.queryIdx].pt for x in m]); pb = np.float32([kb[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, method=cv2.RANSAC, ransacReprojThreshold=4.0)
    if M is None or inl is None or inl.sum() < 10:
        return None
    return float(np.sqrt(abs(np.linalg.det(M[:, :2]))))


def check(clip, box, times=(1.0, 2.0, 3.0, 3.8), limit=0.12, zoom=None, action_end=2.5):
    """box = product box in the first frame, normalised (x, y, w, h), origin top-left. Returns (flags, rows)."""
    f0 = _frame(clip, 0.05)
    if f0 is None:
        return [], []
    H, W = f0.shape
    x, y, w, h = box
    inside = np.zeros_like(f0); inside[int(y * H):int((y + h) * H), int(x * W):int((x + w) * W)] = 255
    outside = 255 - inside
    rows, flags = [], []
    for t in times:
        ft = _frame(clip, t)
        if ft is None:
            continue
        sg, sp = _scale(f0, ft, outside), _scale(f0, ft, inside)
        if sg is None and zoom:          # too little background to measure: compare with the planned push-in instead
            sg = 1 + (zoom - 1) * max(0.0, min(1.0, (t - action_end) / (4.0 - action_end)))
        rows.append(dict(t=t, scene=sg, product=sp))
        if sg and sp and abs(sp / sg - 1) > limit:
            flags.append(dict(t=t, scene=round(sg, 3), product=round(sp, 3), change=f"{100 * (sp / sg - 1):+.0f}%"))
    return flags, rows
