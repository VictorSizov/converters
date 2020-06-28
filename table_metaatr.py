# -*- Encoding: utf-8 -*-

import sys
import csv
from pathlib import Path
from collections import ChainMap, Counter


def search_tables(folder='/place/ruscorpora/corpora'):
    root = Path(folder)
    inf = dict()
    corps = []
    csv_paths = [x for x in root.glob('*/tables/*.csv')] + [y for y in root.glob('*/*/tables/*.csv')]
    for csv_path in csv_paths:
        corpora = csv_path.parents[1].name
        if csv_path.parent.name != 'tables' or corpora != csv_path.stem:
            continue
        corps.append(corpora)
        with csv_path.open() as f:
            try:
                reader = csv.DictReader(f, delimiter=';')
                for name in reader.fieldnames:
                    if name == 'path':
                        continue
                    counter = inf.setdefault(name, Counter())
                    counter[corpora] += 1
                    counter['all'] += 1
            except UnicodeDecodeError:
                print("Exception UnicodeDecodeError while open table {0}".format(csv_path))
    corps = ['all'] + sorted(corps)
    with (root/'info.csv').open('w') as f:
        writer = csv.DictWriter(f, ['property'] + corps, delimiter=';')
        writer.writeheader()
        for name, counter in sorted(inf.items()):
            row = {'property': name}
            for corpora in corps:
                if corpora == 'all':
                    row[corpora] = counter[corpora]
                else:
                    row[corpora] = "+" if counter[corpora] else " "
            writer.writerow(row)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        search_tables(sys.argv[1])
    else:
        search_tables()
