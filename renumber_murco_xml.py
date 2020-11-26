# -*- coding: utf-8 -*-
import sys
from pathlib import Path

r_path = '/place/ruscorpora/corpora/'
def make_elem(paths, n, is_src):
    if isinstance(n, int):
        n = str(n)
    if n.isdigit():
        n = n.rjust(3, '0')
    pref = '_tmp/' if is_src else '/'
    return "{0}{1}{2}_{3}{4}".format(paths[0], pref, paths[1], n, paths[2])


def make_pair(paths, s):
    return make_elem(paths, s[0],True), make_elem(paths, s[1],False)


def make_seq(ll):
    return range(int(ll[0]), int(ll[1])+1)

def renumber():
    corr_list = []
    if len(sys.argv) != 3:
        print("Wrong number of args")
        exit(1)
    paths = []
    with open(sys.argv[1]) as fin,open(sys.argv[2], "w") as f_out:
        f_out.write("set -ex\n")
        for l in fin:
            l = l.strip()
            if not l:
                continue
            if l.startswith('[') and l.endswith(']'):
                if paths:
                    for c_l in corr_list:
                        f_out.write("\cp {0} {1}\n".format(c_l[0], c_l[1]))
                    f_out.write("rm -rf {0}_tmp\n".format(paths[0]))
                corr_list = []
                path = l[1:-1]
                paths = path.split(',')
                if len(paths) != 3:
                    print("Wrong path", path)
                    exit(1)
                if not paths[1]:
                    paths[1] = paths[0].rsplit('/', 1)[-1]
                paths[0] = r_path+paths[0]+'/texts'
                f_out.write("mkdir -p {0}_tmp\n".format(paths[0]))
                f_out.write("cp -r {0}/* {1}_tmp\n".format(paths[0], paths[0]))
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
                    corr_list.append(make_pair(paths, (ll[0][0], ll[1][0])))
                else:
                    ss = zip(make_seq(ll[0]), make_seq(ll[1]))
                    corr_list += [make_pair(paths, s) for s in ss]
        for l in corr_list:
            f_out.write("\cp {0} {1}\n".format(l[0], l[1]))
        f_out.write("rm -rf {0}_tmp\n".format(paths[0]))

if __name__ == '__main__':
    renumber()
