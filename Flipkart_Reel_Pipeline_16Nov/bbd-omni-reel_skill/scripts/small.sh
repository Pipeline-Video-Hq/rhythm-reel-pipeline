#!/bin/zsh
# Delivery copy under 9.5 MB (Chrome/Drive upload limit 10 MB): 2-pass H.264 at a bitrate from the duration.
#   small.sh <in.mp4> <out.mp4>
in="$1"; out="$2"
d=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$in")
kb=$(python3 -c "print(int((9.3*8*1024)/$d - 160))")
[ $kb -gt 6000 ] && kb=6000
tmp=$(mktemp -d)
ffmpeg -y -loglevel error -i "$in" -c:v libx264 -b:v ${kb}k -pass 1 -passlogfile $tmp/p -an -f mp4 /dev/null
ffmpeg -y -loglevel error -i "$in" -c:v libx264 -b:v ${kb}k -pass 2 -passlogfile $tmp/p -c:a aac -b:a 128k -movflags +faststart "$out"
ls -la "$out" | awk '{print $5, $9}'
