"""23-Nov (PIPELINE_SPEED_PROMPT_AB.md, change B): ONE adaptive queue for every Nano Banana image request from every row
process. Omni accepts about 100-120 images per hour for the project; sending faster only produces IMAGE_RATE_LIMITED
rejections, and before this change a second rejection stopped the whole row (6.5 min of stops + 6 min of restarts per reel).

AIMD on one shared gap (state file under a file lock, like run_row.pace()):
  start 30 s between image requests (all processes together);
  10 accepted in a row  -> gap x 0.9 (min 15 s);
  IMAGE_RATE_LIMITED    -> gap x 2   (max 120 s), and the rejected request waits for its next turn (a rejection is not billed).
Clips, uploads and status polls do not use this queue.

    t = ticket(); sleep_until(t)   reserve the next send slot and wait for it
    accepted() / rejected()        report the outcome
    state_line()                   gap, sent and rejected in the last hour, requests waiting (for image_queue.log)"""
import fcntl, json, os, tempfile, time

START_GAP, MAX_GAP, SPEEDUP_AFTER = 30.0, 120.0, 10
MIN_GAP = float(os.environ.get("FK_IMG_MIN_GAP", "15"))   # 23-Nov: lower it if Omni's image limit is raised (Nano Banana 2 has a higher one)
_DIR = os.environ.get("FK_STATE_DIR") or ("/private/tmp" if os.path.isdir("/private/tmp") else tempfile.gettempdir())
STATE = os.path.join(_DIR, "fk_image_queue.json")


def _edit(fn):
    with open(STATE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0); raw = f.read().strip()
            try:
                s = json.loads(raw) if raw else {}
            except ValueError:
                s = {}
            s.setdefault("gap", START_GAP); s.setdefault("next_at", 0.0); s.setdefault("streak", 0)
            s.setdefault("sent", []); s.setdefault("rejected", []); s.setdefault("waiting", [])
            now = time.time()
            for k in ("sent", "rejected"):
                s[k] = [t for t in s[k] if t > now - 3600]
            s["waiting"] = [t for t in s["waiting"] if t > now]
            out = fn(s, now)
            f.seek(0); f.truncate(); f.write(json.dumps(s)); f.flush()
            return out
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


def ticket():
    """Reserve the next free send slot (FIFO across processes). Returns the time to send at."""
    def f(s, now):
        t = max(now, s["next_at"])
        s["next_at"] = t + s["gap"]; s["waiting"].append(t)
        return t
    return _edit(f)


def sleep_until(t):
    w = t - time.time()
    if w > 0:
        time.sleep(w)


def accepted():
    def f(s, now):
        s["sent"].append(now); s["streak"] += 1
        if s["streak"] >= SPEEDUP_AFTER:
            s["gap"] = max(MIN_GAP, s["gap"] * 0.9); s["streak"] = 0
    _edit(f)


def rejected():
    def f(s, now):
        s["rejected"].append(now); s["streak"] = 0
        s["gap"] = min(MAX_GAP, s["gap"] * 2)
        s["next_at"] = max(s["next_at"], now + s["gap"])     # everyone backs off, not only this request
    _edit(f)


def state_line():
    return _edit(lambda s, now: f"{time.strftime('%Y-%m-%d %H:%M:%S')} gap {s['gap']:.1f} s | sent last hour {len(s['sent'])} | "
                                f"rejected last hour {len(s['rejected'])} | waiting {len(s['waiting'])}")


def maybe_log(path, every=60):
    """Append state_line() to path at most once a minute across all processes."""
    def f(s, now):
        if now - s.get("logged_at", 0) < every:
            return None
        s["logged_at"] = now
        return (f"{time.strftime('%Y-%m-%d %H:%M:%S')} gap {s['gap']:.1f} s | sent last hour {len(s['sent'])} | "
                f"rejected last hour {len(s['rejected'])} | waiting {len(s['waiting'])}")
    line = _edit(f)
    if line:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            open(path, "a").write(line + "\n")
        except OSError:
            pass
