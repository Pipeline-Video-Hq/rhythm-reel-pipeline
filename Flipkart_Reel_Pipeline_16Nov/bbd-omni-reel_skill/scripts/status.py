"""One line per BBD row: which stage it has reached.

    python3 status.py [2-121]
Stages: brief -> products -> persona -> plates -> clips -> plan -> master -> qc -> delivered
"""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from row import rows_arg

rows = rows_arg(sys.argv[1] if len(sys.argv) > 1 else "2-501")
for r in rows:
    d = row_dir(r); b = load(os.path.join(d, "brief.json"))
    if not b:
        print(f"{r:3d}  -"); continue
    st = ["brief"]
    if os.path.exists(os.path.join(d, "products.json")): st.append("products")
    if os.path.exists(b["persona"]["image"]): st.append("persona")
    if glob.glob(os.path.join(d, "plates", "*")): st.append("plates")
    n = len(glob.glob(os.path.join(d, "clips", "*.mp4")))
    if n: st.append(f"clips:{n}")
    if os.path.exists(os.path.join(d, "plan.json")): st.append("plan")
    if os.path.exists(os.path.join(d, "final", b["out_name"])): st.append("master")
    q = load(os.path.join(d, "qc", "verdict.json"))
    if q: st.append("qc:" + q.get("verdict", "?"))
    dl = load(os.path.join(d, "delivery.json"))
    if dl: st.append("delivered")
    print(f"{r:3d}  {b['name']:9s} {b['vertical'][:18]:18s} {'music' if b['music_only'] else 'voice':5s}  " + " > ".join(st))
