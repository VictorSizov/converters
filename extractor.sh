#!/usr/bin/env bash
set -ex

NUM=$1
if [[ -z $NUM ]]; then
   NUM=100
fi
python3 ./extractor.py spoken $NUM
python3 ./extractor.py spoken/manual $NUM
python3 ./extractor.py accent/accent_main $NUM
python3 ./extractor.py accent/accent_stihi $NUM
python3 ./extractor.py dialect $NUM
python3 ./extractor.py main/source $NUM
python3 ./extractor.py main/standard $NUM
python3 ./extractor.py murco $NUM
python3 ./extractor.py paper $NUM
python3 ./extractor.py para $NUM
python3 ./extractor.py poetic $NUM
python3 ./extractor.py school $NUM
python3 ./extractor.py slav/birchbark $NUM
python3 ./extractor.py slav/mid_rus $NUM
python3 ./extractor.py slav/old_rus $NUM
python3 ./extractor.py slav/orthlib $NUM
python3 ./extractor.py syntax $NUM
python3 ./extractor.py multiparc/multiparc_rus $NUM
python3 ./extractor.py multiparc/eng-rus $NUM
