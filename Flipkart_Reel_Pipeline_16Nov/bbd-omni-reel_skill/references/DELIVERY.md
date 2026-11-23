# Delivery: Drive (category folders) + sheet column R

Use Claude in Chrome (any connected browser) with a Google account that can open the BBD Drive folder - it is shared
"Anyone with the link - Editor", so any account can upload into it - and that has edit access to the sheet.

Folder layout (user rule, 8-Oct-2026):
```
My Drive / Flipkart BBD - Final videos/            (root id in data/drive_folders.json)
           Sports Footwear/   BBD_row002_Arjun_SportsFootwear.mp4 ...
           Men's Western Wear/ ...
           <one subfolder per column-F vertical, named exactly as in column F>
```
All 21 category subfolders exist (ids in `data/drive_folders.json`). The root is shared **Anyone with the link -
Editor**; everything inside inherits it, so no per-file sharing is needed. If a new vertical
appears, create its folder with Drive's New menu driven from page JS (press() the "New" button, then the "New folder"
menuitem; abort unless a real "New folder" dialog is open), type the name with real keystrokes (`computer type` -
Drive ignores values set from JS), click Create from JS, and reload the folder page between folders.

1. `zsh $SK/small.sh row_NNN/final/<out_name> _deliver/<out_name>` (< 9.5 MB, the browser-bridge limit is 10 MB
   per file_upload call and per batch - upload files in separate calls, never several in one browser_batch).
2. Open the category folder **by URL** (`https://drive.google.com/drive/folders/<id>`) - a fresh load, otherwise
   uploads land in whichever folder the page last had in memory.
3. Upload: inject hidden `<input type=file id=bbdupN>` elements (one per file), `file_upload` each file into its
   own input, set `window.__stage=[...files]`, patch `HTMLInputElement.prototype.click` so Drive's own file input
   receives `__stage` and fires `change` instead of opening the OS picker. Then New -> File upload (click both by
   `find` ref - coordinate clicks miss because the window is throttled; New must show its menu before you `find`
   "File upload"). Up to 5 files go in one hand-off. Wait for "N uploads complete".
4. Read file ids: take a screenshot (forces render), then
   `[...document.querySelectorAll('[role=row][data-id]')].map(r=>[r.innerText.split('\n')[0], r.getAttribute('data-id')])`.
   Link = `https://drive.google.com/file/d/<id>/view`. Check every file sits in the right category folder.
5. Sheet tab "BBD" (gid 1110512177): snapshot A:U via gviz CSV, Name box -> `R<first row>` (click the Name box
   twice, cmd+a, type, Enter; the cell editor must be hidden: `document.activeElement.getBoundingClientRect().y < -1000`),
   dispatch `ClipboardEvent('paste')` with a text/html one-column table of links (setTimeout 50 ms). Never touch A-Q.
6. Verify with gviz CSV: only column R of the delivered rows changed, values equal the links.
7. Write `row_NNN/delivery.json` {drive_id, link, folder, folder_id, length_s, sheet_row, sheet_col, account, date}.
8. Link access check: `curl -sL https://drive.google.com/file/d/<id>/view | grep -o '<title>[^<]*'` must show the file name (logged out).

Sheet column V "Category folder (Drive)" (V2:V501) already holds each row's category folder link (mapped from column F, 8-Oct-2026). Column S is the team's own status column ("done") - never write to it.
