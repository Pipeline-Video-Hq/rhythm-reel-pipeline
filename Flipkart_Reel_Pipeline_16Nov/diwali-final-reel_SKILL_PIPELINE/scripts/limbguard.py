"""LIMB GUARD (22-Nov): an automatic, free, local extra-limb detector (Apple Vision hand/face/body detection through the tiny
Swift tool in limbguard/). A person has two hands and one face: more is an extra hand / ghost head / second torso.
It is run on every person still BEFORE its clip is paid for (a clip made from a still with an extra hand carries the hand into
the video), and on sampled frames of every finished clip (report only)."""
import json, os, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "limbguard", "limbcount.swift")
BIN = os.path.join(HERE, "limbguard", "limbcount")


def _build():
    subprocess.run(["swiftc", "-O", SRC, "-o", BIN], check=True, capture_output=True, timeout=300)


def scan(paths):
    paths = [p for p in paths if os.path.exists(p)]
    if not paths:
        return []
    if not os.path.exists(BIN) or os.path.getmtime(BIN) < os.path.getmtime(SRC):
        _build()
    try:
        r = subprocess.run([BIN] + paths, capture_output=True, text=True, timeout=180)
        if r.returncode != 0 or not r.stdout.strip():
            raise OSError(r.stderr[:200])
    except OSError:
        _build()
        r = subprocess.run([BIN] + paths, capture_output=True, text=True, timeout=180)
    return json.loads(r.stdout)


def verdict(info, person=True, printed_faces=False):
    """(ok, reasons). Detection errors never flag a picture."""
    if info.get("error"):
        return True, []
    why = []
    if person:
        if info["hands"] > 2:
            why.append(f"{info['hands']} hands")
        if info["faces"] > 1 and not printed_faces:   # 23-Nov test: baby packs print a baby face - not a second person
            why.append(f"{info['faces']} faces")
        if info["bodies"] > 1 and not printed_faces:   # a printed baby is a body too
            why.append(f"{info['bodies']} bodies")
    elif info["hands"] > 0 or info["faces"] > 0 or info["bodies"] > 0:
        why.append("a person or hand appears in a product-only picture")
    return (not why), why


if __name__ == "__main__":
    import sys
    for i in scan(sys.argv[1:]):
        ok, why = verdict(i)
        print(("OK   " if ok else "FLAG ") + os.path.basename(i["file"]), f"hands={i['hands']} faces={i['faces']} bodies={i['bodies']}", why)
