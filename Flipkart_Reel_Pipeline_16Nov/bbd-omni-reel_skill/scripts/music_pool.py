"""One UNIQUE background track per video (client 28-Oct-2026: "Use different background music in each video").
Generates instrumental beds on ElevenLabs Music (Higgsfield has no usable music model) into
~/Desktop/Flipkart Fashion with Music/Musics/gen/ and keeps music_pool.json there: {file: {style, used_by}}.

    python3 music_pool.py gen <n> [seed]      -> generate n new tracks (styles rotate)
    python3 music_pool.py take <row> <style>  -> print the path of an UNUSED track of the closest style, mark it used
"""
import json, os, random, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

DIR = os.path.expanduser("~/Desktop/Flipkart Fashion with Music/Musics/gen")
POOL = os.path.join(DIR, "music_pool.json")
KEY = next(l.split("=", 1)[1].strip() for l in open(os.path.expanduser("~/.claude/skills/ugc-lipsync-ad-reel/.env"))
           if l.startswith("ELEVENLABS_API_KEY="))
STYLES = {  # style key -> prompt; theme/category picks a style family
    "festive_dhol": "upbeat Indian festive instrumental, dhol and shehnai over a modern beat, bright and celebratory",
    "sitar_pop": "modern Indian pop instrumental with sitar riffs, light percussion, warm and happy",
    "bollywood_dance": "Bollywood dance-pop instrumental, punchy drums, catchy synth hook, energetic",
    "lofi_chill": "lo-fi chill hop instrumental, soft keys, vinyl texture, relaxed",
    "western_pop": "bright western pop instrumental, claps, plucky synths, feel-good fashion reel",
    "edm_lite": "light EDM / future-bass instrumental, energetic drops, sporty",
    "acoustic": "acoustic guitar and ukulele instrumental, cheerful, cosy home vibe",
    "fashion_house": "chic fashion-runway deep house instrumental, groovy bass, stylish",
    "kids_playful": "playful children's instrumental, xylophone and claps, bouncy and sweet",
    "soft_flute": "soft Indian flute and tabla instrumental, calm, homely, warm",
}
FAMILY = {  # theme/category -> preferred styles
    "festive": ["festive_dhol", "sitar_pop", "bollywood_dance", "soft_flute"],
    "western": ["western_pop", "fashion_house", "edm_lite", "lofi_chill", "bollywood_dance"],
    "sport": ["edm_lite", "western_pop", "bollywood_dance", "fashion_house"],
    "kids": ["kids_playful", "acoustic", "bollywood_dance", "festive_dhol"],
    "home": ["acoustic", "soft_flute", "sitar_pop", "lofi_chill", "festive_dhol"],
}


def load():
    return json.load(open(POOL)) if os.path.exists(POOL) else {}


def save(p):
    json.dump(p, open(POOL, "w"), indent=1)


def gen_one(name, style):
    body = json.dumps({"prompt": STYLES[style] + ", no vocals, 22 seconds, clean ending",
                       "music_length_ms": 24000, "force_instrumental": True}).encode()
    req = urllib.request.Request("https://api.elevenlabs.io/v1/music", data=body,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r, open(os.path.join(DIR, name), "wb") as f:
        f.write(r.read())
    return name, style


def gen(n, seed=0):
    os.makedirs(DIR, exist_ok=True)
    p = load()
    styles = list(STYLES)
    start = len(p)
    jobs = [(f"bed_{start + i:03d}_{styles[(start + i) % len(styles)]}.mp3", styles[(start + i) % len(styles)]) for i in range(n)]
    with ThreadPoolExecutor(4) as ex:
        for fut in [ex.submit(gen_one, *j) for j in jobs]:
            try:
                name, style = fut.result()
                p[name] = {"style": style, "used_by": None}
                save(p)
                print("ok", name, flush=True)
            except Exception as e:
                print("FAIL", e, flush=True)


def take(row, family):
    p = load()
    free = [k for k, v in p.items() if not v["used_by"]]
    pref = FAMILY.get(family, list(STYLES))
    free.sort(key=lambda k: pref.index(p[k]["style"]) if p[k]["style"] in pref else 99)
    if not free:
        sys.exit("NO UNUSED TRACK LEFT - run: music_pool.py gen 10")
    k = free[0]
    p[k]["used_by"] = int(row)
    save(p)
    print(os.path.join(DIR, k))


if __name__ == "__main__":
    if sys.argv[1] == "gen":
        gen(int(sys.argv[2]))
    else:
        take(sys.argv[2], sys.argv[3])
