"""RUN ROW v2 (22-Nov) - the whole planned reel for one row with NO Claude worker: reference sheets, room masters, stills,
4 s clips (360p, first/last frame), plan.json, finish. Talks to the TrueFan Omni MCP over HTTP (token in beauty_pipeline/.env).
PAID - run only after the user's yes.

    FK_MODE=BAU python3 run_row.py <row> --dry                 free: walks the whole run offline, lists every request, catches problems
    FK_MODE=BAU python3 run_row.py <row> --confirmed           run one row (resumes where it stopped)
    FK_MODE=BAU python3 run_row.py launch <row> <row> ... --confirmed   several rows in parallel, detached, Mac kept awake
    FK_MODE=BAU python3 run_row.py status [<row> ...]          one line per row (free)

Approved fallbacks (each is a NEW request or a free local step, so use them only after the user's yes):
    --sheet-alt=<slot>:<k>   make that slot's reference sheet from listing photo k (p<slot>_<k>.jpg) instead of photo 1
    --sheet-pro=<slot,..>    make those slots' reference sheets with Nano Banana Pro
    --sheet-photo=<slot,..>  no sheet request: the listing photo itself is the reference sheet (free)
    --local-photo=<slot,..>  photo-only shots: build the start/end stills locally from the listing photo (free, no image request)

Robustness (why it is built this way):
  * one process per row (lock file) - two processes can never send the same row twice;
  * ALL sends from ALL processes share one pacer: at least 2 s apart, however many rows run in parallel;
  * a failed request is NEVER re-sent by the script (only a rate-limit rejection waits once and sends once more); the run stops,
    writes row_NNN/STOPPED.json with what failed and the ready fallbacks, and everything made so far is kept;
  * a timeout on a paid request is never re-sent (it may have been accepted) - the run stops and says so;
  * a clip's generation_id is saved the moment it is queued, so a resume polls it instead of paying again;
  * every asset remembers the prompt it was made from; a changed plan never silently reuses an old asset;
  * all shots files are read once at the start (a rebuild during the run cannot change it);
  * downloads are checked and retried (free); clips are trimmed/padded to exactly 4.000 s (original kept);
  * 23-Nov (Garvit): plan and limb checks stop the row BEFORE payment; clips already paid for are always assembled, and
    a reel that fails a finish check is kept but marked qc/FAILED.json (never filed or uploaded). FK_LAX no longer skips these;
  * the Mac is kept awake while the run lives; nothing is ever deleted.
"""
import fcntl, glob, hashlib, json, os, re, shutil, socket, subprocess, sys, time, urllib.error, urllib.request
# 23-Nov: FK_LAX no longer defaults on (plan, limb and finish checks always apply)
import continuity, limbguard, imgqueue, netwait
import pipeline as P

FOLDER = "Flipkart_Fashion-Rhythm_AI_Profiles"
BEAUTY_ENV = os.path.join(P.PIPE, "beauty_pipeline", ".env")
GAP = 1.0                 # user 23-Nov: requests 1 s apart (shared by every process; was 2 s)
RATE_WAIT = 75            # one wait after a rate-limit rejection
PROMPT_WARN, PROMPT_HARD = 16000, 19500    # Omni's prompt limit is 20000 characters
PACE_FILE = "/private/tmp/fk_omni_pace"
IMAGE_MODEL = os.environ.get("FK_IMAGE_MODEL", "gemini-3.1-flash-image")   # 23-Nov: switch with FK_IMAGE_MODEL=<id> (list: omni_models.py)
IMG_REQUEUES = 20         # 23-Nov change B: a rate-limited image waits in the queue up to 20 times, then the row stops
QUEUE_LOG = os.path.join(os.path.dirname(P.WORK), "image_queue.log")
DRY = False
SHEET_PROMPT = ("Product reference sheet of the EXACT product in Image 1, unchanged - do not substitute another design. One 3:2 "
                "image on a seamless pure white background, a 3 x 2 grid of six equal panels separated only by white space (no lines, "
                "no text): 1 front, 2 three-quarter front-left, 3 three-quarter front-right, 4 left side, 5 rear, 6 top-down (or open). "
                "ONLY ONE piece of the product (if Image 1 shows a set, the largest piece). Same scale in every panel, soft even studio "
                "light, faint contact shadow. Every colour, print, part and printed text exactly as in Image 1. Remove every sticker, "
                "price tag, label that is not printed on the product, badge, overlay text, watermark, prop, model or hand. Clothing on "
                "an invisible ghost mannequin; footwear as the pair. Photoreal, sharp.")


class StopRun(Exception):
    pass


def _env():
    if "OMNI_MCP_URL" not in os.environ:
        for line in open(BEAUTY_ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    return os.environ["OMNI_MCP_URL"], {"Authorization": f"Bearer {os.environ['OMNI_TOKEN']}", "Content-Type": "application/json",
                                        "Accept": "application/json, text/event-stream"}


def pace():
    """One shared clock for every process: no two sends closer than GAP seconds."""
    with open(PACE_FILE, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0); s = f.read().strip()
        last = float(s) if s else 0.0
        w = last + GAP - time.time()
        if w > 0:
            time.sleep(w)
        f.seek(0); f.truncate(); f.write(str(time.time())); f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)


CALLS = {"image": 0, "video": 0, "upload": 0}


def tool(name, **args):
    paid = name in ("generate_nano_banana_image", "generate_video")
    if DRY:
        if name == "generate_nano_banana_image":
            CALLS["image"] += 1; return {"image_asset_id": f"dry_img_{CALLS['image']}", "image_url": None}
        if name == "generate_video":
            CALLS["video"] += 1; return {"generation_id": f"dry_gen_{CALLS['video']}"}
        if name == "get_generation_status":
            return {"status": "completed", "video_url": None, "video_asset_id": "dry_vid"}
        CALLS["upload"] += 1; return {"upload_command": "echo", "dry": True}
    url, hdr = _env()
    is_img = name == "generate_nano_banana_image"
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}}).encode()
    attempt, requeues, video_rl = 0, 0, False
    while True:
        # 23-Nov (PIPELINE_SPEED_PROMPT_AB.md change B): every image request waits its turn in ONE adaptive queue shared by
        # all rows; clips and uploads keep the 1 s clock; status polls are not paced
        if is_img:
            imgqueue.sleep_until(imgqueue.ticket())
        elif paid or name == "upload_media":
            pace()
        attempt += 1
        try:
            with urllib.request.urlopen(urllib.request.Request(url, body, hdr), timeout=300) as r:
                raw = r.read().decode()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                raise StopRun(f"{name}: Omni refused the token (HTTP {e.code}) - the OMNI_TOKEN in beauty_pipeline/.env is wrong or expired")
            if paid:
                raise StopRun(f"{name}: HTTP {e.code} - NOT re-sent")
            if attempt >= 3:
                raise StopRun(f"{name}: HTTP {e.code}")
            time.sleep(5); continue
        except (socket.timeout, TimeoutError, urllib.error.URLError, OSError) as e:
            if netwait.not_sent(e):    # 23-Nov cause 3: DNS / refused / TLS - never reached Omni, not billed: wait, then send
                attempt -= 1
                netwait.wait_for_network(url, log=lambda m: print(f"{name}: {m}", flush=True)); continue
            if paid:
                raise StopRun(f"{name}: no answer ({e}) - Omni may have accepted it, so it was NOT re-sent; check the Omni assets "
                              f"for the folder before sending again")
            if attempt >= 3:
                raise StopRun(f"{name}: no answer ({e})")
            time.sleep(5); continue
        try:   # 23-Nov: an unexpected reply never crashes the run without STOPPED.json (and its text is kept for the ids)
            if raw.lstrip().startswith(("event:", "data:")):
                raw = next(l[5:] for l in raw.splitlines() if l.startswith("data:"))
            env_ = json.loads(raw)
            if "result" not in env_:
                raise StopRun(f"{name}: Omni error {json.dumps(env_.get('error', env_))[:400]}" + (" - NOT re-sent" if paid else ""))
            res = env_["result"]
            if not res.get("isError"):
                out_ = res.get("structuredContent") or json.loads(res["content"][0]["text"])
                if not isinstance(out_, dict):
                    raise ValueError("reply is not an object")
                if is_img:
                    imgqueue.accepted(); imgqueue.maybe_log(QUEUE_LOG)
                return out_
            msg = res["content"][0]["text"]
        except StopRun:
            raise
        except (StopIteration, ValueError, KeyError, IndexError, TypeError) as e:
            raise StopRun(f"{name}: unreadable reply ({e}) - " + ("NOT re-sent; " if paid else "") + f"raw: {raw[:400]}")
        if "RATE_LIMIT" in msg.upper():
            if is_img and requeues < IMG_REQUEUES:   # a rejection is not an image (not billed): back off, wait for the next turn
                requeues += 1; imgqueue.rejected(); imgqueue.maybe_log(QUEUE_LOG); continue
            if paid and not video_rl:                # clips: wait once and send once more (unchanged)
                video_rl = True; time.sleep(RATE_WAIT); continue
        raise StopRun(f"{name}: {msg[:500]}")


def log(d, msg):
    if DRY:
        print("  " + msg, flush=True); return
    open(os.path.join(d, "log.md"), "a").write(f"- {time.strftime('%H:%M:%S')} {msg}\n"); print(msg, flush=True)


def H(*a):
    return hashlib.sha1(json.dumps(a, sort_keys=True, default=str).encode()).hexdigest()[:12]


def fetch(url, path, kind="image"):
    if DRY:
        return
    last = None
    for _ in range(3):
        try:
            urllib.request.urlretrieve(url, path)
            if os.path.getsize(path) < 1000:
                raise IOError("empty download")
            if kind == "image":
                from PIL import Image
                Image.open(path).verify()
            return
        except Exception as e:            # downloads are free: retry
            last = e; time.sleep(3)
    raise StopRun(f"download of {os.path.basename(path)} failed ({last}); the asset is kept in Omni, nothing was re-generated")


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def normalize_clip(path, want=4.0):
    """Exactly 4.000 s: trim a longer clip, hold the last frame of a slightly shorter one. The original is kept."""
    D = duration(path)
    if D <= 0:
        raise StopRun(f"{os.path.basename(path)} cannot be read (broken file)")
    if abs(D - want) <= 0.03:
        return D, "ok"
    if D < want - 0.45:
        raise StopRun(f"{os.path.basename(path)} is only {D:.2f} s (needs 4.0 s) - it has to be generated again (ask the user)")
    shutil.copy2(path, path[:-4] + ".orig.mp4")
    tmp = path[:-4] + ".norm.mp4"
    vf = f"tpad=stop_mode=clone:stop_duration={want - D + 0.05:.3f}" if D < want else "null"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-vf", vf, "-t", f"{want:.3f}", "-an", "-c:v", "libx264",
                    "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", tmp], check=True)
    os.replace(tmp, path)
    return duration(path), f"fixed from {D:.2f} s"


def upload(path):
    if DRY:
        tool("upload_media"); return "dry_upload"
    r = tool("upload_media", method="service_command", filename=os.path.basename(path),
             mime_type="image/png" if path.endswith(".png") else "image/jpeg")
    out = subprocess.run(r["upload_command"].replace("LOCAL_FILE_PATH", path), shell=True, capture_output=True, text=True)
    try:
        return json.loads(out.stdout)["asset_id"]
    except Exception:
        raise StopRun(f"upload of {os.path.basename(path)} failed: {(out.stdout or out.stderr)[:300]}")


def local_plate(src, dst, zoom=1.0):
    """Free, local 9:16 plate from an original listing photo: the photo over a blurred copy of itself (zoom>1 = push-in crop)."""
    from PIL import Image, ImageFilter
    im = Image.open(src).convert("RGB"); W, Hh = 1080, 1920
    bg = im.copy(); s = max(W / bg.width, Hh / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1)).filter(ImageFilter.GaussianBlur(40))
    bg = bg.crop(((bg.width - W) // 2, (bg.height - Hh) // 2, (bg.width - W) // 2 + W, (bg.height - Hh) // 2 + Hh))
    f = min(W / im.width, (Hh * 0.8) / im.height); fg = im.resize((int(im.width * f), int(im.height * f)))
    bg.paste(fg, ((W - fg.width) // 2, (Hh - fg.height) // 2))
    if zoom > 1.0:
        cw, ch = int(W / zoom), int(Hh / zoom)
        bg = bg.crop(((W - cw) // 2, (Hh - ch) // 2, (W - cw) // 2 + cw, (Hh - ch) // 2 + ch)).resize((W, Hh))
    bg.save(dst, quality=93)


def clip_limb_report(d, n, clip):
    """Report only (never blocks): Apple Vision hand/face count on 5 frames of the finished clip -> limbs_report.json."""
    if os.environ.get("FK_LIMB_GUARD") == "0":
        return
    try:
        fr = os.path.join(d, "work", "limbframes"); os.makedirs(fr, exist_ok=True); paths = []
        for t in (0.2, 1.0, 2.0, 3.0, 3.8):
            p = os.path.join(fr, f"slot{n}_{t}.jpg")
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", clip, "-frames:v", "1", "-vf", "scale=720:-1", p], check=True)
            paths.append(p)
        infos = limbguard.scan(paths); bad = []
        for t, i in zip((0.2, 1.0, 2.0, 3.0, 3.8), infos):
            ok, why = limbguard.verdict(i, True)
            if not ok:
                bad.append(dict(t=t, why=why))
        rp = os.path.join(d, "limbs_report.json")
        rep = json.load(open(rp)) if os.path.exists(rp) else {}
        rep[str(n)] = dict(frames=len(paths), flagged=bad); json.dump(rep, open(rp, "w"), indent=1)
        if bad:
            log(d, f"limb report: slot {n} clip - {len(bad)} of {len(paths)} sampled frames show {bad[0]['why']} (report only)")
    except Exception as e:
        log(d, f"note: limb report for slot {n} could not run ({e})")


def clip_size_report(d, n, clip, f):
    """Report only: does the product change size relative to the scene during the clip? (sizecheck.py, OpenCV, free)"""
    try:
        import sizecheck
        st = os.path.join(d, "plates", f["start_still"]["name"] + ".jpg")
        i = limbguard.scan([st])[0] if os.path.exists(st) else {}
        s_ = i.get("sal") or [0.25, 0.25, 0.5, 0.5]
        z = (f["end_still"].get("locked") or f["end_still"].get("composite") or {}).get("zoom", 1.4)
        flags, rows = sizecheck.check(clip, (s_[0], 1 - (s_[1] + s_[3]), s_[2], s_[3]), zoom=z)
        rp = os.path.join(d, "size_report.json"); rep = json.load(open(rp)) if os.path.exists(rp) else {}
        rep[str(n)] = dict(flagged=flags, rows=rows); json.dump(rep, open(rp, "w"), indent=1)
        if flags:
            log(d, f"size report: slot {n} - the product changes size by itself ({flags[0]['change']} at {flags[0]['t']} s) - report only")
    except Exception as e:
        log(d, f"note: size report for slot {n} could not run ({e})")


def opts_of(argv):
    o = {"sheet_alt": {}, "sheet_pro": set(), "sheet_photo": set(), "local_photo": set(), "accept": set(), "regen": set(), "cands": 1, "only": set(), "redo": set()}
    for a in argv:
        if a.startswith("--sheet-alt="):
            for x in a.split("=", 1)[1].split(","):
                s, k = x.split(":"); o["sheet_alt"][int(s)] = int(k)
        elif a.startswith("--sheet-pro="):
            o["sheet_pro"] = {int(x) for x in a.split("=", 1)[1].split(",")}
        elif a.startswith("--sheet-photo="):
            o["sheet_photo"] = {int(x) for x in a.split("=", 1)[1].split(",")}
        elif a.startswith("--accept-limbs="):
            o["accept"] = set(a.split("=", 1)[1].split(","))
        elif a == "--sheets-only":
            o["sheets_only"] = True
        elif a.startswith("--only="):
            o["only"] = {int(x) for x in a.split("=", 1)[1].split(",")}
        elif a.startswith("--redo="):
            o["redo"] = {int(x) for x in a.split("=", 1)[1].split(",")}
        elif a.startswith("--regen="):
            o["regen"] = set(a.split("=", 1)[1].split(","))
        elif a.startswith("--candidates="):
            o["cands"] = max(1, min(3, int(a.split("=", 1)[1])))
        elif a.startswith("--local-photo="):
            o["local_photo"] = {int(x) for x in a.split("=", 1)[1].split(",")}
    return o


class Ctx:
    pass


def run(row, o):
    d = P.rdir(row); v = P.BATCH[str(row)]
    c = Ctx(); c.d = d
    ap = os.path.join(d, "asset_ids.json")
    c.ids = json.load(open(ap)) if os.path.exists(ap) else {}
    if DRY and "--fresh" in sys.argv:      # free what-if: count everything as if the row were run from scratch
        c.ids = {}
    c.ids.setdefault("_meta", {})
    import threading, concurrent.futures
    _lk = threading.RLock()

    class _Locked(dict):
        """23-Nov: every change to the asset ids happens under the same lock as save() (pictures are made in parallel threads;
        an unlocked change during the dump crashed the row and could lose the newest paid id)."""
        def __setitem__(self, k, v):
            with _lk:
                dict.__setitem__(self, k, v)
        def __delitem__(self, k):
            with _lk:
                dict.__delitem__(self, k)
        def pop(self, *a):
            with _lk:
                return dict.pop(self, *a)
        def setdefault(self, k, v=None):
            with _lk:
                if isinstance(v, dict) and not isinstance(v, _Locked):
                    v = _Locked(v)
                return dict.setdefault(self, k, v)
        def update(self, *a, **kw):
            with _lk:
                dict.update(self, *a, **kw)
    c.ids = _Locked({k: (_Locked(v) if isinstance(v, dict) else v) for k, v in c.ids.items()})

    def save():
        if DRY:
            return
        with _lk:      # several pictures are made at the same time (user 22-Nov: minimum time)
            txt_ = json.dumps(c.ids, indent=1)
            open(ap + ".tmp", "w").write(txt_); os.replace(ap + ".tmp", ap)

    def par(fn, items):
        """Run fn on every item AT THE SAME TIME (each send still waits its turn on the shared 2 s clock); the first failure stops the row."""
        items = list(items)
        if not items:
            return
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(items)) as ex_:
            for fut in [ex_.submit(fn, x) for x in items]:
                fut.result()
    ids = c.ids
    if not DRY:   # 23-Nov: the chosen image model must be one Omni accepts NOW (free check) - a typo never reaches a paid call
        try:
            import omni_models
            _ok = omni_models.models().get("generate_nano_banana_image")
        except Exception as e:      # noqa: BLE001
            _ok = None; log(d, f"note: could not read Omni's model list ({e}) - using {IMAGE_MODEL}")
        if _ok and IMAGE_MODEL not in _ok:
            raise StopRun(f"image model {IMAGE_MODEL} is not accepted by Omni (it accepts: {', '.join(_ok)}) - nothing was sent")
    # 23-Nov: every slot's assets belong to ONE product id. If the sheet's product for a slot changed, that slot's listing
    # upload, reference sheet, pictures and clip are moved aside (never deleted) and made again for the new product.
    if not DRY:
        for n_, u_ in enumerate(v["products"], 1):
            m_ = re.search(r"pid=([A-Za-z0-9]+)", u_); pid_ = m_.group(1) if m_ else None
            old_ = ids["_meta"].get(f"pid:{n_}")
            if old_ and pid_ and old_ != pid_:
                jk = os.path.join(d, "junk_pid_" + time.strftime("%H%M%S")); os.makedirs(jk, exist_ok=True)
                for rel in (f"specs/slot_{n_}/reference_sheet.png", f"plates/slot_{n_}_start.jpg", f"plates/slot_{n_}_end.jpg",
                            f"plates/slot_{n_}_end_action.jpg", f"clips/slot_{n_}.mp4"):
                    if os.path.exists(os.path.join(d, rel)):
                        shutil.move(os.path.join(d, rel), os.path.join(jk, rel.replace("/", "_")))
                for k in [k for k in list(ids) if k in (f"listing_{n_}", f"listing_alt_{n_}", f"sheet_{n_}", f"clip_gen:{n_}", f"clip_done:{n_}")
                          or k.startswith(f"slot_{n_}_")]:
                    ids.pop(k, None); ids["_meta"].pop(k, None)
                log(d, f"slot {n_}: product changed {old_} -> {pid_} - its old assets moved to {os.path.basename(jk)}, made again")
            if pid_:
                ids["_meta"][f"pid:{n_}"] = pid_
        save()
    log(d, f"RUN_ROW v2 start row {row} ({v['name']}, {v['vertical']})" + (" [DRY - nothing is sent]" if DRY else ""))
    sheets_only = bool(o.get("sheets_only"))
    if not DRY and not sheets_only:
        try:
            P.shots_row(row, quiet=True)          # rebuild from the saved plans (free), then read everything ONCE
        except SystemExit as e:                   # 23-Nov: a plan error stops the row BEFORE anything is paid for
            raise StopRun(f"plan check failed - nothing was sent: {e}")
    sd = os.path.join(d, "shots")
    if sheets_only:     # 23-Nov (user: faster, same quality): the 5 product sheets are made while OpenAI is still planning
        import product_planner as PP
        pids = [(re.search(r"pid=([A-Z0-9]+)", str(u)) or [None, ""])[1] for u in (v.get("products") or [])][:5]
        reel = dict(order=[1, 2, 3, 4, 5], rooms=[], room_of={})
        slots = {}
        for n_, pid_ in enumerate(pids, 1):     # the ruler size comes from the listing's own dimensions (Serper removed 23-Nov)
            try:
                sp_ = json.load(open(os.path.join(d, "specs", f"slot_{n_}.json")))
            except (OSError, ValueError):
                sp_ = {}
            ss_ = PP.listing_size(sp_)
            slots[n_] = dict(sheet_scale=(ss_["dims"] if ss_ else ""))
        rooms, skeleton = {}, {}
    else:
        reel = json.load(open(os.path.join(d, "reel_plan.json")))
    only = o["only"] or set(reel["order"])
    for n in sorted(o["redo"]):      # approved redo of ONE slot: the old pictures/clip are moved to junk (never deleted), new ones are made
        junk = os.path.join(d, "junk_" + time.strftime("%H%M%S")); 
        for rel in (f"plates/slot_{n}_start.jpg", f"plates/slot_{n}_end.jpg", f"plates/slot_{n}_end_action.jpg", f"clips/slot_{n}.mp4"):
            p_ = os.path.join(d, rel)
            if os.path.exists(p_) and not DRY:
                os.makedirs(junk, exist_ok=True); shutil.move(p_, os.path.join(junk, os.path.basename(p_)))
        for k in (f"slot_{n}_start", f"slot_{n}_end", f"slot_{n}_end_action", f"slot_{n}_open_sheet", f"clip_gen:{n}", f"clip_done:{n}"):
            c.ids.pop(k, None); c.ids["_meta"].pop(k, None)
        if not DRY:
            json.dump(c.ids, open(ap, "w"), indent=1)
        log(d, f"slot {n}: redo approved - old pictures and clip moved aside, made again")
    if not sheets_only:
        slots = {n: json.load(open(os.path.join(sd, f"slot_{n}.json"))) for n in reel["order"]}
        rooms = {r: json.load(open(os.path.join(sd, f"room_{r}.json"))) for r in reel["rooms"]}
        skeleton = json.load(open(os.path.join(sd, "plan_skeleton.json")))
    names = {f"slot_{n}_reference_sheet": f"sheet_{n}" for n in range(1, 6)}
    names.update({f"slot_{n}_listing_photo": f"listing_{n}" for n in range(1, 6)})
    names.update({f"slot_{n}_open_sheet": f"slot_{n}_open_sheet" for n in range(1, 6)})

    def ref(nm, key):
        k = names.get(key, key)
        if k not in ids:
            raise StopRun(f"{nm}: reference '{key}' has no asset yet (order problem) - nothing was sent for it")
        return ids[k]

    def prompt_ok(nm, prompt):
        if len(prompt) > PROMPT_HARD:
            raise StopRun(f"{nm}: prompt is {len(prompt)} characters (Omni's limit is 20000) - not sent; shorten the plan text")
        if len(prompt) > PROMPT_WARN:
            log(d, f"note: {nm} prompt is long ({len(prompt)} characters)")
        if re.search(r"\bNone\b|\{[a-z_]+\}|\[object", prompt):
            log(d, f"note: {nm} prompt contains a placeholder-like text (None / {{x}}) - check shots/")

    def guard(nm, path, person=True):
        """Limb guard: count hands / faces / bodies with Apple Vision BEFORE the clip made from this picture is paid for."""
        if DRY or os.environ.get("FK_LIMB_GUARD") == "0" or nm in o["accept"] or not os.path.exists(path):
            return
        try:
            info = limbguard.scan([path])[0]
        except Exception as e:
            log(d, f"note: limb guard could not run on {nm} ({e})"); return
        ids["_meta"].setdefault("limb", {})[nm] = dict(hands=info["hands"], faces=info["faces"], bodies=info["bodies"])
        ok, why = limbguard.verdict(info, person)
        if not ok:
            raise StopRun(f"{nm}: possible extra limb / wrong picture - {', '.join(why)} (Apple Vision count) - the clip made from it is NOT generated")

    def make(nm, prompt, ref_keys, path, ar="9:16", model=None, person=None):
        if nm in o["regen"] and nm in ids:                    # user-approved regeneration of ONE picture (a new paid request)
            m_ = re.search(r"slot_(\d)", nm)
            if m_ and f"clip_gen:{m_.group(1)}" in ids:
                raise StopRun(f"{nm}: the clip of slot {m_.group(1)} is already queued - regenerating its still would not change it")
            junk = os.path.join(d, "plates", "junk"); os.makedirs(junk, exist_ok=True)
            if os.path.exists(path):
                shutil.move(path, os.path.join(junk, os.path.basename(path) + time.strftime(".%H%M%S")))
            ids.pop(nm); ids["_meta"].pop(nm, None); save(); log(d, f"{nm}: old picture moved to plates/junk, generating it again (approved)")
        refs = [ref(nm, x) for x in ref_keys]
        h = H(prompt, ref_keys, ar, model)
        if nm in ids:
            old = ids["_meta"].get(nm)
            if old and old != h and nm.startswith(("room_master:", "sheet_")):   # rooms and product sheets are always reused
                ids["_meta"][nm] = h; save(); log(d, f"{nm}: reused (its prompt wording changed since; the picture is kept)"); return
            if old and old != h:
                raise StopRun(f"{nm}: this asset was made from a different prompt (the plan changed since) - it is NOT regenerated; "
                              f"ask the user before regenerating")
            ids["_meta"].setdefault(nm, h); save(); return
        prompt_ok(nm, prompt)
        # 23-Nov (Garvit): Nano Banana 2 = gemini-3.1-flash-image (cheaper, better, higher rate limit) pinned explicitly, so a
        # change of the server's default can never swap the model; Pro only where a slot asks for it (--sheet-pro)
        args = dict(prompt=prompt, image_asset_ids=refs, aspect_ratio=ar, folder=FOLDER, model=model or IMAGE_MODEL)
        if False and o["cands"] > 1 and person is not None:   # best-of-N disabled (user 22-Nov: no automatic checks): N renders (each billed), the cleanest by hand count is kept
            args["generations"] = o["cands"]
        r = tool("generate_nano_banana_image", **args)
        if False and o["cands"] > 1 and person is not None and r.get("images"):
            best = None
            for i, im in enumerate(r["images"]):
                aid = im.get("image_asset_id") or im.get("asset_id"); url = im.get("image_url") or im.get("url")
                tmp = f"{path}.cand{i}.jpg"; fetch(url, tmp)
                try:
                    inf = limbguard.scan([tmp])[0]; okc, why = limbguard.verdict(inf, person); sc = (0 if okc else 1, inf["hands"], inf["faces"])
                except Exception:
                    sc = (0, 0, 0)
                if best is None or sc < best[0]:
                    best = (sc, aid, tmp)
            ids[nm] = best[1]; ids["_meta"][nm] = h; save(); shutil.copy2(best[2], path); log(d, f"{nm} best of {len(r['images'])}: {best[1]} (score {best[0]})")
        else:
            ids[nm] = r["image_asset_id"]; ids["_meta"][nm] = h; save()
            fetch(r["image_url"], path); log(d, f"{nm} {ids[nm]}")

    def need_listing(n):
        if f"listing_{n}" not in ids:
            ids[f"listing_{n}"] = upload(os.path.join(d, "products", f"p{n}_1.jpg")); save()

    # 1) reference sheets (one per product; a photo-only shot starts from the listing photo itself and needs none)
    def sheet_job(n):
        if n not in only:
            return
        sp = os.path.join(d, "specs", f"slot_{n}"); os.makedirs(sp, exist_ok=True)
        need_listing(n)
        if f"sheet_{n}" in ids or slots.get(n, {}).get("photo_shot"):
            return
        if n in o["sheet_photo"]:
            ids[f"sheet_{n}"] = ids[f"listing_{n}"]; save(); log(d, f"slot {n}: the listing photo is its reference sheet (no request)"); return
        keys = [f"listing_{n}"]
        if n in o["sheet_alt"]:
            alt = os.path.join(d, "products", f"p{n}_{o['sheet_alt'][n]}.jpg")
            ids[f"listing_alt_{n}"] = ids.get(f"listing_alt_{n}") or upload(alt); keys = [f"listing_alt_{n}"]
        _sc = str(slots.get(n, {}).get("sheet_scale", "")).strip()
        _sp = SHEET_PROMPT + ((f" SIZE GUIDE (panel 6 only): lay a plain 30 cm wooden ruler with clear centimetre marks right beside the product, "
                               f"at the SAME scale as the product, so its real size ({_sc}) can be read; the ruler is only a guide, not part of the product.")
                              if re.search(r"\d", _sc) else "")
        make(f"sheet_{n}", _sp, keys, os.path.join(sp, "reference_sheet.png"), "3:2",
             "gemini-3-pro-image" if n in o["sheet_pro"] else None)
    for n in range(1, 6):          # uploads first (cheap), then every sheet at once
        if n in only:
            os.makedirs(os.path.join(d, "specs", f"slot_{n}"), exist_ok=True); need_listing(n)
    if "persona_sheet" not in ids:
        ids["persona_sheet"] = upload(os.path.join(P.OMNI, "personas", f"{v['name'].lower()}.jpg")); save()
    # 2) room masters
    os.makedirs(os.path.join(d, "plates"), exist_ok=True); os.makedirs(os.path.join(d, "clips"), exist_ok=True)
    def room_job(rf):
        r, f = rf
        if not any(reel["room_of"][str(n_)] == r for n_ in only):
            return
        make(f"room_master:{r}", f["prompt"], f["refs"], os.path.join(d, "plates", f"room_{r}.jpg"), person=True)
    if sheets_only:
        par(sheet_job, range(1, 6)); log(d, "product sheets ready (made while planning)"); return
    _rooms = list(rooms.items())     # product sheets and the first room picture at the same time; a second room needs the first
    par(lambda job: job(), [(lambda n=n: sheet_job(n)) for n in range(1, 6)] + ([lambda: room_job(_rooms[0])] if _rooms else []))
    par(room_job, _rooms[1:])
    # 3) stills + 4) clips (queued as soon as their stills exist; a saved generation_id is polled, never re-queued)
    def slot_job(n):
        if n not in only:
            return
        f = slots[n]
        if f.get("open_sheet"):
            op = f["open_sheet"]; make(op["name"], op["prompt"], op["refs"], os.path.join(d, "specs", f"slot_{n}", "open_sheet.png"), "3:2")
        if f.get("photo_shot") and n in o["local_photo"]:
            for key, z in (("start_still", 1.0), ("end_still", 1.3)):
                k = f[key]["name"]
                if k not in ids:
                    dst = os.path.join(d, "plates", k + ".jpg")
                    if not DRY:
                        local_plate(os.path.join(d, "products", f"p{n}_1.jpg"), dst, z)
                    ids[k] = upload(dst) if not DRY else "dry_local"; ids["_meta"][k] = "local"; save()
                    log(d, f"{k} built locally from the listing photo (no request)")
        else:
            make(f["start_still"]["name"], f["start_still"]["prompt"], f["start_still"]["refs"],
                 os.path.join(d, "plates", f["start_still"]["name"] + ".jpg"), person=True)
            # 23-Nov Garvit 'block before pay': free local hand/face count BEFORE the clip is paid for (--accept-limbs=<name> overrides)
            guard(f["start_still"]["name"], os.path.join(d, "plates", f["start_still"]["name"] + ".jpg"), person=True)
            if f["end_still"].get("first_only"):   # 23-Nov: the clip gets only the first picture - the video model moves the camera itself
                pass
            elif f["end_still"].get("locked"):  # LOCKED END FRAME: the first frame, closer (local crop, free, nothing generated)
                k = f["end_still"]["name"]
                if k not in ids:
                    dst = os.path.join(d, "plates", k + ".jpg")
                    if not DRY:
                        _sp = os.path.join(d, "plates", f["start_still"]["name"] + ".jpg")
                        _refs = [os.path.join(d, "products", f"p{n}_{k_}.jpg") for k_ in (1, 2, 3)] + [os.path.join(d, "specs", f"slot_{n}", "reference_sheet.png")]
                        _c = continuity.product_center(_sp, [x for x in _refs if os.path.exists(x)]); _how = "product (matched with its listing photo)"
                        if not _c:     # the first picture was composed with the product at this place
                            _c, _how = tuple(f["end_still"]["locked"].get("aim", [0.5, 0.55])), "product (its planned place in the frame)"
                        info = continuity.zoom_only(_sp, dst, f["end_still"]["locked"]["zoom"], center=_c); info["aim"] = _how
                        log(d, f"{k} = the first frame, closer (local crop): {info}")
                    ids[k] = upload(dst) if not DRY else "dry_local"; ids["_meta"][k] = "locked-crop"; save()
            elif f.get("end_action"):          # pixel-locked end frame: edit without camera move, then composite + zoom locally (free)
                ea = f["end_action"]; make(ea["name"], ea["prompt"], ea["refs"], os.path.join(d, "plates", ea["name"] + ".jpg"), person=True)
                k = f["end_still"]["name"]
                if k not in ids:
                    dst = os.path.join(d, "plates", k + ".jpg")
                    if not DRY:
                        info = continuity.composite_zoom(os.path.join(d, "plates", f["start_still"]["name"] + ".jpg"),
                                                         os.path.join(d, "plates", ea["name"] + ".jpg"), dst, f["end_still"]["composite"]["zoom"])
                        log(d, f"{k} built locally (pixel-locked on the first frame): {info}")
                    ids[k] = upload(dst) if not DRY else "dry_local"; ids["_meta"][k] = "composite"; save()
            else:
                make(f["end_still"]["name"], f["end_still"]["prompt"], f["end_still"]["refs"],
                     os.path.join(d, "plates", f["end_still"]["name"] + ".jpg"), person=True)
                guard(f["end_still"]["name"], os.path.join(d, "plates", f["end_still"]["name"] + ".jpg"), person=True)
        cl = f["clip"]; out = os.path.join(d, cl["out"])
        if (os.path.exists(out) and not (DRY and "--fresh" in sys.argv)) or f"clip_gen:{n}" in ids:
            return
        prompt_ok(f"slot_{n}_clip", cl["prompt"])
        g = tool("generate_video", prompt=cl["prompt"], image_asset_ids=[ref(f"slot_{n}_clip", x) for x in cl["image_asset_ids"]],
                 model=cl["model"], resolution=cl["resolution"], aspect_ratio=cl["aspect_ratio"],
                 duration_seconds=cl["duration_seconds"], folder=FOLDER)
        ids[f"clip_gen:{n}"] = g["generation_id"]; save(); log(d, f"slot {n} clip queued {g['generation_id']}")
    par(slot_job, reel["order"])   # every product's pictures and clip at the same time
    for n in reel["order"]:
        if n not in only:
            continue
        out = os.path.join(d, slots[n]["clip"]["out"])
        if os.path.exists(out) and not (DRY and "--fresh" in sys.argv):
            continue
        t0 = time.time()
        while True:
            s = tool("get_generation_status", generation_id=ids[f"clip_gen:{n}"], wait_seconds=25)
            if s["status"] == "completed":
                if DRY:
                    break
                fetch(s["video_url"], out, "video"); D, note = normalize_clip(out)
                try:   # 23-Nov: free local checks of the finished clip (hands / faces, product size drift) -> shown at finish
                    clip_limb_report(d, n, out); clip_size_report(d, n, out, slots[n])
                except Exception as e_:      # noqa: BLE001 - a report must never stop a paid row
                    log(d, f"note: clip report for slot {n} could not run ({e_})")

                ids[f"clip_done:{n}"] = s["video_asset_id"]; save(); log(d, f"slot {n} clip done {s['video_asset_id']} ({D:.2f} s, {note})"); break
            if s["status"] in ("failed", "blocked"):
                raise StopRun(f"slot {n} clip {s['status']}: {s.get('error_code')} {s.get('provider_reason') or s.get('message')} "
                              f"- NOT re-sent (its first/last frames are kept)")
            if time.time() - t0 > 1500:
                raise StopRun(f"slot {n} clip not finished after 25 min (generation {ids[f'clip_gen:{n}']}) - not re-sent; run again to keep waiting")
    if DRY:
        return
    # 5) plan.json + finish
    ft = json.load(open(os.path.join(P.DATA, "film_titles.json"))).get(str(int(row)))
    plan = dict(skeleton)
    for sg in plan.get("segments", []):       # 23-Nov: no post-production zoom - the only zoom is the camera move filmed in the clip
        sg["zoom"] = 1.0; sg.pop("zoom_x", None); sg.pop("zoom_y", None)
    plan.update(supers=[dict(board=P.BOARDS[int(row) % len(P.BOARDS)], head=ft, sub="", start=0, end=20.0, x=0.42, y=0.05, max_w=0.66)],
                logo=True, endslate=True, audio=dict(mode="music", music="default"), camera="steady")
    json.dump(plan, open(os.path.join(d, "plan.json"), "w"), indent=1, ensure_ascii=False)
    try:
        P.finish(row)
    except (SystemExit, subprocess.CalledProcessError) as e:
        open(os.path.join(d, "FINISH_FAILED.txt"), "w").write(str(e))
        log(d, f"FINISH FAILED (the clips are safe; fix and run `pipeline.py finish {row}` - free): {e}")
        sys.exit(4)
    log(d, "RUN_ROW done")


def fallbacks(msg):
    if "extra limb" in msg:
        nm = msg.split(": possible")[0]
        return [f"--accept-limbs={nm}   (use this picture anyway, free)", f"--regen={nm}   (generate this picture again: 1 new request)",
                "--candidates=2   (best-of-2 for every person picture: extra renders, each billed)"]
    m = re.search(r"sheet_(\d)", msg) or re.search(r"slot_?(\d)", msg)
    s = m.group(1) if m else "N"
    if "sheet_" in msg:
        return [f"--sheet-alt={s}:2   (sheet from listing photo 2)", f"--sheet-pro={s}   (Nano Banana Pro)",
                f"--sheet-photo={s}   (no sheet: the listing photo is the reference, free)"]
    if "_start" in msg or "_end" in msg:
        return [f"--local-photo={s}   (photo-only shots: build the still locally, free)"]
    return ["ask the user: re-send once, or leave this row"]


def main(argv):
    global DRY
    if argv and argv[0] == "status":
        return status(argv[1:])
    if argv and argv[0] == "launch":
        rows = [a for a in argv[1:] if a.isdigit()]; extra = [a for a in argv[1:] if a.startswith("--")]
        if "--confirmed" not in extra:
            raise SystemExit("paid run: add --confirmed (only after the user's yes)")
        for r in rows:
            lgp = os.path.join(P.rdir(r), "run.log"); lg = open(lgp, "a")
            subprocess.Popen(["caffeinate", "-i", sys.executable, os.path.abspath(__file__), r] + extra, stdout=lg, stderr=lg,
                             start_new_session=True, env=dict(os.environ, FK_MODE=os.environ.get("FK_MODE", "BAU")))
            print(f"row {r}: launched (log {lgp})")
        return
    row = argv[0]; DRY = "--dry" in argv
    if not DRY and "--confirmed" not in argv:
        raise SystemExit("paid run: add --confirmed (only after the user's yes), or --dry for the free walk-through")
    d = P.rdir(row)
    if not DRY:
        lk = open(os.path.join(d, ".sheets.lock" if "--sheets-only" in argv else ".run.lock"), "w")
        try:
            fcntl.flock(lk, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            raise SystemExit(f"row {row} is already running (lock) - not started a second time")
        try:
            subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
        except OSError:
            pass
    try:
        run(row, opts_of(argv))
    except StopRun as e:
        msg = str(e)
        if DRY:
            print(f"DRY RUN FOUND A PROBLEM: {msg}"); sys.exit(3)
        json.dump(dict(row=int(row), when=time.strftime("%Y-%m-%d %H:%M:%S"), stopped_because=msg, fallbacks=fallbacks(msg),
                       resume=f"FK_MODE=BAU python3 run_row.py {row} --confirmed  (add a fallback flag only after the user's yes)"),
                  open(os.path.join(d, "STOPPED.json"), "w"), indent=1)
        log(d, f"STOPPED: {msg}"); print("fallbacks ready (need the user's yes): " + " | ".join(fallbacks(msg)))
        sys.exit(3)
    if DRY:
        print(f"DRY RUN OK row {row}: would send {CALLS['image']} images, {CALLS['video']} clips, {CALLS['upload']} uploads "
              f"(resume-aware: existing assets are not counted)")


def status(rows):
    rows = rows or [p.split("row_")[1] for p in sorted(glob.glob(os.path.join(P.WORK, "row_*")))
                    if os.path.exists(os.path.join(p, "asset_ids.json"))]
    for r in rows:
        d = P.rdir(r)
        try:
            ids = json.load(open(os.path.join(d, "asset_ids.json")))
        except (OSError, ValueError):
            print(f"row {r}: not started"); continue
        sh = sum(1 for k in ids if k.startswith("sheet_")); st = sum(1 for k in ids if re.match(r"slot_\d_(start|end)$", k))
        cq = sum(1 for k in ids if k.startswith("clip_gen:")); cd = len(glob.glob(os.path.join(d, "clips", "slot_?.mp4")))
        running = False
        lp = os.path.join(d, ".run.lock")
        if os.path.exists(lp):
            try:
                f = open(lp, "w"); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB); fcntl.flock(f, fcntl.LOCK_UN)
            except OSError:
                running = True
        final = bool(glob.glob(os.path.join(P.LATEST, "**", f"*row{int(r):03d}*_480p.mp4"), recursive=True))
        stopped = os.path.exists(os.path.join(d, "STOPPED.json"))
        state = "DONE" if final else "RUNNING" if running else "STOPPED" if stopped else "idle/old-run"
        extra = (" | " + json.load(open(os.path.join(d, "STOPPED.json")))["stopped_because"][:90]) if stopped else ""
        lr = os.path.join(d, "limbs_report.json")
        flags = ""
        if os.path.exists(lr):
            rep = json.load(open(lr)); fl = [f"slot {k} ({len(v['flagged'])}/{v['frames']} frames)" for k, v in rep.items() if v["flagged"]]
            flags = (" | limb flags: " + ", ".join(fl)) if fl else " | limb flags: none"
        print(f"row {r}: {state} | sheets {sh}/5 | stills {st}/10 | clips queued {cq}/5 done {cd}/5{flags}{extra}")


if __name__ == "__main__":
    main(sys.argv[1:])
