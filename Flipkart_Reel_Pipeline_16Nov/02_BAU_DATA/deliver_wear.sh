#!/bin/zsh
# deliver_wear.sh N : QC sheet + Drive upload ONLY (user 14-Nov: "sheet pe link update mat karna jab main na kahun") -> DRIVE_ONLY_day2.tsv
D="${0:A:h:h}"   # 23-Nov: absolute, computed before cd; upload itself refuses a row without a passed finish (qc/pass.json)
"$D/02_BAU_DATA/qc_wear.sh" "$1" || exit 1
cd "$D/diwali-final-reel_SKILL_PIPELINE/scripts"
out=$(FK_MODE=BAU /usr/bin/python3 pipeline.py upload "$1" 2>&1 | grep -v NOTICE)
echo "$out"
link=$(echo "$out" | awk -v r=$1 '$1==r{print $2}')
[ -n "$link" ] && printf "%s\t%s\n" $1 "$link" >> "$D/DRIVE_ONLY_day2.tsv"
