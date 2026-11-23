# MCP Tool Map — Beauty Ads Automation

Audit date: 2026-10-31 · Read-only audit: no generation jobs submitted, no credits spent, no settings changed.

## Verdict on Kling 2.0 Turbo

**Not available.** Both Higgsfield connectors (`higgsfield` and `higgsfield-2`) were searched for Kling video models. Neither has a Kling 2.0 Turbo model.

Kling models that *are* exposed (`mcp__higgsfield__models_explore`, type=video):

| Model ID | Name | Image-to-video input | Duration | Audio control | Notes |
|---|---|---|---|---|---|
| `kling3_0_turbo` | Kling 3.0 Turbo | `start_image` | 3–15 s | none exposed | 720p / 1080p, 9:16 OK. Closest "Turbo" match. On both connectors. |
| `kling2_6` | Kling 2.6 Video | `start_image` | 5 or 10 s | `sound` bool (default **true**) | 9:16 OK |
| `kling3_0` | Kling v3.0 | `start_image`, `end_image` | 3–15 s | `sound` on/off (default **on**) | modes std / pro / 4k |
| `kling4_0` | Kling 4.0 | `start_image`, `end_image`, `image_references`, `video_references` | 3–30 s | — | modes t2v / i2v / ref2v / video-edit; up to 7 Kling element IDs |
| `kling_o3_image_reference` | Kling 3.0 Omni | `image_references` (up to 7) | 3–15 s | `sound` on/off | multi-shot |
| `kling_o3_flf` | Kling 3.0 Omni (Frames) | `start_image`, `end_image` | 3–15 s | `sound` on/off | multi-shot |
| `kling_video_edit` | Kling 3.0 Omni Edit | `video_references`, `image_references` | — | — | edits an existing clip |
| `kling3_0_motion_control` | Kling 3.0 Motion Control | image + video refs | — | — | motion transfer |

**Decision (2026-10-31): use Kling 3.0 Turbo (`kling3_0_turbo`).** The skill's SKILL.md now names it as the video model. Kling 3.0 Turbo is the nearest equivalent (fast, single start-frame image-to-video, budget tier). It has no sound parameter, so audio has to be stripped in the edit. Kling 2.6 and 3.0 default to audio **on**, so `sound` must be set to `false`/`off` explicitly.

## Tools by workflow stage

| Stage | Tool(s) | Key inputs | Status |
|---|---|---|---|
| Product research (Flipkart pages) | `mcp__Claude_Browser__navigate`, `get_page_text`, `read_page` (built-in browser); `mcp__claude-in-chrome__*` (your Chrome) | URL | Available. Flipkart may block bots, so screenshots or pasted details are the fallback. |
| Product image import | `mcp__higgsfield__media_import_url` | `url` (HTTPS, ≤50 MB), `type` | Available. Returns a `media_id` for generation inputs. |
| Local file upload | `mcp__higgsfield__media_upload` → curl PUT → `mcp__higgsfield__media_confirm` | `filename` / `files[]`, then `media_id(s)` + `type` | Available |
| Model refs / keyframes (image gen) | `mcp__higgsfield__generate_image`, `generate_image_batch` | `model` (required), `prompt`, `medias[{value, role}]`, `aspect_ratio`, `count`, `get_cost` | Available |
| Image models of interest | `soul_2` (UGC/character), `seedream_v5_pro` (reference editing), `flux_2`, `marketing_studio_2_image` (product shots with people), `gpt_image_2_5` (tool's default general model) | see `models_explore action=get` | Available |
| Alternative image gen | TrueFan MCP `generate_nano_banana_image` | — | Available (deferred tool) |
| Kling video gen | `mcp__higgsfield__generate_video`, `generate_video_batch` | `model`, `prompt`, `medias[{value, role:start_image}]`, `aspect_ratio:"9:16"`, `duration`, model params (`sound`, `resolution`, `mode`), `get_cost` | Available, but **not Kling 2.0 Turbo** |
| Cost preflight | `generate_*` with `get_cost: true`; `mcp__higgsfield__balance` | — | Available (no job submitted) |
| Job polling | `mcp__higgsfield__jobs_wait` | `jobs[{index, job_id}]` (≤12), `timeout_seconds` ≤15 | Available |
| Asset retrieval | `jobs_wait` returns result URLs → `curl` download locally; `show_generation_by_ids` to view | `job_id`s | Available |
| Local files | Read / Write / Bash | — | Available |
| Final edit / render | Local FFmpeg **9.0.2** (`/opt/homebrew/bin/ffmpeg`, `ffprobe`); Python 3.9.6 | — | Available, so a real MP4 can be rendered locally |
| Licensed background music | `mcp__higgsfield__generate_audio` (AI music) or your own licensed track | — | Available; the music source must be decided per campaign |

## Missing / caveats

1. **Kling 2.0 Turbo**: not exposed. Resolved: Kling 3.0 Turbo approved as the substitute.
2. **Music licensing**: the skill requires authorized music. Either supply a track or approve AI-generated music.
3. **Flipkart page access**: not tested in this audit (no pages fetched). If Flipkart blocks the browser, provide screenshots or product details.
4. Higgsfield `unlim` (free-trial unlimited) is **not available** on this account, so every generation spends credits.

## Can it run end to end without manual browser work?

- Create images: **yes**
- Generate Kling clips: **yes** (with a substitute model)
- Retrieve completed clips: **yes** (`jobs_wait` URLs + curl)
- Render final MP4: **yes** (local FFmpeg)

## Launch command

```
Run Beauty Ads Automation for these Flipkart products: [paste URLs]. Campaign: [name]. Use Kling 3.0 Turbo (kling3_0_turbo), image-to-video, 9:16, background music only, no dialogue or lip-sync. Save everything in a new campaign folder.
```
