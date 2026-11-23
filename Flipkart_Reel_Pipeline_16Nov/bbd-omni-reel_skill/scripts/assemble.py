"""Assemble a BBD reel from row_NNN/plan.json -> row_NNN/final/<out_name>.

    python3 assemble.py <row>

plan.json (written by Claude, see references/PLAN.md):
{
  "segments": [ {"clip": "clips/s1.mp4", "in": 0.0, "out": 7.4, "zoom": 1.0, "audio": "clip"|"mute"} , ... ],
  "audio": {"mode": "speech"|"music", "music": "default"|"<path>", "music_db": -20},
  "supers": [ {"text": "...", "start": 0.3, "end": 3.2, "style": "outline", "x": 0.5, "y": 0.2, "size": 58}, ... ],
  "logo": true, "endslate": true
}
Clips are scaled to 1080x1920 at 24 fps (Omni 720p 9:16 = 720x1280). Speech rows keep the clips' own
(lip-synced) audio with the music bed far below; music rows use the bed only. Loudness -14 LUFS, TP <= -1.5.
"""
import json, os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
import supers as SU
import realism as RL
import visual_qc as VQ

FPS = 24


def main():
    row = int(sys.argv[1]); d = row_dir(row)
    brief, plan = load(os.path.join(d, "brief.json")), load(os.path.join(d, "plan.json"))
    if not plan:
        raise SystemExit("no plan.json")
    # HARD GATE (user rule 27-Oct-2026): every clip must pass the visual checklist (limbs, face, product, room...)
    if not plan.get("skip_visual_qc"):
        bad = VQ.gate(row)
        if bad:
            raise SystemExit("VISUAL QC NOT PASSED - run visual_qc.py, look at every sheet, fix/regenerate:\n  " + "\n  ".join(bad))
    work = os.path.join(d, "work"); os.makedirs(work, exist_ok=True); os.makedirs(os.path.join(d, "final"), exist_ok=True)
    mode = plan.get("audio", {}).get("mode", "music" if brief["music_only"] else "speech")
    # 1) normalise every segment
    segs = []
    for i, s in enumerate(plan["segments"]):
        src = os.path.join(d, s["clip"]); a, b = float(s.get("in", 0)), float(s.get("out", dur(src)))
        if dur(src) < b - 0.05:   # 23-Nov: a short clip was silently shortened (product cut short, every later beat shifted)
            raise SystemExit(f"segment {i} ({s['clip']}): the clip is {dur(src):.2f} s, shorter than its {b:.2f} s take - "
                             f"regenerate that slot's clip")
        z = float(s.get("zoom", 1.0))
        zy = float(s.get("zoom_y", 0.5))   # 30-Oct: punch-in anchor (0 = top, 0.5 = centre, 1 = bottom) for cloth zooms
        zx = float(s.get("zoom_x", 0.5))   # 2-Nov: horizontal anchor (0 = left, 0.5 = centre, 1 = right) for off-centre products
        nfr = max(1, int(round((b - a) * FPS)))   # 21-Nov: EXACT frame count per segment (a missing/held frame at every cut = a hitch)
        vf = (f"scale=1080*{z}:1920*{z}:flags=lanczos,crop=1080:1920:(iw-1080)*{zx}:(ih-1920)*{zy},setsar=1,fps={FPS},"
              f"tpad=stop_mode=clone:stop_duration=0.25,trim=end_frame={nfr},setpts=PTS-STARTPTS,")
        if plan.get("realism", True):          # user rule 27-Oct-2026: footage must look phone-shot, not AI-perfect
            vf += RL.vf(seed=row * 100 + i, strength=float(plan.get("realism_strength", 1.0)), camera=plan.get("camera", "steady")) + ","
        vf += "format=yuv420p,setparams=range=unknown:color_primaries=unknown:color_trc=unknown:colorspace=unknown"  # turbo clips carry bt709 tags; mixing tagged + untagged reset the graph and dropped logo/title (28-Oct)
        o = os.path.join(work, f"seg{i:02d}.mp4")
        has_audio = bool(subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                         "-of", "csv=p=0", src], capture_output=True, text=True).stdout.strip())
        keep = mode == "speech" and s.get("audio", "clip") == "clip" and has_audio
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{a:.3f}", "-to", f"{b:.3f}", "-i", src]
        if mode == "music":   # 21-Nov: music-only reels - video-only segments. A silent AAC track delays each segment by
            # 0.021 s (> half a frame at 24 fps), so every cut dropped/held one frame (a visible hitch). The music bed is added later.
            run(cmd + ["-vf", vf, "-map", "0:v:0", "-an", "-frames:v", str(nfr), "-c:v", "libx264", "-preset", "medium",
                       "-crf", "16", o]); segs.append(o)
            continue
        if not keep:
            cmd += ["-f", "lavfi", "-t", f"{b - a:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
        cmd += ["-vf", vf, "-map", "0:v:0", "-map", "0:a:0" if keep else "1:a:0",
                "-af", "aresample=48000,aformat=channel_layouts=stereo",
                "-frames:v", str(nfr), "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-c:a", "aac", "-b:a", "192k", "-shortest", o]
        run(cmd); segs.append(o)
    # 2) concat
    lst = os.path.join(work, "list.txt")
    open(lst, "w").write("".join(f"file '{p}'\n" for p in segs))
    body = os.path.join(work, "body.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", body])
    T = dur(body)
    # 3) supers + logo overlays
    inputs, chains, last, boxes = ["-i", body], [], "[0:v]", []
    for k, s in enumerate(plan.get("supers", [])):
        png, bb = SU.render(s, os.path.join(work, f"super{k:02d}.png"))
        boxes.append(dict(text=s.get("text") or (s.get("head", "") + " | " + s.get("sub", "")), start=s["start"], end=s["end"], bbox=bb))
        inputs += ["-i", png]
        chains.append(f"{last}[{len(inputs)//2 - 1}:v]overlay=0:0:enable='between(t,{s['start']},{s['end']})'[v{k}]")
        last = f"[v{k}]"
    if plan.get("logo", True):
        inputs += ["-i", LOGO]
        chains.append(f"{last}[{len(inputs)//2 - 1}:v]overlay=0:0[vl]"); last = "[vl]"
    save(boxes, os.path.join(d, "work", "super_boxes.json"))
    # 4) audio: speech keeps clip audio (+ quiet bed), music = bed only
    music = plan.get("audio", {}).get("music", "default")
    music = MUSIC if music == "default" else os.path.join(d, music) if not os.path.isabs(music) else music
    inputs += ["-stream_loop", "-1", "-i", music]
    mi = len([x for x in inputs if x == "-i"]) - 1
    mdb = plan.get("audio", {}).get("music_db", -20 if mode == "speech" else -6)
    if mode == "speech":
        chains.append(f"[{mi}:a]atrim=0:{T:.3f},volume={mdb}dB,afade=t=out:st={max(T-1.2,0):.3f}:d=1.2[bed];"
                      f"[0:a][bed]amix=inputs=2:duration=first:normalize=0[mix]")
    else:
        chains.append(f"[{mi}:a]atrim=0:{T:.3f},volume={mdb}dB,afade=t=in:d=0.3,afade=t=out:st={max(T-1.2,0):.3f}:d=1.2[mix]")
    chains.append("[mix]loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.80:level=false,aresample=48000[aout]")
    main_out = os.path.join(work, "main.mp4")
    run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(chains),
         "-map", last, "-map", "[aout]", "-t", f"{T:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", main_out])
    # 5) end slate
    final = os.path.join(d, "final", brief["out_name"])
    if plan.get("endslate", True):
        run(["ffmpeg", "-y", "-loglevel", "error", "-i", main_out, "-i", ENDSLATE, "-filter_complex",
             f"[1:v]scale=1080:1920,fps={FPS},setsar=1,format=yuv420p[ev];[1:a]aresample=48000,aformat=channel_layouts=stereo[ea];"
             f"[0:v][0:a][ev][ea]concat=n=2:v=1:a=1[v][ac];[ac]loudnorm=I=-14:TP=-1.5:LRA=11,alimiter=limit=0.80:level=false,aresample=48000[a]", "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", final])
    else:
        os.replace(main_out, final)
    print("MASTER", final, f"{dur(final):.2f}s")


if __name__ == "__main__":
    main()
