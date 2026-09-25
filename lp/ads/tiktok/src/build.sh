#!/usr/bin/env bash
# 使い方: cd lp/ads/tiktok/src && npm install && ./build.sh
# 事前に ffmpeg（libx264 入り）をインストールしておくこと
set -euo pipefail
cd "$(dirname "$0")"
for v in a b c; do
  node render.js "$PWD/video_$v.html" "$PWD/frames_$v" 18
  ffmpeg -y -loglevel error -framerate 30 -i "frames_$v/f%04d.jpg" \
    -f lavfi -i anullsrc=r=44100:cl=stereo -shortest \
    -c:v libx264 -profile:v high -pix_fmt yuv420p -crf 18 -preset slow -movflags +faststart \
    -c:a aac -b:a 128k "../tiktok_hook-${v}_18s.mp4"
  rm -rf "frames_$v"
done
echo "done"
