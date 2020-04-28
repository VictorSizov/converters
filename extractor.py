import os
import sys
from shutil import copyfile, copytree,rmtree
import time
import csv


def copy_dir(inp_base_path, out_base_path, proc_path, part):
    inp_base_path += proc_path
    if not os.path.exists(inp_base_path):
        return
    out_base_path += proc_path
    if os.path.exists(out_base_path):
        rmtree(out_base_path)
        time.sleep(.1)
    os.chdir(inp_base_path)
    paths = []
    for root, dirs, files in os.walk('.'):
        if files:
            root = root[2:]
            paths += [os.path.join(root, f) for f in files]
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
    delim = '\t' if corpus == 'poetic' else ';'
    with open(inp_name, 'rb') as fin, open(out_name, 'wb') as fout:
        reader = csv.reader(fin, delimiter=delim)
        writer = csv.writer(fout,  delimiter=delim)
        writer.writerow(reader.next())
        for row in reader:
            row_0 = row[0].split('.')[0]
            if row_0 in paths_set:
                writer.writerow(row)
                paths_set.remove(row_0)
    if len(paths_set) > 0:
        paths_set = paths_set

argc = len(sys.argv)
if argc < 3:
    print "Wrong args number -", argc
    exit(1)
corpus = sys.argv[1]
try:
    part = int(sys.argv[2])
except ValueError:
    print "argument should be integer"
    exit(1)
# code = "windows-1251" if "-1251" in sys.argv else "utf-8"

inp_path = '/place/ruscorpora/corpora/'+corpus
if not os.path.exists(inp_path):
    print "wrong input path", inp_path
out_path = '/place/ruscorpora/test_' + str(part) + '/corpora/' + corpus
paths = copy_dir(inp_path, out_path, "/texts", part)
copy_tree(inp_path, out_path, "/tables")
copy_tree(inp_path, out_path, "/meta")
correct_csv(inp_path, out_path, corpus, paths)
