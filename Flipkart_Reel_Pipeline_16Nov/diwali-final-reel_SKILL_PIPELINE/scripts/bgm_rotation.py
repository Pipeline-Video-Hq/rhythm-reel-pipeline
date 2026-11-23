"""BGM ROUND ROBIN (user 16-Nov): the 22 approved tracks in assets/music/rhythm_bgm_approved are handed out in order
(RHY_BGM_004, 005, ... 031) one per reel, across ALL verticals and both pipelines. After the 22nd it starts again from the first.

State: assets/music/bgm_rotation.json = {"next": <index>, "rows": {"<row>": "<track file>"}}.
Track = approved[(row-1) % 22] (20-Nov: row-based so parallel machines never repeat). A row keeps the track it was given (reruns / re-finish use the same one). Thread-safe across parallel workers (file lock).

    python3 bgm_rotation.py status        # next track + how many rows got each track
    python3 bgm_rotation.py get <row>     # assign (or show) the row's track
"""
import fcntl, json, os, sys

PIPE = os.environ.get("FK_PIPE") or os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
DIR = os.path.join(PIPE, "assets", "music", "rhythm_bgm_approved")
STATE = os.path.join(PIPE, "assets", "music", "bgm_rotation.json")


def tracks():
    return sorted(f for f in os.listdir(DIR) if f.lower().endswith((".wav", ".mp3")) and not f.startswith("."))


def get(row):
    """Return the absolute path of the row's track, assigning the next one in the rotation if the row has none yet."""
    ts = tracks()
    if not ts:
        raise SystemExit(f"no approved BGM in {DIR}")
    with open(STATE + ".lock", "w") as lk:
        fcntl.flock(lk, fcntl.LOCK_EX)
        st = json.load(open(STATE)) if os.path.exists(STATE) else {"next": 0, "rows": {}}
        key = str(int(row))
        if st["rows"].get(key) not in ts:                 # new row (or its track was removed from the approved list)
            # user 20-Nov (repeated music): the track comes from the ROW NUMBER, not a per-machine counter, so every machine
            # and worker gives the same row the same track and neighbouring rows (Day / category batches) never share one.
            st["rows"][key] = ts[(int(row) - 1) % len(ts)]
            st["next"] = (int(row)) % len(ts)
            json.dump(st, open(STATE, "w"), indent=1)
        return os.path.join(DIR, st["rows"][key])


def status():
    ts = tracks(); st = json.load(open(STATE)) if os.path.exists(STATE) else {"next": 0, "rows": {}}
    print(f"{len(ts)} approved tracks; next = {ts[st['next'] % len(ts)]}; rows assigned = {len(st['rows'])}")
    for t in ts:
        print(f"  {t}: {sum(1 for v in st['rows'].values() if v == t)}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["get"]:
        print(get(sys.argv[2]))
    else:
        status()
