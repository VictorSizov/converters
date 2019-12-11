# -*- Encoding: utf-8 -*-
"""
ConverterBasic - базовый класс для конвертера xml - документов.
ConverterWithSteps - базовый класс для отладочного "пошагового" конвертера xml - документов.
"""

from processor_basic import ProcessorBasic, fill_arg_for_processor
import os
import sys
from lxml import etree


class ConverterBasic(ProcessorBasic):
    def __init__(self, args):
        self.outpath = os.path.expanduser(args.outpath)
        self.outcode = args.outcode
        super(ConverterBasic, self).__init__(args)

    def process_file(self, inpfile):
        """ Обработка xml - дерева и запись его
        в выходной файл в соответствующей кодировке"""
        tree = super(ConverterBasic, self).process_file(inpfile)
        if tree is None:
            return
        try:
            outpath = self.outpath if self.outpath is not None else self.inppath
            outfile = os.path.join(outpath, inpfile)
            outdir = os.path.dirname(outfile)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            with open(outfile, 'w') as fout:
                fout.write('<?xml version="1.0" encoding="{0}"?>\n'.format(self.outcode))
                tree.write(fout, encoding=self.outcode, xml_declaration=False)
        except etree.LxmlError as e:
            self.wrong_docs += 1
            if self.line != -1:
                print >> sys.stderr, 'Error in', inpfile, 'line', self.line, ':', e.message


class ConverterWithSteps(ConverterBasic):
    """пошаговый конвертер"""
    def __init__(self, args):
        self.step_mode = args.step_mode
        self.step = None
        super(ConverterWithSteps, self).__init__(args)

    @staticmethod
    def get_steps():
        raise Exception('you should rewrite this function in derived class')

    def check_steps(self, val):
        """ проверка, должен ли выполняться шаг"""
        return self.step == -1 or self.step == val

    def process_step(self, inppath, outpath, err_file_name):
        self.wrong_docs = 0
        if self.step != -1:
            print 'step', self.step
            if err_file_name is not None and self.step < self.get_steps()-1:
                (self.err_file_name, ext) = os.path.splitext(err_file_name)
                self.err_file_name += str(self.step) + ext
            self.inppath = inppath + (str(self.step) if self.step > 0 else '')
            self.outpath = outpath if self.step == self.get_steps()-1 else inppath + str(self.step + 1)
        super(ConverterWithSteps, self).process()

    def process(self):
        """реализация пошаговой конверсии"""
        steps_num = self.get_steps()
        if self.step_mode < self.get_steps():
            self.step = self.step_mode
            self.process_step(self.inppath, self.outpath, self.err_file_name)
        else:
            if self.step_mode > self.get_steps():
                print>>sys.stderr, "too big step_mode value"
                return
            inppath = self.inppath
            outpath = self.outpath
            err_file_name = self.err_file_name
            for self.step in range(self.get_steps()):
                self.process_step(inppath, outpath, err_file_name)


def fill_arg_for_converter(description, action_description=None):
    parser = fill_arg_for_processor(description, action_description)
    parser.add_argument('--outpath', default=None)
    parser.add_argument('--outcode', choices=['utf-8', 'windows-1251'], default='utf-8')
    return parser
