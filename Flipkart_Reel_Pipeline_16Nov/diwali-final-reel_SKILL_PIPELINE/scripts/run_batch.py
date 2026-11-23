"""RUN BATCH (22-Nov): plan + generate + finish many rows, N rows at a time.

    python3 run_batch.py 508 510 1181 1183 --parallel 4 --dry         free: shows what every row would send
    python3 run_batch.py 508 510 1181 1183 --parallel 4 --confirmed   PAID: plans (Serper + OpenAI) and generates (Omni)
    python3 run_batch.py 1001-1010 --parallel 3 --confirmed --replan   re-plan products that already have a saved plan
    python3 run_batch.py 1011-1030 --plan-only --confirmed            PLAN AHEAD (Serper + OpenAI only) - e.g. overnight
    python3 run_batch.py 1011-1030 --parallel 6 --confirmed --generate-only   generate rows planned earlier (no planning wait)
By default every row is planned at once in the background and a row starts generating the moment its plan is ready, so
planning of the next rows overlaps generation of the current ones.

Per row: `pipeline.py new` (if the row folder does not exist), `pipeline.py plan --confirmed` (all products of the row at the same
time), `run_row.py --confirmed` (all pictures and clips of the row at the same time, every send on the shared 2-second clock),
then the reel is assembled and filed. Each row writes runs/BAU_1500_1/03_WORK/row_NNN/full_run.log. A failed request is never
re-sent; that row stops (see its STOPPED.json) and the others go on. The Mac is kept awake while the batch runs.
"""
import concurrent.futures, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("FK_MODE", "BAU")   # 23-Nov: FK_LAX no longer defaults on - plan and finish checks always apply
import pipeline as P


def rows_of(args):
    out = []
    args = [a for i, a in enumerate(args) if not (i > 0 and args[i - 1] == "--parallel")]
    for a in args:
        if a[0].isdigit():
            if "-" in a:
                x, y = a.split("-"); out += list(range(int(x), int(y) + 1))
            else:
                out.append(int(a))
    return out


def sh(cmd, log):
    log.write(f"\n$ {' '.join(cmd)}\n"); log.flush()
    return subprocess.run([sys.executable, "-u"] + cmd, cwd=HERE, stdout=log, stderr=subprocess.STDOUT).returncode


def one(row, confirmed, replan):
    d = P.rdir(row); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "full_run.log"), "a") as log:
        log.write(f"\n===== {time.strftime('%H:%M:%S')} row {row}\n")
        if not os.path.exists(os.path.join(d, "brief.json")) and sh(["pipeline.py", "new", str(row)], log):
            return row, "NOT STARTED: `pipeline.py new` failed (see full_run.log)"
        plan = ["pipeline.py", "plan", str(row)] + (["--confirmed"] if confirmed else []) + (["--replan=1,2,3,4,5"] if replan else [])
        prc = sh(plan, log)
        if confirmed and prc:   # 23-Nov Garvit 'block before pay': a row whose plan failed is never generated
            return row, "NOT GENERATED: the plan failed its checks - nothing was paid for clips (see full_run.log)"
        if not confirmed:
            rc = sh(["run_row.py", str(row), "--dry", "--fresh"], log)
            return row, "dry run written to full_run.log"
        rc = sh(["run_row.py", str(row), "--confirmed"], log)
        log.write(f"===== {time.strftime('%H:%M:%S')} row {row} ended ({rc})\n")
    return row, {0: "done", 3: "STOPPED (see STOPPED.json)", 4: "clips made, assembly failed (FINISH_FAILED.txt)"}.get(rc, f"exit {rc}")


def plan_and_sheets(row, replan):
    """23-Nov (user: faster): OpenAI plans the row while the 5 product sheets are made at the same time."""
    d = P.rdir(row); os.makedirs(d, exist_ok=True)
    if not os.path.exists(os.path.join(d, "brief.json")):
        with open(os.path.join(d, "full_run.log"), "a") as log:
            sh(["pipeline.py", "new", str(row)], log)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        a = ex.submit(plan_only, row, replan)
        def sheets():
            with open(os.path.join(d, "full_run.log"), "a") as log:
                return sh(["run_row.py", str(row), "--confirmed", "--sheets-only"], log)
        s = ex.submit(sheets)
        rc = a.result()[1]; s.result()
    return row, rc


PLAN_TRIES = 3     # 23-Nov change A: a plan that fails its checks / is not valid JSON is re-requested at most 2 more times
                   # (only the failing products; the planner itself refuses a product rejected twice or timed out after sending)


def plan_only(row, replan):
    d = P.rdir(row); os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "full_run.log"), "a") as log:
        log.write(f"\n===== {time.strftime('%H:%M:%S')} row {row} (planning)\n")
        if not os.path.exists(os.path.join(d, "brief.json")) and sh(["pipeline.py", "new", str(row)], log):
            return row, 1
        rc = 1
        for t in range(PLAN_TRIES):
            rc = sh(["pipeline.py", "plan", str(row), "--confirmed"] + (["--replan=1,2,3,4,5"] if replan and t == 0 else []), log)
            if rc == 0:
                break
            log.write(f"===== plan try {t + 1}/{PLAN_TRIES} failed (rc {rc})\n"); log.flush()
    return row, rc


def write_status(state):
    """23-Nov change A: planning / generation progress for the whole batch -> runs/.../batch_status.json + one printed line."""
    c = {k: sum(1 for v in state.values() if v == k) for k in ("waiting", "planning", "planned", "plan failed", "generating", "done", "stopped")}
    line = f"{time.strftime('%H:%M:%S')} " + " | ".join(f"{k} {n}" for k, n in c.items() if n)
    try:
        json.dump(dict(at=time.strftime("%Y-%m-%d %H:%M:%S"), counts=c, rows={str(r): v for r, v in state.items()}),
                  open(os.path.join(os.path.dirname(P.WORK), "batch_status.json"), "w"), indent=1)
    except OSError:
        pass
    print("  progress: " + line, flush=True)


def gen_only(row):
    d = P.rdir(row)
    with open(os.path.join(d, "full_run.log"), "a") as log:
        log.write(f"\n===== {time.strftime('%H:%M:%S')} row {row} (generation)\n")
        rc = sh(["run_row.py", str(row), "--confirmed"], log)
        log.write(f"===== {time.strftime('%H:%M:%S')} row {row} ended ({rc})\n")
    return row, {0: "done", 3: "STOPPED (see STOPPED.json)", 4: "clips made, assembly failed (FINISH_FAILED.txt)"}.get(rc, f"exit {rc}")


def main(argv):
    rows = rows_of(argv)
    n = int(argv[argv.index("--parallel") + 1]) if "--parallel" in argv else 2
    confirmed, dry = "--confirmed" in argv, "--dry" in argv
    if not rows or (confirmed == dry):
        raise SystemExit(__doc__)
    try:
        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    except OSError:
        pass
    print(f"{len(rows)} rows, {n} generating at a time, {'PAID run' if confirmed else 'dry run (nothing is sent)'} - started {time.strftime('%H:%M:%S')}")
    if dry:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, n)) as ex:
            for row, res in ex.map(lambda r: one(r, False, "--replan" in argv), rows):
                print(f"  row {row}: {res}", flush=True)
    elif "--plan-only" in argv:          # plan ahead: every row's planning at once, no generation
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(rows), 12)) as ex:
            for row, rc in ex.map(lambda r: plan_only(r, "--replan" in argv), rows):
                print(f"  row {row}: " + ("planned" if rc == 0 else "PLAN FAILED - will not be generated") + " (see full_run.log)", flush=True)
    else:
        # 23-Nov change A: a planning pool (up to 10 rows at once) fully separate from generation. A generation place only
        # ever takes a row whose plan is READY (first ready, first generated) - it never sits waiting for a plan.
        # Rows planned earlier (--generate-only) are ready at once. Image capacity is shared through imgqueue (change B).
        gen_only_mode = "--generate-only" in argv
        state = {r: ("planned" if gen_only_mode else "waiting") for r in rows}
        last = [0.0]

        def tick(force=False):
            if force or time.time() - last[0] > 180:
                last[0] = time.time(); write_status(state)

        def plan_job(r):     # plan (OpenAI) and the 5 product sheets at the same time (Madhav 23-Nov), then generate
            state[r] = "planning"
            return plan_and_sheets(r, "--replan" in argv)

        def gen_job(r):
            state[r] = "generating"
            out = gen_only(r)
            state[r] = "done" if out[1] == "done" else "stopped"
            return out
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(rows), 10)) as px, \
             concurrent.futures.ThreadPoolExecutor(max_workers=max(1, n)) as gx:
            gens = []
            if gen_only_mode:
                gens = [gx.submit(gen_job, r) for r in rows]
            else:
                pf = {px.submit(plan_job, r): r for r in rows}
                for fut in concurrent.futures.as_completed(pf):
                    r, rc = fut.result()
                    if rc == 0:
                        state[r] = "planned"; gens.append(gx.submit(gen_job, r))
                    else:
                        state[r] = "plan failed"
                        print(f"  row {r}: NOT GENERATED: the plan failed its checks {PLAN_TRIES} times - nothing was paid for "
                              f"clips (see full_run.log)", flush=True)
                    tick()
            for fut in concurrent.futures.as_completed(gens):
                row, res = fut.result()
                print(f"  row {row}: {res}", flush=True); tick()
            tick(True)
    print(f"finished {time.strftime('%H:%M:%S')} - finals in runs/BAU_1500_1/01_LATEST_FINAL/")
    if dry:
        os.system(f"cd '{HERE}' && grep -h 'OpenAI requests needed\\|Google searches\\|DRY RUN' " +
                  " ".join(f"'{P.rdir(r)}/full_run.log'" for r in rows) + " | tail -n " + str(4 * len(rows)))


if __name__ == "__main__":
    main(sys.argv[1:])
