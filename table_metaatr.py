# -*- Encoding: utf-8 -*-
""" Анализ метапараметров """
import sys
import csv
from pathlib import Path
from collections import ChainMap, Counter

ignore = {'comment', 'header', 'aurtor'}

def search_tables(folder='/place/ruscorpora/corpora'):
    root = Path(folder)
    inf = dict()
    corps = []
    csv_paths = [x for x in root.glob('*/tables/*.csv')] + [y for y in root.glob('*/*/tables/*.csv')]
    values_all = dict()
    counter_all = values_all.setdefault(' all', Counter())
    for csv_path in csv_paths:
        corpora = csv_path.parents[1].name
        if csv_path.parent.name != 'tables' or corpora != csv_path.stem:
            continue
        print(corpora)
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
                for row in reader:
                    for key, values in row.items():
                        if key == 'path':
                            continue
                        counter = values_all.setdefault(key, Counter())
                        for value in {v.strip() for v in values.split('|')}:
                            counter[value] += 1
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
    with (root/'info_attr.csv').open('w') as f:
        writer = csv.writer(f, delimiter=';')
        for name, counter in sorted(values_all.items()):
            row = [name] + ["{0}({1})".format(c[0] if len(c[0]) < 30 else c[0][:30]+"..", c[1]) for c in counter.most_common(100)]
            writer.writerow(row)
if __name__ == '__main__':
    if len(sys.argv) > 1:
        search_tables(sys.argv[1])
    else:
        search_tables()
