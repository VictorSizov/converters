#!/usr/bin/env bash

python /place/ruscorpora/ruscorpora-processing/converter/validator.py /place/ruscorpora/corpora_new2/spoken/texts_end \
--schema /place/ruscorpora/corpora_new2/spoken/texts_end/test.xml --err_report /place/ruscorpora/corpora_new2/spoken/val_errors.txt \
--ignore_mess /place/ruscorpora/corpora_new2/tables/validator/ignore_mess.txt --table /place/ruscorpora/corpora_new2/spoken/tables/spoken_utf8.csv\
 --limit 5 --stat /place/ruscorpora/corpora_ne2/spoken/val_errors.txt