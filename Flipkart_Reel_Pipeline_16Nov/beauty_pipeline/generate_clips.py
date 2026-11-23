#!/usr/bin/env python3
"""Submit EVERY clip of a run to Omni at once, then wait for all of them, then download (user rule 2026-11-05).

Usage:  python3 generate_clips.py <run folder> --confirmed [--dry] [--stagger SECONDS]
        --confirmed = the user approved THIS generation (same rule as omni.py); --dry needs no confirmation and costs nothing.
Needs:  <run>/clip_frames.json   {"C1_hook": "asset_...", "C2_show_x": "asset_...", ...}   clip name -> FIRST-FRAME asset id
        <run>/04_actions/<clip name>.json   one action file per clip (same names)
Output: <run>/assets/video_clips/<clip>.mp4 plus .job.json and .status.json for each clip

Behaviour
  1. Builds every prompt (omni.action_prompt appends all locks) and prints them with --dry (nothing is submitted, no cost).
  2. Submits all clips in parallel threads (one take each, 360p, first frame only). --stagger spaces the submits (default 0 = all at once;
     use 15 if the Omni service is flaky: all-at-once failed during the 2026-11-05 outage while staggered submits went through).
  3. A submit that fails is NEVER blindly resubmitted: it is written to <run>/assets/video_clips/<clip>.submit_error.txt and retried once
     after a pause only if the error was raised BEFORE any server reply (connection refused / 502 / timeout with no job id). Because a dropped
     connection may still have created a job on the server, retries are limited to one and are logged so the cost risk is visible.
  4. Polls all jobs together until each is completed/failed/blocked, then downloads the mp4s.
Never use this to re-roll clips that already exist: clips whose .mp4 exists are skipped.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import omni  # noqa: E402

HEAD = ("SILENT VIDEO: no audio, no music, no speech. Vertical 9:16 phone-camera footage, realistic skin texture. "
        "<FIRST_FRAME> is the exact first frame. Continue naturally from it as ONE continuous shot with NO cuts, following the steps and the camera moves below. "
        "Keep every product, label, face and colour exactly as in the first frame; products never move or change unless a step says so. ")
FOLDER = "Flipkart_Fashion-Rhythm_AI_Profiles"
RETRY_PAUSE = 60


def build(run, name, first):
    prompt, dur = omni.action_prompt(f"{run}/04_actions/{name}.json")
    return dict(prompt=HEAD + "\n" + prompt, model="gemini-omni-1.2-flash", resolution="360p", duration_seconds=int(round(dur)),
                aspect_ratio="9:16", folder=FOLDER, image_asset_ids=[first])


def submit(run, name, args, delay):
    out = f"{run}/assets/video_clips"
    time.sleep(delay)
    for attempt in (1, 2):                                   # one submit + at most one logged retry
        try:
            job = omni.tool("generate_video", **args)
            if not isinstance(job, dict) or not job.get("generation_id"):
                raise RuntimeError(f"no generation_id in the reply: {json.dumps(job)[:300]}")
            json.dump(job, open(f"{out}/{name}.job.json", "w"))
            return job
        except Exception as e:                               # noqa: BLE001
            open(f"{out}/{name}.submit_error.txt", "a").write(f"attempt {attempt}: {e}\n")
            print(f"{name}: submit attempt {attempt} failed: {str(e)[:100]}", flush=True)
            # 23-Nov: retry ONLY when the server certainly did not take the job (connection refused / rate limit);
            # a timeout or an error after the request reached Omni may already be billed, so it is never re-sent
            refused = (isinstance(e, urllib.error.URLError) and isinstance(getattr(e, "reason", None), ConnectionRefusedError)) \
                or "RATE_LIMIT" in str(e).upper()
            if attempt == 1 and refused:
                time.sleep(RETRY_PAUSE); continue
            return None
    return None


def download(url, dst):
    """23-Nov: download to .part, check it plays, then rename - a broken download is never left as <clip>.mp4."""
    import subprocess
    part = dst + ".part"
    urllib.request.urlretrieve(url, part)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", part],
                       capture_output=True, text=True)
    try:
        d_ = float(r.stdout.strip())
    except ValueError:
        raise RuntimeError(f"{os.path.basename(dst)}: downloaded file is not a readable video")
    os.replace(part, dst)
    return d_


def main():
    run = os.path.abspath(sys.argv[1])
    dry = "--dry" in sys.argv
    if not dry and "--confirmed" not in sys.argv:
        sys.exit("Obtain the user's confirmation for this generation, then pass --confirmed (or use --dry)")
    import subprocess
    gate = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "check_actions.py"), run], capture_output=True, text=True)
    if gate.returncode and not dry:   # 23-Nov Garvit 'block before pay': the action check always runs before a paid clip
        sys.exit("check_actions.py failed, fix before generating:\n" + gate.stdout)
    stagger = float(sys.argv[sys.argv.index("--stagger") + 1]) if "--stagger" in sys.argv else 0.0
    frames = json.load(open(f"{run}/clip_frames.json"))
    out = f"{run}/assets/video_clips"
    os.makedirs(out, exist_ok=True)
    todo = {n: a for n, a in frames.items() if not os.path.exists(f"{out}/{n}.mp4")}
    # 23-Nov: a clip that was already submitted (job.json saved) is collected, never submitted (paid) a second time
    queued = {}
    for n in list(todo):
        jp = f"{out}/{n}.job.json"
        if os.path.exists(jp):
            try:
                j = json.load(open(jp))
            except ValueError:
                j = {}
            if j.get("generation_id"):
                queued[n] = j; del todo[n]
    if queued:
        print(f"{len(queued)} clip(s) already submitted earlier - collecting them, not re-sending: {sorted(queued)}")
    jobs_args = {n: build(run, n, a) for n, a in todo.items()}
    total = sum(a["duration_seconds"] for a in jobs_args.values())
    print(f"{len(jobs_args)} clips, {total} s of footage to generate (cost scales with seconds)")
    if dry:
        for n, a in jobs_args.items():
            print(f"\n=== {n} ({a['duration_seconds']} s, frame {a['image_asset_ids'][0]}) ===\n{a['prompt'][:600]}...")
        return
    with ThreadPoolExecutor(max_workers=max(1, len(jobs_args))) as ex:           # ALL clips submitted together
        futs = {n: ex.submit(submit, run, n, a, i * stagger) for i, (n, a) in enumerate(jobs_args.items())}
        jobs = {n: f.result() for n, f in futs.items()}
    jobs.update(queued)
    pending = {n: j for n, j in jobs.items() if j}
    print(f"submitted {len(pending)}/{len(jobs_args)}; waiting for all")
    done = {}
    deadline = time.time() + 40 * 60      # 23-Nov: never poll forever; the generation ids stay in *.job.json to collect later
    errs = {}
    while pending:                                                                   # then wait for ALL of them
        for n, j in list(pending.items()):
            try:
                st = omni.tool("get_generation_status", generation_id=j["generation_id"])
            except Exception as e:                                                   # noqa: BLE001
                errs[n] = errs.get(n, 0) + 1
                if errs[n] in (3, 10, 30):
                    print(f"{n}: status check failed {errs[n]} times ({str(e)[:80]})", flush=True)
                continue
            if st.get("status") in ("completed", "failed", "blocked"):
                json.dump(st, open(f"{out}/{n}.status.json", "w"), indent=2)
                stt = st["status"]
                if st.get("video_url"):
                    try:
                        download(st["video_url"], f"{out}/{n}.mp4")
                    except Exception as e:                                           # noqa: BLE001
                        stt = f"download failed ({str(e)[:80]}) - the clip is kept in Omni, NOT regenerated"
                done[n] = stt
                del pending[n]
                print(f"{n}: {stt}", flush=True)
        if pending and time.time() > deadline:
            print(f"STILL RUNNING after 40 min, not re-sent: {sorted(pending)} - run again later to collect them", flush=True)
            break
        if pending:
            time.sleep(10)
    failed = [n for n in list(jobs_args) + list(queued) if done.get(n) != "completed"]
    print("ALL DONE" if not failed else f"NOT COMPLETED: {failed}")


if __name__ == "__main__":
    main()
