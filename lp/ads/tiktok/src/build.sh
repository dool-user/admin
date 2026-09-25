#!/usr/bin/env bash
# 使い方: cd lp/ads/tiktok/src && npm install && python narration.py && ./build.sh
# 事前に ffmpeg（libx264 入り）をインストールしておくこと
set -euo pipefail
cd "$(dirname "$0")"
for v in a b c; do
  node render.js "$PWD/video_$v.html" "$PWD/frames_$v" 21
  # ナレーションを整音（-14 LUFS）して動画と合わせる
  ffmpeg -y -loglevel error -framerate 30 -i "frames_$v/f%04d.jpg" -i "vo_track_$v.wav" \
    -map 0:v -map 1:a -shortest \
    -af "highpass=f=80,acompressor=threshold=-18dB:ratio=3:attack=5:release=80,loudnorm=I=-14:TP=-1.5:LRA=7" -ar 44100 -ac 2 \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
    -c:a aac -b:a 160k "../tiktok_hook-${v}_21s_vo.mp4"
  rm -rf "frames_$v"
done
echo "done"
