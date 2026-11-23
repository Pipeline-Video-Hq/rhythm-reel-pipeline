"""Which models does Omni accept RIGHT NOW? (free: one tools/list call, nothing is generated or billed)

    python3 omni_models.py            -> image and video model lists, straight from the Omni server

Use it after Omni enables a new model (e.g. a newer Nano Banana), then run with  FK_IMAGE_MODEL=<id>.
run_row.py makes the same check before the first paid picture and stops if FK_IMAGE_MODEL is not on the list."""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ENV = os.path.join(HERE, "..", "..", "beauty_pipeline", ".env")


def _env():
    if "OMNI_MCP_URL" not in os.environ and os.path.exists(ENV):
        for line in open(ENV):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    if not os.environ.get("OMNI_MCP_URL") or not os.environ.get("OMNI_TOKEN"):
        raise SystemExit("OMNI_MCP_URL / OMNI_TOKEN missing (beauty_pipeline/.env)")
    return os.environ["OMNI_MCP_URL"], {"Authorization": f"Bearer {os.environ['OMNI_TOKEN']}", "Content-Type": "application/json",
                                        "Accept": "application/json, text/event-stream"}


def models():
    """{tool_name: [model ids]} for the generation tools, read from the server's own tool schemas."""
    url, hdr = _env()
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode()
    raw = urllib.request.urlopen(urllib.request.Request(url, body, hdr), timeout=60).read().decode()
    if raw.lstrip().startswith(("event:", "data:")):
        raw = next(l[5:] for l in raw.splitlines() if l.startswith("data:"))
    out = {}
    for t in json.loads(raw)["result"]["tools"]:
        m = ((t.get("inputSchema") or {}).get("properties") or {}).get("model") or {}
        if m.get("enum"):
            out[t["name"]] = m["enum"]
    return out


if __name__ == "__main__":
    for name, ids in models().items():
        print(f"{name}: {', '.join(ids)}")
    sys.exit(0)
