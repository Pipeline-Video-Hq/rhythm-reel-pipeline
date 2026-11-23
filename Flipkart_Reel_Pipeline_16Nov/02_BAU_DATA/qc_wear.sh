#!/bin/zsh
# qc_wear.sh N -> 1 fps contact sheet of the row's 480p final (whole video incl. end slate)
setopt err_exit pipe_fail
D="${0:A:h:h}"
r=$(printf %03d "$1"); f=$(ls "$D/runs/BAU_1500_1/01_LATEST_FINAL/"*/*/BAU1500_row${r}_*_480p.mp4)
echo "$f $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")"
ffmpeg -v error -y -i "$f" -vf "fps=1,scale=140:-1,tile=13x3" -frames:v 1 "$D/02_BAU_DATA/qc_$r.jpg"
