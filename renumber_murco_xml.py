# -*- coding: utf-8 -*-
import sys
from pathlib import Path

r_path = '/place/ruscorpora/'

def make_elem(paths, n, is_src):
    if isinstance(n, int):
        n = str(n)
    if n.isdigit():
        n = n.rjust(3, '0')
    pref = '_tmp/' if is_src else '/'
    return "{0}{1}{2}{3}{4}".format(paths[0], pref, paths[1], n, paths[2])


def make_pair(paths, s):
    return make_elem(paths, s[0], True), make_elem(paths, s[1], False)


def make_seq(ll):
    return range(int(ll[0]), int(ll[1])+1)

def dump(paths, corr_list, f_out):
    if paths:
        for c_l in corr_list:
            c_l = make_pair(paths, c_l)
            f_out.write("\cp {0} {1}\n".format(c_l[0], c_l[1]))
        if paths[0].find('finalized/') == -1:
            f_out.write("rm -rf {0}_tmp\n".format(paths[0]))
            f_out.write("git add {0}\n".format(paths[0]))
            f_out.write("git commit\n")


def put_head(paths, f_out):
    f_out.write("mkdir -p {0}_tmp\n".format(paths[0]))
    f_out.write("cp -r {0}/* {1}_tmp\n".format(paths[0], paths[0]))



def renumber(name: str):
    corr_list = []
    paths_i = []
    paths_o = []
    base = name.rsplit('.', 1)[0]
    with open(name) as fin, open(base + '.sh', "w") as f_out1, open(base + '_f.sh', "w")as f_out2:
        f_out1.write("set -ex\n")
        f_out2.write("set -ex\n")
        for l in fin:
            l = l.strip()
            if not l:
                continue
            if l.startswith('[') and l.endswith(']'):  # [murco|dirs|file_templ|ext]
                dump(paths_i, corr_list, f_out1)
                dump(paths_o, corr_list, f_out2)
                corr_list = []
                path = l[1:-1]
                paths = path.split('|')
                if len(paths) != 4:
                    print("Wrong path", path)
                    exit(1)
                if not paths[2]:
                    pp = paths[1].rsplit('/', 1)
                    paths[1] += '/texts'
                    paths[2] = pp[1] + '_'
                paths_i = ["{0}corpora/{1}/texts/{2}".format(r_path, paths[0], paths[1]), paths[2], paths[3]]
                paths_o = ["{0}texts/finalized/{1}/{2}".format(r_path, paths[0], paths[1]), paths[2], paths[3]]
                put_head(paths_i, f_out1)
                put_head(paths_o, f_out2)

            else:
                ll = l.split('->')
                if len(ll) != 2:
                    print(l, ": wrong format")
                    return []
                for i in (0, 1):
                    ll[i] = ll[i].split('...')
                l_len = len(ll[0])
                if not l_len or l_len != len(ll[1]):
                    print(l, ": wrong format")
                    return []
                if l_len == 1:
                    corr_list.append((ll[0][0], ll[1][0]))
                else:
                    ss = zip(make_seq(ll[0]), make_seq(ll[1]))
                    corr_list += [s for s in ss]
        dump(paths_i, corr_list, f_out1)
        dump(paths_o, corr_list, f_out2)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Wrong number of args")
        exit(1)
    renumber(sys.argv[1])
