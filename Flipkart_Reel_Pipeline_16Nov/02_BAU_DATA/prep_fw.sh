#!/bin/zsh
# 16-Nov Day 2 Women Footwear (rows 122-141): fetch products, set up row folders + worker prompts
setopt err_exit pipe_fail no_unset   # 23-Nov: stop on the first failure (a failed addrows no longer runs new/prompt on stale data)
D="${0:A:h:h}"                       # 23-Nov: the pipeline folder, computed BEFORE cd (works from any folder)
cd "$D/diwali-final-reel_SKILL_PIPELINE/scripts"
FK_MODE=BAU nice -n 19 /usr/bin/python3 pipeline.py addrows "$D/02_BAU_DATA/sheet_rows_womenfw_day2.json"
for r in {122..141}; do
  FK_MODE=BAU /usr/bin/python3 pipeline.py new "$r" && FK_MODE=BAU /usr/bin/python3 pipeline.py prompt "$r" > "$D/runs/BAU_1500_1/03_WORK/_prompts/row_$r.txt" && echo "READY $r" >> "$D/02_BAU_DATA/ready_fw.txt"
done
echo ALLDONE >> "$D/02_BAU_DATA/ready_fw.txt"
