#!/usr/bin/env bash
# Conform the Higgsfield clips into one 75 s (2250 frames), 1920x1080, 30 fps background plate.
# Usage: tools/build_plate.sh   (re-uses parts that already exist in media/plate_parts)
set -euo pipefail
cd "$(dirname "$0")/.."
C=media/clips; W=media/plate_parts; mkdir -p $W
# name | source | in | frames | slow factor | interp (mci|dup) | extra filter
PARTS=(
 "p01_door|c1_door.mp4|0|264|1|dup|null"
 "p02_chamber|c2_chamber.mp4|0|300|1.244|mci|null"
 "p03a_versus|c3_versus.mp4|0|78|1|dup|null"
 "p03b_recall|c4_neural.mp4|0|70|1|dup|null"
 "p03c_enigma|c4_neural.mp4|2.4|71|1|dup|hue=h=-160:s=1.15,eq=contrast=1.08"
 "p03d_piece|c3_versus.mp4|2.6|70|1|dup|null"
 "p03e_subst|c4_neural.mp4|3.65|71|1|dup|hue=h=95:s=1.3"
 "p03f_adv|c3_versus.mp4|5.6|60|1|dup|null"
 "p04_betrayal|c5_betrayal.mp4|0|270|1.12|mci|null"
 "p05_moon|c6_moon.mp4|0|354|1.25|dup|null"
 "p06_podium|c7_podium.mp4|0|240|1|dup|pad=1920:1170:0:90,crop=1920:1080:0:0"
 "p07_lights|c8_lightsoff.mp4|0|180|1|dup|null"
)
build () {
  IFS='|' read -r name src in frames slow interp extra <<<"$1"
  local raw=$W/$name.mp4 out=$W/${name}.n.mp4
  if [ ! -s "$raw" ] || [ "$(stat -c%s "$raw")" -lt 10000 ]; then
    local vf="setpts=(PTS-STARTPTS)*${slow}"
    if [ "$interp" = mci ]; then vf="$vf,minterpolate=fps=30:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"; else vf="$vf,fps=30"; fi
    ffmpeg -v error -y -ss "$in" -i "$C/$src" -an -vf "$vf,$extra,format=yuv420p" -c:v libx264 -preset fast -crf 14 -r 30 "$raw"
  fi
  # lock the exact frame count
  ffmpeg -v error -y -i "$raw" -an -vf "fps=30,tpad=stop_mode=clone:stop_duration=2,trim=end_frame=${frames},setpts=PTS-STARTPTS,format=yuv420p" \
    -c:v libx264 -preset fast -crf 14 -r 30 "$out"
  echo "$name $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 "$out")/$frames"
}
export -f build; export C W
printf '%s\n' "${PARTS[@]}" | xargs -P 4 -I{} bash -c 'build "$@"' _ {}
ffmpeg -v error -y -f lavfi -i color=c=black:s=1920x1080:r=30 -frames:v 18  -c:v libx264 -preset fast -crf 14 -pix_fmt yuv420p $W/p00_black.n.mp4
ffmpeg -v error -y -f lavfi -i color=c=black:s=1920x1080:r=30 -frames:v 204 -c:v libx264 -preset fast -crf 14 -pix_fmt yuv420p $W/p08_black.n.mp4
ls $W/*.n.mp4 | sort | sed "s#^#file '$(pwd)/#; s#\$#'#" > $W/list.txt
ffmpeg -v error -y -f concat -safe 0 -i $W/list.txt -c:v libx264 -preset slow -crf 15 -r 30 -g 30 -keyint_min 30 -pix_fmt yuv420p -movflags +faststart media/plate.mp4
echo "plate frames: $(ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames -of csv=p=0 media/plate.mp4)"
