# -*- Encoding: utf-8 -*-
""" Поле path в таблицах csv должно содержать путь к документам, отличась только отсутствием расширения xml.
Иногда они отличается больше: содержит неправильное расширение (xhtml), обратный слеш вместо прямого, разная
капитлизация. Скрипт приводит поле path в соответствие с путем к документу. Закомментированный код """

import os
import csv
'''
import string
import time
import copy
upper = set(string.ascii_uppercase)
'''


def get_paths(inppath):
    paths = []
    valid_extensions = ('.xml', '.tgt')
    for root, dirs, files in os.walk(inppath, followlinks=True, topdown=True):
        if '/.git' in root:
            dirs[:] = []
            continue
        if files:
            root = os.path.relpath(root, inppath)
            paths += [os.path.join(root, f) for f in files if os.path.splitext(f)[1] in valid_extensions]
    return sorted(paths)


'''
def lowercase(paths, log, changed):
    prev_start = ''
    need_lower = []
    ii = 0
    for path in paths:
        ii += 1
        if ii % 100000 == 0:
            print('{0} processed'.format(ii))
        if not upper.intersection(set(path)):
            continue
        path_split = path.split('/')
        pos = -1
        lower_n = 0
        for i, part in enumerate(path_split):
            if upper.intersection(set(part)):
                lower_n += 1
                if lower_n == 1:
                    pos = i
        start = '/'.join(path_split[:pos + 1])
        if lower_n > 1:
            nl = path.replace(start, start.lower())
            need_lower.append(nl)
        if prev_start and start == prev_start:
            continue
        prev_start = start
        full_path = os.path.join('/place/ruscorpora/corpora', start)
        lower_path = os.path.join('/place/ruscorpora/corpora', start.lower())
        if os.path.exists(lower_path):
            log.write("{0} -> {1} failed, destination exists\n".format(path, lower_path))
        else:
            try:
                os.rename(full_path, lower_path)
                log.write("{0} -> {1} renamed\n".format(full_path, lower_path))
                corp = path_split[0]
                if corp == 'main':
                    corp = path_split[1]
                changed.add(corp)

            except Exception as ex:
                log.write("{0} -> {1} failed, exception {2}\n".format(full_path, lower_path, str(ex)))
    return need_lower


def main():
    paths = get_paths('/place/ruscorpora/corpora')
    changed = set()
    with open('info.log', 'w') as flog:
        i = 1
        while paths:
            mess = "Iteration {0}, {1} documents".format(i, len(paths))
            print(mess)
            flog.write(mess+'\n')
            i += 1
            paths = lowercase(paths, flog, changed)
    print(changed)
'''


def get_from_table(path):
    corpus = path.split('/')[-1]
    if corpus == 'eng-rus':
        corpus = "multiparc_eng-rus"
    name = "{0}/tables/{1}.csv".format(path, corpus)
    if not os.path.exists(name):
        return
    delim = ';'
    paths_set = set()
    with open(name, 'r') as fin:
        reader = csv.reader(fin, delimiter=delim)
        reader.__next__()
        for row in reader:
            paths_set.add(row[0])
    return paths_set


def replace_csv(basic_path, paths_dict, log):
    n = 0
    corpus = basic_path.split('/')[-1]
    if corpus =='eng-rus':
        corpus = "multiparc_eng-rus"

    basic_name = "{0}/tables/{1}.csv".format(basic_path, corpus)
    if not os.path.exists(basic_name):
        log.write("Table {0} not found".format(basic_name))
        return 0
    back_name = basic_name+'.bak'
    os.rename(basic_name, back_name)
    delim = ';'
    change = 0
    put_err = False
    with open(back_name, 'r') as fin, open(basic_name, 'w') as fout:
        reader = csv.reader(fin, delimiter=delim)
        writer = csv.writer(fout,  delimiter=delim)
        writer.writerow(reader.__next__())
        for row in reader:
            p = row[0]
            for ext in ('.xml', '.xhtml'):
                if p.endswith(ext):
                    p = p[0:-len(ext)]
            if '\\' in p:
                p = p.replace('\\', '/')
            p_disk = paths_dict.get(p.lower(), None)
            if not p_disk:
                if not put_err:
                    log.write("paths from table {0} not found in disk:\n".format(corpus))
                    put_err = True
                log.write(p+'\n')
            else:
                if p_disk != p:
                    p = p_disk
                    n += 1
                del paths_dict[p.lower()]
            if p != row[0]:
                row[0] = p
                change += 1
            writer.writerow(row)
    #  os.remove(basic_name)

    if paths_dict:
        log.write("paths not found in table {0}\n".format(corpus))
        for s in paths_dict.values():
            log.write(s+'\n')
    if change:
        print("{0} lines changed".format(change))
    else:
        os.remove(basic_name)
        os.rename(back_name, basic_name)
    return change


corpuses = ("accent/accent_main", "accent/accent_stihi", "birchbark", "dialect", "main/standard", "main/source",
            "mid_rus", "multi", "multiparc/multiparc_rus", "multiparc/eng-rus", "murco", "old_rus", "orthlib", "paper",
            "para", "poetic", "regional_grodno/regional_grodno_bel", "regional_grodno/regional_grodno_rus", "school",
            "spoken")


def main():
    change = 0
    with open("err.log", "w") as log:
        for corpus in corpuses:
            print(corpus)
            root = os.path.join('/place/ruscorpora/corpora', corpus)
            if corpus == "multiparc/eng-rus":
                corpus = "multiparc_eng-rus"
            elif '/' in corpus:
                corpus = corpus.split('/')[-1]
            paths = get_paths(os.path.join(root, 'texts'))
            path_dict = {}
            media = corpus in ("multiparc_rus", "multiparc_eng-rus", "murco")
            for path in paths:
                if media:
                    path = os.path.dirname(path)
                path = path.replace('.xml', '')
                if path.startswith('./'):
                    path = path[2:]
                path_dict[path.lower()] = path
            change += replace_csv(root, path_dict, log)
    print("total {0} lines changed".format(change))


main()


