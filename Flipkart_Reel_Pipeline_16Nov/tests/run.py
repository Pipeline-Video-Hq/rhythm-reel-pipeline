"""Offline tests for the reel pipeline (23-Nov). Nothing paid is sent: Omni and OpenAI are faked.

    python3 tests/run.py            -> one line per test, PASS / FAIL, exit code 1 if any fails

Covers: finish checks on synthetic clips, size parser, rule 50 handling, rule 51 allowed use, reel-order states,
picture queue + network handling (fake Omni server), planner DNS/timeout, batch plan-ready order, frozen-start cut."""
import http.server, json, os, re, socket, subprocess, sys, tempfile, threading, time, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "diwali-final-reel_SKILL_PIPELINE", "scripts")
sys.path.insert(0, SCRIPTS)
os.environ["FK_MODE"] = "BAU"
TMP = tempfile.mkdtemp(prefix="fk_tests_")
os.environ["FK_STATE_DIR"] = TMP
os.environ["FK_WORK_ROOT"] = os.path.join(TMP, "runs")
os.environ.setdefault("OPENAI_API_KEY", "test-not-real")
RESULTS = []


def test(fn):
    try:
        fn(); RESULTS.append((fn.__name__, "PASS", ""))
    except Exception as e:      # noqa: BLE001
        RESULTS.append((fn.__name__, "FAIL", f"{e.__class__.__name__}: {e}"[:300]))
        traceback.print_exc()
    return fn


def ff(*a):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *a], check=True)


@test
def finish_checks_catch_broken_takes():
    import pipeline as P
    d = os.path.join(TMP, "gate"); os.makedirs(os.path.join(d, "clips"), exist_ok=True)
    for n in (1, 4):
        ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=24:d=4", "-c:v", "libx264", f"{d}/clips/slot_{n}.mp4")
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=24:d=2", "-f", "lavfi", "-i", "smptebars=s=360x640:r=24:d=2",
       "-filter_complex", "[0][1]concat=n=2:v=1", "-c:v", "libx264", f"{d}/clips/slot_2.mp4")              # cut inside
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=24:d=3", "-c:v", "libx264", f"{d}/clips/slot_3.mp4")  # short
    ff("-f", "lavfi", "-i", "color=black:s=360x640:r=24:d=4", "-c:v", "libx264", f"{d}/clips/slot_5.mp4")  # black+frozen
    json.dump({"order": [1, 2, 3, 4, 5]}, open(f"{d}/reel_plan.json", "w"))
    json.dump({"segments": [{"clip": f"clips/slot_{n}.mp4", "slot": n, "in": 0, "out": 4.0, "zoom": 1.0} for n in range(1, 6)]},
              open(f"{d}/plan.json", "w"))
    bad = " | ".join(P.check_planned(999, d))
    assert "slot 2: a cut" in bad and "slot 3: the clip is 3.00" in bad and "slot 5: black" in bad, bad
    assert "slot 1" not in bad and "slot 4" not in bad, bad


@test
def size_parser_reads_units():
    from product_spec import cm_values
    assert cm_values("width 110, height 100, weight 245 g") == [110.0, 100.0]
    assert cm_values("150 ml bottle, height 16 cm") == [16.0]
    assert cm_values("diameter 8 mm, length 1.2 m") == [0.8, 120.0]
    assert cm_values("6 inch") == [15.24]


@test
def rule50_handling_phrases():
    import product_planner as PP
    bad = ["She picks up the bottle from the table", "twists the pump open", "pulls out one wipe", "removes the cap and sprays",
           "the lid opens", "places it on the table", "set it down", "passes it to her other hand"]
    ok = ["holds the jar, it stays in place", "cap stays closed", "close to the camera", "an open jar sits on the table",
          "she never opens the cap", "lifts her fingertip straight off the decal", "with the cap already off she presses the nozzle",
          "her right hand milk begins to rise", "turns the bottle 30 degrees in her full grip"]
    for t in bad:
        assert PP.handling_errors({"action_summary": t, "beats": []}, "fragrance"), f"not caught: {t}"
    for t in ok:
        assert not PP.handling_errors({"action_summary": t, "beats": []}, "fragrance"), f"false alarm: {t}"


@test
def rule51_allowed_use():
    import product_planner as PP
    cases = [("EDP perfume spray", "fragrance", "spray", "she rolls the ball and dabs it", True),
             ("EDP perfume spray", "fragrance", "spray", "index finger presses the nozzle once toward the wrist", False),
             ("Nivea roll-on", "fragrance", "roll-on", "she sprays once", True),
             ("Al Nuaim attar 6 ml", "fragrance", "attar", "she sprays the mist", True),
             ("Philips beard trimmer", "grooming", "trimmer", "she sprays foam", True),
             ("Fastrack analog watch", "fashion_wearables", "watch", "he unbuckles the strap", True),
             ("gift box", "fragrance", "unknown", "she turns it once", False)]
    for title, fam, kind, txt, blocked in cases:
        pa = PP.product_actions({"title": title, "specifications": {}}, fam)
        assert pa["kind"] == kind, (title, pa["kind"])
        assert bool(re.search(pa["forbid"], txt)) == blocked, (title, txt)


@test
def reel_order_ignores_no_change_and_invisible_states():
    import reel_planner as R
    mk = lambda req, chg: {"person": {"state_requires": req, "state_changes": chg}}
    plans = {1: mk({"clothes": "casual"}, {"clothes": "none"}), 2: mk({"clothes": "tee"}, {"clothes": "unchanged"}),
             3: mk({"fragrance": "none applied yet"}, {"fragrance": "wrist spray"}),
             4: mk({"fragrance": "not yet on neck"}, {"fragrance": "applied to neck"}), 5: mk({}, {"footwear": "none after the toe lift"})}
    order = R.order_slots(plans, {s: "room" for s in plans}, ["room"])
    assert order == [1, 2, 3, 4, 5], order


class _Omni(http.server.BaseHTTPRequestHandler):
    script = []
    def log_message(self, *a): pass
    def do_POST(self):
        self.rfile.read(int(self.headers["Content-Length"]))
        res = _Omni.script.pop(0) if _Omni.script else {"structuredContent": {"image_asset_id": "img_ok", "image_url": "http://x"}}
        b = json.dumps({"jsonrpc": "2.0", "id": 1, "result": res}).encode()
        self.send_response(200); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)


@test
def picture_queue_and_network():
    import imgqueue
    imgqueue.START_GAP, imgqueue.MIN_GAP, imgqueue.MAX_GAP = 0.05, 0.02, 0.5
    srv = http.server.HTTPServer(("127.0.0.1", 0), _Omni); threading.Thread(target=srv.serve_forever, daemon=True).start()
    os.environ["OMNI_MCP_URL"] = f"http://127.0.0.1:{srv.server_port}/mcp"; os.environ["OMNI_TOKEN"] = "test"
    import run_row as R, netwait
    R.QUEUE_LOG = os.path.join(TMP, "image_queue.log")
    rl = {"isError": True, "content": [{"type": "text", "text": "IMAGE_RATE_LIMITED"}]}
    _Omni.script[:] = [rl, rl]
    assert R.tool("generate_nano_banana_image", prompt="p", folder="t")["image_asset_id"] == "img_ok"
    real, calls, waits = R.urllib.request.urlopen, {"n": 0}, {"n": 0}
    def dns_once(req, timeout=None):
        calls["n"] += 1
        if calls["n"] == 1:
            raise R.urllib.error.URLError(socket.gaierror(8, "nodename nor servname provided"))
        return real(req, timeout=timeout)
    R.urllib.request.urlopen = dns_once
    netwait.wait_for_network = lambda url, log=print: waits.__setitem__("n", waits["n"] + 1)
    R.tool("generate_nano_banana_image", prompt="p", folder="t"); assert waits["n"] == 1
    def tout(req, timeout=None): raise socket.timeout("timed out")
    R.urllib.request.urlopen = tout
    try:
        R.tool("generate_nano_banana_image", prompt="p", folder="t"); raise AssertionError("a timeout after sending was re-sent")
    except R.StopRun:
        pass
    R.urllib.request.urlopen = real; srv.shutdown()


@test
def planner_waits_for_network_and_never_resends_a_timeout():
    import product_planner as PP
    n = {"c": 0, "w": 0}
    class _R:
        def __enter__(s): return s
        def __exit__(s, *a): pass
        def read(s): return json.dumps({"status": "completed", "output_text": "{}"}).encode()
    def fake(req, timeout=None):
        n["c"] += 1
        if n["c"] == 1:
            raise PP.urllib.error.URLError(socket.gaierror(8, "dns"))
        return _R()
    real = PP.urllib.request.urlopen
    PP.urllib.request.urlopen = fake; PP.netwait.wait_for_network = lambda u, log=print: n.__setitem__("w", n["w"] + 1)
    PP.call({"x": 1}); assert n == {"c": 2, "w": 1}, n
    def tout(req, timeout=None): raise socket.timeout("timed out")
    PP.urllib.request.urlopen = tout
    try:
        PP.call({"x": 1}); raise AssertionError("timeout re-sent")
    except PP.SentTimeout:
        pass
    PP.urllib.request.urlopen = real


@test
def planner_lifts_a_nested_plan():
    import product_planner as PP
    p = PP.parse(json.dumps({"product": {"type": "fabric", "life_size": {}, "scene": {"room": "bedroom"}, "shots": [], "person": {}}}))
    assert "scene" in p and "shots" in p and "scene" not in p["product"], p.keys()


@test
def planner_keeps_web_search_and_repairs_broken_json():
    import product_planner as PP
    if PP.WEB_TOOL:
        body = PP.payload("x", [], "baby_care", "A")
        assert body.get("tools") and "text" not in body, "web search must stay on, without JSON mode"
    sent = []
    real = PP.call
    PP.call = lambda body: (sent.append(body), {"status": "completed", "output_text": '{"product": {"type": "x"}, "scene": {"room": "r"}}'})[1]
    try:
        p = PP.parse(PP.repair_json('{"product": {"type": "x"} "scene": {"room": "r"}}'))
    finally:
        PP.call = real
    assert p["scene"]["room"] == "r" and sent and sent[0]["text"]["format"]["type"] == "json_object" and "tools" not in sent[0]


@test
def asif_fixes_23nov():
    import product_planner as PP, approaches as A, imgqueue as Q, reel_planner as R
    sh = {"push_in_target": "the label", "beats": [{"t_start": 0, "t_end": 2.5, "moves": "right hand", "movement": "turns it",
          "contact": "grip", "still": "rest", "product_state": "closed", "camera": "slow", "gaze": "product"}]}
    PP.complete_beats(sh)
    assert sh["beats"][-1]["t_end"] == 4.0 and sh["beats"][-1]["moves"] == "camera", sh["beats"][-1]
    assert not re.findall(r"\b(table|counter(?![- ]?clockwise)|shelf)\b", "rotates counter-clockwise")
    assert re.findall(r"\b(table|counter(?![- ]?clockwise)|shelf)\b", "sets it on the counter")
    os.environ["OMNI_TOKEN"] = "tokA"; a_ = Q._state(); os.environ["OMNI_TOKEN"] = "tokB"
    assert a_ != Q._state(), "one queue per token"
    mk = lambda req, chg: {"person": {"state_requires": req, "state_changes": chg}}
    plans = {1: mk({"forearm": "dry"}, {"forearm": "lotion residue"}), 2: mk({"forearm": "dry"}, {"forearm": "cream residue"})}
    assert R.order_slots(plans, {1: "r", 2: "r"}, ["r"]) == [1, 2]


@test
def batch_generates_in_plan_ready_order():
    import run_batch as B
    _popen = B.subprocess.Popen
    B.subprocess.Popen = lambda *a, **k: None          # no caffeinate in tests
    os.makedirs(os.path.dirname(B.P.WORK), exist_ok=True)
    pt, order = {1: .3, 2: .05, 3: .15, 4: .1}, []
    B.plan_and_sheets = lambda r, rp: (time.sleep(pt[r]), (r, 1 if r == 4 else 0))[1]
    B.gen_only = lambda r: (order.append(r), (r, "done"))[1]
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            B.main(["1", "2", "3", "4", "--parallel", "1", "--confirmed"])
        finally:
            B.subprocess.Popen = _popen
    assert order == [2, 3, 1], order


@test
def frozen_start_is_cut():
    import run_row as R
    p = os.path.join(TMP, "frozen.mp4")
    ff("-f", "lavfi", "-i", "testsrc2=s=360x640:r=24:d=4.3", "-vf", "loop=loop=2:size=1:start=0", "-t", "4.3", p)
    assert R.frozen_lead(p) > 0.05
    D, note = R.normalize_clip(p)
    assert abs(D - 4.0) < 0.05 and "frozen" in note and R.frozen_lead(p) == 0.0, (D, note)


if __name__ == "__main__":
    print()
    for name, st, why in RESULTS:
        print(f"{st:4}  {name}" + (f"  - {why}" if why else ""))
    print(f"\n{sum(s == 'PASS' for _, s, _ in RESULTS)}/{len(RESULTS)} passed")
    sys.exit(0 if all(s == "PASS" for _, s, _ in RESULTS) else 1)
