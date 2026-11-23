# plan.json (edit plan read by assemble.py)

```json
{
  "segments": [
    {"clip": "clips/s1.mp4", "in": 0.15, "out": 7.40},
    {"clip": "clips/s2.mp4", "in": 0.10, "out": 7.20, "zoom": 1.04},
    {"clip": "clips/s3.mp4", "in": 0.10, "out": 7.60}
  ],
  "audio": {"mode": "speech"},
  "supers": [
    {"text": "3 kurti sets I live in 🫶", "start": 0.2, "end": 3.0, "style": "outline", "x": 0.5, "y": 0.15, "size": 60},
    {"text": "Floral Anarkali", "start": 7.4, "end": 10.0, "style": "pill", "x": 0.5, "y": 0.11, "size": 44},
    {"text": "Flipkart pe ethnic wear shop karo", "start": 18.0, "end": 21.6, "style": "box", "x": 0.5, "y": 0.18, "size": 50}
  ],
  "logo": true,
  "endslate": true
}
```
- `in/out` trim each clip: cut any silent mouth movement before the first word and after the last word; cut
  on a breath or a hard visual change. Find speech edges from the audio energy, not from eyeballing.
- `zoom` (optional, >= 1.0) is a static punch-in for a jump cut.
- `audio.mode`: `speech` keeps the clips' own lip-synced audio with the music bed 20 dB down; `music` = bed only
  (`music_db` default -6). `music` may point to another file.
- Supers: `start/end` in seconds of the edited timeline (before the end slate). `style` = outline | pill | box | bar |
  plain; `x/y` = centre as fractions of the frame; `size` px at 1080 wide; `tilt` degrees optional; `\n` = new line.
  Put supers in the empty part of the frame (sky/wall/top band), never across the product or face; the BBD
  badge sits top-right (x > 0.74, y < 0.16) so keep that corner clear.
