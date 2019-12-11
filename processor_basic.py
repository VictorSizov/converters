# -*- Encoding: utf-8 -*-

"""
ProcessorBasic - базовый класс для обработчика xml - документов.
"""

from lxml import etree

import os
import sys
import time
import argparse


class ProcessorBasic(object):

    def __init__(self, args):
        # инициализация параметров:
        self.inppath = os.path.expanduser(args.inppath)  # входные данные (папка или файл)
        self.files = args.files  # имя файла со списком входных файлов
        self.err_file_name = args.err_report  # имя файла для ошибок
        self.action = args.action if hasattr(args, 'action') else ''  # действие (зарезервировано)
        self.line = -1
        self.inpname = ''
        self.errname = ''
        self.errline = -1
        self.wrong_docs = 0
        self.err_report = None

    def err_proc(self, mess):
        """ вывод сообщения об ошибке в соответствующий файл или stderr
        с указанием документа и строки, где возникла ошибка. """
        if self.err_report is None:  # если файл для вывода сообщения не проинициализирован
            try:

                self.err_report = open(self.err_file_name, 'w') if self.err_file_name is not None else sys.stderr
            except (OSError, IOError) as e:
                self.err_report = sys.stderr
                self.err_proc(self.err_file_name + ' open error, use sys.stderr instead')

        if self.errname == self.inpname:  # don't do message with same coords (document name and line) as previous
            if self.errline == self.line:
                return
        else:
            self.wrong_docs += 1
        self.errname = self.inpname
        self.errline = self.line
        if self.err_report is not None:
            inpname = self.inpname
            if len(inpname) > len(self.inppath) and inpname[:len(self.inppath)] == self.inppath:
                inpname = os.path.relpath(inpname, self.inppath)
            file_mess = ' in ' + inpname if inpname != '' else ''
            line_mess = ' line ' + str(self.line) if self.errline != -1 else ''
            print >> self.err_report, 'Error' + file_mess + line_mess+':', mess


    def process_lxml_tree(self, tree):
        """ обработка xml-дерева.
        В дочерних классах  должна быть реализация """
        raise Exception('you should rewrite this function in derived class')

    def process_file(self, inpfile):
        """ Получение дерева для xml-файла и вызов функции его обработки"""
        try:
            self.inpname = os.path.join(self.inppath, inpfile)
            tree = etree.parse(self.inpname)
            self.process_lxml_tree(tree)
            return tree
        except etree.LxmlError as e:
            self.wrong_docs += 1
            if self.line != -1:
                print >> sys.stderr, 'Error in', inpfile, 'line', self.line, ':', e.message
            return None

    def process(self):
        """ Получение списка xnl-файлов для обработки
            #Если --files не указан
                Если inppath - папка
                    то список формируется из файлов,
                    лежащих в inppath и ее подпапках.
                Если inppath - файл, то он один будет в списке
            Если --files указан,
                из файла с этим именем
                читаются имена файлов для обработки.
                inppath должен быть корневой папкой
                для файлов из списка с relative path.
            """
        d1 = time.clock()
        inppath = self.inppath
        if not os.path.exists(inppath):
            self.err_proc("No file or directory "+inppath+" found")
            return
        check_path = inppath
        if os.path.islink(inppath):
            check_path = os.path.realpath(inppath)
        if os.path.isfile(check_path):
            if self.files is not None:
                self.err_proc("if input is file name, --files is not valid")
                return
            self.process_file('')
        elif os.path.isdir(check_path):
            paths = []
            if self.files is None:
                # os.chdir(inppath)
                for root, dirs, files in os.walk(inppath, followlinks=True):
                    if files:
                        root = os.path.relpath(root, inppath)
                        paths += [os.path.join(root, f) for f in files if os.path.splitext(f)[1] in ('.xml', '.xhtml')]
            else:
                with open(self.files) as flist:
                    paths = [f if os.path.commonprefix([f, inppath]) != inppath else os.path.relpath(f, inppath)
                             for f in flist.read().splitlines()]
            nn = len(paths)
            i = 0
            for p in paths:
                i += 1
                if i % 250 == 0:
                    print "processed ", i, "total", nn
                self.process_file(p)
        else:
            self.err_proc("unknown input type")
            return
        d2 = time.clock()
        print 'processing time', d2-d1, 'sec'
        if self.wrong_docs > 0:
            print >> sys.stderr, "errors found in ", self.wrong_docs, " documents."
            print "errors found in ", self.wrong_docs, " documents. see", \
                self.err_file_name if self.err_file_name is not None else "sys.stderr"


def fill_arg_for_processor(description, action_description=None):
    """Вспомогательная функция для описания параметров программы """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('inppath')
    parser.add_argument('--files', default=None)
    parser.add_argument('--err_report', default=None)
    if action_description is None:
        action_description = {'default': None}
    parser.add_argument('--action', **action_description)
    return parser
