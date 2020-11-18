# -*- coding: utf-8 -*-
from lxml import etree
from processor_basic import ProcessorBasic, fill_arg_for_processor
from pathlib import Path
from collections import Counter
import os
import copy
import pathlib

from lxml_ext import LxmlExt
""" Вспомогательные программы      """
"""  1. Проверка китайских текстов    """
class FeatsChecker(ProcessorBasic):
    def __init__(self, args):
        super().__init__(args)


    def process_lxml_tree(self, tree):
        root = tree.getroot()
        for w in root.iter('w'):
            self.set_line_info(w)
            texts = w.xpath(".//text()")
            if not texts:
                self.err_proc("Empty wordform")
            if len(texts) > 1:
                self.err_proc("multiple wordform")
            if not texts[0]:
                self.err_proc("Empty wordform-2")
        return tree

    def put_info(self):
        '''
        if self.feats_loader.wrong:
            if '' in self.feats_loader.wrong:
                print("Empty!")
            print("Wrong feats: {0}".format(','.join(sorted(self.feats_loader.wrong))))

        with open(Path('~/Documents/china_gr.txt').expanduser(), 'w') as fout:
            fout.write("china feats:\n\n")
            fout.write('\n'.join(sorted(self.feats))+'\n')
            fout.write("china feat sets:\n\n")
            fout.write('\n'.join(sorted(self.feat_grs))+'\n')
        '''
        with open(Path('~/Documents/china_punct.txt').expanduser(), 'w') as fout:
            fout.write("china punct:\n\n")
            for nn in self.punct.most_common(100):
                fout.write('"{0}" - {1}\n'.format(nn[0], nn[1]))

'''
if __name__ == '__main__':
    parser = fill_arg_for_processor('feat checker')
    parser_args = parser.parse_args()
    feats_checker = FeatsChecker(parser_args)
    feats_checker.process()
    # feats_checker.put_info()
'''


"""  2. Проверка видеоклипов    """


""" Старая версия """
def cut_elements(arr, split_data, cut_data=None):
    for n, ss in enumerate(arr):
        sss = ss.split(split_data)
        if not cut_data or sss[-1] in cut_data:
            arr[n] = split_data.join(sss[:-1])
    return arr

''' Удаление расширения в списке клипов наш+yandex'''
def remove_ext_old():
    with open('/place/ruscorpora/corpora/tables/video/ruscorpora-video-mp4.dat') as f:
        video_names = [ss.split()[1] for ss in f if ss.split()[0] != '0']
    video_names = cut_elements(video_names, '.', ('avi', 'AVI', 'db', 'mp3', 'mp4', 'wav', 'wma', 'wmv', 'WMV'))
    with open('/place/ruscorpora/corpora/tables/video/ruscorpora-video-yandex-mp4.dat') as f:
        video_names1 = [ss for ss in f]
        video_names1 = cut_elements(video_names1, '.', ('avi', 'AVI', 'db', 'mp3', 'mp4', 'wav', 'wma', 'wmv', 'WMV'))
        zero_len = [ss.split()[1] for ss in video_names1 if ss.split()[0] == '0']
        video_names1 = [ss.split()[1] for ss in video_names1 if ss.split()[0] != '0']
    video_names = sorted(list(set(video_names1).union(video_names)))
    ''' Составление списка нормальных клипов и клипов 0-й длины. '''
    with open('/place/ruscorpora/corpora/tables/video/video.dat', 'w') as f:
        for ss in video_names:
            f.write(ss+'\n')
    with open('/place/ruscorpora/corpora/tables/video/zero_len.dat', 'w') as f:
        for ss in zero_len:
            f.write(ss+'\n')


def del_doubles(inpname, outname):
    pp = '/place/ruscorpora/corpora/murco/tables/'
    with open(pp+inpname) as finp, open(pp+outname,"w") as fout:
        doubles = set()
        for ss in finp:
            sss = '\t'.join(ss.split(';')[:-1])
            if sss in doubles:
                continue
            doubles.add(sss)
            fout.write(ss)

def del_doubles2(inpname, outname):
    pp = '/place/ruscorpora/corpora/murco/tables/'
    with open(pp+inpname) as finp, open(pp+outname,"w") as fout:
        doubles = set()
        for ss in finp:
            sss = remove_extra(ss.split(';')[0])
            if sss in doubles:
                continue
            doubles.add(sss)
            fout.write(ss)


""" Новая версия                             """
""" Удаление лишнего расширения из имени файла"""
def remove_extra(st):
    st = os.path.basename(st)
    ss_split = os.path.splitext(st)
    if ss_split[1].lower() in ('.avi', '.db', '.mp3', '.mp4', '.wav', '.wma', '.wmv'):
        st = ss_split[0]
    return st

path = '/place/ruscorpora/corpora/tables/video/'

""" Получение корректного описания ошибок в файлах с описанием duration """
def err_proc(name_in, name_out):
    with open(path + name_in) as f_in, open(path + name_out,"w") as f_out:
        for stro in f_in:
            stro_split = stro.split()
            l = len(stro_split)
            if l > 2:
                for st in stro_split[:-2]:
                    f_out.write("{0}\terr\n".format(remove_extra(st)))
            if stro_split[-1][0] == '/':
                f_out.write("{0}\terr\n{1}\terr\n".format(remove_extra(stro_split[-2]), remove_extra(stro_split[-1])))
            else:
                f_out.write("{0}\t{1}\n".format(remove_extra(stro_split[-2]), stro_split[-1]))


# преобразование duration в float
def get_float(data):
    return float(data) if data not in ('-', 'err') else float(-1)

""" Склейка информации об одноименных клипах из  двух папокк """
def join(name_1, name_2, name_res):
    with open(path + name_1) as f_in1, open(path + name_2) as f_in2, open(path + name_res, "w") as f_out:
        dict_res = {}
        for st in f_in1:
            st_split = st.split()
            dict_res[st_split[0]] = [st_split[1], '-']
        for st in f_in2:
            st_split = st.split()
            dict_res.setdefault(st_split[0], ['-', '-'])[1] = st_split[1]

        for key, value in sorted(dict_res.items()):
            f_out.write("{0}\t{1}\t{2}\n".format(key, value[0], value[1]))

""" Сравнение duration двух клипов, преобразование duration в симв. значения """
def cmp_duration(values,n):
    t1 = get_float(values[n])
    t2 = get_float(values[n+1])
    if t1 != -1.:
        values[n] = '+'
        if t2 != -1:
            values[n+1] = '+'
            tt = t1 - t2
            if tt > 0.2:
                values[n+1] = 'l'
            if tt < -0.2:
                values[n] = 'l'
    elif t2 != -1:
        values[n+1] = '+'
    return '\t'.join(values)


def time_proc(inp_name, out_name):
    with open(path + inp_name) as f_in, open(path + out_name, "w") as f_out:
        for st in f_in:
            f_out.write(cmp_duration(st.split(), 1) + '\n')


def put_dict(dict_, out_name,  head):
    with open(path + out_name, "w") as f_out:
        f_out.write(head)
        for key, value in sorted(dict_.items()):
            f_out.write("{0}\t{1}\n".format(key, value))

def classify(inp1, inp2, out1, out2, out3):
    dict1 = {}  # Список задействованных клипов
    with open(path + inp1) as f_in1:
        n=0
        for st in f_in1:
            st_split = st.split()
            dict1[st_split[1]] = st_split[0]
            n+=1
    dict2 = {}  # Список задействованных не найденных/битых клипов
    dict3 = {}  # Список задействованных клипов с проблемами
    dict4 = {}  # Список незадействованных клипов.
    with open(path + inp2) as f_in1:
        for st in f_in1:
            st_split = st.split()
            key = st_split[0]
            value = '\t'.join(st_split[1:])
            ret = dict1.get(key, None)
            if ret is None: # клип не задействован
                dict4[key] = value
            else:
                if value in ('err\t-', '-\terr'):  # битый клип
                    dict2[key] = ret + '\tбитый '+('(yandex)' if value == '-\terr' else '(наш)')
                elif value != '+\t+':   # клип с проблемами
                    dict3[key] = value
                del dict1[key]
    for key, value in dict1.items():
        dict2[key] = value + '\tне найден'
    put_dict(dict2, out1, "clip id\tname\tinfo\n")
    put_dict(dict3, out2, "clip id\tstd\tyandex\n")
    put_dict(dict4, out3, "clip id\tstd\tyandex\n")

def print_doubles(key, values, f_err):
    st = "\t".join(sorted(values))
    f_err.write("{0}\t{1}\n".format(key, st))

def doubles(inp_name,out_name,err_name):
    dict1 = {}
    dict2 = {}
    dd = 0
    with open(path + inp_name) as f_in1:
        for st in f_in1:
            st_split = st.split()
            if len(st_split) != 2:
                raise Exception("Logic error")
            s0 = remove_extra(st_split[0])
            s1 = st_split[1]
            if s1 == 'null':
                continue
            set1=dict1.setdefault(s0, set())
            if s1 in set1:
                print(s0,s1)
                dd+=1
            set1.add(s1)
            dict2.setdefault(s1, set()).add(s0)
    with open(path + out_name, "w") as f_out, open(path + err_name, "w") as f_err:
        for key, values in sorted(dict1.items()):
            values = sorted(values)
            for v in values:
                f_out.write("{0}\t{1}\n".format(key, v))
            if len(values) > 1:
                print_doubles(key, values, f_err)
        for key, values in sorted(dict2.items()):
            if len(values) > 1:
                print_doubles(key, values, f_err)
    print(dd)

def check_doubles(doubles_raw, duration_info, doubles):
    dict1 = {}
    with open(path + duration_info) as f_in1:
        for st in f_in1:
            st_split = st.split()
            if len(st_split) != 2:
                raise Exception("Logic error")
            dict1[st_split[0]] = st_split[1]
    with open(path + doubles_raw) as f_in2, open(path + doubles, "w") as f_out:
        for st in f_in2:
            st_split = st.split()
            st_split.append(dict1[st_split[1]])
            st_split.append(dict1[st_split[2]])
            f_out.write(cmp_duration(st_split, 3)+'\n')


if __name__ == '__main__':
    # err_proc('duration_info_raw.txt', 'duration_info.txt')
    # err_proc('duration_info_yandex_raw.txt', 'duration_info_yandex.txt')
    # join('duration_info.txt', 'duration_info_yandex.txt', 'duration_info_tmp_res.txt')
    # time_proc('duration_info_tmp_res.txt', 'duration_info_res.txt')
    # doubles('video_ids_raw.csv', 'video_ids.csv', 'doubles_raw.txt')
    # classify('video_ids.csv','duration_info_res.txt', 'not_found.txt', 'problems.txt','not_used.txt')
    # check_doubles('doubles_raw.txt', 'duration_info_yandex.txt', 'doubles.txt' )
    del_doubles2('video_ids.csv','video_ids_n.csv')





