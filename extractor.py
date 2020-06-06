# -*- Encoding: utf-8 -*-
""" Создание урезанной копии корпуса из n документов с коррекцией таблицы <corpus>.csv """
import os
import sys
from shutil import copyfile, copytree,rmtree
import time
import csv

def get_paths(inppath):
    paths = []
    valid_extensions = ('.xml', '.xhtml','.tgt')
    for root, dirs, files in os.walk(inppath, followlinks=True):
        parts = os.path.split(root)
        if parts[-1] == '.svn':
            continue
        if files:
            root = os.path.relpath(root, inppath)
            paths += [os.path.join(root, f) for f in files if os.path.splitext(f)[1] in valid_extensions]
    return paths


def copy_dir(inp_base_path, out_base_path, proc_path, part):
    inp_base_path += proc_path
    if not os.path.exists(inp_base_path):
        return
    out_base_path += proc_path
    if os.path.exists(out_base_path):
        rmtree(out_base_path)
        time.sleep(.1)
    paths = get_paths(inp_base_path)
    if part != 0:
        lpaths = len(paths)
        bound = lpaths
        step = lpaths / part
        if step > 0:
            if step * part < lpaths:
                bound = step * part
            paths = paths[:bound:step]
    for p in paths:
        out_path = os.path.join(out_base_path, p)
        out_dir = os.path.dirname(out_path)
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        copyfile(os.path.join(inp_base_path, p), out_path)
    return paths


def copy_tree(inp_path, out_path, copy_path):
    inp_path += copy_path
    out_path += copy_path
    if not os.path.exists(inp_path):
        return
    if os.path.exists(out_path):
        if os.path.exists(out_path):
            rmtree(out_path)
            time.sleep(.1)
    copytree(inp_path, out_path)
    return out_path


def correct_csv(inp_path, out_path, corpus, paths):
    corpus = corpus.split('/')[-1]
    inp_name = "{0}/tables/{1}.csv".format(inp_path, corpus)
    if not os.path.exists(inp_name):
        return
    out_name = "{0}/tables/{1}.csv".format(out_path, corpus)
    tab_delim = ['poetic']
    paths_set = {p.split('.')[0] for p in paths}
    delim = ';'
    with open(inp_name, 'r') as fin, open(out_name, 'w') as fout:
        reader = csv.reader(fin, delimiter=delim)
        writer = csv.writer(fout,  delimiter=delim)
        writer.writerow(reader.__next__())
        for row in reader:
            row_0 = row[0].split('.')[0]
            if row_0 in paths_set:
                writer.writerow(row)
                paths_set.remove(row_0)
    if len(paths_set) > 0:
        paths_set = paths_set


argc = len(sys.argv)
if argc < 3:
    print("Wrong args number -", argc)
    exit(1)
corpus = sys.argv[1]
try:
    part = int(sys.argv[2])
except ValueError:
    print("argument should be integer")
    exit(1)

inp_path = '/place/ruscorpora/corpora/'+corpus
if not os.path.exists(inp_path):
    print("wrong input path", inp_path)
out_path = '/place/ruscorpora/test_' + str(part) + '/corpora/' + corpus
if argc == 3:
    paths = copy_dir(inp_path, out_path, "/texts", part)
elif sys.argv[3] == "--correct":
    paths = get_paths(out_path+'/texts')

copy_tree(inp_path, out_path, "/tables")
copy_tree(inp_path, out_path, "/meta")
correct_csv(inp_path, out_path, corpus, paths)
