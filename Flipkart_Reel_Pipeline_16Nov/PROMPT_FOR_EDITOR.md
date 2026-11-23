# Prompt to paste into Claude Code (send this with ryhtm_pipeline.zip)

Open Claude Code in the unzipped `Flipkart_Reel_Pipeline_16Nov` folder and paste the text below. Replace the parts in < >.

---

You are running the Flipkart Rhythm reel pipeline in this folder. Read `CLAUDE.md` and `README_RUN.md` first, and follow them
exactly. Do not change any code.

Inputs:
- Sheet CSV: <path to "Ai requirements- Truefan_Flipkart (Rhythm) - 1500_1.csv">
- Rows to make: <for example 508-510 1181 1183>
- Rows to run in parallel: <for example 6>

Steps:
1. `cd diwali-final-reel_SKILL_PIPELINE/scripts`, then `export FK_MODE=BAU`.
2. Load the rows. Run `python3 sheet_to_rows.py "<csv>" <rows>`, then `python3 pipeline.py addrows` for each
   `../../02_BAU_DATA/sheet_rows_csv_<Vertical>.json` file it wrote. Then run `python3 pipeline.py setapproach AUTO <rows>`.
3. Dry run, which is free: `python3 run_batch.py <rows> --parallel <N> --dry`. Show me, per row, how many OpenAI requests, images
   and clips it would send. Then STOP and wait for my "yes".
4. After my yes: `python3 run_batch.py <rows> --parallel <N> --confirmed`. Run it in the background and don't poll it. Tell me
   when it ends.
5. When it ends, run `python3 run_row.py status <rows>`. Tell me where each finished reel is
   (`runs/BAU_1500_1/01_LATEST_FINAL/...`) and which rows stopped. A stopped row has a `STOPPED.json`; read it to me. Never
   re-send a failed request without my yes.

Rules:
- Never print or share the keys in `.env` or `beauty_pipeline/.env`.
- Never delete files.
- No QC: don't review or judge the videos yourself.
