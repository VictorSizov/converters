# -*- Encoding: utf-8 -*-

import csv
import copy
import os

def process_accent_stihi(folder=''):
    """  Изменение sphere на "наивная поэзия", удаление столбца "type", перенос HTTP-адреса из header в source
    :param folder: если обрабатывается ноестандартный путь - вставка  "test_100" или любая другая
    :return:
    """
    name1 = '/place/ruscorpora/{0}corpora/accent/accent_stihi/tables/accent_stihi_old.csv'.format(folder)
    name2 = '/place/ruscorpora/{0}corpora/accent/accent_stihi/tables/accent_stihi.csv'.format(folder)
    name3 = os.path.expanduser('~/ruscorpora_sh/convertation/accent_stihi/errfiles.txt')

    with open(name1) as inp, open(name2, "w") as out, open(name3) as filter:
        filters = {fname.rstrip("\r\n").replace('/place/ruscorpora/corpora/accent/accent_stihi/texts/', '').
                   replace('.xml', '') for fname in filter}
        inp_table = csv.DictReader(inp, delimiter=';', restkey='extra', restval='???')
        fieldnames = copy.copy(inp_table.fieldnames)
        fieldnames.remove('type')
        out_table = csv.DictWriter(out, fieldnames=fieldnames, delimiter=';',)
        out_table.writeheader()
        for row in inp_table:
            if not row['path'] in filters:
                spl = row['header'].split(' http://')
                if len(spl) > 1:
                    row['header'] = spl[0]
                    row['source'] = "http://"+spl[1]
                row['sphere'] = 'наивная поэзия'
                del row['type']
                out_table.writerow(row)


process_accent_stihi()
