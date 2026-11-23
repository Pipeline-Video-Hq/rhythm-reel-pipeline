"""Assemble a Diwali (non-BBD) reel: same engine as bbd-omni-reel/assemble.py, but plain Flipkart logo + simple Flipkart end slate.
    BBD_OUT=<diwali_reels> python3 assemble_fk.py <row>
Music (user 30-Oct): ONE continuous take from 0 s to the very end of the video (end slate included), never looped or restarted,
fading out over the last 2 s. Only LONG_TRACKS are used: they play steadily for 30 s. flipkart_batch / flipkart_jeans
(silent from ~21 s), home_line (silent from ~18 s) and penny (near-silent dip at ~18 s) sound like the song ends mid-video,
so any other planned track is swapped for LONG_TRACKS[row % 3].
"""
import os, sys, subprocess
PIPE = os.environ.get("FK_PIPE") or os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", ".."))
SK = os.path.join(PIPE, "bbd-omni-reel_skill", "scripts")
sys.path.insert(0, SK)
import assemble as A
A.VQ.gate = lambda row: []   # 17-Nov user: no QC stages (they slow everything down) - the visual-QC hard gate is off
A.LOGO = os.path.join(A.ASSETS, "brand", "flipkart_logo_overlay.png")
A.ENDSLATE = os.path.join(A.ASSETS, "brand", "flipkart_endslate.mp4")

MUSICS = os.path.join(PIPE, "assets", "music", "legacy")
# 16-Nov user: Rhythm sheet uses ONLY the approved RHY_BGM tracks (not approved: 1 2 3 11 13 14 17 19 22). Rotated by row.
APPROVED = os.path.join(PIPE, "assets", "music", "rhythm_bgm_approved")
LONG_TRACKS = ["shreya_v1_music.mp3", "shirt_haul_skill_bed.mp3", "unboxing_skill_bed.mp3"]
# User 30-Oct night: "20 music only from envato, unhi main se use karte rehna" + "according to niche". Each Envato item is
# unzipped into Musics_Envato/<niche>_<nn>/ (see SHORTLIST.md there); a row plays a track of its category's niche, rotating
# by row so neighbouring rows of one category never share a song.
ENVATO = os.path.join(PIPE, "assets", "music", "envato")
NICHE = {"Women's Ethnic Wear": "ethnic", "Men's Ethnic Wear": "ethnic", "Home Decor": "homedecor", "Women's Western Wear": "western",
         "Women's Footwear": "footwear", "Men's Footwear": "footwear", "Kids Footwear": "footwear",
         "Kids Clothing": "kids", "Fashion Wearables": "wearables", "Makeup": "wearables",
         "Women's Fashion Wearables": "wearables", "Men's Fashion Wearables": "wearables", "Home Furnishing": "furnishing",
         "Household Kitchen": "kitchen", "Household Supplies": "household", "Men's Grooming": "grooming",
         "Baby Care": "baby", "Toys and School Supplies": "toys", "Pets": "pets"}
# User 31-Oct: "ek niche main alag music hona chahiye". Most niches own only 1-2 tracks, so a category's 5-9 rows kept
# repeating one song. Each niche now rotates through its own folders first, then same-mood neighbours, so >= 5 different
# songs per category and neighbouring rows always differ. 2-Nov: pets_20 only for Pets (user: no pets track on baby/toys).
POOL = {"ethnic": ["ethnic_01", "ethnic_02", "ethnic_03", "homedecor_04", "homedecor_05"],
        "homedecor": ["homedecor_04", "homedecor_05", "ethnic_01", "ethnic_02", "ethnic_03"],
        "western": ["western_06", "western_07", "wearables_12", "wearables_13", "footwear_08", "footwear_09"],
        "footwear": ["footwear_08", "footwear_09", "western_06", "western_07", "wearables_12", "wearables_13"],
        "wearables": ["wearables_12", "wearables_13", "western_06", "western_07", "footwear_08", "footwear_09"],
        "kids": ["kids_10", "kids_11", "toys_19", "baby_18"],
        "furnishing": ["furnishing_14", "kitchen_15", "household_16", "homedecor_04", "homedecor_05"],
        "kitchen": ["kitchen_15", "household_16", "furnishing_14", "kids_10", "homedecor_04"],
        "household": ["household_16", "kitchen_15", "furnishing_14", "kids_10", "homedecor_05"],
        "grooming": ["grooming_17", "footwear_09", "wearables_12", "western_06", "footwear_08"],
        "baby": ["baby_18", "kids_11", "toys_19", "kids_10"],
        "toys": ["toys_19", "kids_10", "kids_11", "baby_18"],
        "pets": ["pets_20", "toys_19", "kids_10", "kids_11", "baby_18"]}
BATCH = os.environ.get("FK_BATCH") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "04_DATA", "batch_100.json")
FADE = 2.0


def envato_tracks(row, min_len):
    if os.path.isdir(APPROVED):   # approved pool wins; tracks shorter than the reel are skipped
        fs = sorted(os.path.join(APPROVED, f) for f in os.listdir(APPROVED) if f.lower().endswith((".wav", ".mp3")))
        return [f for f in fs if dur(f) >= min_len + 0.5]
    """The row's niche pool. A zip holds full / 60 s / 30 s / loop cuts, so each <niche>_<nn> folder gives only its
    longest file."""
    if not os.path.isdir(ENVATO):
        return []
    folder = A.load(BATCH).get(str(row), {}).get("folder")
    niche = NICHE.get(folder)
    out = []
    for d in POOL.get(niche, []):
        p = os.path.join(ENVATO, d)
        if not os.path.isdir(p):
            continue
        fs = [os.path.join(rt, f) for rt, _, names in os.walk(p) for f in names
              if f.lower().endswith((".mp3", ".wav", ".m4a", ".aiff")) and not f.startswith(".")
              # 13-Nov BAU (tab 1500_1, not Diwali): never a track named Diwali
              and not (os.environ.get("FK_MODE", "").upper() == "BAU" and "diwali" in f.lower())]
        if fs:
            best = max(fs, key=dur)
            if dur(best) >= min_len + 0.5:
                out.append(best)
    return out


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True, check=True).stdout.strip())


def full_length_music(row):
    d = A.row_dir(row)
    brief, plan = A.load(os.path.join(d, "brief.json")), A.load(os.path.join(d, "plan.json"))
    final = os.path.join(d, "final", brief["out_name"])
    music = plan.get("audio", {}).get("music", "default")
    music = A.MUSIC if music == "default" else music if os.path.isabs(music) else os.path.join(d, music)
    D = dur(final)
    env = envato_tracks(row, D)
    if os.path.isdir(APPROVED):   # 16-Nov: 22-track round robin, wraps to the first after the 22nd (bgm_rotation.py)
        sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
        import bgm_rotation
        music = bgm_rotation.get(row)
    elif env:
        music = env[row % len(env)]
    elif os.path.basename(music) not in LONG_TRACKS or dur(music) < D + 0.5:
        music = os.path.join(MUSICS, LONG_TRACKS[row % len(LONG_TRACKS)])
    mdb = plan.get("audio", {}).get("music_db", -6)
    tmp = final.replace(".mp4", "_mus.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", final, "-i", music, "-filter_complex",
                    f"[1:a]atrim=0:{D:.3f},asetpts=PTS-STARTPTS,volume={mdb}dB,afade=t=in:d=0.3,"
                    f"afade=t=out:st={D - FADE:.3f}:d={FADE},loudnorm=I=-14:TP=-1.5:LRA=11,"
                    f"alimiter=limit=0.80:level=false,aresample=48000[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", f"{D:.3f}",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, final)
    print("MUSIC", os.path.basename(music), f"0-{D:.2f}s, fade-out {FADE}s")


A.main()
full_length_music(int(sys.argv[1]))
