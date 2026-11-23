# Rhythm reel pipeline (code only)

AI shopping-reel pipeline: 5 products per reel, planned per product, pictures with Nano Banana 2 and 4 s clips with
Omni 1.2 (both through the TrueFan Omni service), assembled into a 9:16 reel with music and an end slate.

This public copy holds the code, rules and docs only. Not included, by design:
- keys (`.env`, `beauty_pipeline/.env`): OpenAI, Serper, Omni. Ask the team; never commit them.
- personas, brand assets, music, product data and sheet rows. Ask the team for the assets folder.

Start here: `Flipkart_Reel_Pipeline_16Nov/README_RUN.md`. What changed on 23 Nov and why: `CHANGELOG_23Nov.md`.

Rules for running it:
- `--dry` runs are free and send nothing. Anything with `--confirmed` is paid.
- Test any change on 3-4 rows, each from a different category, before a batch.
- `python3 omni_models.py` (in `diwali-final-reel_SKILL_PIPELINE/scripts`) lists the models Omni accepts; switch the
  picture model with `FK_IMAGE_MODEL=<id>`.

## Use it with Claude Code
Open Claude Code in an empty folder and paste:

    Set up the Rhythm reel pipeline from https://github.com/Pipeline-Video-Hq/rhythm-reel-pipeline on this Mac.
    Stop and ask me whenever you need something.
    1. git clone https://github.com/Pipeline-Video-Hq/rhythm-reel-pipeline ~/rhythm-reel-pipeline
    2. Read README.md, Flipkart_Reel_Pipeline_16Nov/README_RUN.md and CHANGELOG_23Nov.md; explain in 5 lines.
    3. Install what is missing: python3, ffmpeg (brew install ffmpeg), pip3 install pillow numpy opencv-python openpyxl.
    4. Ask me for the keys and the assets folder. Never print, share or commit keys.
    5. Run only the free dry run on 3 rows I give you and show me the output.
    6. Never run --confirmed (paid) or a batch without my explicit yes.
