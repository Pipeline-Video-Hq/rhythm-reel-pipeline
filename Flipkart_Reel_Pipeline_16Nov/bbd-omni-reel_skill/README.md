# bbd-omni-reel kit (TrueFan)

Claude Code skill that turns rows of the **"BBD"** tab of the *Ai requirements- Truefan* sheet into finished 9:16
Flipkart Big Billion Days reels (~20-25 s, Hinglish): the row's persona avatar, its column-K script, the client's
HOOK / PRODUCTS / CLOSE brief (column J), real Flipkart products (columns L-Q) and the BBD badge + end card.

- Lip-sync (Voice) rows -> **Omni 1.1 720p** (TrueFan MCP). Music-only rows -> **Kling 3.0 pro** (Higgsfield MCP).
- Starting frames: Nano Banana (TrueFan; Higgsfield `nano_banana_2` as overflow, max 1-2 jobs at a time).

## Install
1. Unzip into a project's `.claude/skills/` (or `~/.claude/skills/`) so the folder is `.claude/skills/bbd-omni-reel/`.
2. Mac requirements: `python3` with `Pillow` + `numpy` (`pip3 install pillow numpy`), `ffmpeg`/`ffprobe`
   (`brew install ffmpeg`), and `pip3 install mlx-whisper` (needed by the automatic speech gate; or set `WHISPER_BIN`).
   First run downloads the Whisper models `mlx-community/whisper-large-v3-turbo` and `whisper-large-v3-mlx`.
3. Connectors in Claude: **TrueFan Omni MCP** (generate_video, generate_nano_banana_image, upload_media) and
   **Higgsfield MCP** (Kling 3.0, nano_banana_2) - required. Claude in Chrome (any Google account with edit access to the sheet; the
   Drive folder is open to anyone with the link) for Drive + sheet delivery.
4. Output folder: `export BBD_OUT=~/bbd_reels`.
5. Permissions: allow `upload_media` and `curl` uploads to `omni-flash.truefan.in` (auto mode blocks them otherwise).

## Use (in Claude Code)
- "make BBD rows 52-60" / "status of BBD reels" / "redo BBD row 9".
- Big batches: run several sub-agents in parallel, each on its own row range, with `references/PARALLEL.md` as the brief.

## The one-shot pipeline (SKILL.md "Run steps")
`row.py` -> `products.py` -> `shotplan.py` (script split, clip length sized to the line, coverage asserted) -> fill
`shots.json` (Devanagari dialogue, voice from `data/voices.json`, positive wardrobe, plates) -> plate checklist ->
`promptgen.py` (refuses on gaps / prices / romanised Hindi) -> generate -> `clipcheck.py` (PASS / FIX auto-cut / RETAKE)
-> `autoplan.py` (supers at top of frame, product-name labels) -> `assemble.py` -> `qc.py` -> independent QC
(`references/QC_BRIEF.md`) -> delivery (`references/DELIVERY.md`).

## Standing client rules (see SKILL.md)
No prices anywhere (spoken or on screen) - endings are varied Big Billion Days lines - Hindi in Devanagari for the
voice - one take per shot - persona's own clothes/shoes identical across shots and unbranded - product never covered
by text - BBD badge on every frame - no AI model names in client-facing files.

## What is inside
| Path | What |
|---|---|
| SKILL.md | workflow + standing rules (read first) |
| references/ | PROMPTS, PLAN, QC_BRIEF, DELIVERY, PARALLEL (sub-agent worker brief) |
| scripts/ | row/products/shotplan/promptgen/clipcheck/autoplan/assemble/qc/supers + helpers |
| data/ | BBD tab snapshot + column-K scripts (500 rows), references (T/U), persona Drive ids, voices, Drive folder ids |
| personas/ | the 32 BBD persona avatars |
| assets/ | BBD badge overlay, BBD end card, fonts, music bed |
| samples/ | two finished reels: row 2 (Omni, lip-sync) and row 37 (Kling, music-only) |
