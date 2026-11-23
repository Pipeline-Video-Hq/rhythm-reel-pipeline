# How to run the Rhythm reel pipeline

This makes the Flipkart Rhythm reels: 5 products per reel, 4 s each, plus the end slate, for about 21.6 s in total.
You give it sheet row numbers. It plans each product, generates the pictures and clips, then assembles and files the reel.

## 1. One-time setup on your Mac

1. Unzip `ryhtm_pipeline.zip`. Any folder works. The commands below are run inside the unzipped
   `Flipkart_Reel_Pipeline_16Nov` folder.
2. Install these if the Mac doesn't have them yet:
   - Python 3: check with `python3 --version`.
   - ffmpeg: install with `brew install ffmpeg`.
   - The Python libraries: install with `pip3 install pillow numpy opencv-python`.
   - Xcode command line tools: install with `xcode-select --install`. They are optional; they let the zoom at the end of each clip
     centre itself on the hands and the product.
3. Keys:
   - `.env` (in the main folder) already holds the OpenAI key. **Do not share this zip.**
   - `beauty_pipeline/.env` must hold the Omni keys. Ask Madhav for them. The file has these two lines:
     ```
     OMNI_MCP_URL=...
     OMNI_TOKEN=...
     ```
4. Open Terminal and go to the scripts folder:
   ```bash
   cd Flipkart_Reel_Pipeline_16Nov/diwali-final-reel_SKILL_PIPELINE/scripts
   export FK_MODE=BAU
   ```

## 2. Load the rows from the sheet

Download the sheet as CSV (tab `1500_1`), then run:
```bash
python3 sheet_to_rows.py "/path/to/Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv" 508-510 1181 1183
python3 pipeline.py addrows ../../02_BAU_DATA/sheet_rows_csv_HomeDecore.json
python3 pipeline.py addrows ../../02_BAU_DATA/sheet_rows_csv_babycare.json
python3 pipeline.py setapproach AUTO 508-510 1181 1183
```
- `sheet_to_rows.py` writes one file per vertical. The file name is the vertical's name with spaces removed: `sheet_rows_csv_<Vertical>.json`.
- `addrows` downloads the 5 product listings and their photos for each row.
- `setapproach AUTO` gives each row its presentation style (A-E) in rotation.

## 3. Dry run (free): see exactly what will be sent

```bash
python3 run_batch.py 508 510 1181 1183 --parallel 4 --dry
```
For every row this prints:
- how many OpenAI planning requests it would send;
- how many images and clips it would generate.

Nothing is sent and nothing costs anything.

## 4. The real run

**Test first, never on a batch (Garvit, 23 Nov):** after any change to the pipeline, run 3-4 rows, each from a different
category (for example baby care, fragrance, footwear, home decor), and check every reel before running a batch. The list of
changes made on 23 Nov is in `CHANGELOG_23Nov.md`.


```bash
python3 run_batch.py 508 510 1181 1183 --parallel 4 --confirmed
```
- **`--parallel N` sets how many rows generate at the same time.** Since 23 Nov every picture request from every row goes
  through ONE shared image queue that adapts to what Omni accepts (about 100-120 pictures an hour). A rate limit no longer
  stops a row: the picture simply waits for its next turn. So a larger N (for example 12) is safe: extra rows wait in the
  queue while their clips, uploads and assembly overlap. The queue state is logged every minute in
  `runs/BAU_1500_1/image_queue.log`.
- Planning runs in its own pool (up to 10 rows at once). A generation place only takes a row whose plan is ready, and a
  failed plan is tried at most 2 more times. Progress: `runs/BAU_1500_1/batch_status.json`.
- If the Mac loses the network, requests that never left the Mac wait for it to come back and are then sent. A request
  that was sent but got no answer is never sent again automatically, because it may have been billed.
- Row ranges work too: `1001-1010`.
- Add `--replan` to plan products again even when they already have a saved plan.
- Within each row:
  - all 5 products are planned at the same time by OpenAI (with its own web search for real sizes and use);
  - all pictures and clips are made at the same time.

  Across all rows together, a new request starts at most once every second.
- The Mac is kept awake while the run lasts. Don't close the Terminal window.

### Plan ahead (saves 3-6 minutes per batch)

The batch runner already does this on its own. Every row's planning starts at once in the background, and a row starts
generating the moment its own plan is ready. So while rows 1-6 generate, rows 7-12 are already being planned.

You can also plan the next batch in advance, for example overnight, without generating anything:
```bash
python3 run_batch.py 1011-1030 --plan-only --confirmed
```
Later, generate those rows with no planning wait:
```bash
python3 run_batch.py 1011-1030 --parallel 6 --confirmed --generate-only
```

## 5. Where things are

| What | Where |
|---|---|
| Finished reels (480p) | `runs/BAU_1500_1/01_LATEST_FINAL/Day 1/<Category>/` |
| Higher-quality masters | `runs/BAU_1500_1/01_LATEST_FINAL/Day 1/1080p_masters/` |
| Progress of a row | `runs/BAU_1500_1/03_WORK/row_NNN/full_run.log` and `log.md` |
| The 5 clips of a row | `runs/BAU_1500_1/03_WORK/row_NNN/clips/` |

Check every row in one line:
```bash
python3 run_row.py status 508 510 1181 1183
```

## 6. How long it takes

The times below are estimates from the runs made so far.

| Step | Time |
|---|---|
| Planning one row (all 5 products at once; the product sheets are made at the same time) | about 1-3 minutes (overlaps generation) |
| Generating one row (pictures, then clips, all at once) | about 8-12 minutes |

**Total time ≈ about 5 minutes for the first plans + (number of rows ÷ `--parallel`, rounded up) × about 10 minutes.**
- 8 rows with `--parallel 8` takes about 15-20 minutes.
- 12 rows with `--parallel 6` takes about 25-30 minutes.
- Rows planned ahead with `--plan-only` skip the first 5 minutes.
- More than about 8 in parallel brings more Omni rate limits; each one adds a 75-second wait.

## 7. Cost per row

| Service | Requests per row |
|---|---|
| OpenAI (gpt-5 planning) | 5 requests; a product with a saved plan is not planned again |
| Omni (Nano Banana images) | about 8-17 images |
| Omni (gemini-omni-1.2-flash clips) | 5 clips of 4 s at 360p |

## 8. If something fails

- A failed request is **never sent again automatically**. That row stops and writes `row_NNN/STOPPED.json`, which says what
  failed and how to continue. The other rows keep going.
- To continue a stopped row, run its command again. Everything already made is reused:
  `python3 run_row.py <row> --confirmed`
- To redo one product of a row (the old pictures and clip are moved aside, never deleted):
  `python3 run_row.py <row> --confirmed --only=3 --redo=3`
- If the clips are made but the assembly failed, run the assembly again (free):
  `python3 pipeline.py finish <row>`

## 9. What the pipeline does (no checks, no QC)

There are no automatic checks or QC; the rules below are written into every request.
- The planner (OpenAI with web search) looks up the product's real size, how people use it and its parts. Listing photos
  are close-ups, so they are never used for size.
- Each product's clip shows what the product is FOR. The product is in its ready-to-use state from the first frame, for example
  a nibbler already filled with fruit.
- Every second of every clip is described for every body part, finger, the clothing, the product, the props, the light and the
  camera.
- The zoom is a real camera move filmed in the video, always toward the product, with the room still visible around it. Nothing
  appears, opens, grows or moves on its own, and the person never walks toward the camera.
- Wall decor is shown as a close-up beside the wall, with her touching it. She is never in front of it and never points at it.
