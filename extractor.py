# -*- Encoding: utf-8 -*-
""" Создание урезанной копии корпуса из n документов с коррекцией таблицы <corpus>.csv """
import os
import argparse
from shutil import copyfile, copytree, rmtree
import time
import csv
import copy


def get_from_table(path):
    corpus = path.split('/')[-1]
    if corpus == 'eng-rus':
        corpus = 'multiparc_eng-rus'
    name = "{0}/tables/{1}.csv".format(path, corpus)
    if not os.path.exists(name):
        print("table {0} not found".format(name))
        return None
    delim = ';'
    paths_set = set()
    with open(name, 'r') as fin:
        reader = csv.reader(fin, delimiter=delim)
        reader.__next__()
        for row in reader:
            paths_set.add(row[0])
    return paths_set


def copy_tree(inp_path, out_path, copy_path):
    inp_path += copy_path
    out_path += copy_path
    if not os.path.exists(inp_path):
        return
    if not os.path.exists(out_path):
        copytree(inp_path, out_path)


def copy_paths(inp_path_root, out_path_root, paths_set):
    video_names = []
    for path in paths_set:
        inp_path = os.path.join(inp_path_root, 'texts', path)
        not_found = inp_path + '(.xml?) not found'
        if not os.path.exists(inp_path):
            inp_path += '.xml'
        if os.path.exists(inp_path):
            out_path = os.path.join(out_path_root, 'texts', path)
            out_dir = os.path.dirname(out_path)
            if os.path.isdir(inp_path):
                copy_tree(inp_path, out_path, '')
                inp_dir = os.path.dirname(inp_path)
                copy_tree(inp_dir, out_dir, '/table_acts')
                copy_tree(inp_dir, out_dir, '/table_gest')
                video_names.extend([os.path.splitext(f)[0] for f in os.listdir(inp_path)])
            else:
                out_path += '.xml'
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)
                copyfile(inp_path, out_path)
        else:
            print(not_found)
    return video_names


def copy_csv(inp_path, out_path, paths_set):
    paths_set_cp = copy.copy(paths_set)
    corpus = inp_path.split('/')[-1]
    if corpus == 'eng-rus':
        corpus = 'multiparc_eng-rus'
    inp_name = "{0}/tables/{1}.csv".format(inp_path, corpus)
    if not os.path.exists(inp_name):
        return
    out_name = "{0}/tables/{1}.csv".format(out_path, corpus)
    delim = ';'
    with open(inp_name, 'r') as fin, open(out_name, 'w') as fout:
        reader = csv.reader(fin, delimiter=delim)
        writer = csv.writer(fout,  delimiter=delim)
        writer.writerow(reader.__next__())
        for row in reader:
            if row[0] in paths_set_cp:
                writer.writerow(row)
                paths_set_cp.remove(row[0])
    if paths_set_cp:
        print("paths not found in table:")
        for s in paths_set_cp:
            print(s)


def copy_video(inp_path, out_path, video_names):
    paths_set_cp = set(copy.copy(video_names))
    inp_name = "{0}/tables/video_ids.csv".format(inp_path)
    if not os.path.exists(inp_name):
        return
    out_name = "{0}/tables/video_ids.csv".format(out_path)
    delim = ';'
    with open(inp_name, 'r') as fin, open(out_name, 'w') as fout:
        reader = csv.reader(fin, delimiter=delim)
        writer = csv.writer(fout,  delimiter=delim)
        writer.writerow(reader.__next__())
        for row in reader:
            p = os.path.splitext(row[0])[0]
            if p in video_names:
                writer.writerow(row)
                paths_set_cp.discard(p)
    if paths_set_cp:
        print("paths not found in videotable:")
        for s in paths_set_cp:
            print(s)


def add_names_list(paths_set, names_list):
    if not os.path.exists(names_list):
        print('file "', names_list, '" with document names not found"')
        exit(1)
    with open(names_list) as fin:
        for s in fin:
            paths_set.add(s[:-1])


def create_copy(inp_path, out_path, part, names_list):
    if os.path.exists(out_path):
        rmtree(out_path)
        time.sleep(.1)
    copy_tree(inp_path, out_path, "/meta")
    copy_tree(inp_path, out_path, "/tables")
    paths_set = set()
    if part != 0 or not names_list:
        paths_set = get_from_table(inp_path)
        if not paths_set:
            exit(1)
        if part != 0:
            lpaths = len(paths_set)
            bound = lpaths
            step = int(lpaths / part)
            if step > 0:
                if step * part < lpaths:
                    bound = step * part
                paths_set = set(list(paths_set)[:bound:step])
    if names_list:
        add_names_list(paths_set, names_list)
    return paths_set


def add_to_copy(out_path, names_list):
    if not os.path.exists(out_path):
        print("Can't add data to {0} because it not found")
        exit(1)
    paths_set = get_from_table(out_path)
    add_names_list(paths_set, names_list)
    return paths_set


def main():
    parser = argparse.ArgumentParser(description="extract data from corpus")
    parser.add_argument('corpus')
    parser.add_argument('part', type=int)
    parser.add_argument('--names_list', default=None)
    parser.add_argument('--add', default=False, action='store_true')
    parser_args = parser.parse_args()
    corpus = parser_args.corpus
    part = parser_args.part
    inp_path = '/place/ruscorpora/corpora/'+corpus
    if not os.path.exists(inp_path):
        print("wrong input path", inp_path)
        exit(1)
    out_path_root = '/place/ruscorpora/test_' + str(part) + '/corpora/'
    if not os.path.exists(out_path_root + '/tables'):
        copy_tree('/place/ruscorpora/corpora', out_path_root, '/tables')
    out_path = out_path_root + corpus
    names_list = parser_args.names_list
    if not parser_args.add:
        paths_set = create_copy(inp_path, out_path, part, names_list)
    else:
        paths_set = add_to_copy(out_path, names_list)
    copy_csv(inp_path, out_path, paths_set)
    video_names = copy_paths(inp_path, out_path, paths_set)
    if video_names:
        copy_video(inp_path, out_path, video_names)


main()
