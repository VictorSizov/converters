#!/usr/bin/env bash
set -ex

NUM=$1
if [[ -z $NUM ]]; then
   NUM=100
fi
python ./extractor.py spoken $NUM
python ./extractor.py spoken/manual $NUM
python ./extractor.py accent/accent_main $NUM
python ./extractor.py accent/accent_stihi $NUM
python ./extractor.py dialect $NUM
python ./extractor.py main/source $NUM
python ./extractor.py main/standard $NUM
python ./extractor.py murco $NUM
python ./extractor.py paper $NUM
python ./extractor.py para $NUM
python ./extractor.py poetic $NUM
python ./extractor.py school $NUM
python ./extractor.py slav/birchbark $NUM
python ./extractor.py slav/mid_rus $NUM
python ./extractor.py slav/old_rus $NUM
python ./extractor.py slav/orthlib $NUM
python ./extractor.py syntax $NUM
python ./extractor.py multiparc/multiparc_rus $NUM
python ./extractor.py multiparc/eng-rus $NUM
