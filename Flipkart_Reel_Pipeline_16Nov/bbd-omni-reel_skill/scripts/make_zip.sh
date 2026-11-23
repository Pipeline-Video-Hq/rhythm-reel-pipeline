#!/bin/zsh
# Package the kit: skill + assets + data + personas + sample reels -> <dest>/bau-omni-reel-kit_<date>.zip
SK="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${1:-$HOME/Desktop}"
OUTR="${BAU_OUT:-$HOME/bau_reels}"   # 23-Nov: no machine-specific default
mkdir -p "$SK/samples"
for f in "$OUTR"/row_*/final/BAU_row*.mp4; do [ -f "$f" ] && cp "$f" "$SK/samples/"; done
Z="$DEST/bau-omni-reel-kit_$(date +%Y%m%d).zip"
rm -f "$Z"
cd "$SK/.." && zip -qr "$Z" "$(basename "$SK")" -x "*/__pycache__/*" "*.DS_Store" "*/scripts/make_zip.sh"
ls -la "$Z" | awk '{print $5, $9}'
