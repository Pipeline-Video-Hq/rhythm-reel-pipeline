#!/bin/zsh
# 14-Nov Day 2 (Fashion Wearables): fetch products per chunk, set up row folders + worker prompts
setopt err_exit pipe_fail no_unset   # 23-Nov: stop on the first failure (a failed addrows no longer runs new/prompt on stale data)
D="${0:A:h:h}"                       # 23-Nov: the pipeline folder, computed BEFORE cd (works from any folder)
cd "$D/diwali-final-reel_SKILL_PIPELINE/scripts"
mkdir -p "$D/runs/BAU_1500_1/03_WORK/_prompts"
for c in "$D"/02_BAU_DATA/sheet_rows_wear_chunk*.json; do
  FK_MODE=BAU nice -n 19 /usr/bin/python3 pipeline.py addrows "$c"
  for r in $(/usr/bin/python3 -c "import json,sys;print(' '.join(str(x['row']) for x in json.load(open(sys.argv[1]))['rows']))" "$c"); do
    FK_MODE=BAU /usr/bin/python3 pipeline.py new "$r" && FK_MODE=BAU /usr/bin/python3 pipeline.py prompt "$r" > "$D/runs/BAU_1500_1/03_WORK/_prompts/row_$r.txt" && echo "READY $r" >> "$D/02_BAU_DATA/ready_wear.txt"
  done
done
echo ALLDONE >> "$D/02_BAU_DATA/ready_wear.txt"
