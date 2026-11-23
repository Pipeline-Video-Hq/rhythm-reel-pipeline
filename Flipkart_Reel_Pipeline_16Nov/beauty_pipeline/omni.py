"""Omni flash video generation via the MCP HTTP endpoint (generate_video + get_generation_status).
Reads OMNI_MCP_URL and OMNI_TOKEN from .env next to this file.
Usage: /usr/bin/python3 omni.py "prompt" [duration_seconds] [resolution=360p only] [aspect_ratio]
       /usr/bin/python3 omni.py --action action_input.json [resolution=360p only] [aspect_ratio]   (see action_input.example.json)"""
import os, sys, json, time, urllib.request, urllib.error
from pathlib import Path
from pipeline_preflight import validate_run

ROOT = os.path.dirname(os.path.abspath(__file__))
if os.path.exists(os.path.join(ROOT, ".env")):   # 23-Nov: a fresh checkout (no .env) can still import / --dry
    for line in open(os.path.join(ROOT, ".env")):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

URL = os.environ.get("OMNI_MCP_URL", "")
HEADERS = {
    "Authorization": f"Bearer {os.environ.get('OMNI_TOKEN', '')}",
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",   # required by the MCP transport
}


def tool(name, **args):
    if not URL or not os.environ.get("OMNI_TOKEN"):
        raise SystemExit("OMNI_MCP_URL / OMNI_TOKEN missing - put them in beauty_pipeline/.env (ask Madhav)")
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": name, "arguments": args}}).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(URL, body, HEADERS), timeout=120) as r:
            raw = r.read().decode()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:500]}")
    if raw.lstrip().startswith(("event:", "data:")):   # SSE framing
        raw = next(l[5:] for l in raw.splitlines() if l.startswith("data:"))
    env_ = json.loads(raw)
    if "result" not in env_:
        raise RuntimeError(f"Omni error: {json.dumps(env_.get('error', env_))[:400]}")
    result = env_["result"]
    if result.get("isError"):
        raise RuntimeError(result["content"][0]["text"])
    return result.get("structuredContent") or json.loads(result["content"][0]["text"])


def generate(prompt, duration_seconds=6, resolution="360p", aspect_ratio="9:16", *, run_dir=None, confirmed=False, **extra):
    if not confirmed or not run_dir:
        raise ValueError("Specific user confirmation and a validated run are required")
    problems = validate_run(run_dir)
    if problems:
        raise ValueError("Preflight failed: " + "; ".join(problems))
    products = json.loads((Path(run_dir) / "pipeline_products.json").read_text(encoding="utf-8"))["products"]
    if any(product.get("opens") for product in products):
        raise ValueError("Opening clips are blocked: approved image references cannot yet be attached by this client")
    if resolution != "360p":
        raise ValueError("Only 360p video generation is permitted")
    prompt += "\nCAMERA: " + ZOOM_LIMIT
    job = tool("generate_video", prompt=prompt, model="gemini-omni-1.2-flash",
               resolution=resolution, duration_seconds=duration_seconds, aspect_ratio=aspect_ratio, **extra)
    while True:
        status = tool("get_generation_status", generation_id=job["generation_id"])
        if status["status"] in ("completed", "failed", "blocked"):
            return status
        time.sleep(10)          # "queued" with rate_limited=true is not a failure, keep waiting


PROPORTION_LOCK = ("Keep her face, head size, facial proportions and body proportions exactly the same as in the first frame: identical face shape, eye spacing, nose, mouth size, jaw and head-to-shoulder ratio, "
                   "the same distance from the camera, and every product at its true relative size. Do not stretch, widen, shrink or redraw her face.")
NO_DUPLICATES = ("Every product appears exactly once. A product in her hand is not also on the table or anywhere else; the number of products visible stays exactly as in the first frame.")
REALISM_LOCK = ("Photographic realism: hands and background are one real scene shot in a single take on a phone camera; every product lies on a real surface or is gripped firmly by the hands, nothing floats, stands unsupported or balances; hands share the same light direction, colour temperature and soft contact shadows as the scene; one natural skin tone with pores and knuckle creases; natural hand size relative to the products; forearms and sleeves enter from the frame edge.")
HANDS_LOCK = ("Exactly one person and exactly two hands in the whole clip: never a second set of hands, extra arms, extra fingers or a second person; every hand in the frame belongs to the same one person and each hand has five fingers; hands and forearms enter the frame from the bottom or the sides, never from the top edge, each forearm enters from its own side (left forearm from the left, right forearm from the right, never both from the same corner, never crossing); every product is firmly held by a natural grip at its true size, never balanced or stuck on the back of the hand; bottles are gripped by one hand wrapped around the body, never in cupped palms held up like offering a diya; hands and forearms have exactly the same skin tone and undertone as the person's face and neck.")
EYE_STABILITY = ("When an eye is being worked on it stays calm and stable: gaze fixed on one point, head still, no blinking, twitching or flicker of the lid or lashes; one slow steady stroke, the brush or wand reaches the lashes only once.")
OPENING_MOTION = ("Opening a cap, wand or lid is one short steady movement of about two seconds that starts from the half-open state in the first frame: smooth constant speed, no jerks, no repeated attempts.")
APPLY_VISIBLE = ("If a step applies a product (kajal, liner, lipstick, mascara, powder), the application MUST really happen on screen: the product moves steadily along its full path over the stated seconds and leaves a clearly visible, solid, high-contrast mark behind it (a black kajal line is dark and bold enough to read on a small phone screen), and the finished mark stays fully visible and untouched for the last 1.5 seconds of the clip; the clip never ends before the mark is complete and never wipes it away.")
NATURALISM = ("This must look like a casual real phone video filmed at home, not a studio shoot or an ad: ordinary window daylight or a plain room lamp, slightly uneven white balance, mild phone-camera noise and softness, no cinematic or studio lighting, no glow, rim light or bokeh blur; a neat, lived-in room of an upper-middle-class Indian apartment (modular wardrobe or wooden furniture, false ceiling, tidy, tasteful, not luxury, not a showroom, not decorated, not run-down); the person in everyday clothes with natural hair, visible skin texture with pores and small imperfections (never airbrushed or waxy), natural slightly imperfect expressions and blinking; products placed casually, not in a perfect catalogue row.")
ZOOM_LIMIT = ("Keep camera movement to a minimum: the shot is nearly locked off, with at most a barely noticeable push-in of about 10 percent over the whole clip at constant speed; no zoom in or out, no pan, orbit, shake or pulsing, no extreme close-up or macro.")
NATURAL_GESTURE = ("Every action is an ordinary everyday gesture with a natural arm and body position; never an arm raised above the head, never applying on the head, never an awkward pose.")


def action_prompt(path):
    """Flatten an action_input.json plan into one Omni prompt; returns (prompt, duration_seconds)."""
    plan = json.load(open(path))["plan"]
    out = ["ACTION: " + plan["action_summary"], "REQUIREMENTS:"] + ["- " + x for x in plan["script_requirements"]]
    out += ["START POSE: " + plan["start_pose"], "END POSE: " + plan["end_pose"], "STEP-BY-STEP:"]
    for i, st in enumerate(plan["steps"], 1):
        out.append(f"Step {i} ({st['t_start']}-{st['t_end']} s): {st['what_happens']}")
        for k in ("camera", "right_hand", "left_hand", "body_and_gaze", "contact_and_grip", "object_changes", "physics", "natural_detail"):
            if st.get(k):
                out.append(f"  {k.replace('_', ' ')}: {st[k]}")
    out += ["RESULT: " + plan["product_result"], "NEVER:"] + ["- " + x for x in plan["forbidden_mistakes"]] + ["- " + PROPORTION_LOCK, "- " + NO_DUPLICATES, "- " + NATURAL_GESTURE, "- " + ZOOM_LIMIT, "- " + REALISM_LOCK, "- " + HANDS_LOCK, "- " + EYE_STABILITY, "- " + OPENING_MOTION, "- " + APPLY_VISIBLE, "- " + NATURALISM]
    return "\n".join(out), max(st["t_end"] for st in plan["steps"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate one approved clip from a validated run")
    parser.add_argument("--action", required=True, help="Action JSON inside RUN_FOLDER/04_actions")
    parser.add_argument("--run", required=True, help="Run folder containing pipeline_products.json")
    parser.add_argument("--confirmed", action="store_true", help="User confirmed this specific generation")
    parser.add_argument("--aspect-ratio", default="9:16", choices=["9:16"])
    args = parser.parse_args()
    if not args.confirmed:
        parser.error("Obtain user confirmation for this specific generation, then pass --confirmed")
    action = Path(args.action).resolve()
    if action.parent != (Path(args.run).resolve() / "04_actions") or not action.is_file():
        parser.error("Action must be an existing JSON file in the run's 04_actions folder")
    problems = validate_run(args.run)
    if problems:
        parser.error("Preflight failed:\n" + "\n".join(problems))
    prompt, duration = action_prompt(action)
    print(json.dumps(generate(prompt, int(round(duration)), "360p", args.aspect_ratio, run_dir=args.run, confirmed=True), indent=2))
