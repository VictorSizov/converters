# -*- Encoding: utf-8 -*-
"""
ConverterBasic - базовый класс для конвертера xml - документов.
ConverterWithSteps - базовый класс для отладочного "пошагового" конвертера xml - документов.
"""

from processor_basic import ProcessorBasic, fill_arg_for_processor, ProgramTerminated, expanduser
import os
import sys
from lxml import etree
import time


class ConverterBasic(ProcessorBasic):
    def __init__(self, args):
        self.outpath = expanduser(args.outpath)
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
        except (OSError, IOError) as e:
            self.fatal_error("can't write  output file " + outfile)
        except etree.LxmlError as e:
            self.lxml_err_proc(e)


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

    def process_step(self, inppath, outpath):
        if self.step != -1:
            print 'step', self.step
            self.inppath = inppath + (str(self.step) if self.step > 0 else '')
            step_str = str(self.step + 1) if self.step < self.get_steps()-1 else ''
            self.error_processor.err_report_step(step_str)
            self.outpath = outpath if self.step == self.get_steps()-1 else inppath + str(self.step + 1)
        if not super(ConverterWithSteps, self).process():
            raise ProgramTerminated()

    def process_steps(self, range_data):
        inppath = self.inppath
        outpath = self.outpath
        for self.step in range_data:
            self.process_step(inppath, outpath)

    def check_step_str(self, step_str, mess_prefix=''):
        # type: (str, str) -> int
        try:
            step = int(step_str)
        except ValueError:
            self.fatal_error(mess_prefix + 'step_mode is not convertable to int')
        if step < -1 or mess_prefix != '' and step == -1:
            self.fatal_error( mess_prefix + 'step_mode wrong value')
        if step > self.get_steps():
            self.fatal_error(mess_prefix + 'step_mode is too big')
        return step

    def error_report(self, d1): # ignore error_report call in parent
        d2 = time.clock()
        print 'step processing time', d2 - d1, 'sec'

    def process(self):
        """реализация пошаговой конверсии
        можно указать диапазон <low bound>-<upper bound>
        или '-1' - без вывода промежуточных результатов
        """
        try:
            d1 = time.clock()
            if self.step_mode == 'all':
                self.step_mode = str(self.get_steps())
            steps = self.step_mode.split('-') if self.step_mode[0] !='-' else [self.step_mode]
            if len(steps) > 2:
                self.fatal_error("step_mode value wrong format")
            if len(steps) == 2:
                step0 = self.check_step_str(steps[0], 'lower bound of ')
                step1 = self.check_step_str(steps[1], 'upper bound of ')
                self.process_steps(range(step0, step1))
            else:
                step = self.check_step_str(steps[0])
                if step < self.get_steps():
                    self.step = step
                    self.process_step(self.inppath, self.outpath)
                else:
                    self.process_steps(range(self.get_steps()))
            super(ConverterWithSteps, self).error_report(d1)
            return True
        except ProgramTerminated:
            return False


class Normalizer(ConverterBasic):
    def process_lxml_tree(self, tree):
        for elem in tree.getroot().iter():
            tmp = sorted(elem.items())
            elem.attrib.clear()
            elem.attrib.update(tmp)


def fill_arg_for_converter(description, action_description=None):
    parser = fill_arg_for_processor(description, action_description)
    parser.add_argument('--outpath', default=None)
    parser.add_argument('--outcode', choices=['utf-8', 'windows-1251'], default='utf-8')
    return parser


if __name__ == '__main__':
    parser = fill_arg_for_converter('normalizer')
    parser_args = parser.parse_args()
    normalizer = Normalizer(parser_args)
    normalizer.process()
