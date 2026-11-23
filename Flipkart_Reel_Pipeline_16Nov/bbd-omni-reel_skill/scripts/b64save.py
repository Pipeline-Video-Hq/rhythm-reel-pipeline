"""Save a Drive-connector download (JSON with base64 "content", usually auto-saved to a tool-results file) to disk.

    python3 b64save.py <tool_result_file_or_json> <out_path>
"""
import base64, json, sys

src, out = sys.argv[1], sys.argv[2]
raw = open(src).read()
try:
    d = json.loads(raw)
except json.JSONDecodeError:
    d = json.loads(raw[raw.index("{"):raw.rindex("}") + 1])
if isinstance(d, list):
    d = next(x for x in d if isinstance(x, dict) and "content" in x)
if "content" not in d and "text" in d:
    d = json.loads(d["text"])
raw_bytes = base64.b64decode(d["content"])
if out.lower().endswith((".jpg", ".jpeg")):
    import io
    from PIL import Image
    Image.open(io.BytesIO(raw_bytes)).convert("RGB").save(out, quality=90)
else:
    open(out, "wb").write(raw_bytes)
print("saved", out)
