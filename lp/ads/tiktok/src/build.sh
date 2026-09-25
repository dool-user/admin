#!/usr/bin/env bash
# 使い方: cd lp/ads/tiktok/src && npm install && python narration.py && ./build.sh
# 事前に ffmpeg（libx264 入り）をインストールしておくこと
set -euo pipefail
cd "$(dirname "$0")"
declare -A DUR=( [a]=25.4 [b]=25.5 [c]=26.0 )   # 各パターンの長さ（narration.py の TIMELINE の最後）
for v in a b c; do
  node render.js "$PWD/video_$v.html" "$PWD/frames_$v" "${DUR[$v]}"
  # スマホ自撮り風の音（EQ＋かすかな環境音）にして -14 LUFS にそろえ、動画と合わせる
  ffmpeg -y -loglevel error -framerate 30 -i "frames_$v/f%04d.jpg" -i "vo_track_$v.wav" \
    -f lavfi -i "anoisesrc=color=pink:amplitude=0.0035:sample_rate=24000:duration=${DUR[$v]}" \
    -filter_complex "[1:a]highpass=f=120,lowpass=f=9500,equalizer=f=3200:t=q:w=1.2:g=2.5,equalizer=f=250:t=q:w=1:g=-2[v];[2:a]lowpass=f=4000[n];[v][n]amix=inputs=2:weights='1 1':normalize=0,acompressor=threshold=-20dB:ratio=3:attack=4:release=90,loudnorm=I=-14:TP=-1.5:LRA=8[a]" \
    -map 0:v -map "[a]" -shortest -ar 44100 -ac 2 \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
    -c:a aac -b:a 160k "../tiktok_hook-${v}_vo.mp4"
  rm -rf "frames_$v"
done
echo "done"
