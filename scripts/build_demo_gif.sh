#!/usr/bin/env bash
set -euo pipefail

frame_dir="output/playwright/gif-frames"
mkdir -p "$frame_dir" docs/demo

for image_path in screenshots/*.png; do
    image_name="$(basename "$image_path")"
    convert "$image_path" -resize 1200x750 -background '#fbfbfd' \
        -gravity center -extent 1200x750 "$frame_dir/$image_name"
done

convert \
    -delay 150 \
    "$frame_dir/01-workspace.png" \
    "$frame_dir/02-research-brief.png" \
    -delay 230 "$frame_dir/03-grok-guide.png" \
    -delay 150 "$frame_dir/04-live-survey.png" \
    "$frame_dir/05-consent.png" \
    "$frame_dir/06-interviewer-start.png" \
    -delay 230 "$frame_dir/07-adaptive-interview.png" \
    "$frame_dir/08-interview-complete.png" \
    "$frame_dir/09-live-results.png" \
    -delay 260 "$frame_dir/10-structured-evidence.png" \
    "$frame_dir/11-evidence-chat.png" \
    -loop 0 -dither None -colors 256 -layers OptimizeTransparency \
    docs/demo/fastsurvey-walkthrough.gif

echo "Built docs/demo/fastsurvey-walkthrough.gif"
