#!/usr/bin/env bash
set -ex

NUM=$1
if [[ -z $NUM ]]; then
   NUM=20
fi

corpuses1=("accent/accent_main"  "accent/accent_stihi"  "birchbark" "dialect" "main/standard" "main/source" "mid_rus"\
  "multi" "multiparc/multiparc_rus" "multiparc/eng-rus"  "old_rus" "orthlib" "paper" "para" "poetic" \
  "regional_grodno/regional_grodno_bel" "regional_grodno/regional_grodno_rus" "school" "spoken" "spoken/manual" )
corpuses=( "spoken" "spoken/manual" )

for s in "${corpuses[@]}"
do
  python3 ./extractor.py $s $NUM
done
python3 ./extractor.py murco "$NUM" --names_list add_murco.txt