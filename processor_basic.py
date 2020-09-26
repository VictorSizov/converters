# -*- Encoding: utf-8 -*-

"""
ProcessorBasic - базовый класс для обработчика xml - документов.
"""

from lxml import etree

import os
import re
import time
import argparse
from error_processor import ErrorProcessor, ProgramTerminated, expanduser
from collections import Counter


class ProcessorBasic(object):

    valid_extensions = ('.xml', '.xhtml')

    def __init__(self, args):
        # инициализация параметров:
        self.error_processor = ErrorProcessor(args.__dict__)
        self.inppaths = expanduser(args.inppath)  # входные данные (папка или файл)
        self.inppath = ''
        self.files = expanduser(args.files)  # имя файла со списком входных файлов
        self.filter = args.filter
        self.action = args.action if hasattr(args, 'action') else ''  # действие (зарезервировано)
        self.line = -1
        self.inpname = None
        self.outpath = expanduser(args.outpath)
        self.outcode = 'utf-8'
        self.rewrite = args.rewrite
        self.tag_counter_name = expanduser(args.tag_counter) if hasattr(args, 'tag_counter') else None
        self.tag_counter = Counter() if self.tag_counter_name else None

    def count_mess(self, mess, num=1):
        self.error_processor.count_mess(mess, num)

    def fatal_error(self, mess):
        self.error_processor.fatal_error(mess)

    # def err_proc_simple(self, mess):
    #   self.error_processor.proc_message_basic(mess)

    def err_proc(self, mess, example=''):
        """ вывод сообщения об ошибке в соответствующий файл или stderr
        с указанием документа и строки, где возникла ошибка. """
        self.error_processor.proc_message(mess, self.inpname, self.line, example)

    def lxml_err_proc(self, lxml_error):
        for entry in lxml_error.error_log:
            self.error_processor.proc_message(entry.message, entry.filename, entry.line)
        etree.clear_error_log()

    @staticmethod
    def is_empty(text):
        return text is None or text == '' or text.isspace()

    @staticmethod
    def nostructured(elem):
        return elem.tag is etree.PI or elem.tag is etree.Comment

    def set_line_info(self, elem=None):
        if elem is None or elem.tag is etree.PI or elem.tag is etree.Comment:
            self.line = -1
        else:
            self.line = elem.sourceline

    def process_lxml_tree(self, tree):
        for elem in tree.getroot().iter():
            tmp = sorted(elem.items())
            elem.attrib.clear()
            elem.attrib.update(tmp)
        return tree

    def process_file(self, inpfile):
        """ Получение дерева для xml-файла и вызов функции его обработки
            если inpfile - relative path, он конкатенируются с inppath
        """
        self.line = -1
        inpname = os.path.join(self.inppath, inpfile) if inpfile != '' else self.inppath
        try:
            tree = etree.parse(inpname)
            self.inpname = inpname
            self.error_processor.err_num_doc = 0
            tree = self.process_lxml_tree(tree)
            self.inpname = ""
            if not self.outpath:
                if not self.rewrite:
                    return True
                self.outpath = self.inppath
            outfile = os.path.join(self.outpath, inpfile) if inpfile != '' else self.outpath
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            tree.write(outfile, encoding='utf-8', xml_declaration=True)
            return True
        except (OSError, IOError) as e:
            self.error_processor.proc_message("file open/reading error '{0}'".format(inpname))
            self.error_processor.wrong_docs[inpname] += 1
        except etree.LxmlError as e:
            self.lxml_err_proc(e)
        return False

    def get_paths(self, inppath):
        """ Получение списка xnl-файлов для обработки
            Если параметер --files был указан,
                из файла с этим именем читается список файлов для обработки.
            Если --files  не указан или файл с этим именем не содержит данных,
                то список формируется из файлов, лежащих в inppath и ее подпапках
                и имеющих расширение ('.xml', '.xhtml')
            """
        paths = []
        if self.files is not None:
            try:
                with open(self.files) as flist:
                    paths = [f if os.path.commonprefix([f, inppath]) != inppath else os.path.relpath(f, inppath)
                             for f in flist.read().splitlines()]
            except (OSError, IOError) as e:
                self.fatal_error("can't opens {0} file (file list)".format(self.files))
        if not paths:
            for root, dirs, files in os.walk(inppath, followlinks=True):
                parts = os.path.split(root)
                if parts[-1] == '.svn':
                    continue
                if files:
                    root = os.path.relpath(root, inppath)
                    paths += [os.path.join(root, f) for f in files if os.path.splitext(f)[1] in self.valid_extensions]
        if self.filter:
            try:
                ff = re.compile(self.filter)
                paths = [path for path in paths if ff.match(path)]
            except re.error as e:
                self.fatal_error('error "' + e.message + '"in regular expression "' + self.filter)

        print(len(paths), "file(s) found")
        return paths

    def process(self):
        # type: () -> bool
        """ Получение данных для обработки, обработка и сообщение об ошибках
            Если inppath - папка (или линк, указывающий на папку)
                tо список формируется методом self.get_paths()
                Далее файлы из списка в цикле обрабатываются self.process_file()
            Если inppath - файл, то он один будет обработан self.process_file()
        """
        try:
            d1 = time.perf_counter()
            self.error_processor.load_ignore_mess()
            for self.inppath in self.inppaths.split(';'):
                inppath = self.inppath
                if not os.path.exists(inppath):
                    self.fatal_error("No file or directory "+inppath+" found")
                check_path = inppath
                if os.path.islink(inppath):
                    check_path = os.path.realpath(inppath)
                if os.path.isfile(check_path):
                    if self.files is not None:
                        self.fatal_error("if input is file name, --files is not valid")
                    self.process_file('')
                elif os.path.isdir(check_path):
                    paths = self.get_paths(inppath)
                    nn = len(paths)
                    i = 0
                    for p in paths:
                        i += 1
                        if i % 250 == 0:
                            print("processed ", i, "total", nn)
                        self.process_file(p)
                else:
                    self.fatal_error("unknown input type")
            self.error_report(d1)
            return True
        except ProgramTerminated:
            return False

    def error_report(self, d1):
        d2 = time.perf_counter()
        print('processing time', d2 - d1, 'sec')
        self.error_processor.report()

    def print_tag_stat(self):
        if self.tag_counter_name:
            with open(self.tag_counter_name, "w", encoding="utf8") as f:
                for stat in self.tag_counter.most_common():
                    f.write("tag:{0} - {1} times\n".format(stat[0], stat[1]))

def fill_arg_for_processor(description, action_description=None, default_rewrite=False):
    """Вспомогательная функция для описания параметров программы """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('inppath')
    parser.add_argument('--files', default=None)
    parser.add_argument('--filter', default=None)
    parser.add_argument('--err_report', default=None)
    parser.add_argument('--stat', default=None)
    parser.add_argument('--outpath', default=None)
    parser.add_argument('--tag_counter', default=None)
    parser.add_argument('--rewrite', default=default_rewrite, action='store_true')
    parser.add_argument('--limit', type=int, default=-1)
    parser.add_argument('--limit_doc', type=int, default=-1)


    if action_description is None:
        action_description = {'default': None}
    parser.add_argument('--action', **action_description)
    return parser


class Normalizer(ProcessorBasic):
    def process_lxml_tree(self, tree):
        for elem in tree.getroot().iter():
            tmp = sorted(elem.items())
            elem.attrib.clear()
            elem.attrib.update(tmp)
            if self.tag_counter_name:
                self.tag_counter[elem.tag] +=1
        return tree


if __name__ == '__main__':
    parser = fill_arg_for_processor('normalizer')
    parser_args = parser.parse_args()
    normalizer = Normalizer(parser_args)
    normalizer.process()
    normalizer.print_tag_stat()
